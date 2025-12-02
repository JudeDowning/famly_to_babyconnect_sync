from fastapi import APIRouter, Query

from ..core.sync_service import (
    scrape_famly_and_store,
    scrape_babyconnect_and_store,
    sync_to_babyconnect,
)

router = APIRouter(tags=["sync"])

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
