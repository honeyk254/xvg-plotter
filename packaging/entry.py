"""PyInstaller entry point (import-path wiring lives in build.py --paths)."""
import sys
import time

_T0 = time.perf_counter()

from xvg_plotter.app import main

if __name__ == "__main__":
    import xvg_plotter.app as _app

    _app.START_T0 = _T0  # cold-start timing -> app log (C03)
    sys.exit(main())
