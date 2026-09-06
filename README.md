# XVG Plotter

<p align="center">
  <img src="docs/screenshot-dark.png" alt="XVG Plotter — dark theme" width="820">
</p>

**Interactive cross-platform desktop viewer for GROMACS `.xvg` analysis files** — a modern
replacement for xmgrace, built with PySide6 + matplotlib.

![Release](https://img.shields.io/github/v/release/honeyk254/xvg-plotter)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-informational)
![Tests](https://img.shields.io/badge/tests-24%20passing-brightgreen)

<p align="center">
  <table>
    <tr>
      <td align="center"><img src="docs/screenshot-dark.png" alt="dark theme" width="420"><br><sub><b>Dark</b> — follows your OS theme</sub></td>
      <td align="center"><img src="docs/screenshot-light.png" alt="light theme" width="420"><br><sub><b>Light</b> — switch anytime from the View menu</sub></td>
    </tr>
  </table>
</p>

## Why

MD simulation workflows produce hundreds of `.xvg` files. xmgrace is powerful but dated;
opening files one by one to eyeball convergence is slow. XVG Plotter scans a folder,
lists every file with its metadata, and gets you from *file* to *figure* in one click —
including overlays, replica averaging, and clipboard-ready exports for slides.

## Features

- **Browse** an analysis folder: every `.xvg` listed with title, series count, points, size,
  modified date — parsed from headers, problem files flagged in red with the reason.
- **Plot instantly**: click a file — title, axis labels and legend are pulled from the XVG header.
- **Compare**: checkbox several files to overlay them; select replicas and toggle
  **Average replicas** for a mean ± SD band (with faint member curves).
- **Annotate**: moving-average smoothing overlay (adjustable window), ps → ns/µs/ms time-axis
  conversion with relabeling, log axes, grid, legend placement, color palettes,
  line style/width, title and label overrides.
- **Interact**: pan, zoom, home, live cursor coordinates; click a legend entry to
  show/hide a series. Style tweaks keep your zoom.
- **Theme**: polished light & dark UI (Fusion + themed matplotlib canvas).
  Auto (follows the OS) / Light / Dark, remembered between runs.
- **Export**: PNG (DPI 100–600), PDF, SVG, EPS, transparent background — plus
  *Copy Image* straight to the clipboard for slides.
- **Native app**: own icon, single-instance (opening a second `.xvg` reuses the running
  window), recent folders, remembered window/export settings. No command line required.

## Download

Grab `XVGPlotter.exe` from the [latest release](https://github.com/honeyk254/xvg-plotter/releases/latest)
— it's portable: double-click and run, no installer, no admin.

| OS | Status |
|---|---|
| Windows | ✅ portable exe attached to releases |
| macOS / Linux | build from source (PyInstaller cannot cross-compile — `python packaging/build.py` on the target OS) |

Double-clicking an `.xvg` file (where the association is registered) opens it directly in the app;
launching with a file argument plots it immediately.

## Build from source

Requirements: Python ≥ 3.10.

```bash
pip install -e .[dev]

# Windows (PyInstaller exe; adds an Inno Setup installer if ISCC.exe is installed)
python packaging/build.py

# macOS (app bundle + DMG) / Linux (AppImage)
python packaging/build.py
```

Artifacts land in `dist/`. Icons are generated with `python assets/make_icons.py` (Pillow).

## Development

```bash
pip install -e .[dev]
python -m pytest tests/               # parser, analysis, and UI smoke tests
python -m xvg_plotter [folder-or-xvg] # run from source
```

Layout: `src/xvg_plotter/core/` (parser, models, analysis — pure Python, unit-tested, no Qt),
`src/xvg_plotter/ui/` (PySide6 widgets + matplotlib canvas, theme in `ui/theme.py`),
`packaging/` (per-OS build scripts).

## Project docs

- [PRD.md](PRD.md) — product requirements and scope
- [SPEC.md](SPEC.md) — technical specification
- [USER_PANEL.md](USER_PANEL.md) — simulated 30-person user panel
- [PROBLEM_LIST.md](PROBLEM_LIST.md) — consolidated pain points, mapped to v1 status

## Notes

- Handles GROMACS-style XVG: `@ title/xaxis/yaxis` headers, `@ sN legend`, error-bar files
  (`@ sN type xydy|xydx|xydxdy`), multi-dataset files (`&` separators), NaN/Inf values,
  CRLF and BOM. Unknown grace directives are ignored gracefully; malformed rows are skipped
  and reported per file — a bad file never crashes the app.
- macOS builds are unsigned in v1 (right-click → Open on first launch).
