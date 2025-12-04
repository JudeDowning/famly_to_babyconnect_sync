# Changelog

## 0.0.11
- Sleep rows are now sorted using the end time only when they span past midnight (start > end) so overnight Baby Connect sleeps appear at the correct spot in the following morning’s list; all other events keep using their start time.

## 0.0.10
- Overnight Baby Connect sleep entries remain in the day they were scraped (the “Today” list) but are ordered using their end time so morning wake-ups appear in the correct chronological slot.
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
- Cleaned up the progress overlay text so it displays “Scraping …” without mojibake.
- Rebuilt the frontend bundle after the text fix.

## 0.0.5
- Added API logging/exception handling for scrape/sync endpoints so failures show up in Home Assistant logs.
- Added backend credential test endpoint plus frontend integration so the “Test” buttons actually verify logins.
- Added lightweight login verification helpers in both Famly and Baby Connect clients.
- Rebuilt the frontend bundle with the new credential test UI.

## 0.0.4
- Frontend API calls now respect the Home Assistant ingress prefix, fixing credential and settings operations inside the HA UI.
- Rebuilt the frontend bundle with the ingress-aware fetch logic.

## 0.0.3
- Seed default Famly → Baby Connect event mappings (meals, nappy, sleep, sign in/out) so fresh installs have sensible sync starters.

## 0.0.2
- Improved Home Assistant compatibility: ingress-friendly frontend, persistent data paths, and Playwright-backed container image.
## 0.0.12
- Added `/api/debug/events` endpoint plus a “Scraped data (debug)” section in the settings drawer so you can inspect the raw Famly/Baby Connect rows directly from the UI.
- Rebuilt the frontend bundle with the debug view.
