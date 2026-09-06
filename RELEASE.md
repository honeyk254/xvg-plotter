# Release & IT-deployment notes

Audience: whoever cuts a release, and IT departments deciding whether to allow
XVG Plotter on managed machines. Product docs live in [README.md](README.md) and
[SPEC.md](SPEC.md).

## What ships (v1.0.1)

| Artifact | Contents |
|---|---|
| `XVGPlotter.exe` | portable onefile build (no install, no admin) |
| `XVGPlotter-<ver>-win64.zip` | onedir build (`--onedir`), fastest cold start |
| `XVGPlotter-Setup-<ver>.exe` | per-user installer (Inno Setup, no admin) |
| `XVGPlotter-Setup-<ver>-machine.exe` | per-machine installer variant (`--machine`, admin) |
| `SHA256SUMS.txt` | SHA-256 of every file artifact above |

macOS ships `XVGPlotter.dmg`; Linux ships `XVGPlotter-x86_64-<ver>.AppImage`.
`packaging/build.py` generates the checksums file automatically at the end of
each build.

**Build hygiene**: builds must run inside a clean virtualenv (`python -m venv .venv`
+ `pip install -e .[dev]`). PyInstaller bundles the dependency graph of the
interpreter it runs under — a global site-packages leaks unrelated packages and
version drift into the artifact, and the freeze list becomes unreproducible.

## Integrity verification (no code signing)

Builds are **not code-signed**; the SHA-256 sums in `SHA256SUMS.txt` are the
integrity guarantee. Verify before running:

```text
Windows (PowerShell):  Get-FileHash .\XVGPlotter.exe -Algorithm SHA256
Windows (cmd):         certutil -hashfile XVGPlotter.exe SHA256
macOS / Linux:         shasum -a 256 <artifact>    # or sha256sum
```

Compare against `SHA256SUMS.txt` from the same release. If your distribution
channel re-hosts the files, publish the sums through a second channel.

## SmartScreen / Gatekeeper / antivirus

Because the binaries are unsigned:

- **Windows SmartScreen** shows "Windows protected your PC" on first run of a
  downloaded exe — *More info* → *Run anyway*. This is expected for unsigned
  publishers, not an indication of malware.
- **Antivirus heuristics** sometimes flag unsigned PyInstaller onefile exes.
  Verify the hash and allowlist by file hash (below).
- **macOS Gatekeeper** blocks the first launch — right-click → Open → Open.
  (Signing/notarization is backlog.)

## Managed deployment (Windows)

- **Silent install**: the Inno Setup installer supports the standard flags —
  `XVGPlotter-Setup-1.0.1.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART`
  (add `/TASKS="desktopicon assoc"` to opt into shortcuts/association; the
  `.xvg` association is off by default).
- **Per-machine install**: use the `-machine` installer variant (installs to
  Program Files, requires admin).
- **AppLocker/WDAC**: hash-allowlist the exe using the published SHA-256, or
  package the onedir build. A publisher-rule allowlist is not possible until
  the binaries are code-signed.
- **Update story**: the app performs no network traffic on its own; Help ▸
  *Check for updates* is strictly user-triggered and only queries the GitHub
  releases API. Pin a version by deploying the installer; nothing auto-updates.

## Network behavior

- No telemetry, no crash reporting service, no analytics.
- The only optional outbound request is the manual update check
  (`api.github.com/repos/honeyk254/xvg-plotter/releases/latest`).

## Logs & support

A rotating log (`xvg_plotter.log`, 1 MB × 3) lives in the per-user app-data
folder (Windows: `%APPDATA%\XVGPlotter\XVG Plotter\`). Unexpected errors show a
dialog with copyable details and are written to this log — request it when
triaging a ticket.

## Code signing (backlog)

The complete fix for the warning friction (problem C01) is signing:
an OV/EV certificate for Windows (`signtool` wired into `build.py` +
`setup.iss` SignTool directive) and Apple Developer ID + notarization for
macOS. The build scripts have placeholder-free manual flows today; signing
hooks were deliberately deferred until certificates are purchased.
