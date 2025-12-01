from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from typing import Any, Dict

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

def parse_time_to_utc(time_str: str) -> datetime:
    """
    TODO: Implement robust parsing from whatever format Famly/BabyConnect uses
    into a timezone-aware UTC datetime.

    For now, this is a stub.
    """
    # Placeholder: interpret incoming string as naive UTC for now.
    return datetime.fromisoformat(time_str)

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
    start_time_utc = parse_time_to_utc(raw.time_str)
    details_snippet = raw.raw_text or ""
    fingerprint = build_fingerprint(
        child_name=raw.child_name,
        event_type=raw.event_type,
        start_time_utc=start_time_utc,
        details_snippet=details_snippet,
    )
    return {
        "source_system": "famly",
        "fingerprint": fingerprint,
        "child_name": raw.child_name,
        "event_type": raw.event_type,
        "start_time_utc": start_time_utc,
        "end_time_utc": None,
        "details_json": {
            "raw_text": raw.raw_text,
            "raw_data": raw.raw_data,
        },
    }

def normalise_babyconnect_event(raw: RawBabyConnectEvent) -> Dict[str, Any]:
    """
    Convert a raw Baby Connect event into a dictionary compatible with the Event model.
    """
    start_time_utc = parse_time_to_utc(raw.time_str)
    details_snippet = raw.raw_text or ""
    fingerprint = build_fingerprint(
        child_name=raw.child_name,
        event_type=raw.event_type,
        start_time_utc=start_time_utc,
        details_snippet=details_snippet,
    )
    return {
        "source_system": "baby_connect",
        "fingerprint": fingerprint,
        "child_name": raw.child_name,
        "event_type": raw.event_type,
        "start_time_utc": start_time_utc,
        "end_time_utc": None,
        "details_json": {
            "raw_text": raw.raw_text,
            "raw_data": raw.raw_data,
        },
    }
