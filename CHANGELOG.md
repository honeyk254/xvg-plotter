# Changelog

## 1.2.0 — 2026-09-13

Phase 2 of the remediation plan ([REMEDIATION_PLAN.md](REMEDIATION_PLAN.md)) — all
remaining "fully open" Phase 2 problems plus the v1.0.2 partials, closed.

**Series readability (C17 — now fully closed)**

- **Okabe–Ito** becomes the default color palette: up to 8 overlaid series stay
  distinguishable for colorblind readers ("Default" matplotlib cycle remains available).
- **Per-series color picker**: a color swatch next to every series in the Series panel;
  click to choose a color, right-click to reset to the palette cycle. Overrides survive
  restyles.
- **Legend: outside right** — the legend moves out of the plot area (constrained-layout
  reserves its space), so it stops covering data.

**Performance (C23)**

- Series above 20,000 points are drawn with **min/max bucket decimation** on the
  interactive canvas — spikes survive, multi-million-point files stop lagging.
  Exports, prints and clipboard copies re-render with **full data**.

**Files & folders (C08, C09)**

- **Subfolder scan**: a per-pane "subfolders" toggle walks the whole tree (hidden and
  dotted directories are skipped), so nested analysis folders appear in one list.
- **Cloud-safe scanning**: OneDrive/Dropbox placeholders are listed with a
  "cloud-only" warning **without triggering a download**; selecting one fetches just
  that file.

**Publication figures (C16)**

- **Fig size (in)**: exact width x height in inches — exports and prints honor the
  exact size (tight cropping is skipped when a size is set).
- **Font family**: pick the plot font (Arial, Times, DejaVu, CJK families...);
  remembered between launches.

**Export & output (C29, C30, C33)**

- **Export all checked files...** (Ctrl+Shift+E): every checked file becomes its own
  plot in a chosen folder, with a progress dialog and cancel.
- **Export data (CSV)...** (Ctrl+D): the plotted numbers - visible series with
  ±/dx columns, or mean ± SD when averaging - honoring the current unit conversion.
- **Print...** (Ctrl+P): prints at the printer's resolution, centered and
  aspect-correct.

**Workflow (C19, C20, C22)**

- **Keyboard**: Ctrl+F jumps to the folder filter (Esc clears), Ctrl+1/2/3 toggle the
  Files/Series/Style panels, Ctrl+R refreshes both panes - and Help > *Keyboard
  shortcuts* lists everything.
- **Focus mode** (F11): one keypress hides every panel, leaving only the plot.
- **Open Folder in New Window...** (Ctrl+Shift+O): a real second window for
  two-monitor setups; only the primary window persists layout state.

**Onboarding (C37)**

- A one-screen **welcome intro** on first launch; Help > *Reading the analyses*
  explains RMSD, Rg, RDF, xydy, replicas and pins in plain language; tooltips on the
  analysis and style controls.

**Tests**: 57 -> 73. Fixes tracked in [PROBLEM_LIST.md](PROBLEM_LIST.md).

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
