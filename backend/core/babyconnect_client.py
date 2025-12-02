"""
Baby Connect client (automation).
---------------------------------

This module uses Playwright to:

- Log into Baby Connect
- Open the appropriate activity entry forms (meal, nap, nappy, etc.)
- Fill them based on a normalised event
- Submit the forms to create events as if a user did it manually
"""

from __future__ import annotations

from typing import Dict, Any, List
import logging
import re
from datetime import datetime, timedelta

from playwright.sync_api import sync_playwright, Page

from .config import BABYCONNECT_PROFILE_DIR, HEADLESS
from .normalisation import RawBabyConnectEvent

BABYCONNECT_LOGIN_URL = "https://app.babyconnect.com/login"
BABYCONNECT_HOME_URL = "https://app.babyconnect.com/home2"

# Login selectors (confirmed)
BC_EMAIL_SELECTOR = "#username"
BC_PASSWORD_SELECTOR = "#password"
BC_LOGIN_BUTTON_SELECTOR = "#save"

CHILD_NAME_SELECTOR = ".name a"


# Today’s status list selectors
STATUS_LIST_CONTAINER = "#status_list_container"
STATUS_LIST_WRAP = "#status_list_wrap"
STATUS_LIST_SELECTOR = "#status_list"
BC_EVENT_SELECTOR = ".st"
BC_EVENT_ICON_SELECTOR = ".st_img img"
BC_EVENT_TITLE_SELECTOR = ".st_body .st_tl"
BC_EVENT_NOTE_SELECTOR = ".st_body .st_note"
BC_POSTED_BY_CONTAINER_SELECTOR = ".posted_by"
DATE_DISPLAY_SELECTOR = "#kid_date"
DATE_LEFT_SELECTOR = "#dateLeft"

logger = logging.getLogger(__name__)

class BabyConnectClient:
    def __init__(self, email: str, password: str) -> None:
        self.email = email
        self.password = password

    def login_and_scrape(self, days_back: int = 0) -> List[RawBabyConnectEvent]:
        events: List[RawBabyConnectEvent] = []

        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(BABYCONNECT_PROFILE_DIR),
                headless=HEADLESS,
            )
            page = browser.new_page()

            # 1. Login (if session not already stored)
            logger.info("BabyConnect: opening home page")
            page.goto(BABYCONNECT_HOME_URL, wait_until="networkidle")

            if "login" in page.url:
                logger.info("BabyConnect: redirected to login, performing login flow")
                page.wait_for_selector(BC_EMAIL_SELECTOR)
                page.fill(BC_EMAIL_SELECTOR, self.email)
                page.fill(BC_PASSWORD_SELECTOR, self.password)
                page.click(BC_LOGIN_BUTTON_SELECTOR)
                page.wait_for_load_state("networkidle")
                logger.info("BabyConnect: login complete, returning to home")
                page.goto(BABYCONNECT_HOME_URL, wait_until="networkidle")
            else:
                logger.info("BabyConnect: existing session active")

            page.wait_for_selector(DATE_DISPLAY_SELECTOR, timeout=10000)
            child_name = self._read_child_name(page) or "Baby Connect"

            collected_days = 0
            seen_dates: set[str] = set()

            while True:
                status_list = self._get_status_list(page)
                if not status_list:
                    logger.warning("BabyConnect: status list missing for current day")
                    break

                day_label, day_iso = self._get_current_day_info(page)
                if day_iso in seen_dates:
                    logger.info("BabyConnect: already collected date %s, stopping", day_iso)
                    break
                seen_dates.add(day_iso)

                daily_events = self._collect_events_for_day(
                    status_list=status_list,
                    child_name=child_name,
                    day_label=day_label,
                    day_iso=day_iso,
                )
                events.extend(daily_events)
                logger.info("BabyConnect: collected %d events for %s", len(daily_events), day_label)

                if collected_days >= days_back:
                    break

                if not self._go_to_previous_day(page, day_label):
                    break

                collected_days += 1

            browser.close()
            logger.info("BabyConnect: scraped %d events across %d days", len(events), len(seen_dates))

        return events

    def _extract_time_and_author(self, node) -> tuple[str, str]:
        container = node.query_selector(BC_POSTED_BY_CONTAINER_SELECTOR)
        if not container:
            return "", ""

        spans = container.query_selector_all("span")
        time_str = ""
        author = ""
        if spans:
            time_str = spans[0].inner_text().strip()
            if len(spans) > 1:
                author_raw = spans[1].inner_text().strip()
                m = re.search(r"by\s+(.*)", author_raw, re.IGNORECASE)
                author = m.group(1).strip() if m else author_raw

        return time_str, author

    def _infer_event_type(self, title: str, icon_src: str) -> str:
        t = title.lower()
        s = (icon_src or "").lower()

        if "eat_v2" in s:
            return "solid"
        if "diapers_v2" in s:
            return "nappy"
        if "bib_v2" in s:
            return "bottle"
        if "sleep_v2" in s:
            return "sleep"
        if "medicine_v2" in s:
            return "medicine"
        if "temperature_v2" in s:
            return "temperature"
        if "bath_v2" in s:
            return "bath"

        if "diaper" in t or "nappy" in t:
            return "nappy"
        if "sleep" in t:
            return "sleep"
        if "medicine" in t or "calpol" in t:
            return "medicine"
        if "temperature" in t:
            return "temperature"
        if "breakfast" in t or "lunch" in t or "dinner" in t or "meal" in t or "ate" in t or "drank" in t or "food" in t:
            return "solid"
        if "bottle" in t or "formula" in t:
            return "bottle"
        if "bath" in t:
            return "bath"

        return "other"

    def _read_child_name(self, page) -> str:
        try:
            name_el = page.query_selector(CHILD_NAME_SELECTOR)
            if name_el:
                return name_el.inner_text().strip()
        except Exception:
            logger.exception("BabyConnect: failed to read child name")
        return ""

    def _get_status_list(self, page: Page):
        try:
            page.wait_for_selector(STATUS_LIST_CONTAINER, timeout=10000)
            status_container = page.query_selector(STATUS_LIST_CONTAINER)
            if not status_container:
                return None
            status_wrap = status_container.query_selector(STATUS_LIST_WRAP)
            if not status_wrap:
                return None
            return status_wrap.query_selector(STATUS_LIST_SELECTOR)
        except Exception:
            logger.exception("BabyConnect: error locating status list")
            return None

    def _get_current_day_info(self, page: Page) -> tuple[str, str]:
        text = page.inner_text(DATE_DISPLAY_SELECTOR).strip()
        lower = text.lower()
        today = datetime.now()
        if lower == "today":
            dt = today
        elif lower == "yesterday":
            dt = today - timedelta(days=1)
        else:
            try:
                dt = datetime.strptime(text, "%A, %d %B, %Y")
            except ValueError:
                dt = today
        iso = dt.date().isoformat()
        label = text if lower not in {"today", "yesterday"} else dt.strftime("%A, %d %B %Y")
        return label, iso

    def _go_to_previous_day(self, page: Page, current_label: str) -> bool:
        try:
            page.click(DATE_LEFT_SELECTOR)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(800)
            page.wait_for_selector(DATE_DISPLAY_SELECTOR, timeout=5000)
            logger.info("BabyConnect: moved to previous day from %s", current_label)
            return True
        except Exception:
            logger.exception("BabyConnect: failed to move to previous day")
            return False

    def _collect_events_for_day(
        self,
        status_list,
        child_name: str,
        day_label: str,
        day_iso: str,
    ) -> List[RawBabyConnectEvent]:
        if not status_list:
            return []

        rows = status_list.query_selector_all(BC_EVENT_SELECTOR)
        collected: List[RawBabyConnectEvent] = []

        for node in rows:
            icon_src = ""
            icon_el = node.query_selector(BC_EVENT_ICON_SELECTOR)
            if icon_el:
                icon_src = icon_el.get_attribute("src") or ""

            title_el = node.query_selector(BC_EVENT_TITLE_SELECTOR)
            if not title_el:
                continue
            title_text = title_el.inner_text().strip()

            note_el = node.query_selector(BC_EVENT_NOTE_SELECTOR)
            note_text = note_el.inner_text().strip() if note_el else ""

            time_str, author = self._extract_time_and_author(node)
            event_type = self._infer_event_type(title_text, icon_src)
            start_iso, end_iso, display_range = self._parse_time_range(day_iso, time_str)
            detail_lines = self._build_detail_lines(
                event_type=event_type,
                title_text=title_text,
                note_text=note_text,
                display_range=display_range,
            )

            raw_data = {
                "icon_src": icon_src,
                "author": author,
                "note": note_text,
                "raw_html": node.inner_html(),
                "day_label": day_label,
                "day_date_iso": day_iso,
            }
            if end_iso:
                raw_data["end_event_datetime_iso"] = end_iso
            if detail_lines:
                raw_data["detail_lines"] = detail_lines

            collected.append(
                RawBabyConnectEvent(
                    child_name=child_name,
                    event_type=event_type,
                    time_str=time_str,
                    raw_text=title_text,
                    raw_data=raw_data,
                    event_datetime_iso=start_iso,
                )
            )

        return collected

    def _combine_date_with_time(self, day_iso: str, token: str) -> datetime | None:
        match = re.match(r"(\d{1,2}):(\d{2})\s*(am|pm)?", token.strip(), re.IGNORECASE)
        if not match:
            return None
        hour = int(match.group(1))
        minute = int(match.group(2))
        meridiem = match.group(3)
        if meridiem:
            meridiem = meridiem.lower()
            if meridiem == "pm" and hour < 12:
                hour += 12
            if meridiem == "am" and hour == 12:
                hour = 0
        try:
            date_part = datetime.strptime(day_iso, "%Y-%m-%d").date()
            return datetime.combine(date_part, datetime.min.time()).replace(hour=hour, minute=minute)
        except Exception:
            return None

    def _parse_time_range(
        self,
        day_iso: str,
        time_str: str,
    ) -> tuple[str | None, str | None, str | None]:
        if not day_iso or not time_str:
            return None, None, None

        matches = re.findall(r"\d{1,2}:\d{2}\s*(?:am|pm)?", time_str, re.IGNORECASE)
        if not matches:
            return None, None, None

        start_dt = self._combine_date_with_time(day_iso, matches[0])
        end_dt = None
        if len(matches) > 1:
            end_dt = self._combine_date_with_time(day_iso, matches[1])
            if start_dt and end_dt and end_dt <= start_dt:
                end_dt = end_dt + timedelta(days=1)

        display = None
        if len(matches) >= 2:
            display = f"{matches[0]} - {matches[1]}"
        else:
            display = matches[0]

        return (
            start_dt.isoformat() if start_dt else None,
            end_dt.isoformat() if end_dt else None,
            display,
        )

    def _build_detail_lines(
        self,
        event_type: str,
        title_text: str,
        note_text: str,
        display_range: str | None,
    ) -> List[str]:
        seen = set()
        lines: List[str] = []

        def add_line(value: str | None):
            if not value:
                return
            cleaned = value.strip()
            if not cleaned or cleaned in seen:
                return
            seen.add(cleaned)
            lines.append(cleaned)
        if event_type == "sleep" and display_range:
            add_line(display_range)
        add_line(title_text)
        add_line(note_text)
        return lines
