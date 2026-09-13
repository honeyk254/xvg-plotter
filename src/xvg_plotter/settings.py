"""QSettings persistence (SPEC §9)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings

_s = QSettings("XVGPlotter", "XVGPlotter")

THEME_AUTO, THEME_LIGHT, THEME_DARK = "auto", "light", "dark"
RECENTS_MAX = 10


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


def pinned() -> list[str]:
    v = _s.value("pinned", [])
    if v is None or v == "":
        return []
    if isinstance(v, str):
        return [v]
    return [str(x) for x in v]


def toggle_pinned(path: str) -> bool:
    """Pin/unpin a folder; returns the new state (C14)."""
    p = str(path)
    cur = pinned()
    if p in cur:
        cur.remove(p)
    else:
        cur = [p] + [x for x in cur if x != p]
    _s.setValue("pinned", cur)
    return p in cur


def recent_items() -> list[str]:
    """Pinned folders first, then recents, dead entries pruned (C14)."""
    pin = [x for x in pinned() if Path(x).is_dir()]
    rec = [x for x in recents() if Path(x).is_dir() and x not in pin]
    return pin + rec[:RECENTS_MAX]


def add_recent(path: str) -> None:
    p = str(path)
    # dead entries are pruned here so the list never fills with stale paths
    r = [p] + [x for x in recents() if x != p and Path(x).is_dir()]
    _s.setValue("recents", r[:RECENTS_MAX])


def export_settings(path: str) -> int:
    """Copy every setting into an INI file (C40). Returns the key count."""
    dst = QSettings(str(path), QSettings.Format.IniFormat)
    keys = _s.allKeys()
    for k in keys:
        dst.setValue(k, _s.value(k))
    dst.sync()
    return len(keys)


def import_settings(path: str) -> int:
    """Load settings from an INI file over the current ones (C40)."""
    src = QSettings(str(path), QSettings.Format.IniFormat)
    keys = src.allKeys()
    for k in keys:
        _s.setValue(k, src.value(k))
    _s.sync()
    return len(keys)
