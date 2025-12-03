from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..core.sync_service import (
    scrape_famly_and_store,
    scrape_babyconnect_and_store,
    sync_to_babyconnect,
    create_babyconnect_entries as create_entries_service,
    get_missing_famly_event_ids,
)

router = APIRouter(tags=["sync"])

class CreateEntriesPayload(BaseModel):
    event_ids: list[int]

@router.post("/scrape/famly")
def scrape_famly(days_back: int = Query(0, ge=0, le=7, description="Number of previous days to include")):
    """
    Trigger a scrape of Famly events and persist them.

    Returns a simple summary (e.g. count of events).
    """
    events = scrape_famly_and_store(days_back=days_back)
    return {
        "status": "ok",
        "scraped_count": len(events),
        "days_back": days_back,
    }

@router.post("/scrape/baby_connect")
def scrape_baby_connect(days_back: int = Query(0, ge=0, le=14, description="Number of previous days to include")):
    events = scrape_babyconnect_and_store(days_back=days_back)
    return {
        "status": "ok",
        "scraped_count": len(events),
        "days_back": days_back,
    }

@router.post("/sync")
def sync():
    """
    Trigger synchronisation of unsynced Famly events into Baby Connect.

    Currently a stub until BabyConnectClient is fully implemented.
    """
    result = sync_to_babyconnect()
    return result

@router.post("/sync/baby_connect/entries")
def create_babyconnect_entries(payload: CreateEntriesPayload):
    return create_entries_service(payload.event_ids)

@router.post("/sync/missing")
def sync_missing_entries():
    """
    Compute missing Famly events and create them in Baby Connect.
    """
    missing_ids = get_missing_famly_event_ids()
    if not missing_ids:
        return {"status": "ok", "created": 0, "missing_event_ids": []}
    result = create_entries_service(missing_ids)
    response = dict(result)
    response.setdefault("status", "ok")
    response["missing_event_ids"] = missing_ids
    return response
