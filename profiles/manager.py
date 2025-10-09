"""Загрузка и управление профилями парсинга."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

from core.config import get_settings


def _resolve_profiles_path() -> Path:
    settings = get_settings()
    path = settings.resolve_path(settings.profiles_path)
    if path.exists():
        return path
    fallback = Path(__file__).resolve().parent / "parsing_profiles.json"
    return fallback


@lru_cache(maxsize=1)
def load_profiles() -> Dict[str, Any]:
    path = _resolve_profiles_path()
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def refresh_profiles() -> Dict[str, Any]:
    load_profiles.cache_clear()
    return load_profiles()


__all__ = ["load_profiles", "refresh_profiles"]
