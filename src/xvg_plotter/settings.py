"""QSettings persistence (SPEC §9)."""
from __future__ import annotations

from PySide6.QtCore import QSettings

_s = QSettings("XVGPlotter", "XVGPlotter")

THEME_AUTO, THEME_LIGHT, THEME_DARK = "auto", "light", "dark"


def get(key: str, default=None):
    return _s.value(key, default)


def set_(key: str, value) -> None:
    _s.setValue(key, value)


def theme_mode() -> str:
    mode = str(get("theme", THEME_AUTO))
    return mode if mode in (THEME_AUTO, THEME_LIGHT, THEME_DARK) else THEME_AUTO


def set_theme_mode(mode: str) -> None:
    set_("theme", mode)


def recents() -> list[str]:
    v = _s.value("recents", [])
    if v is None or v == "":
        return []
    if isinstance(v, str):
        return [v]
    return [str(x) for x in v]


def add_recent(path: str) -> None:
    p = str(path)
    r = [p] + [x for x in recents() if x != p]
    _s.setValue("recents", r[:10])
