"""Plot option lists shared by the style dock and the canvas.

Deliberately Qt- and matplotlib-free so lightweight widgets can import it.
"""
from __future__ import annotations

LEGEND_LOCS = ["best", "upper right", "upper left", "lower left", "lower right",
               "right", "outside right", "off"]
LINE_STYLES = {"Solid": "-", "Dashed": "--", "Points": "o"}
PALETTES: dict[str, list[str] | None] = {
    # first entry = the default palette; Okabe–Ito keeps up to 8 overlaid series
    # distinguishable for colorblind readers (C17)
    "Okabe–Ito (colorblind-safe)": ["#0072B2", "#D55E00", "#009E73", "#E69F00",
                                    "#CC79A7", "#56B4E9", "#F0E442", "#000000"],
    "Default": None,  # matplotlib default cycle
    "Vibrant": ["#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4", "#00b3c8", "#f032e6", "#8c6d31"],
    "Muted": ["#7f8c9b", "#8e6c8a", "#6a8caf", "#9b8a5f", "#6f9b7f", "#a0716f", "#5f7f9b", "#9b6f5f"],
}
