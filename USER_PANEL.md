# XVG Plotter — Simulated User Panel (n = 30)

| | |
|---|---|
| **Purpose** | Pre-release pain-point discovery for XVG Plotter v1 |
| **Method** | Synthetic panel: 30 simulated users profiled from the PRD target population (MD researchers, students, collaborators, support staff) across OS, skill level, data scale, and workflow. Each person's problems are derived from what v1 actually does and does not do (PRD §3/§6/§7, SPEC §5–§13). |
| **Companion doc** | [PROBLEM_LIST.md](PROBLEM_LIST.md) — separate consolidated list of every problem, with frequency, severity, and v1 status |
| **Note** | These are simulated personas (expert judgment, not survey data). Problem IDs `[Cnn]` reference the consolidated list. |

---

## Panel at a glance

| ID | Name | Role | OS | Skill | Primary workflow |
|---|---|---|---|---|---|
| P01 | Amara Okafor | 1st-year PhD student, membrane proteins | Windows 11 | Novice | First RMSD/Rg plots for group meeting |
| P02 | Lukas Schmidt | Finishing PhD student, thesis writing | Linux (Ubuntu) | Intermediate | 300+ figures for a thesis |
| P03 | Yuki Tanaka | Postdoc, daily GROMACS | macOS (M2) | Intermediate | Replica comparison, slide figures |
| P04 | Prof. Elena Marchetti | PI / group leader | macOS | Novice (GUI only) | Viewing students' results |
| P05 | Daniel Reyes | Undergraduate intern | Windows 10 | Novice | Learning MD analysis |
| P06 | Dr. Priya Raghavan | Research software engineer | Linux | Expert | Pipelines, automation |
| P07 | Mateusz Kowalski | Lab sysadmin / HPC support | Linux + Windows fleet | Expert | Deploying to ~40 lab machines |
| P08 | Sofia Rossi | Experimentalist collaborator | Windows | Novice | Receives `.xvg` files by email |
| P09 | Dr. Ahmed Hassan | Computational biophysicist, big datasets | Linux workstation | Expert | Multi-million-point trajectories |
| P10 | Ingrid Larsson | Free-energy researcher, 48 λ-windows | Linux | Intermediate | dhdl/RDF per window |
| P11 | Jean-Pierre Dubois | 20-year xmgrace veteran | Linux | Expert | Migrating daily xmgrace work |
| P12 | Dr. Hannah Weber | Teaching-lab instructor | Windows | Intermediate | Course materials, student examples |
| P13 | Carlos Mendes | Co-supervisor reviewing student data | macOS + iPad | Novice | Reviewing, commenting on plots |
| P14 | Dr. Wei Zhang | ML-oriented researcher | Linux / Windows | Expert | Exporting features for ML |
| P15 | Fatima Al-Sayed | MSc student, screen-reader user (NVDA) | Windows 11 | Intermediate | Independent analysis for thesis |
| P16 | Chen Wei | PhD student, Chinese-speaking | Windows | Intermediate | Standard protein-ligand analyses |
| P17 | Dr. Olga Petrova | Simulation-center staff scientist | Linux | Expert | QA of ~40 students' runs |
| P18 | Robert Klein | Computational chemist (non-GROMACS grace files) | Windows | Expert | Files from other codes |
| P19 | Aisha Bello | PhD student on small old laptop | Windows 10 | Intermediate | Everyday plotting |
| P20 | Tomás Silva | Postdoc, OneDrive-synced data | Windows 11 | Intermediate | Everyday plotting on synced folders |
| P21 | Emily Carter | Experimentalist, never used MD | macOS | Novice | Opening a colleague's `energy.xvg` |
| P22 | Dr. Rajesh Kumar | Replicas of different lengths | Linux | Intermediate | Averaging 6 replicas |
| P23 | Peter Novák | Researcher on 2015 laptop (HDD) | Windows 10 | Intermediate | Everyday plotting, slow hardware |
| P24 | Laura García | Scientific illustrator | macOS | GUI expert | Journal figure preparation |
| P25 | Dmitri Volkov | Pharma scientist, locked-down PC | Windows (corporate) | Intermediate | Analysis behind corporate policy |
| P26 | Nomsa Dlamini | Multi-project researcher (3 collaborations) | Windows 11 | Intermediate | Juggling many folders |
| P27 | Alex Turner | Keyboard-only power user | Linux | Expert | Mouse-averse daily use |
| P28 | Dr. Mei Ling | Biophysicist, unusual axes/units | macOS + Linux | Expert | Non-time X axes, unit conversions |
| P29 | Jonas Berg | Researcher on two machines | Windows 11 | Intermediate | Desktop at office, laptop at home |
| P30 | Zara Ahmed | Early adopter, first friend to install | Windows 11 | Intermediate | First contact with bugs/updates |

---

## Individual profiles and problems

### P01 — Amara Okafor · 1st-year PhD student · Windows 11 · novice
First month of her first simulation project. Has never used xmgrace; everything she knows about analysis comes from her supervisor's examples.

- **[C01]** The installer triggers a Windows SmartScreen "unknown publisher" warning. She nearly cancels the install — nobody told her unsigned apps look like this.
- **[C37]** No onboarding or help. She does not know what `xydy` means in the series dock, or what "Rg" is, and there is no tooltip or tour to explain any of it.
- **[C24]** Her supervisor asks for "an exponential fit to the RMSD plateau." The app is a viewer only — no fitting — so she is back to rewriting a matplotlib script.
- **[C13]** Her instinct is to drag files from Explorer onto the window. Nothing happens; drag-and-drop is not supported.

### P02 — Lukas Schmidt · finishing PhD student · Linux · intermediate
Thesis submission in three months. Needs roughly 300 consistent figures plus a data deposit.

- **[C29]** No batch export: the same export dialog, 300 times, one file at a time.
- **[C18]** His supplement needs 24 Rg curves as a grid of small multiples. Only single-axes plots exist.
- **[C16]** Journal template requires fixed figure width, Helvetica, and specific tick styles. There is no figure-size, font-family, or tick-format control.
- **[C30]** The research-data repository wants the averaged Rg curves as numbers. He cannot export plotted/averaged data as CSV — only images.
- **[C32]** The journal accepts TIFF; the app exports PNG/PDF/SVG/EPS only.

### P03 — Yuki Tanaka · postdoc · macOS (M2) · intermediate
Uses GROMACS daily; makes figures for talks and papers; upgrades tools eagerly.

- **[C01]** First launch of the unsigned DMG is blocked by Gatekeeper; the right-click → Open ritual is not discoverable and she initially thinks the app is broken.
- **[C02]** No update check. She will still be on v1.0 a year from now and never hear about fixes.
- **[C31]** *Copy Image* pastes into Keynote at screen resolution; on her 4K display the pasted figure looks soft next to the 300-dpi PNGs she exports manually.
- **[C21]** Yesterday's carefully selected file set, zoom window and styling are gone on relaunch — settings persist, but the working state does not.

### P04 — Prof. Elena Marchetti · PI · macOS · GUI-only
Never touches the cluster. Wants to see what her students produced, now.

- **[C15]** Wants to drop an arrow and the note "look at 40 ns" on a plot before the group meeting. There are no annotation tools at all.
- **[C08]** Students' analyses are spread across nested per-protein folders. She must open each folder separately; there is no recursive scan or cross-folder search.
- **[C12]** Asked the app to "just open the trajectory and the contact map" — `.xtc`/`.xpm`/`.edr` are out of scope, so she keeps three tools around anyway.
- **[C21]** Cannot pull up last week's comparison; nothing about the session (selected files, styles) is restorable.

### P05 — Daniel Reyes · undergraduate intern · Windows 10 · novice
Six-week rotation project; first exposure to molecular simulation.

- **[C37]** The UI assumes he knows what RMSD, replicas, and ps→ns mean. No tooltips, glossary, or guided example.
- **[C01]** Downloaded the portable `.exe`; his antivirus quarantined it as suspicious (unsigned, heuristic flag). He assumed he had downloaded malware.
- **[C13]** Tried dragging `.xvg` files in from the desktop. No drag-and-drop support.
- **[C17]** Overlaying five files produces five curves whose default colors are hard to tell apart, and the legend lands on top of the data.

### P06 — Dr. Priya Raghavan · research software engineer · Linux · expert
Wraps lab software into reproducible pipelines. Judges tools by whether they can be automated.

- **[C29]** No CLI, no headless export, no scripting API. The app cannot participate in her pipeline, so she keeps her own matplotlib scripts anyway.
- **[C04]** The cluster login nodes have no FUSE; the AppImage refuses to start and the `--appimage-extract` workaround is not documented anywhere in the app.
- **[C24]** Wants block-averaging error estimates on the plotted series. Viewer scope says no.
- **[C38]** Her desktop theme is dark; the app is a blinding white rectangle (UI theme and canvas are not handled).

### P07 — Mateusz Kowalski · lab sysadmin · Linux + Windows fleet · expert
Keeps ~40 lab machines working; everything must be deployable, updateable, auditable.

- **[C05]** Windows installer is per-user only. No MSI/silent install, so he cannot push it; every student installs (or mis-installs) their own copy.
- **[C02]** No update channel. Within a semester, 40 machines run 6 different versions.
- **[C04]** Linux pool machines mount homes over NFS without FUSE — AppImages fail to execute there.
- **[C01]** Unsigned artifacts are blocked by campus AV policy; there are no published checksums he could whitelist or verify against.
- **[C09]** Scanning shared analysis drives over the network is slow and wakes the AV scanner on every machine.

### P08 — Sofia Rossi · experimentalist collaborator · Windows · novice
Her MD collaborator emails her `.xvg` files; she just needs to look at them.

- **[C37]** Opens `energy.xvg` and sees six checkboxes (Potential, Kinetic, Total…). She does not know which one is "the energy" and there is no guidance.
- **[C17]** With several series shown at once, colors are similar and the legend overlaps the curves; she screenshots the wrong thing twice.
- **[C06]** She declined the file association during install, so every double-click on an `.xvg` throws the Windows "How do you want to open this?" dialog at her.
- **[C13]** Expected to drag the attachment straight from her mail client into the app.

### P09 — Dr. Ahmed Hassan · computational biophysicist · Linux workstation · expert
Runs millisecond-scale trajectories; analysis files have millions of rows.

- **[C23]** With 20 large files overlaid, redraws get sluggish — plot decimation is explicitly backlog, and the 100k-row performance budget does not cover his files.
- **[C08]** His project tree has ~100 subfolders; there is no recursive scan, so folder-to-folder navigation is constant.
- **[C26]** He eyeballs convergence by numbers first. Min/max/mean readouts are only a "nice to have" (P2) and may not ship.
- **[C22]** Single-window, single-instance design: he cannot put project A and project B side by side on two monitors.

### P10 — Ingrid Larsson · free-energy researcher · Linux · intermediate
Runs 48 lambda windows; each window produces `dhdl.xvg` (multi-dataset) plus RDF/hbond files.

- **[C17]** Overlaying even 10 windows exhausts the default color cycle; colors repeat and legends become unreadable. No per-series color picker.
- **[C29]** Needs all 48 window plots exported for her report — one dialog round-trip per file.
- **[C11]** `dhdl.xvg` files contain multiple `&`-separated datasets; only the first dataset is shown by default, and she cannot overlay dataset 2 of file A against file B.
- **[C27]** "Average replicas" refuses her selection with an "incompatible signature" tooltip (windows have different column layouts) and no explanation of what would make them compatible.
- **[C22]** Wants two windows side by side to compare system A vs system B. Single-instance design sends every launch to the one window.

### P11 — Jean-Pierre Dubois · 20-year xmgrace veteran · Linux · expert
Productive in xmgrace via keyboard and scripts; deeply skeptical of "modern replacements."

- **[C19]** Six menu shortcuts exist; the file table, docks, and export dialog are mouse-only. His keyboard-driven workflow has no equivalent.
- **[C10]** His curated `.xvg` files carry grace styling (`@ with g0` regions, `@ sN color`, in-file formulas). The app ignores all of it, so his files look "naked" and some multi-graph files lose their structure.
- **[C16]** No precise axis control: custom tick placement, minor-log ticks, exact range entry. Zoom-rectangle only.
- **[C24]** He routinely fit straight lines to regions in grace. No fitting here.
- **[C32]** matplotlib's EPS output trips over font embedding in his submission pipeline.

### P12 — Dr. Hannah Weber · teaching-lab instructor · Windows · intermediate
Builds course packs and worksheets from student example data.

- **[C33]** No print function; handouts require export → open in another viewer → print.
- **[C29]** Wants one action that exports all 12 example plots for the course pack. Must repeat the dialog 12 times.
- **[C40]** Wants to hand students a shared "course style" template (colors, grid, legend). Settings are private per machine; no template import/export.
- **[C18]** Worksheets want 6 small plots per page (grid). Not available.
- **[C01]** Her students hit the same SmartScreen warning she did; half of them called IT.

### P13 — Carlos Mendes · co-supervisor · macOS + iPad · novice
Reviews student figures; comments by email and screenshots.

- **[C15]** Wants to annotate (circle the plateau, write "re-run this") directly on the plot. No annotation support.
- **[C12]** A student sends an `.xpm` contact map; the app cannot open it, and he does not understand why "the plot app" refuses a file from the same simulation.
- **[C31]** Pastes copied images into email; they arrive visibly soft on recipients' high-DPI screens.

### P14 — Dr. Wei Zhang · ML-oriented researcher · Linux/Windows · expert
Uses MD output as training data; the app is a sanity-check tool on the way to Python.

- **[C30]** Needs the exact numbers he is looking at (smoothed, converted, averaged) exported as CSV for feature extraction. Images only — he re-parses the raw files instead.
- **[C25]** His files use frame index as X, not time. The ps→ns conversion silently mislabels the axis; there is no awareness that X may not be time, and no Y-axis unit conversion (nm→Å) either.
- **[C28]** Smoothing window is defined in *points*. Across files with different `dt`, the same window spans different physical times — misleading for comparison.
- **[C24]** Wants derivative/normalization as quick operations. Out of scope.

### P15 — Fatima Al-Sayed · MSc student, NVDA screen-reader user · Windows 11 · intermediate
Works independently; the app is either accessible or it is not usable for her.

- **[C34]** The matplotlib canvas is invisible to her screen reader: no textual summary, no way to query values except the mouse-following coordinate readout in the status bar.
- **[C19]** Keyboard navigation of the file table, series dock, and style dock is undocumented and incomplete; the six shortcuts are all there is.
- **[C20]** At 200 % Windows display scaling, the docks consume most of the window and the canvas is a sliver; no compact mode.

### P16 — Chen Wei · PhD student, Chinese-speaking · Windows · intermediate
Comfortable with GROMACS; data lives in a cloud-synced folder.

- **[C35]** UI is English-only; he second-guesses terms like "Average replicas" and "moving-average overlay" (localization is backlog).
- **[C36]** His file titles and his supervisor's required Chinese annotations in label overrides render as boxes in exported PNGs — the bundled matplotlib fonts lack CJK glyphs.
- **[C09]** His sync client keeps files as cloud placeholders; scanning the folder triggers a mass download, and files locked mid-sync show spurious warnings.

### P17 — Dr. Olga Petrova · simulation-center staff scientist · Linux · expert
Quality-checks ~40 students' runs weekly; lives in the file system.

- **[C08]** Wants to point at the root directory and see every student's analyses recursively. Must instead open 40 folders.
- **[C26]** For QA she wants instant min/max/mean and drift on the visible series; the stats readout is P2, not guaranteed.
- **[C29]** Weekly report needs the same dozen plots exported every week. No batch export.
- **[C23]** Students' 1M-point energy files make interactions noticeably heavier; no decimation.

### P18 — Robert Klein · computational chemist (non-GROMACS) · Windows · expert
His `.xvg` files come from other codes that write plain grace.

- **[C10]** Files using `@ with g0`, `@ target`, in-series styling and formulas lose all of that: unknown directives are ignored by design, so his files render differently from every other grace tool.
- **[C11]** Multi-graph grace files map awkwardly: only the first dataset is surfaced, with no cross-file dataset mixing.
- **[C06]** He has grace installed and working; the association offer and Windows' "open with" prompts fight his existing setup.

### P19 — Aisha Bello · PhD student · 1366×768 Windows 10 laptop · intermediate
The laptop is her only machine.

- **[C20]** File list + series dock + style dock leave the canvas a quarter of the screen; she collapses docks constantly and there is no compact mode.
- **[C03]** The portable exe (onefile) extracts itself on every launch from her spinning disk; cold start is 10–20 s and feels broken.
- **[C17]** With the canvas small, legend and curves overlap badly; distinguishing four similar colors on 768p is frustrating.

### P20 — Tomás Silva · postdoc · OneDrive-synced analysis folders · Windows 11 · intermediate
Moved his project into OneDrive "for backup."

- **[C09]** Scanning the synced folder hydrates cloud placeholders (a surprise multi-GB download) and files locked by the sync show warnings that look like corrupt data.
- **[C14]** After the move, his recents all point at dead pre-migration paths; there is no cleanup and no way to pin favorites.

### P21 — Emily Carter · experimentalist, never used MD · macOS · novice
Received `energy.xvg` from a collaborator; wants one number out of it.

- **[C01]** macOS refuses to open the unsigned app with a frightening "cannot be opened" dialog; she needs her collaborator to walk her through right-click → Open.
- **[C37]** Does not know RMSD from Rg; nothing in the app explains what she is looking at.
- **[C17]** Six series switch on by default in similar colors; she cannot tell which legend entry is "Total Energy."
- **[C13]** Tries to drag the attachment into the app; unsupported.

### P22 — Dr. Rajesh Kumar · replicas of different lengths · Linux · intermediate
Five replicas: 50, 100, 100, 200, 200 ns, sampled at different `nst`.

- **[C27]** Averaging aligns everything onto the *first* file's X grid by interpolation: his 50 ns replica silently truncates the 200 ns ones' contribution structure, and the ">5 % points" warning text does not explain the consequence or offer a reference/common-range choice.
- **[C28]** The smoothing window (points) means different physical times per replica, so "smoothed" curves are not comparable.
- **[C17]** Six member curves in near-identical default colors.
- **[C30]** For the paper he needs the mean ± SD table itself, not just the picture.

### P23 — Peter Novák · 2015 laptop, HDD · Windows 10 · intermediate
Everything is slow; patience is finite.

- **[C03]** Cold start on the HDD takes ~15 s (onefile extraction); he believes it hangs and force-quits it twice.
- **[C23]** Two 500k-point files overlaid + smoothing = multi-second redraws; no decimation.
- **[C01]** SmartScreen warning on install; he is not sure the app is "safe."

### P24 — Laura García · scientific illustrator · macOS · GUI expert
Prepares publication figures for the group; judges apps by typographic control.

- **[C16]** No figure-size/aspect control (85 mm single-column!), no font-family choice, no tick-format control. matplotlib defaults are not her journal's spec.
- **[C32]** EPS/SVG export has font-embedding and text-as-paths quirks; transparency behaves differently per format.
- **[C15]** Needs panel labels (a, b, c) and arrows. No annotation layer.
- **[C17]** Color palettes are fixed presets; she cannot load the journal's palette or assign per-series colors precisely.

### P25 — Dmitri Volkov · pharma scientist · locked-down Windows · intermediate
No admin rights; AppLocker and corporate AV decide what runs.

- **[C01]** The unsigned installer/portable exe is blocked outright by corporate policy. No signed build exists in v1, so he cannot use the app at all on his work machine.
- **[C07]** Even for an exception request, IT demands a publisher signature or published checksums — neither exists.
- **[C39]** When the app fails to launch in his environment, there is no log file and no error detail (`--noconsole` build); his IT ticket has no evidence to attach.

### P26 — Nomsa Dlamini · multi-project researcher · Windows 11 · intermediate
Three collaborations, three folder trees, constant context switching.

- **[C08]** No cross-folder search or recursive scan: finding "that one RDF" means opening each collaboration folder in turn.
- **[C22]** Wants project A and project B side by side in two windows. Single-instance design refuses a second window.
- **[C14]** The 10-entry recents fill instantly and hold stale paths after she reorganized; no favorites/pinning.

### P27 — Alex Turner · keyboard-only power user · Linux · expert
Runs Emacs-style; the mouse is the last resort.

- **[C19]** Beyond six shortcuts there is no keyboard path to the file table, docks, filter box, legend toggling, or export fields. No command palette.
- **[C22]** Opening a second folder from the file manager is forwarded to the single running window, hijacking his current selection.

### P28 — Dr. Mei Ling · biophysicist, unusual axes · macOS + Linux · expert
Compares simulations with X in steps, Å-based Y values, and unit-labeled energies.

- **[C25]** Conversions exist only for time on X (ps→ns/µs/ms). No Y-axis conversion (nm→Å, kJ/mol→kcal/mol), no generic scale/offset, and X is assumed to be column 0 / time.
- **[C36]** Å, ε, ±, and µ glyphs in labels occasionally export with wrong/fallback fonts depending on format.
- **[C30]** Wants the unit-converted series as data, not just as a relabeled axis.

### P29 — Jonas Berg · two-machine researcher · Windows 11 · intermediate
Desktop at the office, laptop at home; same project on both.

- **[C40]** Settings (recents, export defaults, dock layout) live in each machine's registry; no export/import or sync, so he reconfigures every switch.
- **[C14]** Recents from the office machine are dead paths on the laptop; no pruning, no favorites.

### P30 — Zara Ahmed · early adopter · Windows 11 · intermediate
The "friend" of PRD success criterion 2: installs first, recruits others.

- **[C39]** Hits a crash on a malformed file from a colleague. No log file, no error details, no feedback channel in the About dialog — she cannot report it meaningfully, so she just stops using that folder.
- **[C02]** No check-for-updates; she must manually watch for new releases and will miss fixes.
- **[C01]** Every colleague she recruits hits the SmartScreen warning; two gave up at that step.
