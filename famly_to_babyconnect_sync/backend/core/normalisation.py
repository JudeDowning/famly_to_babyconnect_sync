from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta, date
import logging
import re
from hashlib import sha256
from typing import Any, Dict

logger = logging.getLogger(__name__)
TIME_RANGE_PATTERN = re.compile(
    r"(\d{1,2}:\d{2}\s*(?:am|pm)?)\s*(?:-|to)\s*(\d{1,2}:\d{2}\s*(?:am|pm)?)",
    re.IGNORECASE,
)

@dataclass
class RawFamlyEvent:
    """
    A lightweight structure for the initial scrape result from Famly.

    This is the shape returned by FamlyClient before normalisation.
    """
    child_name: str
    event_type: str
    time_str: str
    raw_text: str
    raw_data: Dict[str, Any]
    event_datetime_iso: str | None = None

@dataclass
class RawBabyConnectEvent:
    """
    A lightweight structure for events scraped from Baby Connect (if needed).
    """
    child_name: str
    event_type: str
    time_str: str
    raw_text: str
    raw_data: Dict[str, Any]
    event_datetime_iso: str | None = None



def parse_time_to_utc(time_str: str) -> datetime:
    """
    Convert a scraped time string into a UTC datetime.

    Current logic:
    - Try ISO-8601 parsing (allowing trailing Z / missing TZ info)
    - If the ISO string is embedded inside other text, extract it
    - Fallback to the first HH:MM token (mainly for legacy paths)
    """
    if not time_str:
        raise ValueError("parse_time_to_utc: empty time string")

    cleaned = re.sub(r"\s+by\s+.*$", "", time_str.strip(), flags=re.IGNORECASE)
    cleaned = cleaned.replace("–", "-")

    def _try_iso(candidate: str) -> datetime | None:
        trimmed = candidate.strip()
        if not trimmed:
            return None
        if trimmed.endswith("Z"):
            trimmed = trimmed[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(trimmed)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        else:
            parsed = parsed.astimezone(timezone.utc)
        return parsed

    iso_candidates = [cleaned]
    embedded_iso = re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?", cleaned)
    if embedded_iso:
        iso_candidates.insert(0, embedded_iso.group(0))

    for candidate in iso_candidates:
        parsed = _try_iso(candidate)
        if parsed:
            return parsed

    time_match = re.search(r"\d{1,2}:\d{2}\s*(am|pm)?", cleaned, flags=re.IGNORECASE)
    if time_match:
        base = datetime.now(timezone.utc)
        combined = _combine_date_with_time(base, time_match.group(0))
        if combined:
            return combined

    raise ValueError(f"parse_time_to_utc: unable to parse '{time_str}'")


def _canonical_details_snippet(
    raw_text: str,
    raw_data: Dict[str, Any],
    *,
    child_name: str | None = None,
    event_type: str | None = None,
) -> str:
    """
    Produce a normalised snippet that is consistent between Famly and Baby Connect.
    - Ignore leading detail lines that are purely timestamps/ranges
    - Strip `[Sync]` markers and collapse whitespace
    - Force lowercase so casing differences don't affect matching
    """

    def _clean(value: str | None) -> str:
        if not value:
            return ""
        cleaned = re.sub(r"\[sync\]", "", value, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
        return cleaned

    child_lower = child_name.strip().lower() if child_name else None
    detail_lines = raw_data.get("detail_lines") if isinstance(raw_data, dict) else None
    normalized_lines: list[str] = []
    def _strip_leading_time(token: str) -> str:
        match = re.match(
            r"^\s*\d{1,2}:\d{2}\s*(?:am|pm)?\s*[:\-]?\s*(.*)$",
            token,
            flags=re.IGNORECASE,
        )
        if match:
            remainder = match.group(1).strip()
            if remainder:
                return remainder
        return token

    def _normalise_time_token(token: str) -> str | None:
        t_match = re.match(
            r"^\s*(\d{1,2}):(\d{2})\s*(am|pm)?\s*$",
            token,
            flags=re.IGNORECASE,
        )
        if not t_match:
            return None
        hour = int(t_match.group(1))
        minute = int(t_match.group(2))
        meridiem = t_match.group(3).lower() if t_match.group(3) else None
        if meridiem == "pm" and hour < 12:
            hour += 12
        if meridiem == "am" and hour == 12:
            hour = 0
        return f"{hour:02d}:{minute:02d}"

    def _canonical_time_range(token: str) -> str | None:
        match = TIME_RANGE_PATTERN.search(token)
        if not match:
            return None
        start = _normalise_time_token(match.group(1))
        end = _normalise_time_token(match.group(2))
        if start and end:
            return f"{start}-{end}"
        return None

    seen_ranges: set[str] = set()
    first_time_only: str | None = None
    if isinstance(detail_lines, list):
        for idx, line in enumerate(detail_lines):
            if not line:
                continue
            trimmed = line.strip()
            range_token = _canonical_time_range(trimmed)
            if range_token and range_token not in seen_ranges:
                normalized_lines.append(range_token)
                seen_ranges.add(range_token)
            if idx == 0 and re.search(r"\d{1,2}:\d{2}", trimmed):
                original_trimmed = trimmed
                trimmed = _strip_leading_time(trimmed)
                if not trimmed:
                    first_time_only = _normalise_time_token(original_trimmed)
                    continue
            lowered = trimmed.lower()
            if child_lower and lowered.startswith(child_lower):
                trimmed = trimmed[len(child_name) :].lstrip(" -:\u2013").strip() if child_name else trimmed
                if not trimmed:
                    continue
            if lowered.startswith("famly -"):
                continue
            cleaned = _clean(trimmed)
            if cleaned:
                normalized_lines.append(cleaned)

    note_val = raw_data.get("note") if isinstance(raw_data, dict) else ""
    if note_val:
        cleaned = _clean(note_val)
        if cleaned:
            normalized_lines.append(cleaned)

    if normalized_lines:
        if event_type and "sleep" in event_type.lower():
            return seen_ranges.pop() if seen_ranges else normalized_lines[0]
        return " | ".join(dict.fromkeys(normalized_lines))

    if not normalized_lines and first_time_only and event_type and "message" in event_type.lower():
        normalized_lines.append(first_time_only)

    for fallback in (
        note_val,
        raw_data.get("original_title") if isinstance(raw_data, dict) else "",
        raw_text,
    ):
        cleaned = _clean(fallback or "")
        if cleaned:
            return cleaned

    return ""

def _combine_date_with_time(
    base_dt: datetime,
    time_token: str,
    day_iso: str | None = None,
) -> datetime | None:
    """
    Combine a parsed time token (e.g. '7:23AM') with either the provided
    day_iso ('2025-12-04') or the date portion of base_dt.
    """
    match = re.match(r"^\s*(\d{1,2}):(\d{2})\s*(am|pm)?\s*$", time_token, flags=re.IGNORECASE)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2))
    meridiem = match.group(3).lower() if match.group(3) else None
    if meridiem == "pm" and hour < 12:
        hour += 12
    if meridiem == "am" and hour == 12:
        hour = 0

    result = base_dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if day_iso:
        try:
            day_val = date.fromisoformat(day_iso)
            result = result.replace(year=day_val.year, month=day_val.month, day=day_val.day)
        except ValueError:
            pass
    return result

def _infer_end_time_from_detail(
    raw_data: Dict[str, Any],
    fallback_text: str,
    start_time_utc: datetime,
) -> datetime | None:
    detail_lines = raw_data.get("detail_lines") if isinstance(raw_data, dict) else None
    candidate = None
    if isinstance(detail_lines, list):
        for line in detail_lines:
            match = TIME_RANGE_PATTERN.search(line)
            if match:
                candidate = match.group(2)
                break
    if not candidate and fallback_text:
        match = TIME_RANGE_PATTERN.search(fallback_text)
        if match:
            candidate = match.group(2)
    if not candidate:
        return None
    day_iso = raw_data.get("day_date_iso") if isinstance(raw_data, dict) else None
    end_dt = _combine_date_with_time(start_time_utc, candidate, day_iso)
    if not end_dt:
        return None
    if end_dt <= start_time_utc:
        end_dt = end_dt + timedelta(days=1)
    return end_dt

def build_fingerprint(
    child_name: str,
    event_type: str,
    start_time_utc: datetime,
    details_snippet: str,
) -> str:
    """
    Deterministically compute a fingerprint that uniquely (enough) represents
    an event across systems.

    This enables idempotent syncing and matching without external IDs.
    """
    key = "|".join([
        child_name.strip().lower(),
        event_type.strip().lower(),
        start_time_utc.replace(second=0, microsecond=0).isoformat(),
        details_snippet.strip().lower()[:100],
    ])
    return sha256(key.encode("utf-8")).hexdigest()

def normalise_famly_event(raw: RawFamlyEvent) -> Dict[str, Any]:
    """
    Convert a raw Famly event into a dictionary compatible with the Event model.
    """
    timestamp_source = raw.event_datetime_iso or raw.time_str
    start_time_utc = parse_time_to_utc(timestamp_source)
    if start_time_utc is None:
        logger.warning("normalise_famly_event: missing start time, defaulting to now")
        start_time_utc = datetime.now(timezone.utc)
    raw_data = raw.raw_data or {}
    details_snippet = _canonical_details_snippet(
        raw.raw_text or "",
        raw_data,
        child_name=raw.child_name,
        event_type=raw.event_type,
    )
    fingerprint = build_fingerprint(
        child_name=raw.child_name,
        event_type=raw.event_type,
        start_time_utc=start_time_utc,
        details_snippet=details_snippet,
    )
    end_time_utc = None
    end_iso = raw_data.get("end_event_datetime_iso")
    if end_iso:
        try:
            end_time_utc = datetime.fromisoformat(end_iso)
        except ValueError:
            logger.debug("normalise_famly_event: invalid end iso %s", end_iso)

    return {
        "source_system": "famly",
        "fingerprint": fingerprint,
        "child_name": raw.child_name,
        "event_type": raw.event_type,
        "start_time_utc": start_time_utc,
        "end_time_utc": end_time_utc,
        "details_json": {
            "raw_text": raw.raw_text,
            "raw_data": raw.raw_data,
        },
    }

def normalise_babyconnect_event(raw: RawBabyConnectEvent) -> Dict[str, Any]:
    """
    Convert a raw Baby Connect event into a dictionary compatible with the Event model.
    """
    timestamp_source = raw.event_datetime_iso or raw.time_str
    start_time_utc = parse_time_to_utc(timestamp_source)
    if start_time_utc is None:
        logger.warning("normalise_babyconnect_event: missing start time, defaulting to now")
        start_time_utc = datetime.now(timezone.utc)
    raw_data = raw.raw_data or {}
    details_snippet = _canonical_details_snippet(
        raw.raw_text or "",
        raw_data,
        child_name=raw.child_name,
        event_type=raw.event_type,
    )
    fingerprint = build_fingerprint(
        child_name=raw.child_name,
        event_type=raw.event_type,
        start_time_utc=start_time_utc,
        details_snippet=details_snippet,
    )
    end_time_utc = None
    end_iso = raw_data.get("end_event_datetime_iso")
    if end_iso:
        try:
            end_time_utc = datetime.fromisoformat(end_iso)
        except ValueError:
            logger.debug("normalise_babyconnect_event: invalid end iso %s", end_iso)
    elif "sleep" in (raw.event_type or "").lower():
        inferred = _infer_end_time_from_detail(raw_data, raw.raw_text or "", start_time_utc)
        if inferred:
            end_time_utc = inferred

    return {
        "source_system": "baby_connect",
        "fingerprint": fingerprint,
        "child_name": raw.child_name,
        "event_type": raw.event_type,
        "start_time_utc": start_time_utc,
        "end_time_utc": end_time_utc,
        "details_json": {
            "raw_text": raw.raw_text,
            "raw_data": raw.raw_data,
        },
    }
