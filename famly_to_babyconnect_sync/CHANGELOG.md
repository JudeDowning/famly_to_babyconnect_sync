# Changelog

## 0.0.38
- Baby Connect entry writers now copy the exact Famly detail payload (e.g. BM | Very loose, meal menus, sleep summaries) into the note field before appending [Sync], and the scraper records those lines so canonical snippets are identical on both sides.
- Diaper detail payloads retain the first HH:MM ... row after stripping the timestamp, so type information like BM survives hashing.
- Rebuilt the add-on image with the updated backend logic.

## 0.0.36
- `/api/debug/events` (and the Settings → Debug viewer) now include each event's `fingerprint`, making it easier to compare Famly vs Baby Connect rows when troubleshooting matching issues.

## 0.0.37
- Canonical detail snippets now skip the Baby Connect auto-generated headline (child name, "Famly - …") and fall back to the note/original title, so the fingerprints hash the same text as Famly again.
- `normalise_famly_event`/`normalise_babyconnect_event` pass the child name into the canonicaliser to ensure consistent hashes across both systems.

## 0.0.32
- Front-end pairing now keys off the same canonical detail snippet used by the backend (ignoring the first detail line and `[Sync]` markers), so Famly entries you pushed into Baby Connect immediately show up as matched instead of lingering in the "Missing" list.

## 0.0.33
- Baby Connect automation now copies the Famly detail text (e.g. "Loose", meal menus, sleep summaries) into the note field before appending `[Sync]`, and the comparison view treats that note/original title as part of the canonical signature. This lets nappies, sleeps, and other entries created via the add-on line up 1:1 with their Famly counterparts.

## 0.0.34
- Backend matching logic now compares Famly and Baby Connect fingerprints (the canonical detail signature) instead of just day+start minute, so entries you synced—like nappies and sleeps with slight timestamp drift—are recognised as matched rather than staying "missing".

## 0.0.35
- The canonical detail snippet used by fingerprints now ignores leading time lines, strips `[Sync]`, collapses whitespace, and lowercases everything so Famly and Baby Connect entries generate identical hashes even when their casing or notes differ.

## 0.0.31
- Fingerprints now use a canonical detail snippet for both Famly and Baby Connect events (stripping the first detail line and `[Sync]` suffixes), so solids/nappies you sync into Baby Connect match back to their Famly originals instead of appearing as outstanding items.

## 0.0.30
- Restored proper ISO timestamp parsing when normalising Famly/Baby Connect events so `start_time_utc` is derived from the scraped `event_datetime_iso` instead of silently defaulting to the current time, fixing the regression that caused scrapes to fail with `"NoneType has no attribute 'replace'"` errors.

## 0.0.29
- Added a safety fallback when normalising events: if a Famly or Baby Connect entry is missing a parseable start time, we now default to the current UTC time instead of crashing, preventing fresh scrapes from failing mid-run.

## 0.0.28
- Famly scraper now falls back to the first child entry automatically if no specific `FAMLY_CHILD_ID` selector is configured, preventing fresh installs from failing before a child profile is selected.
- Front-end scrape watchers now stop even when a scrape fails, so `/api/scrape/progress` polling ceases promptly after errors and the progress overlay closes reliably.
- Rebuilt the frontend bundle with the watcher fix.

## 0.0.27
- Baby Connect sleep events now parse the "start to end" time range from the detail lines and populate `end_time_utc`, so overnight sleeps are displayed in the correct chronological order the following morning.
- The comparison view now sorts Baby Connect sleep entries using the day label plus the wake-up time so overnight sleeps appear in the morning slot of the correct day.

## 0.0.26
- Prevent Baby Connect diaper syncs from failing if the modal takes too long to detach; we now tolerate the lingering dialog instead of raising an exception.

## 0.0.25
- Relaxed the duplicate detector by stripping portion descriptors (text inside parentheses) from Famly detail lines, so meals like "Fruit platter (Half)" vs "Fruit platter (Little)" still count as duplicates.
- Rebuilt the frontend bundle with the updated normalization.

## 0.0.24
- Duplicate detection now looks at the explicit time tokens embedded in Famly detail lines, so solids/meals logged at 16:05 vs 15:50 are correctly highlighted even if their stored `start_time_utc` matches.
- Rebuilt the frontend bundle with the improved detector.

## 0.0.23
- Highlight potential duplicate Famly entries (same content, same day, different times) with a yellow tile plus "Possible duplicate" badge, so you can spot them before syncing.
- Ignore overlay now uses a denser hatch pattern for better visibility.
- Rebuilt the frontend bundle with the duplicate detector and styling tweaks.

## 0.0.22
- Ignored Famly cards now show a hatched overlay across the entire tile so it’s obvious they’ll be skipped during syncs.
- Rebuilt the frontend bundle to include the updated styling.

## 0.0.21
- Added an "Ignore" toggle beneath each Famly entry so you can mark duplicates directly in the comparison view; ignored rows gray out and are excluded from the "missing" counts.
- Rebuilt the frontend bundle with the new controls.

## 0.0.20
- Scrape progress overlay now fills in the Famly/Baby Connect counters as soon as the API response returns, so you still see how many entries were captured even when the scrape finishes too quickly for the polling loop to catch intermediate updates.
- Rebuilt the frontend bundle to include the progress fix.

## 0.0.19
- Connection chips switch to a stacked layout on =640px screens so the service name, status, and "Last scrape" text each get their own line instead of being squashed horizontally.
- Rebuilt the frontend bundle to ship the mobile layout tweak.

## 0.0.18
- Day column headers now use a shorter weekday (e.g. "Fri") and a reduced font size so the Famly/date/Baby Connect labels no longer overlap on 375×667 mobile layouts.
- Rebuilt the frontend bundle to include the CSS/JS changes.

## 0.0.17
- Status chips now reset to green after a successful scrape and show "Last scrape: DD/MM/YY HH:MM" by exposing the most recent scrape timestamp from the backend.
- The `/api/status` endpoint now returns `last_scraped_at` for Famly and Baby Connect so the UI can render those timestamps.
- Backend avoids unnecessary Baby Connect re-scrapes when a sync fails, and diaper dialog radio buttons are now forced via their label when hidden.
- Rebuilt the frontend bundle with the new status UI.

## 0.0.16
- Added a sync progress overlay that shows an "X of Y" counter for both single-entry pushes and Sync All so you can track Home Assistant automations while they run.
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
- Seed default Famly ? Baby Connect event mappings (meals, nappy, sleep, sign in/out) so fresh installs have sensible sync starters.

## 0.0.2
- Improved Home Assistant compatibility: ingress-friendly frontend, persistent data paths, and Playwright-backed container image.

