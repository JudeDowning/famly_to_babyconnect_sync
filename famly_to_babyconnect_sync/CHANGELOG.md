# Changelog

## 0.0.18
- Day column headers now use a shorter weekday (e.g. "Fri") and a reduced font size so the Famly/date/Baby Connect labels no longer overlap on 375×667 mobile layouts.
- Rebuilt the frontend bundle to include the CSS/JS changes.

## 0.0.19
- Connection chips switch to a stacked layout on ≤640px screens so the service name, status, and “Last scrape” text each get their own line instead of being squashed horizontally.
- Rebuilt the frontend bundle to ship the mobile layout tweak.

## 0.0.20
- Scrape progress overlay now fills in the Famly/Baby Connect counters as soon as the API response returns, so you still see how many entries were captured even when the scrape finishes too quickly for the polling loop to catch intermediate updates.
- Rebuilt the frontend bundle to include the progress fix.

## 0.0.21
- Added an “Ignore” toggle beneath each Famly entry so you can mark duplicates directly in the comparison view; ignored rows gray out and are excluded from the “missing” counts.
- Rebuilt the frontend bundle with the new controls.

## 0.0.17
- Status chips now reset to green after a successful scrape and show “Last scrape: DD/MM/YY HH:MM” by exposing the most recent scrape timestamp from the backend.
- The `/api/status` endpoint now returns `last_scraped_at` for Famly and Baby Connect so the UI can render those timestamps.
- Backend avoids unnecessary Baby Connect re-scrapes when a sync fails, and diaper dialog radio buttons are now forced via their label when hidden.
- Rebuilt the frontend bundle with the new status UI.

## 0.0.16
- Added a sync progress overlay that shows an “X of Y” counter for both single-entry pushes and Sync All so you can track Home Assistant automations while they run.
- Famly rows that fail to sync now remain highlighted with a warning arrow, making retries obvious in the comparison grid.
- Frontend bundle rebuilt with the new progress/failure UI refinements.

## 0.0.15
- Baby Connect "potty" events now display as "Potty" with the correct icon in both the comparison view and the Famly column. Rebuilt the frontend bundle.

## 0.0.14
- Mapping UI now normalizes stored targets so the dropdown reflects the actual configured type (instead of defaulting to Solid) and rebuilt the frontend bundle.

## 0.0.13
- Baby Connect scraper now stores the `posted_by` person (parsed from the "by ..." tag) alongside the time so we can reference who logged each event. Existing `raw_data.author` continues to hold the timestamp for compatibility.

## 0.0.12
- Added `/api/debug/events` endpoint plus a "Scraped data (debug)" section in the settings drawer so you can inspect the raw Famly/Baby Connect rows directly from the UI.
- Rebuilt the frontend bundle with the debug view.

## 0.0.11
- Sleep rows are now sorted using the end time only when they span past midnight (start > end) so overnight Baby Connect sleeps appear at the correct spot in the following morning's list; all other events keep using their start time.

## 0.0.10
- Overnight Baby Connect sleep entries remain in the day they were scraped (the "Today" list) but are ordered using their end time so morning wake-ups appear in the correct chronological slot.
- Rebuilt the frontend bundle with the ordering tweak.

## 0.0.9
- Overnight Baby Connect sleep entries now appear on the day they end, using the end time for both sorting and display in the UI.
- Rebuilt the frontend bundle to include the new grouping logic.

## 0.0.8
- Filter out Famly's "Expected pick up" entries during scraping so they never reach the database or UI.

## 0.0.7
- Served icon assets via the ingress-aware path so event icons render correctly inside the HA add-on UI.
- Fixed residual mojibake in the progress overlay and rebuilt the frontend bundle.

## 0.0.6
- Made the Famly child profile selector configurable via `FAMLY_CHILD_ID` and added a fallback that clicks the first child entry when the configured ID isn’t found. Scrape failures now log a clear runtime error instead of timing out silently.
- Cleaned up the progress overlay text so it displays "Scraping …" without mojibake.
- Rebuilt the frontend bundle after the text fix.

## 0.0.5
- Added API logging/exception handling for scrape/sync endpoints so failures show up in Home Assistant logs.
- Added backend credential test endpoint plus frontend integration so the "Test" buttons actually verify logins.
- Added lightweight login verification helpers in both Famly and Baby Connect clients.
- Rebuilt the frontend bundle with the new credential test UI.

## 0.0.4
- Frontend API calls now respect the Home Assistant ingress prefix, fixing credential and settings operations inside the HA UI.
- Rebuilt the frontend bundle with the ingress-aware fetch logic.

## 0.0.3
- Seed default Famly → Baby Connect event mappings (meals, nappy, sleep, sign in/out) so fresh installs have sensible sync starters.

## 0.0.2
- Improved Home Assistant compatibility: ingress-friendly frontend, persistent data paths, and Playwright-backed container image.
