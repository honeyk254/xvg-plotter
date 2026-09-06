"""Export helpers (SPEC §8)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication


def save_figure(fig, path: Path, dpi: int = 300, transparent: bool = False) -> None:
    fig.savefig(path, dpi=dpi, transparent=transparent, bbox_inches="tight")


def copy_image(canvas) -> None:
    QApplication.clipboard().setPixmap(canvas.grab())
