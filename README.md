# Famly → Baby Connect Sync (Home Assistant Add-on)

Headless Playwright automation that scrapes activities from the Famly nursery platform and replicates them into Baby Connect. Ships as a Home Assistant add-on but can also run as a standalone Docker container.

> **Status:** Alpha – expect API/UI changes while stabilising selectors and sync behaviour.

---

## Table of Contents

1. [Features](#features)
2. [Screenshots](#screenshots)
3. [Quick Start (Docker)](#quick-start-docker)
4. [Home Assistant Installation](#home-assistant-installation)
5. [Configuration](#configuration)
6. [Automations & Services](#automations--services)
7. [API Reference](#api-reference)
8. [Architecture Overview](#architecture-overview)
9. [Development](#development)
10. [Roadmap](#roadmap)

---

## Features

- Playwright automation for Famly + Baby Connect.
- Unified event model (meals, nappies, sleep, attendance, custom).
- Fingerprint-based matching and “missing entry” detection.
- React dashboard for credentials, day-by-day comparison, one-click sync.
- Sync filters (choose which event types “Sync All” will push).
- Multi-stage Docker image & HA add-on manifest.
- Persistent SQLite database + browser profiles under `/data`.


## Quick Start (Docker)

```bash
# build image from repo root
docker build -t famly-sync famly_to_babyconnect_sync

# run container
docker run \
  -p 8000:8000 \
  -v "$(pwd)/famly_to_babyconnect_sync/data:/data" \
  -e HEADLESS=true \
  famly-sync
```

Browse to `http://localhost:8000` to open the UI.

### Environment Variables

| Variable | Default | Notes |
| --- | --- | --- |
| `HEADLESS` | `true` | Set to `false` while tuning selectors. |
| `DB_PATH` | `/data/db.sqlite` | SQLite db (keep under `/data`). |
| `FAMLY_PROFILE_DIR` | `/data/famly-profile` | Browser profile & cookies. |
| `BABYCONNECT_PROFILE_DIR` | `/data/babyconnect-profile` | Browser profile & cookies. |
| `APP_HOST` / `APP_PORT` | `0.0.0.0` / `8000` | Uvicorn bind. |
| `LOG_LEVEL` | `INFO` | Uvicorn/Playwright logs. |

---

## Home Assistant Installation

1. Add this repository as a custom add-on repo or copy the code into your HA add-on folder.
2. Build/install the add-on (`famly_to_babyconnect_sync/config.yaml` + `famly_to_babyconnect_sync/Dockerfile` are HA-compliant).
3. Map `/data` (default) for DB and Playwright profiles.
4. Start the add-on; the UI is available via ingress or the exposed port.
5. Use the dashboard to store Famly/Baby Connect credentials, scrape, and sync.

> **Secrets:** credentials are stored in the add-on database. You can also pre-populate them by calling `/api/credentials/{service}` from HA (see API reference).

---

## Configuration

### UI Settings

- **Credentials** – stored per service via the dashboard. No manual YAML required.
- **Date format** – choose between `Mon Dec 01` or `Mon 01 Dec`.
- **Sync filters** – toggle which canonical types (“Solid”, “Nappy”, “Sleep”, etc.) are included when running “Sync All”.

These preferences are persisted in `data/settings.json`.

### Files & Persistence

| Path | Purpose |
| --- | --- |
| `/data/db.sqlite` | SQLite database (events, credentials, links, settings). |
| `/data/famly-profile` | Chromium profile for Famly (keeps cookies). |
| `/data/babyconnect-profile` | Chromium profile for Baby Connect. |
| `/data/logs/famly_sync.log` | Rolling log file (log level configurable). |

Make sure `/data` is mapped to HA’s data folder or a Docker volume.

---

## Automations & Services

Define `rest_command` entries in Home Assistant to trigger scrapes/syncs:

```yaml
rest_command:
  famly_sync_scrape:
    url: "http://ADDON_HOST:ADDON_PORT/api/scrape/famly?days_back=0"
    method: POST
  babyconnect_sync_scrape:
    url: "http://ADDON_HOST:ADDON_PORT/api/scrape/baby_connect?days_back=0"
    method: POST
  famly_sync_all_missing:
    url: "http://ADDON_HOST:ADDON_PORT/api/sync/missing"
    method: POST
```

Automation example:

```yaml
automation:
  - alias: "Nightly Famly → Baby Connect sync"
    trigger:
      - platform: time
        at: "22:30:00"
    action:
      - service: rest_command.famly_sync_scrape
      - service: rest_command.babyconnect_sync_scrape
      - service: rest_command.famly_sync_all_missing
```

If calling through Supervisor’s proxy, add an `Authorization: "Bearer ${SUPERVISOR_TOKEN}"` header.

---

## API Reference

| Method & Path | Description |
| --- | --- |
| `POST /api/credentials/{service}` | Save credentials for `famly` or `baby_connect`. Body: `{ "email": "...", "password": "..." }`. |
| `POST /api/test-connection/{service}` | Playwright login test (returns OK/ERROR). |
| `POST /api/scrape/famly?days_back=X` | Scrapes Famly events (`scraped_count` in response). |
| `POST /api/scrape/baby_connect?days_back=X` | Scrapes Baby Connect events. |
| `GET /api/events?source=famly|baby_connect` | Returns latest stored events for each side. |
| `GET /api/events/missing` | Returns Famly event IDs missing from Baby Connect. |
| `POST /api/sync/baby_connect/entries` | Body: `{ "event_ids": [1,2,3] }` – create specific entries. |
| `POST /api/sync/missing` | Computes missing events (respecting sync filters) and creates them in Baby Connect. |
| `GET /api/status` | Connection & event summary for the dashboard. |
| `GET/PUT /api/settings/event-mapping` | Retrieve/update Famly→canonical event mappings. |
| `GET/PUT /api/settings/sync-preferences` | Retrieve/update sync filters (event types included in sync-all). |

All endpoints return JSON and require no authentication when running locally. For HA deployments consider restricting access to HA’s network or adding a reverse proxy with auth.

---

## Architecture Overview

(Paths below are relative to the `famly_to_babyconnect_sync/` directory.)



### Backend (FastAPI + Playwright)

- `famly_to_babyconnect_sync/backend/core/famly_client.py` – navigates Famly UI, scrapes events.
- `famly_to_babyconnect_sync/backend/core/babyconnect_client.py` – logs into Baby Connect and submits forms.
- `famly_to_babyconnect_sync/backend/core/normalisation.py` – converts scraped DOM nodes into a normalised event model and generates fingerprints.
- `famly_to_babyconnect_sync/backend/core/sync_service.py` – orchestrates scraping, matching, filtering, and creation of missing entries.
- `famly_to_babyconnect_sync/backend/core/storage.py` / `models.py` – SQLite storage for events, credentials, sync links.
- `famly_to_babyconnect_sync/backend/core/settings_store.py` – persists event mappings and sync filters in JSON.
- `famly_to_babyconnect_sync/backend/api/*` – FastAPI routers for credentials/status/events/sync/settings.

### Frontend (React + Vite)

- `famly_to_babyconnect_sync/frontend/src/App.tsx` – three-column dashboard (Famly | Sync | Baby Connect).
- `famly_to_babyconnect_sync/frontend/src/components/*` – Connection cards, comparison blocks, settings drawer, progress overlay, toast notifications.
- `famly_to_babyconnect_sync/frontend/src/api.ts` – Fetch helpers for the API endpoints.
- Built assets served from `famly_to_babyconnect_sync/frontend/dist` via FastAPI.

### Containerisation

- Root `famly_to_babyconnect_sync/Dockerfile` builds the frontend (Node stage) then bundles it with the backend on top of `mcr.microsoft.com/playwright/python`.
- `famly_to_babyconnect_sync/entrypoint.sh` launches Uvicorn with the configured host/port.
- `famly_to_babyconnect_sync/config.yaml` is the HA add-on manifest (ingress-enabled, `/data` mapped read/write).

---

## Development

### Backend

```bash
cd famly_to_babyconnect_sync
python -m venv .venv
source .venv/bin/activate  # on Windows use: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.api.main:app --reload --port 8000
```

### Frontend

```bash
cd famly_to_babyconnect_sync/frontend
npm install
npm run dev   # http://localhost:5173
```

Tips:

- Set `HEADLESS=false` when debugging Playwright selectors.
- Use test accounts until selectors and sync flows are stable.
- Run `npm run build` before packaging the container/add-on.

---

## Roadmap

- Refine HA add-on configuration (surface credentials/headless/log level via UI schema).
- Add scheduling/background sync inside the add-on (optional cron).
- Support multiple children & advanced filtering.
- Provide manual matching/conflict resolution UI.
- Expand logging/status history view in the dashboard.

Contributions and issue reports are welcome!


