# Changelog

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
