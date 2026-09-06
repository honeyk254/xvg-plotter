# XVG Plotter — Technical Specification

| | |
|---|---|
| **Product** | XVG Plotter |
| **Version** | 1.0 (v1 scope) |
| **Status** | Draft — for review |
| **Date** | 2026-09-05 |
| **Companion doc** | [PRD.md](PRD.md) (product requirements) |

---

## 1. Overview

A cross-platform PySide6 desktop application with an embedded matplotlib canvas. One Python
codebase produces three native artifacts (Windows installer/exe, macOS DMG, Linux AppImage).
Users only ever touch the packaged artifacts; the dev entry point (`python -m xvg_plotter`)
exists for development only.

```
┌────────────────────────────────────────────────────────────────────┐
│ UI layer (PySide6)      main_window · folder_browser · file_table  │
│                         series_selector · style_dock · export_dlg  │
├────────────────────────────────────────────────────────────────────┤
│ Plot layer              plot_canvas (FigureCanvasQTAgg +           │
│                         NavigationToolbar2QT)                      │
├────────────────────────────────────────────────────────────────────┤
│ Core layer (no Qt)      parser.py · models.py · analysis.py        │
├────────────────────────────────────────────────────────────────────┤
│ Services                export.py · settings.py · single_instance  │
└────────────────────────────────────────────────────────────────────┘
```

Design rule: `core/` is pure Python + numpy and fully unit-testable without a display. The UI
layer renders state derived from `core` models and never parses files itself.

---

## 2. Tech stack and dependencies

| Dependency | Version | Role |
|---|---|---|
| Python | ≥ 3.10 | Runtime |
| PySide6 | ≥ 6.6 | UI framework (LGPL; QtAgg integration) |
| matplotlib | ≥ 3.8 | Plotting + export (Agg/QtAgg backends) |
| numpy | ≥ 1.24 | Data arrays, averaging, smoothing |
| pytest | dev | Unit tests |
| PyInstaller | build | Per-OS executables/bundles |
| Inno Setup | build (Win) | Windows installer |
| create-dmg / hdiutil | build (mac) | DMG assembly |
| appimagetool | build (Linux) | AppImage assembly |

`pyproject.toml` defines the package, dev extras, and version (single source of truth, read at
runtime via `importlib.metadata`; display in About dialog).

---

## 3. Repository layout

```
xvg_plotter/
├── pyproject.toml
├── PRD.md · SPEC.md · README.md
├── src/xvg_plotter/
│   ├── app.py               # QApplication bootstrap, icon, single-instance server
│   ├── __main__.py          # dev entry: python -m xvg_plotter [file-or-folder]
│   ├── core/
│   │   ├── models.py        # XvgFile, Dataset, SeriesSpec, ParseStats, ParseWarning
│   │   ├── parser.py        # XVG text → models
│   │   └── analysis.py      # averaging, smoothing, unit rescale
│   ├── ui/
│   │   ├── main_window.py   # menus, docks, status bar, wiring
│   │   ├── folder_bar.py    # path bar, Open Folder, recents dropdown
│   │   ├── file_table.py    # metadata table, selection model, warnings
│   │   ├── series_dock.py   # per-file column/series checkboxes, ± pairing
│   │   ├── style_dock.py    # colors, line/marker, grid, log, legend, units, smoothing
│   │   ├── plot_canvas.py   # FigureCanvasQTAgg + toolbar + legend toggling
│   │   └── export_dialog.py
│   ├── export.py            # savefig wrapper + clipboard
│   ├── settings.py          # QSettings keys, recents
│   └── single_instance.py   # QLocalServer/QLocalSocket handshake
├── assets/icon.svg → icon.ico / icon.icns / png set (generated)
├── packaging/
│   ├── build.py             # per-OS build orchestration
│   ├── windows/setup.iss
│   ├── macos/               # Info.plist additions, dmg script
│   └── linux/xvgplotter.desktop
└── tests/
    ├── fixtures/*.xvg       # see §14
    ├── test_parser.py · test_analysis.py
    └── smoke/               # manual UI + packaging checklists
```

---

## 4. Data model

```python
Kind = Literal["line", "xydy", "xydx", "xydxdy"]

@dataclass
class SeriesSpec:
    y_col: int                  # column index of Y (dataset.columns[y_col])
    dy_col: int | None          # ± column for xydy/xydxdy
    dx_col: int | None          # x-error column for xydx/xydxdy
    legend: str | None
    kind: Kind

@dataclass
class Dataset:
    index: int                  # dataset number within the file (& separators)
    columns: list[np.ndarray]   # equal-length columns; columns[0] is X
    series: list[SeriesSpec]    # semantic view over columns

@dataclass
class XvgFile:
    path: Path
    title: str | None           # from '@ title'
    subtitle: str | None
    x_label: str | None         # from '@ xaxis label'
    y_label: str | None
    datasets: list[Dataset]
    warnings: list[str]         # human-readable, shown in UI
    stats: ParseStats           # rows_ok, rows_skipped, directives_ignored, n_cols
```

Notes:
- X is always column 0 (GROMACS convention; verified per dataset during parse).
- `series` is derived from `@ sN` directives when present (see §5.3), else from the default
  rule in §5.4. A `SeriesSpec` is a *view* over raw columns, so error-bar pairing can be
  re-assigned in the UI without re-parsing.
- Column count mismatch between rows (ragged file): rows are skipped and counted in
  `rows_skipped`; a warning is attached.

---

## 5. XVG format support

### 5.1 Line classification

A line is classified by its first non-blank character:

| Prefix | Meaning | Handling |
|---|---|---|
| `#` | Comment (GROMACS metadata, command line) | Ignored |
| `@` | Grace directive | Parsed per §5.2; unknown directives ignored (counted) |
| `&` | Dataset separator (also `& Dn` forms) | Finalize current dataset, start next |
| other | Data row | Parse per §5.5 |
| blank | — | Ignored |

### 5.2 Directives parsed (subset)

| Directive | Effect |
|---|---|
| `@ title "…"` / `@ subtitle "…"` | File title / subtitle (quoted or unquoted forms both accepted) |
| `@ xaxis label "…"` / `@ yaxis label "…"` | Axis labels |
| `@ sN legend "…"` | Legend for series N |
| `@ sN type xy\|xydy\|xydx\|xydxdy` | Series semantics (error-bar columns) |
| `@ sN color/symbol/linetype…`, `@ world …`, `@ with gN`, `@ gN …`, `@ target …`, `@ legend …` others | **Ignored** (app owns styling); counted in `directives_ignored` |

Grace writes variable whitespace after `@` (`@    title "RMSD"`) and occasionally none
(`@title "RMSD"`); the tokenizer handles both, honors double quotes with `\"` escapes.

### 5.3 Error-bar semantics (grace types)

| Type | Column layout (0-based) | Rendering |
|---|---|---|
| `xy` | 0: x, 1: y | Line/points |
| `xydy` | 0: x, 1: y, 2: dy | `errorbar(y, yerr=dy)` |
| `xydx` | 0: x, 1: dx, 2: y | `errorbar(x, xerr=dx)` |
| `xydxdy` | 0: x, 1: dx, 2: y, 3: dy | both errors |

A file containing `xydx*` types renders with error bars and a note; nothing degrades silently.

### 5.4 Default classification (no `@ sN type` present)

- 2 columns → one line series.
- N columns (N > 2) → columns 1…N−1 are independent Y series sharing X (the `gmx energy`
  convention, with `@ sN legend` for each).
- The series dock additionally exposes a manual **“±” pairing** control: mark any column as the
  error column of the series to its left (covers `xydy`-shaped files emitted without directives).

### 5.5 Data-row parsing

- Tokens: whitespace-separated; each must parse as float via numpy-tolerant rules
  (`nan`, `inf`, `-inf`, `+1.0e5`, `-.5E-3` all valid).
- Numeric-only columns expected; rows containing unparseable tokens are skipped, counted, and
  surfaced as a warning (never fatal).
- Rows whose token count differs from the established column count are skipped + counted.
- Encoding: UTF-8 with BOM tolerance (`utf-8-sig`), fallback `latin-1`; newlines: LF, CRLF.
- A file with zero data rows is still loaded (headers usable) and flagged
  “no data rows” in the UI.

### 5.6 Multi-dataset files (`&`)

Each `&`-separated block becomes a `Dataset`. When a loaded file has > 1 dataset, the series dock
shows a dataset selector (default: first dataset). Export/averaging operate on the visible dataset.

---

## 6. UI specification

### 6.1 Layout

```
┌──────────────────────────────────────────────────────────────────────────┐
│ File  View  Help                                  (native menu bar)      │
├──────────────────────────────────────────────────────────────────────────┤
│ [📁 Open Folder] [C:\sim\analysis            ▼recents] [⟳] [filter box]  │
├───────────────────────────────┬──────────────────────────────────────────┤
│ File list                     │  ⌂ ↶ ✋ pan 🔍 zoom  [toolbar]            │
│ ☐  Name      Title   Ser Pts  │                                          │
│ ☑  rmsd.xvg   RMSD    1  5001 │        matplotlib canvas                 │
│ ☑  rmsd_r2.xvg RMSD   1  5001 │        (pan/zoom/inspect)                │
│ ☐  energy.xvg Energy  6  5001 │                                          │
│ ⚠  broken.xvg — (no rows)     │                                          │
├───────────────────────────────┴──────────────────────────────────────────┤
│ Series dock                                  │ Style dock                │
│ ▾ rmsd.xvg      [dataset ▼ if >1]            │ grid ☑  log-X ☐ log-Y ☐   │
│    X: col 0 (Time (ps))  [fixed]             │ legend: best ▼            │
│    Y: ☑ col 1 "RMSD"  [±: none ▼]            │ colors: cycle ▼           │
│ ▾ rmsd_r2.xvg …                              │ line: ●━/‑‑  width 1.5    │
│                                              │ title override [____]     │
│ [☑ Average replicas]  [show members ☐]       │ labels override [__] [__] │
│ [☑ Smooth overlay] window [21] pts           │ X unit: ps ▼ (auto/ns/µs) │
├──────────────────────────────────────────────────────────────────────────┤
│ Status: x=123.4 ps  y=1.42 nm · 3 files · 2 warnings                     │
└──────────────────────────────────────────────────────────────────────────┘
```

Docks are collapsible and movable; layout state persists.

### 6.2 File list behavior

- Checkbox = add to the plot overlay; double-click row = **replace** plot with that file alone.
- Columns: Name, Title, Series, Points, Size, Modified; warning files show ⚠ with tooltip text.
- Scan runs on a worker thread; results stream into the table in batches (UI never blocks).
- Right-click row: Show in Explorer/Finder/Files, Copy path, Export this file.

### 6.3 Plot canvas behavior

- `NavigationToolbar2QT` provides home / back / forward / pan / zoom / save (its save opens the
  app's export dialog for consistent defaults).
- **Legend-click toggling**: legend artists are pickable; clicking a legend entry toggles that
  series' visibility (standard interactive-legend pattern).
- **Coordinate readout**: `motion_notify_event` → status bar `x=… y=…` in current unit.
- Restyle operations mutate existing artists and `draw_idle()`; full rebuild only on file set change.
- Color assignment: matplotlib default cycle per (file, series) pair, stable across re-styles.

### 6.4 Menus and shortcuts (Ctrl maps to Cmd on macOS automatically)

| Action | Shortcut |
|---|---|
| Open Folder… | Ctrl/Cmd+O |
| Refresh scan | F5 |
| Export… | Ctrl/Cmd+E |
| Copy image to clipboard | Ctrl/Cmd+Shift+C |
| Export / Import settings (v1.0.1) | File menu (no shortcut) |
| Check for updates (v1.0.1, manual) | Help menu |
| Set as default .xvg viewer (v1.0.1, Windows) | Help menu |
| Quit | Ctrl/Cmd+Q |
| About | via Help menu |

---

## 7. Analysis features (P1)

### 7.1 Replica averaging

- Trigger: “Average replicas” toggled while ≥ 2 selected files have **compatible signatures**
  (same column count, same kinds, same labels).
- X-grids may differ across replicas (different `nst`): align by linear interpolation onto the
  first file's X grid; if > 5 % of aligned points fall outside a replica's own range, emit a
  warning naming the replica and the truncated span (v1.0.1).
- **Common time range** option (v1.0.1): average only the span every replica covers, so
  shorter runs never truncate longer ones.
- Render: mean line (thicker), SD band via `fill_between(mean−σ, mean+σ)` at α=0.25;
  “show members” draws each replica thin & faint beneath.
- Incompatible selection → toggle disabled with explanatory tooltip (no silent behavior).

### 7.2 Smoothing

- Centered moving average, window N (odd-enforced spinbox, default 21 points); `np.convolve`
  with edge padding.
- The dock shows the window's physical span for the active file ("≈ 2.1 ns") via the median
  X spacing (v1.0.1).
- Rendered as a dashed overlay in the matching series color; original curve always remains.
- Applies per visible series; excluded from exports when hidden.

### 7.3 Time-unit conversion

- Applies to the X axis. Units: ps (native) → ns (÷1e3), µs (÷1e6), ms (÷1e9), plus **auto**
  (largest unit such that x_max ≥ 1).
- **Time-axis guard (v1.0.1)**: `auto` rescales only when the X label identifies a time axis
  (`time`, `ps`, `ns`, `µs`, `ms`, `fs`; unlabeled counts as time). A non-time X (frame index,
  position) keeps its label untouched on `auto`; an explicit unit pick is still honored.
  `dx` error columns are converted alongside X.
- Axis label updated in place: `Time (ps)` → `Time (ns)`; files without a labeled axis get a
  generated label.

---

## 8. Export

- Dialog fields: filename (default: sanitized plot title or first file stem), destination folder
  (default: source data folder), format (PNG/PDF/SVG/EPS/TIFF), DPI spin (100–600, default 300;
  PNG/TIFF), transparent background checkbox (disabled for EPS, which cannot carry
  transparency); remembers last choices via `settings.py`.
- Implementation: `fig.savefig()` with `bbox_inches="tight"`, `facecolor="none"` when
  transparent; raster DPI applies to PNG/TIFF only (vector formats ignore it).
- **Copy image to clipboard**: rendered at the configured export DPI (PNG via
  `savefig` → `QImage`; v1.0.1 — previously a widget grab at screen resolution), then
  `QApplication.clipboard().setImage()`.
- Export uses the *current view state* (log axes, units, smoothing, averaging, zoom window).

---

## 9. Settings and persistence (QSettings: `XVGPlotter` / `XVGPlotter`)

| Key | Content |
|---|---|
| `geometry/state` | Window size, dock layout |
| `recents` | Last 10 folders (deduplicated, most-recent-first, dead paths pruned) |
| `pinned` | Pinned folders, shown above recents (v1.0.1) |
| `last_folder` | Restored on launch |
| `export/*` | format, dpi, transparent, last destination |
| `view/*` | unit mode, smoothing window, grid, legend position defaults |

Backed by the registry (Windows) / plist (macOS) / ini (Linux) per Qt conventions.

---

## 10. Robustness and services

1. **Per-file isolation**: any parse failure produces a warning row; the app never crashes on
   bad input. Warnings list is visible per file (tooltip + status summary).
2. **Async everything slow**: directory scan, per-file parse, and metadata load run on a
   `QThreadPool`; the UI thread only renders models.
3. **Single instance**: `QLocalServer`/`QLocalSocket` named pipe per user; a second launch
   forwards its argv (file/folder) to the running instance and exits — this is what makes OS
   file-association launches feel native.
4. **File association launch**: argv containing an `.xvg` path → open that file's folder and
   plot it immediately (maps to U1).
5. **Missing files** (deleted between scan and click): row marked stale, warning shown, no crash.
6. **Logging (v1.0.1)**: rotating file log (`xvg_plotter.log`, 1 MB × 3) in the per-user
   app-data folder; `sys.excepthook` + Qt message handler write there and show a crash
   dialog with copyable details (nothing is transmitted). Startup time is logged against
   the §13 cold-start budget.

---

## 11. App identity

- Single `assets/icon.svg` (line-chart glyph in a rounded square) → generated: `icon.ico`
  (16/32/48/64/128/256), `icon.icns`, and hicolor PNGs (16–512).
- `QApplication.setApplicationName("XVG Plotter")`, `setDesktopFileName`, window icon set before
  `show()` so title bar, taskbar, and dock are correct on all OSes.
- About dialog: name, version (from package metadata), matplotlib/numpy/Qt versions, license note.

---

## 12. Cross-platform packaging matrix

Build scripts live in `packaging/build.py` with one target per OS. **PyInstaller cannot
cross-compile** — each artifact is produced on its native OS (manual run per OS now; CI in backlog).

| OS | Steps | Artifact |
|---|---|---|
| Windows | PyInstaller `--noconsole --onefile --icon assets/icon.ico --name XVGPlotter` (`--onedir` variant via `build.py --onedir`; the installer then wraps the directory and a zip is emitted) → Inno Setup `setup.iss` (`/DAPP_VERSION`, `/DONEDIR`, `/DMACHINE` defines; AppId, Start Menu + Desktop icons, `.xvg` ProgId + `shell\open\command` + DefaultIcon, uninstall entries; per-user by default, per-machine via `/DMACHINE`) | `XVGPlotter-Setup-<ver>[.exe|-machine.exe]` + portable exe/zip |
| macOS | PyInstaller `--windowed --name "XVG Plotter" --icon assets/icon.icns`; bundle `Info.plist` additions: `CFBundleDocumentTypes` + exported UTI `org.xvgplotter.xvg` → DMG with Applications symlink | `XVGPlotter.dmg` |
| Linux | PyInstaller `--noconsole --onedir`; AppDir with `.desktop` (`Exec`, `Icon`, `MimeType=application/x-xvg;`), hicolor icons → `appimagetool` | `XVGPlotter-x86_64-<ver>.AppImage` |

Every build finishes by writing `SHA256SUMS.txt` (v1.0.1) next to the file artifacts it
produced.

Guardrails: `--noconsole/--windowed` everywhere (no console flash); hidden-imports for
matplotlib backends verified per platform; onefile startup-time checked (< 3 s warm) — fall back
to `onedir`-based installer if unacceptable on Windows.

---

## 13. Performance targets

| Operation | Budget |
|---|---|
| Folder scan (500 files, metadata only) | < 3 s, non-blocking |
| Click-to-plot, 100k-row file | < 1 s |
| Style-change redraw | < 200 ms |
| 300-dpi PNG export of 100k-point plot | < 3 s |
| Packaged app cold start | < 3 s warm OS cache |

Parsing is numpy-batched (numeric matrix assembly after line filtering), not per-value Python loops.

---

## 14. Testing strategy

**Unit (pytest, no display)** — `tests/`:

- `test_parser.py`: fixtures cover — minimal 2-column; `gmx energy`-style multi-series with
  `@ sN legend`; `xydy` error bars; `xydxdy`; multi-dataset `&`; CRLF; UTF-8 BOM; latin-1 bytes;
  `nan`/`inf`/scientific tokens; ragged rows; comments-and-headers-only file; empty file;
  malformed tokens. Asserts values, labels, legends, kinds, warnings, stats.
- `test_analysis.py`: averaging (known small arrays, mismatched grids → interpolation + warning
  path, incompatible signature → rejected), smoothing (exact expected arrays, odd-window
  enforcement), unit conversion (scale factors, label rewrite, auto-pick).

**Manual smoke checklists** (`tests/smoke/`):

- UI: golden path from PRD §5; legend-toggle; warning file handling; recents; export all four
  formats; clipboard paste into an image editor.
- Packaging (per OS): artifact builds clean; launches from icon/shortcut; menu entry exists
  (Win/macOS); double-click `.xvg` opens app with file plotted; uninstall clean (Windows).

---

## 15. Milestones (implementation phase, after doc sign-off)

| Milestone | Deliverable | Depends on |
|---|---|---|
| **M1** | `core/` parser + models + analysis, full unit tests, fixtures | — |
| **M2** | Main window shell: folder bar, file table, single-file plot, toolbar | M1 |
| **M3** | Multi-file overlay, series dock, style dock, legend toggling | M2 |
| **M4** | Averaging, smoothing, unit conversion | M3 |
| **M5** | Export dialog, clipboard, settings persistence | M2 |
| **M6** | App identity + packaging: icon pipeline, per-OS builds, installer/DMG/AppImage, associations | M5 |
| **M7** | Polish: warnings UX, single-instance, README with per-OS install screenshots, smoke pass | M6 |

Each milestone ends runnable; M2 onward is usable daily on the developer machine.

---

## 16. Risks and mitigations

| Risk | Mitigation |
|---|---|
| XVG dialects beyond GROMACS (grace `@with g0` regions, in-file `@ sN` restyles) | Unknown directives ignored by design; graceful degradation tested with foreign fixtures |
| PyInstaller + PySide6 large artifact (~80–150 MB) | Accepted for v1; onedir variant if onefile start-time regresses |
| macOS Gatekeeper blocks unsigned DMG | README documents right-click→Open; signing is backlog |
| `.xvg` association conflicts with existing grace install | Association is **offered, not forced** (installer checkbox); per-OS fallback documented |
| Very large files (multi-MB, 1M+ rows) | numpy-batched parse, async load with progress; plot decimation is backlog if needed |
