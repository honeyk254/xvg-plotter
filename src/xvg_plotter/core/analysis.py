"""Analysis extras: averaging, smoothing, time-unit conversion (SPEC §7)."""
from __future__ import annotations

import re

import numpy as np

UNITS = {"ps": 1.0, "ns": 1e-3, "µs": 1e-6, "ms": 1e-9}


def moving_average(y, window: int) -> np.ndarray:
    """Centered moving average, edge-padded; even windows rounded up to odd."""
    window = max(int(window), 1)
    if window % 2 == 0:
        window += 1
    y = np.asarray(y, dtype=float)
    if window <= 1 or y.size == 0:
        return y
    pad = window // 2
    yp = np.pad(y, pad, mode="edge")
    return np.convolve(yp, np.full(window, 1.0 / window), mode="valid")


def average_replicas(curves) -> tuple[np.ndarray, np.ndarray, np.ndarray, str | None]:
    """curves: list of (x, y). Aligns all onto the first X grid and returns
    (x, mean, std, warning). Assumes X ascending (GROMACS output always is)."""
    x0 = np.asarray(curves[0][0], dtype=float)
    ys: list[np.ndarray] = []
    aligned = False
    for x, y in curves:
        x = np.asarray(x, dtype=float)
        if len(x) == len(x0) and np.array_equal(x, x0):
            ys.append(np.asarray(y, dtype=float))
        else:
            ys.append(np.interp(x0, x, np.asarray(y, dtype=float)))
            aligned = True
    stack = np.stack(ys)
    mean = np.nanmean(stack, axis=0)
    std = np.nanstd(stack, axis=0, ddof=1) if len(curves) > 1 else np.zeros_like(mean)
    warn = "replica X grids differ; aligned by interpolation onto the first file" if aligned else None
    return x0, mean, std, warn


def auto_unit(x) -> str:
    """Largest unit such that the scaled axis max is >= 1 (SPEC §7.3)."""
    m = float(np.nanmax(np.abs(x))) if np.asarray(x).size else 0.0
    for u in ("ms", "µs", "ns"):
        if m * UNITS[u] >= 1.0:
            return u
    return "ps"


def scale_label(label: str | None, unit: str) -> str:
    if label is None:
        return f"Time ({unit})"
    if "(ps)" in label:
        return label.replace("(ps)", f"({unit})")
    if re.search(r"\bps\b", label):
        return re.sub(r"\bps\b", unit, label, count=1)
    return f"{label} ({unit})"


def convert_x(x, unit: str) -> np.ndarray:
    return np.asarray(x, dtype=float) * UNITS[unit]
