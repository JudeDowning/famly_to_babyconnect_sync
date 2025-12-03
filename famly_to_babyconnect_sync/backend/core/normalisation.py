from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import re
from hashlib import sha256
from typing import Any, Dict

logger = logging.getLogger(__name__)

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
    - Try ISO-8601 parsing
    - Try parsing HH:MM (assume today, local timezone, convert to UTC)
    - Fall back to "now" if parsing fails
    """
    if not time_str:
        logger.warning("parse_time_to_utc: empty time string, defaulting to now")
        return datetime.now(timezone.utc)
    cleaned = re.sub(r"\s+by\s+.*$", "", time_str.strip(), flags=re.IGNORECASE)
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        logger.debug("parse_time_to_utc: %s not ISO format", cleaned)

    try:
        if "to" in cleaned.lower():
            parts = cleaned.lower().split("to")[0].strip()
        else:
            parts = cleaned.split("-")[0].strip()
        numbers = re.findall(r"\d{1,2}", parts)
        hour = int(numbers[0]) if numbers else 0
        minute = int(numbers[1]) if len(numbers) > 1 else 0
        am_pm_match = re.search(r"(am|pm)", parts, flags=re.IGNORECASE)
        if am_pm_match:
            meridiem = am_pm_match.group(1).lower()
            if meridiem == "pm" and hour < 12:
                hour += 12
            if meridiem == "am" and hour == 12:
                hour = 0
        now = datetime.now(timezone.utc)
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return candidate
    except Exception:
        logger.warning("parse_time_to_utc: unable to parse '%s', defaulting to now", time_str)
        return datetime.now(timezone.utc)

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
    details_snippet = raw.raw_text or ""
    fingerprint = build_fingerprint(
        child_name=raw.child_name,
        event_type=raw.event_type,
        start_time_utc=start_time_utc,
        details_snippet=details_snippet,
    )
    end_time_utc = None
    raw_data = raw.raw_data or {}
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
    details_snippet = raw.raw_text or ""
    fingerprint = build_fingerprint(
        child_name=raw.child_name,
        event_type=raw.event_type,
        start_time_utc=start_time_utc,
        details_snippet=details_snippet,
    )
    end_time_utc = None
    raw_data = raw.raw_data or {}
    end_iso = raw_data.get("end_event_datetime_iso")
    if end_iso:
        try:
            end_time_utc = datetime.fromisoformat(end_iso)
        except ValueError:
            logger.debug("normalise_babyconnect_event: invalid end iso %s", end_iso)

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
