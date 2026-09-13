"""Export helpers (SPEC §8)."""
from __future__ import annotations

import io
from pathlib import Path

import numpy as np
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication


def save_figure(fig, path: Path, dpi: int = 300, transparent: bool = False,
                tight: bool = True) -> None:
    """tight=True crops to content; tight=False honors the exact figure size
    (the publication-size workflow, C16)."""
    if tight:
        fig.savefig(path, dpi=dpi, transparent=transparent, bbox_inches="tight")
    else:
        fig.savefig(path, dpi=dpi, transparent=transparent)


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


def print_figure(fig, printer) -> None:
    """Draw the figure onto a QPrinter at the printer's resolution (C33)."""
    from PySide6.QtPrintSupport import QPrinter  # local: QtPrintSupport is optional to load

    img = render_image(fig, dpi=printer.resolution())
    painter = QPainter(printer)
    try:
        page = printer.pageRect(QPrinter.Unit.DevicePixel)
        scaled = img.scaled(int(page.width()), int(page.height()),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation)
        painter.drawImage(
            QPointF((page.width() - scaled.width()) / 2,
                    (page.height() - scaled.height()) / 2),
            scaled)
    finally:
        painter.end()


def write_csv(path: Path, sections) -> None:
    """Write plotted series as CSV — one block per section (C30).

    sections: iterable of (comments: list[str], headers: list[str],
    columns: list[array]); columns within a section must have equal length."""
    out = []
    for comments, headers, cols in sections:
        buf = io.StringIO()
        np.savetxt(buf, np.column_stack(cols), delimiter=",", fmt="%.10g",
                   header="\n".join(list(comments) + [",".join(headers)]),
                   comments="# ")
        out.append(buf.getvalue().strip("\n"))
    Path(path).write_text("\n\n".join(out) + "\n", encoding="utf-8")
