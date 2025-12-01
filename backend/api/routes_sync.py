from fastapi import APIRouter

from ..core.sync_service import scrape_famly_and_store, sync_to_babyconnect

router = APIRouter(tags=["sync"])

@router.post("/scrape/famly")
def scrape_famly():
    """
    Trigger a scrape of Famly events and persist them.

    Returns a simple summary (e.g. count of events).
    """
    events = scrape_famly_and_store()
    return {
        "status": "ok",
        "scraped_count": len(events),
    }

@router.post("/sync")
def sync():
    """
    Trigger synchronisation of unsynced Famly events into Baby Connect.

    Currently a stub until BabyConnectClient is fully implemented.
    """
    result = sync_to_babyconnect()
    return result
