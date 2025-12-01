from fastapi import APIRouter
from ..core.storage import get_session
from ..core.models import Credential, Event

router = APIRouter(tags=["status"])

@router.get("/status")
def get_status():
    """
    Return a lightweight status snapshot for the dashboard.
    """
    with get_session() as session:
        famly_cred = session.query(Credential).filter(Credential.service_name == "famly").first()
        bc_cred = session.query(Credential).filter(Credential.service_name == "baby_connect").first()
        famly_events_count = session.query(Event).filter(Event.source_system == "famly").count()
        bc_events_count = session.query(Event).filter(Event.source_system == "baby_connect").count()

    return {
        "famly": {
            "has_credentials": bool(famly_cred),
        },
        "baby_connect": {
            "has_credentials": bool(bc_cred),
        },
        "counts": {
            "famly_events": famly_events_count,
            "baby_connect_events": bc_events_count,
        },
    }
