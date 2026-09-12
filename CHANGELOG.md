# Changelog

## 1.0.2 — 2026-09-12

**Fixes**

- Switching the plotted file no longer keeps the previous file's axes: the
  zoom-preservation cache now keys on the plotted data's identity (file,
  dataset, visible series), not just the legend labels. Style-only changes
  still keep your zoom.
- Title/X/Y labels and the auto X-unit now follow the *active* file when
  several files are plotted, instead of whichever row sorts first.
- The second folder pane is restored correctly on startup.

**Features**

- **Two folder panes**: the Files panel is two stacked panes, each with its own
  folder bar, refresh, filter and remembered folder — check files in either
  pane to overlay multiple MD systems on one plot. Dropping two folders at
  once fills both panes. The status bar warns "mixed X axes" when overlaying
  time-based and frame-based files.
- **Curve pins**: right-click a legend entry → *Pin curve*. Pinned curves
  survive file and folder switches so you can overlay anything on anything;
  View ▸ *Clear all pins* removes them. A folder refresh re-reads pinned
  files' new data, and pins follow the current palette/line style.
- **Style tab**: the right-side Style dock is now a collapsible "Style ▸" tab
  above the plot — out of the way until you need it.

**Tests**: 52 → 57.

## 1.0.1 — 2026-09-07

Remediation release: ships Phases 0–1 of [REMEDIATION_PLAN.md](REMEDIATION_PLAN.md)
(pain points C01–C40 from the [user panel](USER_PANEL.md) and
[problem list](PROBLEM_LIST.md)).

**Distribution & trust**

- **C07**: every build writes `dist/SHA256SUMS.txt` covering its artifacts; README
  explains how to verify.
- **C01**: release + README documentation for expected SmartScreen/Gatekeeper/AV
  warnings; [RELEASE.md](RELEASE.md) gives IT departments hash-pinning and
  allowlisting guidance (code signing remains backlog).
- **C03**: `build.py --onedir` produces a fast-starting onedir build (installer wraps
  the directory, portable zip included); startup time is logged against the
  < 3 s guardrail.
- **C05**: `build.py --machine` builds a per-machine installer variant; Inno Setup
  `/SILENT` / `/VERYSILENT` documented.
- **C06**: Help ▸ *Set as default .xvg viewer* (Windows, per-user) mirrors the
  installer's optional association; README explains coexistence with grace.

**App fixes & features**

- **C02**: Help ▸ *Check for updates…* (manual, GitHub releases API); version is now
  single-sourced from `src/xvg_plotter/version.py` (pyproject + installer derive it).
- **C10**: ignored grace directives are counted **and shown** per file ("N grace
  directive(s) ignored — in-file styling not applied").
- **C12**: supported formats stated on the empty canvas and in About (`.xvg` only;
  `.xtc`/`.xpm`/`.edr` are not supported).
- **C13**: drag-and-drop of `.xvg` files and folders onto the window.
- **C14**: recent folders prune dead paths; folders can be pinned to the top.
- **C25**: "auto" ps→ns conversion only applies to genuine time axes (a frame-index
  X axis is never rescaled or relabeled); x-error (`dx`) columns now follow the
  X unit conversion.
- **C26**: status bar shows live min/max/mean of every plotted series.
- **C27**: replica averaging warns only above the SPEC's 5 % interpolation threshold,
  with an honest message about truncation, plus an optional **Common time range**
  mode that averages only the span all replicas share.
- **C28**: the smoothing window shows its physical span ("≈ 2.1 ns") for the active file.
- **C31**: *Copy Image* renders at the configured export DPI (no more soft pastes
  on high-DPI displays).
- **C32**: TIFF export; DPI applies to PNG **and** TIFF; EPS disables transparency
  with an explanation.
- **C34**: the plot canvas exposes an accessible name/description with the same
  min/max/mean summary (screen-reader friendly).
- **C36**: platform CJK font fallback in plots — µ Å ± ε and Chinese/Japanese/Korean
  titles no longer render as boxes.
- **C38**: no change needed — dark mode (Auto/Light/Dark) already shipped in v1.0;
  verified and documented.
- **C39**: rotating file log (`xvg_plotter.log` in the per-user app-data folder) +
  uncaught-exception dialog with copyable details.
- **C40**: File ▸ Export Settings… / Import Settings… (INI round-trip).

**Tests**: 24 → 52 (one per fix, plus packaging checks). See
[PROBLEM_LIST.md](PROBLEM_LIST.md) for what remains open (Phases 2–4).

## 1.0.0 — 2026-09-05

Initial release: folder browsing with metadata, click-to-plot XVG viewer, multi-file
overlay, replica averaging, smoothing, time-unit conversion, publication exports,
Windows/macOS/Linux packaging, light/dark theme.
