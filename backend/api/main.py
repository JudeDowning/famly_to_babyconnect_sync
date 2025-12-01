from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from ..core.config import CORS_ORIGINS, BASE_DIR
from ..core.storage import init_db
from .routes_status import router as status_router
from .routes_events import router as events_router
from .routes_sync import router as sync_router

app = FastAPI(title="Famly to Baby Connect Sync")

# Init DB on startup
@app.on_event("startup")
def startup() -> None:
    init_db()

# CORS (mainly for dev; tighten for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(status_router, prefix="/api")
app.include_router(events_router, prefix="/api")
app.include_router(sync_router, prefix="/api")

# Serve frontend (if built)
frontend_dist = BASE_DIR / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
