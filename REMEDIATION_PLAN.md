# XVG Plotter — Remediation Plan (C01–C40)

| | |
|---|---|
| **Scope** | All 40 problems from [PROBLEM_LIST.md](PROBLEM_LIST.md), surfaced by the 30-person panel in [USER_PANEL.md](USER_PANEL.md) |
| **Grounding** | Full audit of the implementation: 22 source files (~2,156 lines) under `src/xvg_plotter/`, `packaging/` (`build.py`, `windows/setup.iss`), `tests/`, `assets/`, `pyproject.toml` |
| **Signing decision** | No code-signing budget for v1.x — C01 is addressed with checksums + documentation; signing remains the complete fix if a budget appears |
| **Sequencing** | 5 phases, each independently shippable. Effort codes: **S** ≤ ~50 lines or docs-only · **M** 50–120 lines · **L** 120+ lines |

---

## 0. Code-reality corrections (read before any fix)

The audit corrected several assumptions in the problem list:

- **C38 (dark mode) is already implemented.** `ui/theme.py` defines `LIGHT`/`DARK` token sets (`theme.py:49-71`), a View▸Theme submenu with Auto(system)/Light/Dark (`main_window.py:155-166`), full canvas + toolbar-icon retheme (`plot_canvas.py:116-136`), and OS scheme tracking (`main_window.py:199-201`). Covered by `tests/test_ui_smoke.py:34-49`. **No code needed** — only verification and a docs/panel correction.
- **C21 (session restore) is partially solved.** Zoom limits already survive style-only re-renders (`plot_canvas.py:140-146, 190-193`, tested at `test_ui_smoke.py:52-70`), and dock layout/window geometry persist (`main_window.py:118-125, 444-447`). What's missing is only cross-restart persistence of the *plot selection and style state*.
- **C04 (AppImage/FUSE) is partially solved.** `build.py:126-127` already rewrites the AppImage invocation with `--appimage-extract-and-run` when `/dev/fuse` is absent. Remaining work is documentation only.
- **C27 (averaging):** the SPEC's ">5 % of points" threshold **does not exist in code** — `average_replicas` warns whenever grids differ at all (`analysis.py:32, 40`).
- **C25 (unit conversion) is two real bugs**, not one gap: no guard against non-time X axes (`main_window.py:313-320` applies `auto_unit` to any X), and `dx` error columns are never converted (`main_window.py:376-385` passes the raw column).
- **C10:** `ParseStats.directives_ignored` is counted (`parser.py:88, 90`) but read by nothing — the UI never shows it.
- **C31 (soft clipboard images):** root cause is `copy_image` = `canvas.grab()` at screen resolution (`export.py:13-14`).
- **No logging exists anywhere in src** (grep-verified) — relevant to C39.
- **Version is duplicated in three places**: `src/xvg_plotter/version.py:1`, `pyproject.toml:7`, `setup.iss:8`.
- **`tests/smoke/` does not exist** despite being referenced by SPEC §14; there are no large-file or CJK fixtures (largest fixture is 11 lines).
- Windows currently ships **onefile only** (`build.py:52-53`; `dist/XVGPlotter.exe` = 73.9 MB); the SPEC §12 onedir fallback is documented but not implemented.

---

## 0b. Re-triage after v1.0.2 (2026-09-12)

v1.0.2 (shipped from a parallel session: dual folder panes, curve pins, Style-as-tab, CI)
changed the picture for three plan items and supersedes parts of §0:

- **C22 — largely covered.** Dual folder panes (independent folder bar, scanner, filter
  and remembered folder per pane) + curve pins overlay two MD systems in one window,
  with a "mixed X axes" warning for time-vs-frame combinations. Remaining: a literal
  second OS window (two-monitor workflows, P09).
- **C17 — partially mitigated.** Curve pins (right-click a legend entry) keep reference
  curves across file/folder switches and follow the palette. Still open: colorblind-safe
  default palette, per-series color picker, legend-overlap handling.
- **C20 — largely covered.** The Style dock became a collapsible tab above the canvas
  instead of a permanent right dock. Remaining: compact handling of the left
  file/series docks on 1366×768 / 200 % scaling.
- **C21 — the zoom half was a bug, now fixed**: the view cache keys on plotted data
  identity, so switching files rescales while style-only changes keep zoom; both folder
  panes restore on startup. Cross-restart session restore (checked files, styles, zoom)
  remains open.
- **C38 — semantics updated**: the canvas is deliberately publication-light in every UI
  theme; only the chrome follows dark/light.
- **CI now exists** (`.github/workflows/build.yml` builds Windows/macOS/Linux artifacts
  and attaches them to releases) — supersedes the pre-v1.0.2 audit's "CI: NOT PRESENT"
  finding and the PRD §3 "CI release automation" non-goal.
- **Unchanged**: C08, C09, C11, C15, C16, C18, C19, C23, C24, C29, C30, C33, C35, C37 —
  their plan entries stand as written.

---

## Phase 0 — Release integrity & distribution (build scripts + docs, no app code)

### C07 — Publish SHA-256 checksums — **S**
**Fix:** `build.py` collects every artifact it produced (portable exe, Setup.exe, DMG, AppImage) and writes `SHA256SUMS.txt` next to them (`hashlib.file_digest`, one loop). README gains a "Verify your download" section with the `sha256sum -c` / `certutil -hashfile` one-liners.
**Files:** `packaging/build.py` (end of each per-OS branch, ~137-146); `README.md` (Install section).
**Verify:** run `build.py --no-install` on Windows; assert `SHA256SUMS.txt` exists and `certutil -hashfile dist\XVGPlotter.exe SHA256` matches.

### C01 — Security warnings block installation (no-signing path) — **S**
**Fix:** without certificates, remove the *surprise*: (a) README per-OS section "Why does my OS warn me?" — Windows SmartScreen ("More info → Run anyway"), AV false positives (portable exe unsigned), macOS Gatekeeper right-click → Open; (b) new `RELEASE.md` written for IT departments: pinned SHA-256 hashes, AppLocker/WDAC allowlisting guidance, "unsigned build, checksums are the integrity guarantee" statement; (c) the download page/docs state the warnings are expected. If a budget appears later: `Signtool` in `build.py` + `SignTool` directive in `setup.iss`, `codesign --deep --options runtime` + `notarytool` for macOS — one gated block each.
**Files:** `README.md`, new `RELEASE.md`.
**Verify:** docs review against a fresh Windows VM / macOS VM first-launch.

### C03 — Slow cold start / heavy install — **S**
**Fix:** add `--onedir` mode to `build.py` Windows branch (PyInstaller `--onedir`; installer's `[Files]` sources the whole dist folder instead of the single exe). Installer ships onedir (fast start, no per-launch extraction); portable onefile exe remains available. Add a crude startup-timing print (time from `main()` to `MainWindow.show()`) and check against the SPEC < 3 s budget.
**Files:** `packaging/build.py:52-58, 63-77`; `packaging/windows/setup.iss` (`[Files]` block).
**Verify:** cold start of the onedir build from an HDD-profile VM < 3 s; installer installs and launches.

### C04 — AppImage friction (chmod, FUSE) — **S**
**Fix:** docs only (the FUSE fallback already ships, `build.py:126-127`): README Linux row gets "`chmod +x` once; on systems without FUSE the app auto-extracts (`--appimage-extract-and-run`)".
**Files:** `README.md:35`.
**Verify:** docs review; manual AppImage run on a FUSE-less container already covered by build.py behavior.

### C05 — No silent/per-machine deployment — **S**
**Fix:** `/SILENT`/`/VERYSILENT` already work (nothing in `setup.iss` disables them) — document the flags in README/RELEASE.md (`/VERYSILENT /SUPPRESSMSGBOXES /NORESTART`). Add `--machine` flag to `build.py` that renders a per-machine installer variant (`PrivilegesRequired=admin`) for managed deployment; keep per-user default.
**Files:** `packaging/build.py` (iss generation/define), `setup.iss:22`, `RELEASE.md`.
**Verify:** `XVGPlotter-Setup.exe /VERYSILENT` installs without UI; per-machine variant installs to Program Files with admin.

### C06 — File-association friction — **S**
**Fix:** (a) README explains the association checkbox (default **off**, `setup.iss:29-30`), how to change it later (Settings ▸ Default Apps / `Open with`), and that grace keeps working when the box is left unchecked; (b) small in-app Help action **"Set as default .xvg viewer"** (Windows only) writing the same `ProgId` + `OpenWithProgids` keys via `winreg` — idempotent, with a confirmation dialog.
**Files:** `README.md`; `ui/main_window.py` (`_menus`, ~20 lines); new `packaging`-mirroring registry constants (winreg block ~25 lines).
**Verify:** toggling the action flips the ProgId (inspect registry); double-clicking an `.xvg` opens the app.

### C12 — Unsupported sibling formats (.edr/.xtc/.xpm) surprise users — **S**
**Fix:** state the boundary where the confusion happens: empty-state canvas text ("Drop a GROMACS `.xvg` file… — plots RMSD/energy/RDF-style `.xvg` output; trajectories (.xtc) and maps (.xpm) are not supported"), plus a Supported-formats line in About and README.
**Files:** `ui/main_window.py` (empty-state label), `_about` (`main_window.py:176-185`), `README.md`.
**Verify:** manual — launch with no folder, text visible.

---

## Phase 1 — Small code fixes (each ≤ ~50 lines + a test)

### C10 — Surface ignored grace directives — **S**
**Fix:** in `FileTable.add_file` (`file_table.py:106-140`), when `f.stats.directives_ignored > 0` append to the row tooltip: `"{n} grace directive(s) ignored — in-file styling not applied"`. Same count appears in the per-file warnings list shown after a scan.
**Files:** `ui/file_table.py:120-121`.
**Test:** unit — parse a fixture with unknown directives; assert `directives_ignored`; UI — tooltip text contains the notice.

### C13 — Drag-and-drop of files/folders — **S**
**Fix:** `MainWindow.setAcceptDrops(True)` + `dragEnterEvent` (accept folders and `*.xvg`) + `dropEvent` → `open_path()` per URL (folders load; multiple `.xvg` files → check them on after scan via the existing `_pending` mechanism, `main_window.py:241-249`).
**Files:** `ui/main_window.py` (~25 lines).
**Test:** offscreen UI test synthesizing a `QMimeData` drop with a fixture path; assert file becomes active.

### C14 — Recents hygiene + favorites — **S**
**Fix:** `settings.recents()` drops paths that no longer exist (and `load_folder` prunes on failure, `main_window.py:205-228`); add `pinned` list + `toggle_pinned(path)` in `settings.py`; FolderBar's recents combo gets a 📌 context action; pinned entries sort first and survive the cap.
**Files:** `settings.py:28-40`, `ui/folder_bar.py:20-89`.
**Test:** unit — add_recent + prune behavior with `tmp_path`; pin/unpin round-trip.

### C25 — Unit-conversion correctness (two bugs) — **S**
**Fix:** (a) guard: conversion applies only when the file's `x_label` looks like time (`time`, `(ps`, `ns`, `µs`, `ms`, case-insensitive) or the user picks a unit explicitly; otherwise the X-unit combo is disabled with tooltip "X axis is not time"; (b) convert `dx` columns alongside X in `_compose_state` (`main_window.py:376-385`) so x-error bars scale too; (c) `scale_label` keeps the existing rewrite rules.
**Files:** `ui/main_window.py:313-320, 376-385`; `core/analysis.py:44-64`.
**Test:** analysis — non-time label → conversion refused; dx scaling asserted; UI — combo disabled state.

### C26 — Stats readout in the status bar — **S**
**Fix:** on `update_plot` (`main_window.py:391-400`), compute `min/max/mean` per visible series (numpy, from the same composed arrays) and render compactly in the permanent status label: `RMSD: min 0.12 · max 1.43 · mean 0.87 nm`. Shared helper `_series_summary()` reused by C34.
**Files:** `ui/main_window.py:391-400`; small helper in `core/analysis.py`.
**Test:** unit — summary values on a known fixture.

### C27 — Averaging: threshold, honest warning, common range — **M**
**Fix:** in `average_replicas` (`analysis.py:24-41`): (a) implement the SPEC's >5 % rule — compute the interpolated fraction of points off-grid; only warn above 5 %, worded with the consequence: `"replica 'X' covers 50–200 ns; aligned to 0–50 ns of <first file> — shorter replicas truncate the mean"`; (b) add "Common time range" checkbox (series dock Analysis group): intersect all replicas' X ranges *before* averaging so no replica silently truncates; (c) disabled-tooltip text explains *why* signatures must match (column structure per `_compatible`, `main_window.py:297-309`).
**Files:** `core/analysis.py:24-41`, `ui/series_dock.py:60-70, 127-129`, `ui/main_window.py:341-365`.
**Test:** analysis — threshold exactness (4.9 % quiet, 5.1 % warning), common-range intersection correctness with mismatched lengths (extends the existing `test_average_interp_warning`).

### C28 — Smoothing window in physical time — **S**
**Fix:** the window spin suffix (`series_dock.py:62-67`) gains a live physical-time readout from the active file's median Δt: `"window 21 pts ≈ 2.1 ns"` (recomputed per active file; hidden when X isn't time).
**Files:** `ui/series_dock.py:62-67`, `ui/main_window.py` (active-file hook).
**Test:** unit — median-Δt label math on a fixture with known dt.

### C31 — Clipboard at export resolution — **S**
**Fix:** replace `canvas.grab()` (`export.py:13-14`) with a render of the figure to a `QImage` at the configured export DPI (Agg buffer via `fig.canvas.print_to_buffer` or a temporary `FigureCanvasAgg` re-render at `dpi`, transparent per setting), then `clipboard().setImage()`. Status message unchanged.
**Files:** `export.py:13-14`, `ui/main_window.py:434-440`.
**Test:** offscreen — copied image ≥ `fig_width_in × 300` px.

### C32 — TIFF + raster-format honesty — **S**
**Fix:** `FORMATS += ("tif", "TIFF")` (`export_dialog.py:22`); DPI spin enabled for png *and* tif (relabel "DPI (raster)"); EPS gets `transparent` forced off (savefig limitation) with a tooltip note; export dialog tooltip lists per-format caveats.
**Files:** `ui/export_dialog.py:22, 39-43, 71-72`; `ui/main_window.py:411-432`.
**Test:** offscreen — save a `.tif` with Pillow readable back; EPS + transparent → warning shown.

### C34 — Canvas accessibility — **S**
**Fix:** `PlotPanel` sets `setAccessibleName("plot canvas")` and `setAccessibleDescription(<C26 summary + file titles + axis labels>)` on every render (`plot_canvas.py:138-196`); keyboard path documented in Help▸Keyboard (C19). The summary doubles as the screen-reader view of the data.
**Files:** `ui/plot_canvas.py`, reuses `_series_summary()` from C26.
**Test:** offscreen — accessibleDescription populated after render.

### C36 — Unicode/CJK glyph fallback — **S**
**Fix:** in `apply_theme` rcParams (`plot_canvas.py:118-133`): `font.sans-serif = ["DejaVu Sans", "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", "Malgun Gothic", "Arial"]` and `axes.unicode_minus = False`. DejaVu already covers µ/Å/±/ε; the platform CJK entries fix Chinese/Japanese/Korean titles and labels (zero bundling cost — uses fonts present on user machines).
**Files:** `ui/plot_canvas.py:118-133`.
**Test:** render a fixture whose title/labels contain `µ Å ± RMSD 均方根位移` into a buffer; assert no matplotlib "Glyph missing" warnings.

### C38 — Dark mode — **already implemented, verify only — S**
**Fix:** none in code. Verify Auto/Light/Dark end-to-end (canvas, toolbar icons, warning rows, export facecolor) and correct the record: update `PROBLEM_LIST.md` status and the README to mention the theme switcher.
**Files:** `PROBLEM_LIST.md` (status), `README.md` (Features).
**Verify:** run existing `test_theme_*` smoke tests + manual dark-mode export (background must follow theme unless "transparent").

### C39 — Logging + crash reporting — **S**
**Fix:** `app.py` bootstraps `logging` with a `RotatingFileHandler` at `QStandardPaths.writableLocation(AppDataLocation)/xvg_plotter.log` (1 MB × 3); `sys.excepthook` (and Qt `messageHandler`) logs the traceback, then shows a non-fatal error dialog with the traceback and a **Copy details** button (the `--noconsole` build currently swallows everything). Parse/single-instance events logged at INFO.
**Files:** `src/xvg_plotter/app.py:16-45` (~40 lines, logging configured before Qt imports touch anything).
**Test:** offscreen — raising inside a slot produces the dialog path and a log line (assert file exists and contains the exception name).

### C40 — Settings export/import — **S**
**Fix:** File▸Export Settings… / Import Settings…: write all current `QSettings("XVGPlotter","XVGPlotter")` keys to a user-chosen `.ini` (`QSettings(path, IniFormat)` + key copy + `sync()`), and the reverse for import (then re-apply theme/geometry).
**Files:** `ui/main_window.py` (`_menus` + two ~20-line helpers), `settings.py` (iterator over keys).
**Test:** offscreen — export → mutate → import → settings round-trip equal.

### C02 — Update check + single-sourced version — **S**
**Fix:** (a) Help▸"Check for updates…" — `QNetworkAccessManager` GET of a `releases_url` constant (GitHub API `…/releases/latest`, placeholder until the repo has a remote), compare against `APP_VERSION`, dialog with download link; strictly user-triggered (no startup phoning home); About gains the project URL. (b) single-source version: `pyproject.toml` uses `dynamic = ["version"]` reading `xvg_plotter.version`; `build.py` passes `/DAPP_VERSION` to ISCC so `setup.iss` stops hardcoding `1.0.0`.
**Files:** `ui/main_window.py` (`_menus`, `_about`, ~50 lines), `pyproject.toml:7`, `packaging/build.py:27-34, 63-77`, `setup.iss:8`.
**Test:** version-comparison helper (older/equal/newer) unit-tested; UI smoke — menu action exists and handles a bad URL gracefully.

---

## Phase 2 — UX features (moderate)

### C08 — Recursive scan / cross-folder search — **S**
**Fix:** FolderBar gains an "include subfolders" checkbox (persisted); `FolderScanner` (`file_table.py:43-67`) walks with `QDirIterator(Dirs | Files, Subdirs)`, skipping hidden/dotted dirs; status bar reports scanned-folder count; filter box (already matches name+title, `file_table.py:173-178`) then effectively becomes cross-folder search.
**Files:** `ui/folder_bar.py`, `ui/file_table.py`, `ui/main_window.py:205-228`.
**Test:** offscreen — scan a tmp tree (2 levels, hidden dir skipped), all `.xvg` rows appear.

### C09 — Cloud-placeholder-safe scanning (OneDrive/Dropbox) — **S**
**Fix:** during scan, Windows-only: `ctypes.windll.kernel32.GetFileAttributesW` check for `FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS (0x400000)` / `RECALL_ON_OPEN (0x40000)`; placeholder files skip the read-based parse entirely (no hydration) and get a `"cloud-only — click to download"` warning instead of a parse warning; other OSes: no-op.
**Files:** `ui/file_table.py` (FolderScanner, ~35 lines).
**Verify:** manual on a OneDrive folder in "online-only" mode (no mass download; correct badge); unit-test the attribute predicate with synthetic values.

### C17 — Many-series readability — **M**
**Fix:** (a) `PALETTES` (`options.py:9-13`) gains **"Okabe–Ito (colorblind-safe)"** and becomes the default; (b) per-series color override: each series row in the series dock gets a color swatch button → `QColorDialog`, stored on the `Line`/overlay state so restyles keep it; "reset" returns to the cycle; (c) `LEGEND_LOCS` (`options.py:7`) gains **"outside right"** (`bbox_to_anchor=(1.02, 1), loc="upper left"`) so legends stop covering data.
**Files:** `ui/options.py`, `ui/series_dock.py:147-177`, `ui/plot_canvas.py:138-196`, `ui/main_window.py:36-49, 322-389`.
**Test:** offscreen — override survives a re-render; outside-right legend axes shrink correctly.
**v1.0.2 status:** partially mitigated — curve pins shipped (pins survive file/folder switches and follow the palette). Remaining: (a) colorblind-safe palette, (b) per-series color picker, (c) legend placement outside the axes.

### C16 — Figure geometry & typography — **M**
**Fix:** Style dock gains: width/height-inch spinboxes (persisted; "auto" = current canvas size) and a font-family combo (Match UI, DejaVu Sans, Arial/Helvetica, Times New Roman + detected CJK families). Applied via `fig.set_size_inches(..., forward=False)` and `rcParams["font.family"]`; export uses the same state so the saved figure matches the preview.
**Files:** `ui/style_dock.py:21-105`, `ui/plot_canvas.py:118-133, 138-196`, `ui/main_window.py:322-389`.
**Test:** offscreen — set 85×60 mm-equivalent size, export PNG, assert pixel dimensions = inches × dpi.

### C19 — Keyboard support — **S**
**Fix:** add shortcuts: `Ctrl+F` focus filter (Esc clears + refocuses canvas), `Ctrl+1/2/3` toggle the three docks, `Ctrl+R` = refresh alias, arrow-key row activation already native — plus a Help▸Keyboard dialog listing everything (existing six from `main_window.py:129-174` included).
**Files:** `ui/main_window.py:129-174`, `ui/folder_bar.py` (Esc handling), new small `ui/keyboard_dialog.py` (~40 lines).
**Test:** offscreen — QShortcut existence and filter-focus behavior.

### C20 — Focus mode — **S**
**Fix:** View▸Focus Mode (F11): hide all docks; second press restores the exact prior dock state (`saveState`/`restoreState` snapshot around the toggle).
**Files:** `ui/main_window.py` (~15 lines).
**Test:** offscreen — toggle hides all docks; untoggle restores visibility flags.
**v1.0.2 status:** largely covered — Style moved out of the permanent right dock into a collapsible tab above the canvas, removing the worst crowding source. A focus/compact mode for the left file+series docks remains useful on 1366×768 / 200 % scaling.

### C21 — Full session restore — **M**
**Fix:** on close (`main_window.py:444-447`) persist: current folder, checked file paths, active file + dataset, visible series, `StyleState`/`AnalysisState`, and the canvas `xlim/ylim`. On launch, after `last_folder` load, re-check files whose paths still exist, re-apply state, restore view. Restores yesterday's comparison exactly.
**Files:** `ui/main_window.py` (~60 lines), `settings.py` (namespaced `session/*` keys).
**Test:** offscreen — construct window, set state, simulate close, construct a second window, assert state equal.

### C22 — Side-by-side windows — **M**
**Fix:** File▸"Open Folder in New Window" (`Ctrl+Shift+O`): instantiates a second `MainWindow` in the same process on the chosen folder (single-instance still guards *processes* via `single_instance.py`). Primary window owns persisted `geometry/last_folder`; secondary windows skip persisting those keys. Docks/theme state comes from the same settings.
**Files:** `ui/main_window.py` (~40 lines), `app.py` (window list + quit handling when last window closes).
**Test:** offscreen — open two windows with different folders; each plots its own selection independently.
**v1.0.2 status:** largely covered — dual folder panes (independent folders, scanners, filters) + curve pins cover the overlay-two-systems workflow in one window, with a "mixed X axes" warning. Remaining: a literal second OS window for two-monitor setups.

### C23 — Decimation for interactive performance — **M**
**Fix:** in `PlotPanel.render` (`plot_canvas.py:138-196`), when a series exceeds ~20k points, draw a min/max bucket decimation (numpy reshape + per-bucket min & max, preserving spikes) for the *interactive canvas only*; exports re-render full data (or up to a higher cap). Cursor readout and stats (C26) always use full data. Add a 1M-row generated fixture + a render-time regression test against the SPEC < 1 s click-to-plot budget.
**Files:** `ui/plot_canvas.py` (~30 lines), `core/analysis.py` (decimate helper), new `tests/fixtures/perf_1m.xvg` (generated in-test, not committed).
**Test:** decimation output contains true min/max of every bucket; 1M-row render under budget in CI-lite (assert < 3 s locally).

### C29 — Batch export — **M**
**Fix:** File▸"Export all checked files…" (`Ctrl+Shift+E`): folder picker + current export defaults; loops checked files, renders each *alone* with the current style/unit/smoothing state, saves `"<stem>.<fmt>"` into the chosen folder (collision suffix `-2`), `QProgressDialog` with cancel. Reuses `save_figure` (`export.py:9-10`).
**Files:** `ui/main_window.py` (~70 lines).
**Test:** offscreen — 3 checked fixture files → 3 output files with correct stems; cancel mid-loop stops.

### C30 — Data export (CSV) — **M**
**Fix:** File▸"Export data (CSV)…" (`Ctrl+D`): writes the *visible* series of the current view — X column + one column per series (+ `dy`/`dx`), and when replica averaging is active, `mean` + `sd` columns — with the file's title/labels as `#` header comments, honoring the current unit conversion (x-data written post-conversion). `np.savetxt`.
**Files:** `ui/main_window.py` (~50 lines), `core/analysis.py` (compose-exported-arrays helper shared with C29).
**Test:** unit — exported CSV parses back to the composed arrays; averaging path yields mean/sd columns.

### C33 — Printing — **S**
**Fix:** File▸Print… (`Ctrl+P`): `QPrintDialog`; render the figure to the printer's resolution (`QImage` at `printer.resolution()` DPI + `QPainter.drawImage`, landscape/portrait respected via `pageLayout`). PySide6 ships QtPrintSupport.
**Files:** `ui/main_window.py` (~35 lines).
**Test:** offscreen — print to a `QPrinter` in pdf mode produces a non-empty file.

### C37 — Onboarding & jargon help — **M**
**Fix:** tooltips on every control (series/style docks, export dialog, file-list columns); a one-screen, dismissable first-run intro (remembered via `settings.py`); a Help ▸ "Reading the analyses" glossary explaining common GROMACS output names (RMSD, Rg, RDF, xydy, replica) in plain language. *(Originally missing from the phase lists — flagged when the v1.0.1 open-items list was compiled.)*
**Files:** `ui/series_dock.py`, `ui/style_dock.py`, `ui/export_dialog.py`, `ui/file_table.py`, new `ui/first_run.py` (~60 lines), `ui/main_window.py` (Help menu).
**Test:** offscreen — intro shows on first launch, is suppressed afterwards; glossary dialog reachable from Help.

---

## Phase 3 — Larger features

### C11 — Multi-dataset files as first-class series — **M**
**Fix:** for files with `&`-separated datasets (`parser.py:114-126`), the series dock lists *every dataset* of the active file as toggleable entries ("dataset 2 · 1,024 pts"), not just the selected one (`series_dock.py:158-164` dataset selector stays as the "focus" default). Overlaying dataset 2 of file A against dataset 1 of file B then works through the existing overlay pipeline (`main_window.py:_compose_state` iterates targets already).
**Files:** `ui/series_dock.py:107-181`, `ui/main_window.py:261-266, 322-389` (~50 lines).
**Test:** offscreen — `tests/fixtures/multidataset.xvg`: toggle dataset 2, two artists render; overlay across two multi-dataset files.

### C15 — Text annotations — **L**
**Fix:** canvas annotation mode: toolbar/mode toggle "Add text" → click places a text artist at data coordinates after a `QInputDialog` prompt; annotations live in `PlotState` (`plot_canvas.py:44-53`) as `(x, y, text)` per view, survive re-renders/rethemes (recreated in `render`), are included in exports/prints (C29/C30 n/a, C33 yes), draggable in edit mode, and a "Clear annotations" action resets. Arrows/panel labels intentionally deferred to a follow-up unless requested.
**Files:** `ui/plot_canvas.py` (~100 lines), `ui/main_window.py` (mode wiring ~20 lines).
**Test:** offscreen — add annotation, re-render with a style change, assert artist persists at same data coords; export contains it (artist count).

### C18 — Grid view (small multiples) — **L**
**Fix:** View▸"Grid view of checked files": renders every checked file as its own axes in an auto-sized N×M grid (cap e.g. 24 with a warning), each cell titled by file name, sharing the global style; pan/zoom per-axes (native toolbar applies to last-touched axes; Home resets all); export/print output the whole grid. Single-axes mode remains the default.
**Files:** `ui/plot_canvas.py` (~120 lines: multi-axes render path), `ui/main_window.py` (mode flag ~20 lines).
**Test:** offscreen — 6 checked files → 6 axes; each artist count = 1; export PNG dimensions grow with grid.

### C24 — Derived quantities (normalize / baseline / fit) — **M**
**Fix:** Analysis group (`series_dock.py:45-93`) gains: **Normalize** combo (off / first value / max) and **Subtract baseline (first point)** toggle — applied per visible series in the compose pipeline; **Fit line** action draws a least-squares `np.polyfit(degree=1)` over the *visible X range* as a dashed overlay with `y = a·x + b` in the legend entry. Core math in `core/analysis.py` (unit-testable, pure numpy); fit is display-only (never mutates the file's data).
**Files:** `core/analysis.py` (~40 lines), `ui/series_dock.py` (~25 lines), `ui/plot_canvas.py` (~30 lines), `ui/main_window.py:322-389`.
**Test:** analysis — normalize/baseline exact arrays on known input; fit recovers a synthetic `y = 2x + 1` within tolerance.

---

## Phase 4 — Localization

### C35 — i18n with a shipped zh-CN translation — **L**
**Fix:** (a) wrap all user-facing strings in `self.tr()` / `QCoreApplication.translate` across `ui/` (mechanical pass, ~150 keys); (b) `pyside6-lupdate` / `pyside6-lrelease` steps in `build.py` producing `.qm` files bundled as package data; (c) ship `i18n/xvgplotter_zh_CN.ts` (menu, docks, dialogs, warnings); (d) language combo in settings (System/English/中文) with `QTranslator` install before `MainWindow` construction; (e) the C36 font-fallback chain (Phase 1) guarantees CJK renders in-canvas. English remains the fallback for any untranslated key.
**Files:** all `ui/*.py` (string pass), new `i18n/` sources, `packaging/build.py` (lrelease step), `ui/main_window.py` + `app.py` (translator install).
**Verify:** run app with `LANGUAGE=zh_CN` (Linux) / locale set — main menus, docks, and export dialog appear in Chinese; existing tests keep passing in English (`tr()` returns source text when no translator is installed).

---

## Verification & regression strategy

- **One test per fix**, in the existing style: core logic → `tests/test_parser.py` / `tests/test_analysis.py`; UI behavior → `tests/test_ui_smoke.py` (offscreen, `QT_QPA_PLATFORM=offscreen` at `test_ui_smoke.py:11`). No new frameworks.
- **New fixtures:** CJK-titled file (C36), non-time-X file (C25), placeholder-attribute case documented as manual check (C09), generated-in-test 1M-row file (C23, not committed).
- **Recreate `tests/smoke/`** (referenced by SPEC §14 but missing): per-OS packaging checklist + golden-path walkthrough, including the Phase 0 items (silent install, checksums, onedir start time, association toggle).
- **Docs stay truthful:** at the end of each phase, update SPEC §5–§13 (behavior changes: C23 decimation, C25 guard, C27 threshold, C29–C33 new export surface), PRD §6/§9 (features move from backlog to shipped), and flip the matching status in `PROBLEM_LIST.md`.

## Effort summary

| Phase | Items | Effort | Ships |
|---|---|---|---|
| 0 — Release integrity & docs | C01, C03, C04, C05, C06, C07, C12 | 0.5–1 day | immediately |
| 1 — Small code fixes | C02, C10, C13, C14, C25, C26, C27, C28, C31, C32, C34, C36, C38*, C39, C40 | 2–3 days | v1.0.1 |
| 2 — UX features | C08, C09, C16, C17, C19, C20, C21, C22, C23, C29, C30, C33, C37 | 5–7 days | v1.1 |
| 3 — Larger features | C11, C15, C18, C24 | 4–6 days | v1.2 |
| 4 — Localization | C35 | 2–3 days | v1.2 |

\* C38 = verification + docs only (already implemented).

**Total ≈ 3 weeks of single-developer work; every phase is independently shippable and each item carries its own test.**
