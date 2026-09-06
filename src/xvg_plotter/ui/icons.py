"""Themed icons rendered from inline Feather-style SVG sources.

Icons are tinted with the active theme's text color at draw time, so a theme
switch calls ``icon(name)`` again (see each widget's ``retheme()``).
"""
from __future__ import annotations

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from .theme import current

_PREAMBLE = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
             'stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">')
_POSTAMBLE = "</svg>"

_SVGS = {
    "folder": '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>',
    "refresh": ('<polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/>'
                '<path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>'),
    "search": '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
    "pin": '<path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>',
}

_CACHE: dict[tuple[str, str], QIcon] = {}


def icon(name: str, color: str | None = None) -> QIcon:
    """Return a themed icon; rendered at 64 px and downscaled by Qt (crisp at UI sizes)."""
    c = color or current().text
    key = (name, c)
    if key not in _CACHE:
        svg = _PREAMBLE.format(c=c) + _SVGS[name] + _POSTAMBLE
        renderer = QSvgRenderer(QByteArray(svg.encode()))
        img = QImage(64, 64, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(Qt.GlobalColor.transparent)
        painter = QPainter(img)
        renderer.render(painter)
        painter.end()
        _CACHE[key] = QIcon(QPixmap.fromImage(img))
    return _CACHE[key]
