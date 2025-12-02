import json
from pathlib import Path
from typing import Any, Dict

from .config import BASE_DIR

SETTINGS_DIR = BASE_DIR / "data"
SETTINGS_PATH = SETTINGS_DIR / "settings.json"
DEFAULT_SETTINGS: Dict[str, Any] = {}

_settings_cache: Dict[str, Any] | None = None


def _ensure_loaded() -> Dict[str, Any]:
    global _settings_cache
    if _settings_cache is not None:
        return _settings_cache

    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    if SETTINGS_PATH.exists():
        try:
            with SETTINGS_PATH.open("r", encoding="utf-8") as f:
                _settings_cache = json.load(f)
        except json.JSONDecodeError:
            _settings_cache = DEFAULT_SETTINGS.copy()
    else:
        _settings_cache = DEFAULT_SETTINGS.copy()
        _save()
    return _settings_cache


def _save() -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    data = _settings_cache or DEFAULT_SETTINGS.copy()
    with SETTINGS_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_settings() -> Dict[str, Any]:
    return _ensure_loaded()

