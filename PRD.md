# XVG Plotter — Product Requirements Document

| | |
|---|---|
| **Product** | XVG Plotter |
| **Version** | 1.0 (v1 scope) |
| **Status** | Draft — for review |
| **Date** | 2026-09-05 |
| **Companion doc** | [SPEC.md](SPEC.md) (technical specification) |

---

## 1. Summary

XVG Plotter is a cross-platform **desktop application** for interactively viewing and exporting
GROMACS `.xvg` analysis files. It replaces the xmgrace workflow with a modern matplotlib-backed
viewer: browse a folder, see every analysis file with readable metadata, click to plot, compare
replicas, restyle, and export publication-quality figures — with **no command line at any point**,
from installation to daily use.

**One-liner:** *“Double-click an `.xvg`, get a proper plot.”*

---

## 2. Problem statement

GROMACS analysis tools (`gmx rms`, `gmx energy`, `gmx rdf`, `gmx gyrate`, `gmx hbond`, …) write
their results as Grace/Xmgr `.xvg` files. Today the only realistic way to view them is xmgrace,
which is:

- **Dated and hostile** — unintuitive UI, cryptic dialogs, poor discoverability.
- **Browse-hostile** — no way to see *what* analyses exist in a folder of dozens of `.xvg` files
  without opening each one.
- **Workflow-awkward** — common MD tasks (overlaying replicas, averaging replicate runs,
  unit conversion ps→ns) require grace scripting or manual CSV wrangling.
- **Export-poor** — default exports look nothing like publication quality.

Researchers fall back to ad-hoc matplotlib scripts that are rewritten (and forgotten) every time.

---

## 3. Goals and non-goals

### Goals (v1)

1. **Instant insight** — open a folder → see all `.xvg` files with title, series count, and size;
   click a file → plot appears with axis labels and legend pulled from the file header.
2. **Comparison workflows** — overlay multiple files/series on one plot; average replicate runs
   into a mean ± SD band with one toggle.
3. **Interactive exploration** — pan, zoom, inspect coordinates, toggle series, restyle
   (colors, line/marker style, grid, log axes, legend position) with immediate feedback.
4. **Publication-quality export** — PNG (configurable DPI), PDF, SVG, EPS, plus
   copy-image-to-clipboard for slides.
5. **Zero command line** — installs like a normal app on Windows, macOS, and Linux; launches
   from an app icon with the product's own branding; can be set as the default viewer for `.xvg`.
6. **Shareable** — a friend installs it themselves on any OS without help (download → double-click
   → launch from icon).

### Non-goals (v1)

| Deferred | Reason |
|---|---|
| Curve fitting / data editing | Display-only helpers (normalize, baseline, least-squares fit line) shipped in v1.3; full data editing stays out of scope |
| Reading `.xpm`, `.edr`, `.xtc` directly | Scope; these need different renderers |
| Subplot grid layouts | ~~Nice-to-have~~ shipped in v1.3 (View ▸ Grid view of checked files) |
| Batch export of many files at once | ~~Backlog~~ shipped in v1.2 (File ▸ Export all checked files) |
| Remote/server mode | Data is local; a desktop app is the right shape |
| Auto-update / code-signed macOS builds | Backlog; documented workaround for Gatekeeper instead |
| CI release automation | Build scripts are runnable by hand per-OS first |

---

## 4. Target users and platforms

- **Who**: molecular-dynamics researchers and students (the author + labmates/colleagues), plus
  anyone who receives `.xvg` files from collaborators.
- **Skill profile**: comfortable with GUI apps; should never need to know Python exists.
- **Platforms**: Windows 10/11, macOS 12+, and mainstream Linux (glibc-based distributions).
  One codebase; per-OS packaged artifacts (see §7 and SPEC §12).

---

## 5. User stories and workflows

| # | Story | Priority |
|---|---|---|
| U1 | As a researcher, I **double-click the app icon** (or double-click an `.xvg` file that is associated with the app) and the app opens at my last-used folder (or the clicked file's folder). | P0 |
| U2 | I **open a folder** and immediately see every `.xvg` in it listed with its title, number of series, number of points, size, and modified date — so I can find “that Rg analysis” without opening files one by one. | P0 |
| U3 | I **click a file** and instantly get its plot, with title and axis labels auto-populated from the XVG header — no configuration. | P0 |
| U4 | I **checkbox-select several files** (e.g., `rg_prod1.xvg`, `rg_prod2.xvg`) to overlay them on one plot for comparison. | P0 |
| U5 | In a multi-series file (`energy.xvg` from `gmx energy`), I **toggle individual series** (Total, Potential, Kinetic…) on and off, including an error-bar column if present. | P0 |
| U6 | I select **replica runs of the same analysis** and toggle “average replicas” → mean line ± shaded SD band, with optional faint member curves. | P1 |
| U7 | I **rescale the X axis** from ps to ns (or µs) with the axis label updated to match. | P1 |
| U8 | I toggle a **moving-average smoothing overlay** (adjustable window) to see trends in noisy data. | P1 |
| U9 | I **pan and zoom** the plot, read out cursor coordinates, and click a legend entry to show/hide that series. | P0 |
| U10 | I **export** the current plot as PNG (300 dpi default) / PDF / SVG / EPS, optionally with transparent background — and I can just hit *Copy Image* and paste it into a slide. | P0 |
| U11 | When a file is malformed or empty, I see a clear per-file warning instead of a crash, and the rest of the folder still works. | P0 |

### Golden path (acceptance walkthrough)

1. Launch app → window opens at last-used folder.
2. Click *Open Folder* → pick simulation analysis directory → file list populates (U1, U2).
3. Click `rmsd.xvg` → plot renders with “RMSD”, “Time (ps)”, “RMSD (nm)” and legend (U3).
4. Check `rmsd_replica2.xvg`, `rmsd_replica3.xvg` → three curves overlaid (U4).
5. Toggle *Average replicas* → mean ± SD band appears (U6).
6. Set X unit to **ns** → axis rescales and relabels (U7).
7. *Export…* → PNG, 300 dpi → figure lands in the analysis folder (U10).

**Bar: the golden path must be doable in under 30 seconds with zero documentation.**

---

## 6. Feature list (v1)

### P0 — must ship

- Folder browsing: path bar, *Open Folder* button, recent-folder dropdown, async scan (UI never freezes).
- File list with metadata columns (Name, Title, Series, Points, Size, Modified) and per-file warning indicators.
- Robust XVG parser (see SPEC §5): GROMACS headers, multi-series, error-bar files (`xydy`), multi-dataset files (`&`), graceful handling of malformed files.
- Plotting via matplotlib: single-click plot, multi-file overlay, per-series toggle, error bars.
- Interaction: pan/zoom/home toolbar, coordinate readout, legend-click to toggle series.
- Styling: color cycle, line/marker toggles, grid, log-X/log-Y, legend position, title/axis-label overrides.
- Export: PNG / TIFF / PDF / SVG / EPS with DPI control and transparent-background option; copy image to clipboard (at the export DPI); batch export of every checked file; CSV export of the plotted data; printing. Settings export/import. Exact figure size (inches) and font family for journal specs.
- Settings persistence: last folder, recents, window geometry, export defaults.

### P1 — should ship in v1 (agreed must-have extras)

- **Replica averaging** (mean ± SD, member-curve display toggle, optional common time
  range so shorter replicas cannot truncate longer ones).
- **Smoothing** (centered moving average, adjustable window, drawn as overlay).
- **Time-unit conversion** (ps → ns/µs/ms, auto-pick mode, axis relabeling).

### P2 — nice to have if time allows

- Column-level “±” pairing UI for error-bar files lacking `@ sN type` directives.
- Status-bar preview stats (min/max/mean of visible series).

---

## 7. Launch & distribution experience (first-class requirement)

The app must feel like a native application on every OS. No terminal, no pip, no Python.

| OS | Artifact | Install experience | Launch experience | Icon |
|---|---|---|---|---|
| **Windows** | `XVGPlotter-Setup.exe` (Inno Setup) + portable `.exe` | Double-click installer → Next → Finish. Creates Start Menu + Desktop shortcuts; offers `.xvg` file association; clean uninstaller. | Start Menu / Desktop shortcut; taskbar shows app icon. | `.ico` |
| **macOS** | `XVGPlotter.dmg` (contains `XVG Plotter.app`) | Open DMG → drag app to Applications. | Launchpad / Applications / Spotlight. | `.icns` |
| **Linux** | `XVGPlotter-x86_64.AppImage` | Download, `chmod +x` once, run. Bundled `.desktop` entry integrates with the app menu (via AppImage metadata). | App menu entry or double-click the AppImage. | hicolor `.png` set |

Additional experience requirements:

- **App identity everywhere**: window title bar, taskbar/dock, installer/shortcut, and About dialog all show the *XVG Plotter* name and icon (SPEC §11).
- **`.xvg` file association** (offered, not forced): double-clicking an `.xvg` opens XVG Plotter with that file pre-plotted and its folder loaded (per-OS mechanism in SPEC §12).
- **Single instance**: launching again (or opening a second `.xvg`) focuses the running window and loads the new file/folder there.
- **macOS note**: v1 ships unsigned; the README documents the standard “right-click → Open” first-launch step. Signed/notarized builds are backlog.
- Users never see a console window (`--noconsole` builds; no stdout dependency).

---

## 8. Success criteria

1. **Golden path** (§5) completes in < 30 s, zero documentation, on all three OSes.
2. A friend installs and plots their own GROMACS output unaided.
3. Standard GROMACS outputs (`gmx rms/energy/rmsf/gyrate/rdf/hbond/mindist/density/sasa`…) plot correctly with no manual settings.
4. Exports are directly usable in a paper/thesis (300-dpi PNG, vector PDF/SVG) with labels and legend already correct.
5. No crash on any malformed input file; warnings are visible and actionable.
6. Plot refresh after any style change feels instant (< 200 ms typical; SPEC §13).

---

## 9. Backlog (post-v1)

- Built-in file preview panel (sparkline) in the file list.
- Signed/notarized macOS builds; CI-based release artifacts for all OSes.
- Localization (a zh-CN pass was built for v1.3 and removed by decision; `tr()` wrappers remain).

---

## 10. Open questions (to resolve during review)

1. **Name**: “XVG Plotter” — fine, or would you prefer something more distinctive?
2. **Default export DPI**: 300 assumed — some journals want 600; keep both presets?
3. **macOS priority**: is anyone in the friend group actually on macOS for v1, or is Windows+Linux enough to validate first? (Affects when M6-macOS gets exercised.)

---

## 11. Traceability

| Requirement | Spec section |
|---|---|
| U1 launch/association/single-instance | SPEC §11, §12, §10.4 |
| U2 folder browsing, metadata, async | SPEC §6.1, §13 |
| U3–U5 parsing, plotting, series toggle | SPEC §5, §6.3, §6.4 |
| U6–U8 averaging, units, smoothing | SPEC §7 |
| U9 interaction | SPEC §6.3 |
| U10 export/clipboard | SPEC §8 |
| U11 robustness | SPEC §5.5, §10 |
