"""Update-check helpers (C02). Pure functions; networking lives in the UI layer.

The release URLs point at the project's GitHub releases; until the repository
has a public remote they simply return an error, which the UI reports as
"could not check".
"""
from __future__ import annotations

RELEASES_URL = "https://api.github.com/repos/honeyk254/xvg-plotter/releases/latest"
DOWNLOADS_URL = "https://github.com/honeyk254/xvg-plotter/releases/latest"


def parse_version(v: str) -> tuple[int, ...]:
    """'v1.2.3' / '1.0' / 'V2.10.1-beta' -> (1, 2, 3) / (1, 0) / (2, 10, 1)."""
    core = str(v).strip().lstrip("vV").split("-")[0]
    parts = []
    for tok in core.split(".")[:4]:
        digits = "".join(ch for ch in tok if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def is_newer(remote: str, local: str) -> bool:
    a, b = parse_version(remote), parse_version(local)
    n = max(len(a), len(b))
    a += (0,) * (n - len(a))
    b += (0,) * (n - len(b))
    return a > b


def latest_from_json(data) -> str | None:
    """tag_name out of a GitHub releases/latest payload ('v1.0.2' -> '1.0.2')."""
    tag = data.get("tag_name") if isinstance(data, dict) else None
    return tag.lstrip("vV") if isinstance(tag, str) and tag else None
