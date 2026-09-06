"""Build XVG Plotter distributables (SPEC §12).

Run on the TARGET OS (PyInstaller cannot cross-compile):
    python packaging/build.py               # builds for the current OS
    python packaging/build.py --no-dmg      # macOS: skip DMG step
    python packaging/build.py --no-install  # Windows: skip Inno Setup step
    python packaging/build.py --onedir      # Windows: installer wraps a onedir build
                                            # (fast cold start, SPEC §12 guardrail)
    python packaging/build.py --machine     # Windows: per-machine installer variant

Every file artifact produced is listed in dist/SHA256SUMS.txt (C07).

Artifacts:
    Windows -> dist/XVGPlotter.exe or dist/XVGPlotter-<ver>-win64.zip
               (+ installer(s) via Inno Setup)
    macOS   -> dist/XVG Plotter.app (+ XVGPlotter.dmg)
    Linux   -> dist/XVGPlotter-x86_64-<ver>.AppImage
"""
from __future__ import annotations

import argparse
import hashlib
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "src" / "xvg_plotter"
ASSETS = PKG / "assets"
APP_NAME = "XVG Plotter"


def _version() -> str:
    """Single source of truth: src/xvg_plotter/version.py."""
    ns: dict = {}
    exec((PKG / "version.py").read_text(encoding="utf-8"), ns)
    return ns["APP_VERSION"]


VERSION = _version()


def _run(cmd: list[str]) -> None:
    print("+", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True, cwd=ROOT)


def _checksums(artifacts: list[Path], out_dir: Path | None = None) -> None:
    """Write SHA256SUMS.txt covering every file artifact (C07).

    Merges with an existing sums file so sequential build runs accumulate
    their artifacts instead of clobbering each other."""
    out = (out_dir or ROOT / "dist") / "SHA256SUMS.txt"
    lines: list[str] = []
    if out.exists():
        existing = out.read_text(encoding="utf-8").splitlines()
    else:
        existing = []
    new_names = {p.name for p in artifacts if p.is_file()}
    lines += [ln for ln in existing
              if ln.strip() and ln.split("  ", 1)[-1] not in new_names]
    for p in artifacts:
        if not p.is_file():
            continue
        h = hashlib.sha256()
        with open(p, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        lines.append(f"{h.hexdigest()}  {p.name}")
    if lines:
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"checksums: {out}")


def _pyinstaller(target: str, onedir: bool = False) -> Path:
    import platform as _p
    sep = ";" if _p.system() == "Windows" else ":"
    icon = {"windows": ASSETS / "icon.ico", "darwin": ASSETS / "icon.icns"}.get(target, ASSETS / "icon.png")
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
           "--name", APP_NAME if target == "darwin" else "XVGPlotter",
           "--icon", icon,
           "--paths", ROOT / "src",
           "--add-data", f"{ASSETS}{sep}xvg_plotter/assets",
           "--collect-submodules", "xvg_plotter"]
    if target == "windows":
        cmd += ["--noconsole", "--onedir" if onedir else "--onefile"]
    elif target == "darwin":
        cmd += ["--windowed", "--osx-bundle-identifier", "org.xvgplotter.xvgplotter"]
    else:
        cmd += ["--noconsole", "--onedir"]
    cmd.append(ROOT / "packaging" / "entry.py")
    _run(cmd)
    if target == "darwin":
        return ROOT / "dist" / "XVG Plotter.app"
    if target == "windows" and not onedir:
        return ROOT / "dist" / "XVGPlotter.exe"  # onefile: the exe itself
    return ROOT / "dist" / "XVGPlotter"


def _windows(exe: Path, do_install: bool, onedir: bool = False,
             machine: bool = False) -> None:
    artifacts: list[Path] = []
    if onedir:
        d = ROOT / "dist" / "XVGPlotter"
        zip_path = ROOT / "dist" / f"XVGPlotter-{VERSION}-win64.zip"
        print(f"packing {zip_path}")
        shutil.make_archive(str(zip_path.with_suffix("")), "zip", d)
        artifacts.append(zip_path)
        print(f"built {d}")
    else:
        artifacts.append(exe)
        print(f"built {exe}")
    if not do_install:
        _checksums(artifacts)
        return
    iscc = None
    for cand in (Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
                 Path(r"C:\Program Files\Inno Setup 6\ISCC.exe")):
        if cand.exists():
            iscc = cand
            break
    if iscc is None:
        print("Inno Setup 6 not found; skipping installer (portable build is ready).")
        _checksums(artifacts)
        return
    cmd = [iscc, f"/DAPP_VERSION={VERSION}"]
    if onedir:
        cmd.append("/DONEDIR")
    if machine:
        cmd.append("/DMACHINE")
    cmd.append(ROOT / "packaging" / "windows" / "setup.iss")
    _run(cmd)
    base = f"XVGPlotter-Setup-{VERSION}" + ("-machine" if machine else "")
    installer = ROOT / "packaging/windows/Output" / f"{base}.exe"
    artifacts.append(installer)
    print(f"installer: {installer}")
    _checksums(artifacts)


def _macos(app: Path, do_dmg: bool) -> None:
    plist_path = app / "Contents" / "Info.plist"
    with open(plist_path, "rb") as fh:
        info = plistlib.load(fh)
    info["CFBundleDocumentTypes"] = [{
        "CFBundleTypeName": "GROMACS XVG plot",
        "CFBundleTypeRole": "Viewer",
        "LSItemContentTypes": ["org.xvgplotter.xvg"],
        "CFBundleTypeExtensions": ["xvg"],
    }]
    info["UTImportedTypeDeclarations"] = [{
        "UTTypeIdentifier": "org.xvgplotter.xvg",
        "UTTypeDescription": "GROMACS XVG plot",
        "UTTypeConformsTo": ["public.data"],
        "UTTypeTagSpecification": {"public.filename-extension": ["xvg"]},
    }]
    with open(plist_path, "wb") as fh:
        plistlib.dump(info, fh)
    print(f"built {app} with .xvg document types")
    if not do_dmg:
        return
    dmg = ROOT / "dist" / "XVGPlotter.dmg"
    _run(["hdiutil", "create", "-volname", "XVGPlotter", "-srcfolder", app,
          "-ov", dmg])
    print(f"dmg: {dmg}")
    _checksums([dmg])


def _linux(_exe: Path) -> None:
    appdir = ROOT / "dist" / "AppDir"
    inner = appdir / "usr" / "bin"
    inner.mkdir(parents=True, exist_ok=True)
    _run(["cp", "-r", ROOT / "dist" / "XVGPlotter" / ".", inner])
    (appdir / "xvgplotter.desktop").write_text(
        (ROOT / "packaging" / "linux" / "xvgplotter.desktop").read_text()
        .replace("Exec=XVGPlotter", f"Exec={inner / 'XVGPlotter'}"))
    icon_dir = appdir / "usr" / "share" / "icons" / "hicolor" / "512x512" / "apps"
    icon_dir.mkdir(parents=True, exist_ok=True)
    (icon_dir / "xvgplotter.png").write_bytes((ASSETS / "icon.png").read_bytes())
    (appdir / "AppRun").symlink_to(inner / "XVGPlotter")
    tool = ROOT / "dist" / "appimagetool.AppImage"
    if not tool.exists():
        _run(["curl", "-L", "-o", tool,
              "https://github.com/AppImage/appimagetool/releases/latest/download/appimagetool-x86_64.AppImage"])
    _run(["chmod", "+x", tool])
    out = ROOT / "dist" / f"XVGPlotter-x86_64-{VERSION}.AppImage"
    cmd = [tool]
    if not Path("/dev/fuse").exists():  # WSL2/containers: run via bundled runtime
        cmd.append("--appimage-extract-and-run")
    _run(cmd + [appdir, out])
    print(f"appimage: {out}")
    _checksums([out])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-dmg", action="store_true")
    ap.add_argument("--no-install", action="store_true")
    ap.add_argument("--onedir", action="store_true",
                    help="Windows: installer wraps a onedir build (fast cold start)")
    ap.add_argument("--machine", action="store_true",
                    help="Windows: per-machine installer variant (admin install)")
    args = ap.parse_args()

    import platform
    system = {"Windows": "windows", "Darwin": "darwin"}.get(platform.system(), "linux")
    onedir = args.onedir or system != "windows"  # Linux is already onedir
    exe = _pyinstaller(system, onedir)
    if system == "windows":
        _windows(exe, not args.no_install, args.onedir, args.machine)
    elif system == "darwin":
        _macos(exe, not args.no_dmg)
    else:
        _linux(exe)


if __name__ == "__main__":
    main()
