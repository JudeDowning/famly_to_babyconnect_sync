"""
Sync service.
-------------

High-level orchestration for:

- Scraping Famly events
- Scraping Baby Connect events (optional)
- Normalising and storing them
- Matching via fingerprint
- Creating missing events in Baby Connect
"""

from __future__ import annotations

from typing import Dict, Any, List
from datetime import datetime

from .storage import get_session
from .models import Event, Credential, SyncLink
from .normalisation import normalise_famly_event, RawFamlyEvent, RawBabyConnectEvent, normalise_babyconnect_event
from .famly_client import FamlyClient
from .babyconnect_client import BabyConnectClient  # to be used when implemented

def get_credentials(service_name: str) -> Credential | None:
    with get_session() as session:
        return (
            session.query(Credential)
            .filter(Credential.service_name == service_name)
            .order_by(Credential.updated_at.desc())
            .first()
        )

def scrape_famly_and_store(days_back: int = 0) -> List[Event]:
    """
    Scrape events from Famly, normalise them, and save to the database.
    """
    cred = get_credentials("famly")
    if not cred:
        raise RuntimeError("No Famly credentials configured.")

    client = FamlyClient(email=cred.email, password=cred.password_encrypted)  # TODO: decrypt when encryption is added
    raw_events: List[RawFamlyEvent] = client.login_and_scrape(days_back=days_back)
    normalised: List[Dict[str, Any]] = [normalise_famly_event(r) for r in raw_events]

    stored_events: List[Event] = []
    with get_session() as session:
        session.query(Event).filter(Event.source_system == "famly").delete()
        session.flush()
        for ev in normalised:
            new_ev = Event(**ev)
            session.add(new_ev)
            session.flush()  # assign id
            stored_events.append(new_ev)

    return stored_events

def get_events(source_system: str, limit: int = 100) -> List[Event]:
    """
    Return the most recent events for a given source system.
    """
    with get_session() as session:
        return (
            session.query(Event)
            .filter(Event.source_system == source_system)
            .order_by(Event.start_time_utc.desc())
            .limit(limit)
            .all()
        )

def _compute_babyconnect_days(days_back: int) -> int:
    today = datetime.utcnow().date()
    with get_session() as session:
        latest = (
            session.query(Event)
            .filter(Event.source_system == "famly")
            .order_by(Event.start_time_utc.desc())
            .first()
        )
    if not latest:
        return days_back
    diff = (today - latest.start_time_utc.date()).days
    base_offset = max(diff, 0)
    return base_offset + max(days_back, 0)

def scrape_babyconnect_and_store(days_back: int = 0) -> List[Event]:
    """
    Scrape events from Baby Connect and persist them.
    """
    cred = get_credentials("baby_connect")
    if not cred:
        raise RuntimeError("No Baby Connect credentials configured.")

    effective_days = _compute_babyconnect_days(days_back)

    client = BabyConnectClient(email=cred.email, password=cred.password_encrypted)
    raw_events: List[RawBabyConnectEvent] = client.login_and_scrape(days_back=effective_days)
    normalised: List[Dict[str, Any]] = [normalise_babyconnect_event(r) for r in raw_events]

    stored_events: List[Event] = []
    seen_fingerprints: set[str] = set()
    with get_session() as session:
        session.query(Event).filter(Event.source_system == "baby_connect").delete()
        session.flush()
        for ev in normalised:
            fp = ev["fingerprint"]
            if fp in seen_fingerprints:
                continue
            seen_fingerprints.add(fp)
            new_ev = Event(**ev)
            session.add(new_ev)
            session.flush()
            stored_events.append(new_ev)

    return stored_events
def sync_to_babyconnect() -> Dict[str, Any]:
    """
    Placeholder for the main sync operation.
    Actual Baby Connect automation needs to be implemented.
    """
    # TODO: implement Baby Connect write-side automation
    return {
        "status": "not_implemented",
        "message": "Sync to Baby Connect is not implemented yet.",
    }
