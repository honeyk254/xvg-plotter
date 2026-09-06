# XVG Plotter — Consolidated Problem List

*Separate companion to [USER_PANEL.md](USER_PANEL.md). Every problem observed across the 30-person simulated panel, deduplicated, categorized, and ranked.*

| | |
|---|---|
| **Source** | 30 simulated panelists ([USER_PANEL.md](USER_PANEL.md)), 110 problem mentions total |
| **Remediation** | [REMEDIATION_PLAN.md](REMEDIATION_PLAN.md) — phased fix plan covering every item below |
| **Frequency** | = number of panelists facing the problem |
| **Status** | Where the issue stands relative to PRD.md / SPEC.md v1: **covered** (v1 addresses it), **partial** (addressed but with a gap), **backlog** (explicitly deferred in PRD §9 / SPEC §16), **non-goal** (deliberately out of v1 scope), **gap** (not addressed anywhere in the docs) |

---

## Top issues at a glance (by frequency × severity)

| Rank | ID | Problem | Freq. | Severity |
|---|---|---|---|---|
| 1 | C01 | Unsigned downloads trigger OS/AV warnings; blocked in some environments | 9 | **High** |
| 2 | C17 | Many-series overlays: repeating colors, unreadable legend, colorblind-unsafe | 7 | **High** |
| 3 | C29 | No batch export / no CLI or scripting automation | 5 | **High** |
| 4 | C37 | No onboarding/help; jargon unexplained for novices | 4 | **High** |
| 5 | C08 | No recursive scan or cross-folder search | 4 | Medium |
| 6 | C13 | No drag-and-drop of files/folders | 4 | Medium |
| 7 | C22 | Single-window/single-instance; no side-by-side comparison | 4 | Medium |
| 8 | C24 | No fitting or derived quantities (fits, derivative, normalization) | 4 | Medium |
| 9 | C30 | No data export (CSV/text of plotted/averaged/converted curves) | 4 | Medium |
| 10 | C02 | No auto-update or update check | 3 | Medium |
| 11 | C23 | Large-file performance: no decimation, sluggish redraws | 3 | Medium |

Full catalog follows.

---

## A. Installation, updates & deployment

**C01 · Unsigned artifacts trigger security warnings — the #1 adoption blocker.** Windows SmartScreen/"unknown publisher" on the installer and portable exe; antivirus quarantine; macOS Gatekeeper refusal (right-click → Open is undiscoverable); corporate AppLocker policies block entirely. Directly threatens PRD goal 6 ("a friend installs it themselves… without help") and success criterion 2.
Freq. 9 (P01, P03, P05, P07, P12, P21, P23, P25, P30) · Severity **High** · Status: partial — macOS case acknowledged (PRD §7, SPEC §16; signing in backlog §9); the Windows/AV side has no documented mitigation. → Recommendation: code signing where affordable; publish SHA-256 checksums + a "your browser/AV may warn you" install-page section; consider EV cert for the Windows installer first.

**C02 · No auto-update and no update check.** Users never learn that fixes exist; fleets drift across versions (P07's 40 machines). Freq. 3 (P03, P07, P30) · Severity Medium · Status: non-goal (PRD §3, backlog §9). → Cheap interim: "check for updates" link + current-version note in About.

**C03 · Heavy download and slow cold start on old/slow hardware.** ~80–150 MB artifacts (SPEC §16); onefile self-extraction on HDD makes cold start 10–20 s (P23), far past the < 3 s budget. Freq. 2 (P19, P23) · Severity Medium · Status: covered — SPEC §12 already mandates a onedir fallback if startup regresses. Keep that guardrail enforced in the smoke checklist.

**C04 · AppImage friction on Linux.** `chmod +x` barrier for novices; fails outright without FUSE (cluster nodes, NFS homes); workaround undocumented. Freq. 2 (P06, P07) · Severity Medium · Status: gap — PRD §7 assumes the AppImage just runs. → Document `--appimage-extract`; consider offering a `.deb`/tarball.

**C05 · No silent/per-machine deployment for managed fleets.** Per-user Inno Setup only; no MSI/parametrized install for sysadmins. Freq. 1 (P07) · Severity Medium · Status: gap. → Inno Setup supports silent flags; document them, add a per-machine option.

**C06 · `.xvg` file-association friction.** Conflicts with existing grace installs (association is offered, not forced — SPEC §16); when declined, Windows "Open with" nagging repeats on every double-click. Freq. 3 (P08, P11, P18) · Severity Medium · Status: partial. → Document the choice clearly; consider in-app "set as default viewer" toggle.

**C07 · No checksums/signatures for offline verification.** Air-gapped/regulated environments require integrity verification for exception approvals. Freq. 1 (P25) · Severity Low · Status: gap. → Publish SHA-256 sums with each release (pairs with C01).

## B. Browsing & file handling

**C08 · No recursive scan or cross-folder search.** Only the current flat folder is listed; nested project trees (per-protein, per-student, per-window) require manual folder hopping. Freq. 4 (P04, P09, P17, P26) · Severity Medium · Status: gap (not in backlog). → Candidate for v1.x: optional "include subfolders" scan with depth limit.

**C09 · Cloud-synced and network folders misbehave.** OneDrive/Dropbox placeholder hydration during scan (surprise downloads), sync-locked files surfacing as spurious warnings, slow network scans. Freq. 3 (P07, P16, P20) · Severity Medium · Status: gap. → Detect cloud placeholder attributes (Windows) and skip/hydrate lazily with a notice.

**C10 · Grace dialect features silently ignored.** `@ with g0` regions, in-file series styling, `@ target`, formulas: ignored by design (SPEC §5.2/§16), so files curated in grace lose their structure and styling. Freq. 2 (P11, P18) · Severity Medium · Status: non-goal-ish (by design) — but *silent*. → Surface "N grace directives were ignored" prominently per file (stats already count them; make them visible).

**C11 · Multi-dataset (`&`) files: only the first dataset is surfaced.** Dataset selector exists (SPEC §5.6) but datasets cannot be overlaid across files, and users don't discover the selector. Freq. 2 (P10, P18) · Severity Medium · Status: partial. → Make the dataset selector obvious; consider dataset-as-series overlay in v1.x.

**C12 · No support for sibling GROMACS formats (`.xpm`, `.edr`, `.xtc`).** Deliberate non-goal (PRD §3), but users' mental model is "the GROMACS plotting app," so the boundary surprises them. Freq. 2 (P04, P13) · Severity Low · Status: non-goal. → Expectation management: explicit "supported formats" note in-app and on the download page.

**C13 · No drag-and-drop.** Dropping files/folders from Explorer/Finder onto the window does nothing; novices try it first. Freq. 4 (P01, P05, P08, P21) · Severity Medium · Status: gap. → Cheap, high-yield: accept drops of `.xvg` files and folders.

**C14 · Recents/favorites gaps.** Recents hold dead paths after folders move (no pruning), no file-level recents, no pinning. Freq. 3 (P20, P26, P29) · Severity Low · Status: partial (recents exist; hygiene doesn't). → Prune dead entries on failure; add pin-to-favorites.

## C. Plotting & interaction

**C15 · No annotation tools.** No text, arrows, or panel labels on the canvas — wanted for talks, supervision feedback, and publication figures. Freq. 3 (P04, P13, P24) · Severity Medium · Status: gap (not in backlog). → Even a minimal "add text" annotation, exported with the figure, covers most requests.

**C16 · No figure-geometry/typography control.** Figure size/aspect, font family, tick formatting are all fixed; journal figure specs (85 mm column, Helvetica) are unreachable without post-editing. Freq. 3 (P02, P11, P24) · Severity Medium · Status: gap — styling exists (colors, grid, legend) but not geometry/typography. → Figure-size + font-family settings would satisfy most publication workflows.

**C17 · Many-series overlays are unreadable.** Default color cycle repeats beyond ~10 series, colors are colorblind-unsafe, no per-series color picker, legend overlaps data on small canvases. Undermines the core U4 comparison workflow. Freq. 7 (P05, P08, P10, P19, P21, P22, P24) · Severity **High** · Status: partial (preset palettes and legend position exist; per-series editing doesn't). → Add per-series color/label editing, colorblind-safe palettes (e.g., Okabe–Ito default option), and smart legend placement.

**C18 · No subplot grids / small multiples.** Comparing 10–50 files requires overlays; supplement figures want grids. Freq. 2 (P02, P12) · Severity Low · Status: backlog (PRD §9).

**C19 · Thin keyboard support.** Six shortcuts total (SPEC §6.4); file table, docks, filter, legend toggling, and export dialog are mouse-first; no command palette. Freq. 3 (P11, P15, P27) · Severity Medium · Status: gap. → Define keyboard navigation order + core shortcuts per widget; also serves accessibility (C34).

**C20 · Dock-heavy layout crowds small screens.** On 1366×768 (and at 200 % scaling) the three docks leave a sliver of canvas; no compact/zen mode. Freq. 2 (P15, P19) · Severity Medium · Status: partial (docks are collapsible/movable and persist). → Add a "focus mode" that auto-collapses docks.

**C21 · No session save/restore.** Selected files, styles, zoom survive until the app closes; yesterday's comparison is gone (only folders/geometry persist, SPEC §9). Freq. 2 (P03, P04) · Severity Low · Status: gap. → Persist last plot state like last folder.

**C22 · Single-window/single-instance prevents side-by-side work.** PRD §7 *requires* single-instance forwarding, but the effect is that two projects/folders can never be compared on two monitors, and a second launch hijacks the current selection. Freq. 4 (P09, P10, P26, P27) · Severity Medium · Status: non-goal by omission — a deliberate v1 design with a real cost. → Consider opt-out ("open in new window" modifier) in v1.x.

**C23 · Large-file performance.** No plot decimation (SPEC §16 backlog "if needed"); multi-million-point overlays and smoothing make redraws sluggish and memory-heavy; the < 1 s budget covers only 100k rows. Freq. 3 (P09, P17, P23) · Severity Medium · Status: backlog (SPEC §16). → Measure with a 1M-row fixture before release; implement min/max decimation for interactive view.

## D. Analysis

**C24 · No fitting or derived quantities.** Viewer-only scope (PRD §3 non-goal): no line/exponential fits, derivative, normalization, baseline, block averaging — the reason power users keep their scripts and novices get stuck on supervisor requests. Freq. 4 (P01, P06, P11, P14) · Severity Medium · Status: non-goal; PRD §9 backlog has "simple derived quantities". → Ship the backlog item (running average/baseline) and set expectations in-app ("viewer — fit in your script").

**C25 · Unit conversion is X-time only.** ps→ns/µs/ms on the X axis (SPEC §7.3); no Y-axis conversions (nm→Å, kJ→kcal/mol), no generic scale/offset, and X is assumed to be time — conversion misfires on step-index axes. Freq. 2 (P14, P28) · Severity Medium · Status: gap beyond the specced feature. → At minimum, detect non-time X labels and disable the conversion; Y-scale factor is a cheap generalization.

**C26 · No quick stats readout.** Min/max/mean of visible series is only a P2 nice-to-have (PRD §6); QA and convergence eyeballing want numbers first. Freq. 2 (P09, P17) · Severity Low · Status: P2 (may not ship). → Promote to P1; it is small and high-value.

**C27 · Replica-averaging caveats are opaque.** Averaging requires "compatible signatures" (disabled toggle with a terse tooltip) and interpolates onto the *first file's* X grid — silently truncating mixed-length replicas, with a >5 % warning that doesn't explain consequences or offer a reference/common-range choice (SPEC §7.1). Freq. 2 (P10, P22) · Severity Medium · Status: partial — feature works, UX doesn't. → Explain in the tooltip; offer reference-grid and common-time-range options.

**C28 · Smoothing window is in points, not physical time.** Same window = different timescales across files with different `dt`; misleading comparisons; no alternative filters. Freq. 2 (P14, P22) · Severity Medium · Status: gap beyond SPEC §7.2. → Show the window in physical time next to the point count.

## E. Export

**C29 · No batch export, no CLI/scripting automation.** One dialog round-trip per figure (a 300-figure thesis = 300 round-trips); no headless export or API for pipelines. Freq. 5 (P02, P06, P10, P12, P17) · Severity **High** · Status: backlog (PRD §9 has batch export); CLI/automation entirely absent (consistent with the zero-CLI *user* positioning, but a real loss for power users). → Ship batch export ("export all selected"); a hidden `--export` CLI flag later would serve RSEs without touching the GUI promise.

**C30 · No data export.** Images only; the plotted, averaged, smoothed, or unit-converted series cannot be saved as CSV/text — needed for data repositories, ML features, and papers. Freq. 4 (P02, P14, P22, P28) · Severity Medium · Status: gap. → "Export data (CSV)" of the current view is cheap and closes the biggest gap between "viewer" and "usable in a research workflow."

**C31 · Copy-to-clipboard resolution unspecified.** Pasted figures land at screen resolution and look soft on high-DPI displays/4K projectors (SPEC §8 defines mechanism, not DPI). Freq. 2 (P03, P13) · Severity Medium · Status: gap. → Copy at the configured export DPI (or 300 default).

**C32 · Vector/format gaps.** No TIFF (journal staple); EPS/SVG font-embedding and text-as-paths quirks; transparency differs per format; no font selection to control embedding. Freq. 3 (P02, P11, P24) · Severity Medium · Status: partial (four formats + DPI 100–600 exist). → TIFF via Pillow is trivial; document per-format caveats.

**C33 · No printing.** Handouts require export → external viewer → print. Freq. 1 (P12) · Severity Low · Status: gap (low priority).

## F. UX, language & accessibility

**C34 · Canvas is invisible to assistive technology.** No textual data summary, no keyboard-accessible value inspection, fixed contrast on the canvas. Freq. 1 (P15) · Severity Medium · Status: gap — accessibility is unaddressed in both docs. → A "describe this plot" status summary (min/max/trend/n points) serves screen readers and everyone else.

**C35 · No localization.** English-only UI (backlog, PRD §9); terminology like "replica averaging" is a hurdle for non-native speakers. Freq. 1 (P16) · Severity Low · Status: backlog.

**C36 · Glyph/font fallback in exports.** µ, Å, ±, ε, and especially CJK characters can render as boxes in exported figures depending on bundled fonts — silent corruption of non-ASCII labels. Freq. 2 (P16, P28) · Severity Medium · Status: gap. → Ship a Unicode-complete default font stack (e.g., DejaVu + Noto fallback); test CJK in the export fixtures.

**C37 · No onboarding, help, or jargon explanations.** Zero tooltips/tour; the README is developer-oriented; PRD's own bar is "zero documentation" golden path — but *understanding* the science (Rg, xydy, replicas) is left to luck. Freq. 4 (P01, P05, P08, P21) · Severity **High** for the novice segment · Status: gap. → Tooltips on every control, a one-screen first-run intro, and plain-language legend for common GROMACS analyses.

**C38 · No dark-mode/theme handling.** Hard-coded light UI + white canvas glare on dark desktop themes. Freq. 1 (P06) · Severity Low · Status: gap (cosmetic).

## G. Trust, support & settings

**C39 · No logs or crash reporting.** `--noconsole` builds fail silently; no log file location, no error detail dialogs, no feedback channel in About — bug reports are impossible for the people who hit the bugs. Freq. 2 (P25, P30) · Severity Medium · Status: gap. → Ring-buffer log written to the standard OS app-data dir + "Copy diagnostics" in About.

**C40 · Settings are not portable.** QSettings live per-machine in registry/plist/ini (SPEC §9): no export/import or sync, no shared style templates for labs/courses. Freq. 2 (P12, P29) · Severity Low · Status: gap. → "Export/import settings" plus a styles-file concept later.

---

## Recommended next steps

**Quick wins (small effort, closes frequent or embarrassing gaps):**
1. C13 drag-and-drop · 2. C31 clipboard at export DPI · 3. C14 recents pruning + favorites · 4. C27 averaging warning text · 5. C36 Unicode font fallback · 6. C07 publish checksums (pairs with C01) · 7. C26 promote stats to P1 · 8. C10 surface "N directives ignored" per file.

**Decide before release (High severity):**
- **C01**: signing/AV strategy — this alone decides whether goal 6 ("friend installs unaided") is achievable.
- **C17**: per-series color editing + colorblind-safe default palette.
- **C29**: batch export promotion from backlog to v1 (the export dialog loop is the single most repeated action in the panel).
- **C37**: tooltips + first-run intro for the novice segment.

**Conscious trade-offs to document (not fix):** C12 (formats non-goal), C24 (viewer-not-analysis scope), C22 (single-instance cost) — all defensible v1 boundaries, but they should be stated in-app so users' expectations land correctly.
