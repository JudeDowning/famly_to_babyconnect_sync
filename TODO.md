# TODO.md — Famly → Baby Connect Sync Project Plan

A structured development plan for turning this project into a fully functional app + eventual Home Assistant add-on.

---

# ✔️ 0. Environment & Setup

- ✔️ Create GitHub repo (`famly-to-babyconnect`)
- ✔️ Add initial scaffold (backend, frontend, Docker, README)
- ✔️ Create Python virtual environment (`python -m venv .venv`)
- ✔️ Configure VSCode to auto-activate `.venv`
- ✔️ Install backend deps (`pip install -r requirements.txt`)
- ✔️ Install Playwright browsers (`playwright install`)
- ✔️ Create `data/` folder for SQLite
- ✔️ Run backend (`uvicorn backend.api.main:app --reload --port 8000`)
- ✔️ Install frontend deps (`npm install`)
- ✔️ Run frontend dev server (`npm run dev`)

---

# 1. Database & Models

- ✔️ Define SQLAlchemy models:
  - `Credential`
  - `Event`
  - `SyncLink`
- ✔️ Configure engine + session + `init_db()`
- ✔️ Ensure DB directory exists before connecting
- ✔️ Call `init_db()` on startup
- ✔️ Test `/api/status` returns without error on fresh DB

---

# 2. Credentials Management

### Backend
- ✔️ Add endpoint: `POST /api/credentials/{service}`
- ✔️ Store email + password (later encrypted)
- ✔️ Add `GET /api/credentials/{service}` for showing stored email
- ✔️ Extend `/api/status` to include stored email

### Frontend
- ✔️ Add UI in `ConnectionCard` or modal:
  - Email input
  - Password input
  - Save button → POST to `/api/credentials/{service}`
- ✔️ Refresh connection status after saving

---

# 3. Famly Scraping (Read-Side)

### 3.1 DOM Inspection
- ⬜ Inspect Famly login page & activity feed
- ⬜ Identify selectors:
  - login fields
  - activity cards
  - child name
  - time string
  - event type
  - raw text

### 3.2 Implement `FamlyClient`
- ⬜ Implement login (Playwright)
- ⬜ Navigate to activity feed
- ⬜ Scrape cards → `RawFamlyEvent[]`
- ⬜ Return raw events

### 3.3 Store in DB
- ✔️ Normalisation function ready
- ✔️ DB insertion with fingerprint dedupe
- ⬜ Test `/api/scrape/famly`
- ⬜ Verify `GET /api/events?source=famly`

---

# 4. Baby Connect Scraping (Optional)

- ⬜ Inspect DOM for Baby Connect activity list
- ⬜ Implement minimal `BabyConnectClient.login_and_scrape`
- ⬜ Normalise Baby Connect events
- ⬜ Expose via `/api/events?source=baby_connect`

---

# 5. Baby Connect Automation (Write-Side)

### 5.1 DOM Inspection
- ⬜ Identify selectors for:
  - login
  - meal form
  - nap form
  - nappy form

### 5.2 Event Creation
- ⬜ Implement `_login()` in BabyConnectClient
- ⬜ Implement helper functions:
  - `add_meal(event)`
  - `add_nap(event)`
  - `add_nappy(event)`
- ⬜ Implement `add_event_from_normalised`

---

# 6. Sync Engine (Backend)

- ⬜ Load unsynced Famly events (no SyncLink)
- ⬜ Create BabyConnectClient
- ⬜ Write events into Baby Connect
- ⬜ Create `SyncLink` for successes
- ⬜ Return sync summary:
  ```json
  { "status": "ok", "synced": N, "failed": M }
  ```

---

# 7. Frontend Integration

- ✔️ Basic layout (3 columns)
- ⬜ Bind connection card to real status
- ⬜ Add credential forms
- ⬜ Wire “Scrape Famly” → `/api/scrape/famly`
- ⬜ Wire “Sync All” → `/api/sync`
- ⬜ Highlight matched events (via SyncLink)

---

# 8. Home Assistant Add-on (Later)

- ⬜ Complete `docker/ha-config.json`
- ⬜ Enable Ingress
- ⬜ Bind `/data` for DB + Playwright profiles
- ⬜ Build final Docker image
- ⬜ Test installation inside HA

---

# 9. Future Enhancements

- ⬜ Auto-sync scheduler
- ⬜ Multi-child support
- ⬜ Conflict resolution UI
- ⬜ Better error logging
- ⬜ Password encryption
