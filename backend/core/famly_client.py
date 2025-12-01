"""
Famly client (scraping).
------------------------

This module contains a thin wrapper around Playwright to:

- Launch a browser context (headless or not, depending on config)
- Log into Famly using email/password
- Navigate to the relevant activity view
- Extract a list of RawFamlyEvent objects

Only high-level behaviour is sketched here; DOM selectors and flows need to be
implemented against the real Famly web app.
"""

from __future__ import annotations

from typing import List
from playwright.sync_api import sync_playwright

from .config import FAMLY_PROFILE_DIR, HEADLESS
from .normalisation import RawFamlyEvent

FAMLY_LOGIN_URL = "https://app.famly.co/"  # TODO: verify exact URL

class FamlyClient:
    def __init__(self, email: str, password: str) -> None:
        self.email = email
        self.password = password

    def login_and_scrape(self) -> List[RawFamlyEvent]:
        """
        Main entrypoint: log into Famly (if necessary) and return a list of
        raw scraped events.

        In development, set HEADLESS=false to watch the flow and tweak selectors.
        """
        events: List[RawFamlyEvent] = []

        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(FAMLY_PROFILE_DIR),
                headless=HEADLESS,
            )
            page = browser.new_page()
            page.goto(FAMLY_LOGIN_URL, wait_until="networkidle")

            # TODO: Implement login detection and form fill
            # if page.is_visible("input[type=email]"):
            #     page.fill("input[type=email]", self.email)
            #     page.fill("input[type=password]", self.password)
            #     page.click("button:has-text('Log in')")
            #     page.wait_for_load_state("networkidle")

            # TODO: Navigate to activity feed and scrape cards
            # cards = page.query_selector_all("CSS-SELECTOR-FOR-ACTIVITY-CARD")
            # for card in cards:
            #     # Extract text and construct RawFamlyEvent
            #     events.append(RawFamlyEvent(...))

            browser.close()

        return events
