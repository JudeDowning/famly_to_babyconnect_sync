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

from .storage import get_session
from .models import Event, Credential, SyncLink
from .normalisation import normalise_famly_event, RawFamlyEvent
from .famly_client import FamlyClient
# from .babyconnect_client import BabyConnectClient  # to be used when implemented

def get_credentials(service_name: str) -> Credential | None:
    with get_session() as session:
        return (
            session.query(Credential)
            .filter(Credential.service_name == service_name)
            .order_by(Credential.updated_at.desc())
            .first()
        )

def scrape_famly_and_store() -> List[Event]:
    """
    Scrape events from Famly, normalise them, and save to the database.
    """
    cred = get_credentials("famly")
    if not cred:
        raise RuntimeError("No Famly credentials configured.")

    client = FamlyClient(email=cred.email, password=cred.password_encrypted)  # TODO: decrypt when encryption is added
    raw_events: List[RawFamlyEvent] = client.login_and_scrape()
    normalised: List[Dict[str, Any]] = [normalise_famly_event(r) for r in raw_events]

    stored_events: List[Event] = []
    with get_session() as session:
        for ev in normalised:
            existing = (
                session.query(Event)
                .filter(
                    Event.source_system == ev["source_system"],
                    Event.fingerprint == ev["fingerprint"],
                )
                .first()
            )
            if existing:
                stored_events.append(existing)
                continue

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
