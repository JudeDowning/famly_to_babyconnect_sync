"""
Baby Connect client (automation).
---------------------------------

This module uses Playwright to:

- Log into Baby Connect
- Open the appropriate activity entry forms (meal, nap, nappy, etc.)
- Fill them based on a normalised event
- Submit the forms to create events as if a user did it manually
"""

from __future__ import annotations

from typing import Dict, Any
from playwright.sync_api import sync_playwright

from .config import BABYCONNECT_PROFILE_DIR, HEADLESS
from .normalisation import normalise_babyconnect_event  # might be used for verification

BABYCONNECT_LOGIN_URL = "https://www.babyconnect.com/"  # TODO: verify exact URL

class BabyConnectClient:
    def __init__(self, email: str, password: str) -> None:
        self.email = email
        self.password = password

    def _login(self):
        # Internal: start browser and ensure we are logged in.
        pass

    def add_event_from_normalised(self, event: Dict[str, Any]) -> None:
        """
        Given a normalised event dictionary, trigger the appropriate UI flow in
        Baby Connect to create the event.

        For example:
        - event_type="meal" => click "Meal" button and fill notes/time
        - event_type="nap" => click "Sleep" button and set start/end
        """
        # TODO: implement UI automation with Playwright
        raise NotImplementedError("BabyConnectClient.add_event_from_normalised is not implemented yet.")
