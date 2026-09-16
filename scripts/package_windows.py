#!/usr/bin/env python3
"""Build film_lab_windows.zip for Liam's desktop install.

Not a daily launcher. Run from the repo root:
  python scripts/package_windows.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.desktop import DAILY_LAUNCHER, INSTALLER, build_windows_zip


def main() -> int:
    parser = argparse.ArgumentParser(description="Zip Film Lab for Windows desktop install.")
    parser.add_argument(
        "-o",
        "--out",
        default=str(ROOT / "dist" / "film_lab_windows.zip"),
        help="Output zip path",
    )
    args = parser.parse_args()
    dest = build_windows_zip(ROOT, Path(args.out))
    print(f"Wrote {dest} ({dest.stat().st_size} bytes)")
    print(f"On Windows: unzip, then double-click {INSTALLER}")
    print(f"Daily: {DAILY_LAUNCHER} or the Film Lab desktop icon. No PowerShell.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
