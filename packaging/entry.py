"""PyInstaller entry point (import-path wiring lives in build.py --paths)."""
import sys

from xvg_plotter.app import main

if __name__ == "__main__":
    sys.exit(main())
