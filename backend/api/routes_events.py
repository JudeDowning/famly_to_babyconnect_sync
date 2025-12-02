from typing import List

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..core.sync_service import get_events

router = APIRouter(tags=["events"])

class EventOut(BaseModel):
    id: int
    source_system: str
    child_name: str
    event_type: str
    start_time_utc: str
    matched: bool = False
    summary: str | None = None
    raw_text: str | None = None
    raw_data: dict | None = None

@router.get("/events", response_model=List[EventOut])
def list_events(source: str = Query(..., regex="^(famly|baby_connect)$")):
    """
    Return the most recent events for the given source system.

    This is used to populate the left (Famly) and right (Baby Connect) columns in the UI.
    """
    events = get_events(source)
    # TODO: mark matched events based on SyncLink table
    output: List[EventOut] = []
    for e in events:
        output.append(EventOut(
            id=e.id,
            source_system=e.source_system,
            child_name=e.child_name,
            event_type=e.event_type,
            start_time_utc=e.start_time_utc.isoformat(),
            matched=False,  # placeholder until matching is wired
            summary=e.details_json.get("raw_text") if isinstance(e.details_json, dict) else None,
            raw_text=e.details_json.get("raw_text") if isinstance(e.details_json, dict) else None,
            raw_data=e.details_json.get("raw_data") if isinstance(e.details_json, dict) else None,
        ))
    return output
