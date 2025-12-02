from fastapi import APIRouter
from pydantic import BaseModel

from ..core.event_mapping import (
    canonicalise_famly_label,
    get_event_mapping as load_event_mapping,
    get_known_famly_types,
    set_event_mapping as save_event_mapping,
)
from ..core.storage import get_session
from ..core.models import Event


class EventMappingPayload(BaseModel):
    mapping: dict[str, str]


router = APIRouter(tags=["settings"])


@router.get("/settings/event-mapping")
def get_event_mapping():
    return {"mapping": load_event_mapping()}


@router.put("/settings/event-mapping")
def set_event_mapping(payload: EventMappingPayload):
    save_event_mapping(payload.mapping)
    return {"status": "ok", "mapping": load_event_mapping()}


@router.get("/settings/famly-event-types")
def list_famly_event_types():
    with get_session() as session:
        types = (
            session.query(Event.event_type)
            .filter(Event.source_system == "famly")
            .distinct()
            .order_by(Event.event_type.asc())
            .all()
        )
    db_types = [t[0] for t in types if t[0]]

    canonicalized = [
        canonicalise_famly_label(raw)
        for raw in db_types
    ]
    canonicalized = [item for item in canonicalized if item]

    known = set(get_known_famly_types())
    known.update(canonicalized)
    known.update(label.strip() for label in load_event_mapping().keys() if label.strip())
    cleaned = sorted({item for item in known if item})
    return {"types": cleaned}
