from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.storage import get_session
from ..core.models import Credential

router = APIRouter(tags=["credentials"])


class CredentialIn(BaseModel):
    email: str
    password: str


class CredentialOut(BaseModel):
    service_name: str
    email: str | None


def _validate_service(service: str) -> str:
    if service not in ("famly", "baby_connect"):
        raise HTTPException(status_code=400, detail="Invalid service name")
    return service


@router.post("/credentials/{service}", response_model=CredentialOut)
def set_credentials(service: str, data: CredentialIn):
    """
    Store or update credentials for a given service ("famly" or "baby_connect").

    NOTE: password is stored in plaintext for now. Later we can add encryption.
    """
    service = _validate_service(service)

    with get_session() as session:
        existing = (
            session.query(Credential)
            .filter(Credential.service_name == service)
            .first()
        )

        if existing:
            existing.email = data.email
            existing.password_encrypted = data.password  # TODO: encrypt
        else:
            cred = Credential(
                service_name=service,
                email=data.email,
                password_encrypted=data.password,  # TODO: encrypt
            )
            session.add(cred)

    return CredentialOut(service_name=service, email=data.email)


@router.get("/credentials/{service}", response_model=CredentialOut)
def get_credentials(service: str):
    """
    Return the stored email for a service so the UI can display it.
    (Password is never returned.)
    """
    service = _validate_service(service)

    with get_session() as session:
        cred = (
            session.query(Credential)
            .filter(Credential.service_name == service)
            .first()
        )

    return CredentialOut(
        service_name=service,
        email=cred.email if cred else None,
    )
