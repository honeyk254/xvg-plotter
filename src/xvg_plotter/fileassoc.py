"""Per-user .xvg file association (C06) — Windows only, no admin needed.

Mirrors the installer's optional association (packaging/windows/setup.iss) at
runtime: registers the ProgId under HKCU and adds it to .xvg's
OpenWithProgids, so XVG Plotter appears as a choice for .xvg files.
Idempotent; never touches another app's registration.
"""
from __future__ import annotations

PROGID = "XVGPlotter.xvg"


def register_xvg_association(exe_path: str) -> None:
    import winreg

    def _set(key_path: str, name: str | None, value: str) -> None:
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path, 0,
                                winreg.KEY_WRITE) as k:
            winreg.SetValueEx(k, name, 0, winreg.REG_SZ, value)

    _set(rf"Software\Classes\{PROGID}", None, "GROMACS XVG plot")
    _set(rf"Software\Classes\{PROGID}\DefaultIcon", None, f"{exe_path},0")
    _set(rf"Software\Classes\{PROGID}\shell\open\command", None,
         f'"{exe_path}" "%1"')
    _set(r"Software\Classes\.xvg\OpenWithProgids", PROGID, "")
