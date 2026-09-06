"""Build XVG Plotter distributables (SPEC §12).

Run on the TARGET OS (PyInstaller cannot cross-compile):
    python packaging/build.py            # builds for the current OS
    python packaging/build.py --no-dmg   # macOS: skip DMG step
    python packaging/build.py --no-install  # Windows: skip Inno Setup step

Artifacts:
    Windows -> dist/XVGPlotter.exe (+ installer via Inno Setup)
    macOS   -> dist/XVG Plotter.app (+ XVGPlotter.dmg)
    Linux   -> dist/XVGPlotter-x86_64.AppImage
"""
from __future__ import annotations

import argparse
import plistlib
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


def _pyinstaller(target: str) -> Path:
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
        cmd += ["--noconsole", "--onefile"]
    elif target == "darwin":
        cmd += ["--windowed", "--osx-bundle-identifier", "org.xvgplotter.xvgplotter"]
    else:
        cmd += ["--noconsole", "--onedir"]
    cmd.append(ROOT / "packaging" / "entry.py")
    _run(cmd)
    return ROOT / "dist" / ("XVG Plotter.app" if target == "darwin" else "XVGPlotter")


def _windows(exe: Path, do_install: bool) -> None:
    print(f"built {exe}")
    if not do_install:
        return
    iscc = None
    for cand in (Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
                 Path(r"C:\Program Files\Inno Setup 6\ISCC.exe")):
        if cand.exists():
            iscc = cand
            break
    if iscc is None:
        print("Inno Setup 6 not found; skipping installer (portable exe is ready).")
        return
    _run([iscc, ROOT / "packaging" / "windows" / "setup.iss"])
    print(f"installer: {ROOT / 'packaging/windows/Output/XVGPlotter-Setup.exe'}")


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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-dmg", action="store_true")
    ap.add_argument("--no-install", action="store_true")
    args = ap.parse_args()

    import platform
    system = {"Windows": "windows", "Darwin": "darwin"}.get(platform.system(), "linux")
    exe = _pyinstaller(system)
    if system == "windows":
        _windows(exe, not args.no_install)
    elif system == "darwin":
        _macos(exe, not args.no_dmg)
    else:
        _linux(exe)


if __name__ == "__main__":
    main()
