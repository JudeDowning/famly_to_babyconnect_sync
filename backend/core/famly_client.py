"""
Famly client (scraping).
------------------------

This module contains a thin wrapper around Playwright to:

- Launch a browser context (headless or not, depending on config)
- Log into Famly using email/password
- Navigate to the relevant activity view
- Extract a list of RawFamlyEvent objects
"""

from __future__ import annotations

from typing import List, Optional
import re
import logging
from datetime import datetime, date, time, timedelta

from playwright.sync_api import sync_playwright

from .config import FAMLY_PROFILE_DIR, HEADLESS
from .normalisation import RawFamlyEvent
from .event_mapping import normalize_famly_title

FAMLY_LOGIN_URL = "https://app.famly.co/#/login"

EMAIL_SELECTOR = "#email"
PASSWORD_SELECTOR = "#password"
LOGIN_BUTTON_SELECTOR = "#loginSubmit"

# Activity page selectors
DAY_SELECTOR = "div.ActivityDay"
DAY_HEADING_SELECTOR = "h3"
EVENT_SELECTOR = "div.Event"
EVENT_CONTENT_SELECTOR = "[data-e2e-class='event-content']"
EVENT_TITLE_SELECTOR = "[data-e2e-class='event-title']"
EVENT_DETAIL_LINES_SELECTOR = "small"

# Child selection
CHILD_ID = "4b0ce49e-6393-4c65-97ee-9c80ec71b177"  # TODO: move to env/config
CHILD_LINK_SELECTOR = f"a[data-e2e-id='NavigationGroup-Child-{CHILD_ID}']"
CHILD_NAME_SELECTOR = "#personProfile h2.title-test-marker"

logger = logging.getLogger(__name__)


class FamlyClient:
    def __init__(self, email: str, password: str) -> None:
        self.email = email
        self.password = password

    def login_and_scrape(self, days_back: int = 0) -> List[RawFamlyEvent]:
        """
        Main entrypoint: log into Famly (if necessary) and return a list of
        raw scraped events.

        In development, set HEADLESS = False to watch the flow and tweak selectors.
        """
        events: List[RawFamlyEvent] = []
        entry_day_limit = max(0, days_back)
        reference_date = datetime.now().date()

        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(FAMLY_PROFILE_DIR),
                headless=HEADLESS,
            )
            page = browser.new_page()

            # 1. Go to login page
            logger.info("Famly scrape: navigating to login page")
            page.goto(FAMLY_LOGIN_URL, wait_until="networkidle")

            # 2. If login fields are visible, login; otherwise assume already logged in
            if page.is_visible(EMAIL_SELECTOR):
                logger.info("Famly scrape: entering credentials")
                page.fill(EMAIL_SELECTOR, self.email)
                page.fill(PASSWORD_SELECTOR, self.password)
                page.click(LOGIN_BUTTON_SELECTOR)
                page.wait_for_load_state("networkidle")
                logger.info("Famly scrape: login submitted, waiting for dashboard")
            else:
                logger.info("Famly scrape: login form not visible, assuming existing session")

            # At this point we should be on /account/feed/me

            # 3. Click the child icon/link in the sidebar
            logger.info("Famly scrape: selecting child link %s", CHILD_LINK_SELECTOR)
            page.wait_for_selector(CHILD_LINK_SELECTOR)
            page.click(CHILD_LINK_SELECTOR)

            # 4. Wait for navigation to child's activity feed
            logger.info("Famly scrape: waiting for child activity feed to load")
            page.wait_for_load_state("networkidle")
            page.wait_for_selector(CHILD_NAME_SELECTOR, timeout=10000)
            page.wait_for_selector(DAY_SELECTOR, timeout=10000)

            # 4b. Read child name from the profile header
            child_full_name = ""
            child_first_name = ""
            try:
                child_name_el = page.query_selector(CHILD_NAME_SELECTOR)
                if child_name_el:
                    child_full_name = child_name_el.inner_text().strip()
                    if child_full_name:
                        child_first_name = child_full_name.split()[0]
                logger.info("Famly scrape: detected child name %s", child_full_name or "Unknown")
            except Exception:
                # Non-fatal - we'll just leave child name blank if this fails
                logger.exception("Famly scrape: failed to read child name")
                pass
                
            # 5. Scrape days and events
            logger.info("Famly scrape: collecting day blocks")
            day_blocks = page.query_selector_all(DAY_SELECTOR)
            logger.info("Famly scrape: found %d day blocks", len(day_blocks))

            days_included = 0

            for day_block in day_blocks:
                # e.g. "Monday, Dec 1"
                day_heading_el = day_block.query_selector(DAY_HEADING_SELECTOR)
                day_label = (
                    day_heading_el.inner_text().strip()
                    if day_heading_el
                    else ""
                )
                day_date = self._parse_day_label(day_label, reference_date)

                event_blocks = day_block.query_selector_all(EVENT_SELECTOR)
                if not event_blocks:
                    continue

                for ev_block in event_blocks:
                    content = ev_block.query_selector(EVENT_CONTENT_SELECTOR)
                    if not content:
                        continue

                    title_el = content.query_selector(EVENT_TITLE_SELECTOR)
                    if not title_el:
                        continue

                    raw_title = title_el.inner_text().strip()
                    event_title = normalize_famly_title(raw_title)

                    # Collect detail lines and split entries
                    detail_lines = self._extract_detail_lines(content)
                    entry_blocks = self._split_entry_blocks(detail_lines)

                    if not entry_blocks:
                        entry_blocks = [detail_lines]

                    for idx, entry in enumerate(entry_blocks):
                        entry_text = " | ".join(entry) if entry else ""
                        time_str = self._extract_time_string([day_label] + entry)
                        logger.debug(
                            "Famly scrape: entry %s - %s (%s)",
                            day_label,
                            event_title,
                            time_str,
                        )

                        event_dt = self._build_event_datetime(day_date, time_str)

                        preferred_name = child_full_name or child_first_name or "Unknown"
                        events.append(
                            RawFamlyEvent(
                                child_name=preferred_name.strip(),
                                event_type=event_title,
                                time_str=time_str,
                                raw_text=f"{day_label} - {event_title}: {entry_text or event_title}",
                                raw_data={
                                    "day_label": day_label,
                                "detail_lines": entry,
                                "child_full_name": child_full_name,
                                "day_date_iso": day_date.isoformat() if day_date else None,
                                "event_datetime_iso": event_dt.isoformat() if event_dt else None,
                                "original_title": raw_title,
                                "entry_index": idx,
                            },
                                event_datetime_iso=event_dt.isoformat() if event_dt else None,
                            )
                        )
            browser.close()
            logger.info("Famly scrape: finished with %d events", len(events))

        events.sort(key=lambda ev: ev.event_datetime_iso or "", reverse=True)
        limited = self._limit_events_by_entry_days(events, entry_day_limit)
        limited.sort(key=lambda ev: ev.event_datetime_iso or "")
        return limited

    def _extract_time_string(self, lines: list[str]) -> str:
        """
        Very simple heuristic:

        - If we find a pattern like 'HH:MM - HH:MM', return that.
        - Else if we find a pattern like 'HH:MM', return the first one.
        - Else just return the first non-empty line.
        """
        joined = " | ".join(lines)

        # Range like "12:11 - 13:16"
        m_range = re.search(r"\b\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\b", joined)
        if m_range:
            return m_range.group(0)

        # Single time like "08:20" or "14:20"
        m_single = re.search(r"\b\d{1,2}:\d{2}\b", joined)
        if m_single:
            return m_single.group(0)

        # Fallback – at least something human-readable
        for line in lines:
            if line.strip():
                return line.strip()

        return ""

    def _extract_detail_lines(self, content) -> List[str]:
        detail_els = content.query_selector_all(EVENT_DETAIL_LINES_SELECTOR)
        lines: List[str] = []
        last_line: Optional[str] = None
        for el in detail_els:
            if not el:
                continue
            text = el.inner_text().strip()
            if not text:
                continue
            if text == last_line:
                continue
            lines.append(text)
            last_line = text
        return lines

    def _split_entry_blocks(self, lines: List[str]) -> List[List[str]]:
        blocks: List[List[str]] = []
        current: List[str] = []
        for line in lines:
            if self._is_time_line(line):
                if current:
                    blocks.append(current)
                current = [line]
            else:
                current.append(line)
        if current:
            blocks.append(current)
        return blocks

    def _is_time_line(self, line: str) -> bool:
        return bool(re.search(r"\b\d{1,2}:\d{2}\b", line or ""))
    def _limit_events_by_entry_days(
        self,
        events: List[RawFamlyEvent],
        extra_entry_days: int,
    ) -> List[RawFamlyEvent]:
        """
        Keep only events from the most recent (extra_entry_days + 1) days with entries.
        """
        if extra_entry_days <= 0:
            allowed_days = 1
        else:
            allowed_days = extra_entry_days + 1

        result: List[RawFamlyEvent] = []
        seen_days: list[str] = []

        for event in events:
            day_key = event.raw_data.get("day_date_iso") or event.raw_data.get("day_label") or ""
            if day_key not in seen_days:
                if len(seen_days) >= allowed_days:
                    continue
                seen_days.append(day_key)
            result.append(event)

        return result

    def _parse_day_label(self, label: str, reference: date) -> Optional[date]:
        """
        Attempt to parse labels like "Today", "Yesterday", or "Monday, Dec 1".
        """
        if not label:
            return reference

        slug = label.strip().lower()
        if slug == "today":
            return reference
        if slug == "yesterday":
            return reference - timedelta(days=1)

        patterns_with_year = [
            "%A, %d %B, %Y",
            "%A, %B %d, %Y",
            "%A %d %B %Y",
            "%A %B %d %Y",
        ]
        for pattern in patterns_with_year:
            try:
                return datetime.strptime(label, pattern).date()
            except ValueError:
                continue

        patterns = [
            "%A, %b %d",
            "%A, %B %d",
            "%A %b %d",
            "%A %B %d",
        ]
        for pattern in patterns:
            try:
                parsed = datetime.strptime(f"{label} {reference.year}", f"{pattern} %Y").date()
                # If parsing jumps into the future (e.g. December when it's January), assume last year.
                if parsed > reference + timedelta(days=1):
                    parsed = parsed.replace(year=parsed.year - 1)
                return parsed
            except ValueError:
                continue
        logger.debug("Famly scrape: unable to parse day label '%s'", label)
        return None

    def _build_event_datetime(self, day: Optional[date], time_str: str) -> Optional[datetime]:
        if not day:
            return None
        match = re.search(r"\b(\d{1,2}):(\d{2})\b", time_str or "")
        hour = 0
        minute = 0
        if match:
            hour = min(int(match.group(1)), 23)
            minute = min(int(match.group(2)), 59)
        return datetime.combine(day, time(hour=hour, minute=minute))
