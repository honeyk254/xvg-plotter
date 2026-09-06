"""Export helpers (SPEC §8)."""
from __future__ import annotations

import io
from pathlib import Path

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication


def save_figure(fig, path: Path, dpi: int = 300, transparent: bool = False) -> None:
    fig.savefig(path, dpi=dpi, transparent=transparent, bbox_inches="tight")


def render_image(fig, dpi: int = 300, transparent: bool = False) -> QImage:
    """Render the figure at an explicit DPI, independent of the on-screen widget
    size — the clipboard copy shares the export pipeline's resolution (C31)."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, transparent=transparent,
                bbox_inches="tight")
    img = QImage.fromData(buf.getvalue(), "PNG")
    if img.isNull():
        raise RuntimeError("could not render the plot to an image")
    return img


def copy_image(canvas, dpi: int = 300, transparent: bool = False) -> QImage:
    img = render_image(canvas.figure, dpi, transparent)
    QApplication.clipboard().setImage(img)
    return img
