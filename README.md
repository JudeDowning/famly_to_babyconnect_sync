# 📘 Famly → Baby Connect Sync Tool  
*A headless-browser automation service that scrapes activity entries from the Famly nursery platform and replicates them into Baby Connect.*

---

## 🧩 Overview

### What the Tool Does  
This tool automates the transfer of recorded activities (meals, naps, nappies, attendance, pickups, and other events) from **Famly** to **Baby Connect**.

Because **neither platform provides an API**, the tool uses a **headless browser** to:

1. Log in to Famly using user-provided credentials  
2. Scrape activity entries from the Famly web UI  
3. Normalise and store the scraped events  
4. Log in to Baby Connect  
5. Simulate user clicks and form submissions to recreate events  
6. Detect matching events between systems using fingerprints  
7. Provide a web dashboard that:  
   - Stores credentials (Famly + Baby Connect)  
   - Tests each login (green/red status)  
   - Displays Famly events (left) and BC events (right)  
   - Allows manual syncing (middle column)  
   - Shows matched events in green  

Later, the tool will be packaged as a **Home Assistant add-on**, but the core app is fully standalone and container-friendly.

---

## 📁 Project Structure

Below is the intended structure of this repository. Each section also explains the purpose of the files/folders.

```
famly-bc-sync/
│
├── README.md
│
├── backend/
│   ├── api/
│   │   ├── main.py                # FastAPI app entrypoint; serves routes + frontend
│   │   ├── routes_status.py       # Health & connection testing endpoints
│   │   ├── routes_events.py       # Fetch source/target events for the UI
│   │   ├── routes_sync.py         # Perform Famly→BabyConnect sync operations
│   │
│   ├── core/
│   │   ├── famly_client.py        # Scrapes Famly via Playwright (login, navigate, extract events)
│   │   ├── babyconnect_client.py  # Creates BC entries via Playwright (login, simulate forms)
│   │   ├── normalisation.py       # Converts scraped events into a unified internal event model
│   │   ├── sync_service.py        # Orchestrates scraping, matching, syncing, and error handling
│   │   ├── storage.py             # SQLite DB wrapper (engine/session management, basic CRUD)
│   │   ├── models.py              # DB models: Event, SyncLink, Credential, fingerprints
│   │   ├── config.py              # Environment variable handling (paths, headless mode, etc.)
│   │
│   ├── tests/
│       ├── test_normalisation.py  # Unit tests for event parsing & cleaning
│       ├── test_fingerprints.py   # Unit tests for fingerprint/idempotency logic
│       ├── test_sync.py           # Tests sync orchestration using mocks
│
├── frontend/
│   ├── index.html                 # Frontend entry HTML (for Vite/React)
│   ├── vite.config.ts             # Vite configuration for dev & build
│   ├── tsconfig.json              # TypeScript configuration
│   ├── src/
│   │   ├── main.tsx               # React entrypoint; bootstraps the UI
│   │   ├── App.tsx                # Main dashboard layout (source / sync / target columns)
│   │   ├── components/
│   │   │   ├── ConnectionCard.tsx # Source/target box component with status colours + actions
│   │   │   ├── EventsColumn.tsx   # Column component to display lists of events
│   │   │   ├── SyncControls.tsx   # Middle-column buttons (sync all / sync selected)
│   │   ├── types.ts               # Shared TypeScript types for events, statuses, etc.
│   │
│   ├── public/                    # Static assets (favicon, icons)
│   ├── dist/                      # Built production UI (output of `npm run build`)
│
├── requirements.txt               # Python backend dependencies
├── package.json                   # Frontend dependencies and scripts (React/Vite)
├── tsconfig.json                  # (Frontend) TypeScript config (referenced by Vite)
├── .gitignore                     # Ignore Python, Node, Playwright, build artefacts
│
├── docker/
│   ├── Dockerfile                 # Container image definition (Playwright + backend + built frontend)
│   ├── ha-config.json             # Home Assistant add-on manifest (future deployment)
│
└── data/                          # (Dev only) SQLite DB, Playwright profiles, persisted cookies
```

---

## 🛠️ Technical Architecture

### 1. Headless Browser Automation (Playwright)

Because neither system has an API, the backend uses **Playwright** to:

- Launch a persistent headless Chromium session  
- Log into Famly  
- Navigate to the child activity feed  
- Scrape events using DOM selectors  
- Log into Baby Connect  
- Simulate clicks and field entry to create new events  
- Optionally read back Baby Connect entries for verification

Browser sessions are kept persistent via `user_data_dir` so credentials and cookies survive between runs, reducing the need to log in every time.

The browser automation lives inside:

- `backend/core/famly_client.py`
- `backend/core/babyconnect_client.py`

These modules should expose high-level methods like:

- `FamlyClient(email, password).login_and_scrape()`
- `BabyConnectClient(email, password).add_event_from_normalised(event)`


### 2. Normalised Event Model

All scraped events are converted into a unified structure defined in `backend/core/models.py`, something along the lines of:

```jsonc
{
  "id": 123,
  "source_system": "famly",            // or "baby_connect"
  "fingerprint": "sha256-hash-here",   // deterministic idempotency key
  "child_name": "Eli",
  "event_type": "meal",                // "meal" | "nap" | "nappy" | "pickup" | ...
  "start_time_utc": "2025-01-01T12:00:00Z",
  "end_time_utc": null,
  "details_json": { "raw": "Lunch – ate 75%" },
  "created_at": "2025-01-01T13:00:00Z"
}
```

The **normalisation** logic (parsing text, interpreting dates/times, mapping to event types) is implemented in:

- `backend/core/normalisation.py`

This abstraction allows the rest of the system to ignore the quirks of each provider’s UI and work with a consistent event model.

---

### 3. Fingerprinting (Idempotency)

Neither Famly nor Baby Connect exposes stable event IDs. To avoid duplicates and enable matching, the tool generates a **deterministic fingerprint** for each event, for example:

```text
sha256(
  child_name.trim().lower() +
  event_type +
  start_time_utc (rounded to minute) +
  normalised details snippet
)
```

These fingerprints are stored in the DB and used to:

- Prevent duplicate insertions during scraping  
- Detect whether a Famly event has already been mirrored into Baby Connect  
- Drive the UI’s “matched” (green) state

Fingerprint logic and tests live in:

- `backend/core/normalisation.py`
- `backend/tests/test_fingerprints.py`

---

### 4. Sync Engine (SyncService)

The sync engine orchestrates higher-level operations and lives in:

- `backend/core/sync_service.py`

Responsibilities:

1. Scrape **Famly** events via `FamlyClient` and normalise them.  
2. Scrape **Baby Connect** events via `BabyConnectClient` (for matching) and normalise them.  
3. Store / update events via `storage.py`.  
4. Compare fingerprints from both systems.  
5. For each unmatched Famly event:
   - Invoke the appropriate method on `BabyConnectClient` (e.g. `add_nap`, `add_meal`, etc.) to simulate form submission.  
   - Confirm creation (e.g. re-scrape or trust the outcome) and create a sync link.  
6. Return a structured result (e.g. counts, failures, error messages) for the API and UI.

Sync logic is tested using mocks in:

- `backend/tests/test_sync.py`

---

### 5. Storage Layer (SQLite)

The storage layer uses SQLite (and potentially SQLAlchemy or another ORM) and lives in:

- `backend/core/storage.py`
- `backend/core/models.py`

Core entities:

- `Credential`  
  - Stores encrypted credentials for Famly and Baby Connect.
- `Event`  
  - Stores normalised events from each system.
- `SyncLink`  
  - Links a Famly event to a Baby Connect event and tracks sync status and errors.

The DB file path is configurable via environment variables and typically points to:

- `./data/db.sqlite` (for local dev)  
- `/data/db.sqlite` (inside a container / Home Assistant add-on)

---

### 6. Backend API (FastAPI)

The HTTP API is implemented under `backend/api/` and exposes endpoints such as:

- `POST /api/credentials/{service}`  
  Store or update credentials for a given service (`famly` or `baby_connect`).

- `POST /api/test-connection/{service}`  
  Uses Playwright to log into the selected service and returns a simple OK/ERROR result for the UI.

- `POST /api/scrape/famly`  
  Triggers a scrape of Famly activities, normalises the events, stores them, and returns the latest entries.

- `GET /api/events?source=famly|baby_connect`  
  Returns stored events for the specified source to populate the left/right columns in the UI.

- `POST /api/sync`  
  Performs a sync of unsynced Famly events into Baby Connect, using the SyncService to coordinate everything.

- `GET /api/status`  
  Returns general status information for the dashboard (e.g., whether credentials exist, last successful sync time, connection health).

The FastAPI app also serves the **built frontend** from `frontend/dist/`, making it easy to deploy everything in a single container.

---

### 7. Frontend UI (React + Vite)

The frontend lives under `frontend/` and is built with React and Vite.

Key concepts:

- **Three-column layout**:
  - Left: Famly events list  
  - Middle: Sync controls (buttons)  
  - Right: Baby Connect events list  

- **Connection cards**:
  - One for Famly (source)
  - One for Baby Connect (target)
  - Each shows:
    - Service name
    - Email
    - Connection test button
    - Background colour:
      - Green for success
      - Red for failure
      - Neutral for unknown

- **Event highlighting**:
  - Events that are matched (via sync links and fingerprints) are displayed with a green background or badge in both columns.

The key components:

- `ConnectionCard.tsx`  
  Renders a box for Famly/Baby Connect with the current status and actions.

- `EventsColumn.tsx`  
  Displays a scrollable list of events for either source or target.

- `SyncControls.tsx`  
  Holds buttons like “Sync All” (and later “Sync Selected” or “Auto-sync”).

- `App.tsx`  
  Wires everything together into the 3-column layout.

- `types.ts`  
  Shared TypeScript types that mirror the backend API models for events, statuses, etc.

---

### 8. Docker & Home Assistant Add-on

The `docker/` folder contains:

- `Dockerfile`  
  Builds a container image with:
  - Python backend  
  - Playwright + browsers  
  - Built frontend assets  
  - Uvicorn as the process manager  

- `ha-config.json`  
  A Home Assistant add-on manifest stub that will eventually:
  - Enable ingress (so the UI appears in the HA sidebar)
  - Map `/data` for persistent DB and Playwright profiles
  - Expose configuration options (e.g. headless mode, log level)

The goal is to be able to:

1. Develop locally as a normal web app.  
2. Build a Docker image from the same codebase.  
3. Register that image as a Home Assistant add-on without major code changes.

---

## 🚀 Development Workflow

### Backend (FastAPI)

From the project root:

```bash
# (Recommended) Create a virtual environment first
python -m venv .venv
source .venv/bin/activate  # on Windows use: .venv\Scripts\activate

# Install backend dependencies
pip install -r requirements.txt

# Run the backend API (and static file server for built frontend)
uvicorn backend.api.main:app --reload --port 8000
```

### Frontend (React + Vite)

From the `frontend/` folder:

```bash
npm install
npm run dev      # Starts Vite dev server (usually on http://localhost:5173)
```

For production:

```bash
npm run build    # Builds to frontend/dist/
```

The backend can then serve the static files from `frontend/dist/`.

---

### Recommended for Development

- Set `HEADLESS=false` (e.g. via `.env` or environment variables) to inspect and debug the Playwright browser windows while you develop selectors.  
- Work against real Famly / Baby Connect test accounts to stabilise the scraping and form-filling.  
- Keep DOM selectors in as few places as possible for ease of maintenance.  
- Add unit tests for:
  - Normalisation
  - Fingerprinting
  - SyncService orchestration with mocks (no browser)

---

## 🔮 Future Enhancements

- Fully implement and refine the Home Assistant add-on manifest.  
- Add scheduling (e.g., hourly automatic sync) using a background scheduler.  
- Support multi-child accounts and filters in the UI.  
- Provide manual matching and conflict resolution tools in the UI.  
- Add richer logging and a status/history view.

---

This README is intended as a blueprint so that any developer (including future-you) can quickly understand:

- What the project does  
- How the codebase is laid out  
- How the scraping, normalisation, and syncing work  
- How to run and extend the tool locally and in Home Assistant.
