"""Data models for parsed XVG files (SPEC §4)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np

Kind = Literal["xy", "xydy", "xydx", "xydxdy"]


@dataclass
class SeriesSpec:
    """Semantic view over dataset columns (SPEC §4)."""

    y_col: int
    legend: str | None = None
    kind: Kind = "xy"
    dy_col: int | None = None
    dx_col: int | None = None


@dataclass
class Dataset:
    """One '&'-separated data block; columns[0] is X."""

    index: int
    columns: list[np.ndarray]
    series: list[SeriesSpec]

    @property
    def x(self) -> np.ndarray:
        return self.columns[0]


@dataclass
class ParseStats:
    rows_ok: int = 0
    rows_skipped: int = 0
    directives_ignored: int = 0
    n_cols: int = 0


@dataclass
class XvgFile:
    path: Path
    datasets: list[Dataset] = field(default_factory=list)
    title: str | None = None
    subtitle: str | None = None
    x_label: str | None = None
    y_label: str | None = None
    warnings: list[str] = field(default_factory=list)
    stats: ParseStats = field(default_factory=ParseStats)


def series_label(s: SeriesSpec, y_label: str | None = None,
                 series_count: int = 1) -> str:
    """Single source for series display names (dock, legend, averages).

    Preference: `@ sN legend` from the file, then the file's y-axis label when
    the dataset has a single series (e.g. "RMSD (nm)"), else the column number.
    """
    if s.legend:
        return s.legend
    if series_count == 1 and (y_label or "").strip():
        return y_label.strip()
    return f"column {s.y_col}"
