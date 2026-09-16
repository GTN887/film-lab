#!/usr/bin/env python3
"""Offline-first desktop: banner, safe mode, START / Repair assets."""

from __future__ import annotations

import ast
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.hub import FORBIDDEN_BRANDS, hub_chrome_html
from film_lab.offline import (
    CORE_DESKS,
    ONLINE_OPTIONAL,
    WORKS_OFFLINE,
    boot_quality,
    offline_banner_html,
    offline_forced,
    repair_markdown,
    safe_mode,
    set_safe_mode,
)
from film_lab.providers import resolve_text_pick, resolve_voice_provider
from film_lab.quality import QUALITY_480


def _no_brands(blob: str) -> None:
    low = blob.lower()
    for banned in FORBIDDEN_BRANDS:
        if banned in low:
            raise AssertionError(banned)


class OfflineDesktopTests(unittest.TestCase):
    def test_banner_and_chrome(self) -> None:
        chrome = hub_chrome_html().lower()
        self.assertIn("local only", chrome)
        self.assertIn("offline", chrome)
        self.assertIn("online optional", chrome)
        banner = offline_banner_html().lower()
        self.assertIn("offline", banner)
        self.assertIn("online optional", banner)
        for desk in CORE_DESKS:
            self.assertIn(desk.lower().split()[0], banner)
        for name in ONLINE_OPTIONAL:
            self.assertIn(name.lower(), banner)
        self.assertIn("works offline for local generation", banner)
        _no_brands(chrome + banner + repair_markdown())

    def test_force_offline_skips_cloud_text(self) -> None:
        os.environ["FILM_LAB_OFFLINE"] = "1"
        try:
            self.assertTrue(offline_forced())
            route = resolve_text_pick("Grok", None)
            self.assertTrue(route.wired)
            self.assertIn("offline", route.message.lower())
            voice = resolve_voice_provider("ElevenLabs")
            self.assertTrue(voice.local)
            self.assertIn("offline", voice.message.lower())
        finally:
            os.environ.pop("FILM_LAB_OFFLINE", None)
        self.assertFalse(offline_forced())

    def test_safe_mode_quality(self) -> None:
        flag = ROOT / "data" / "safe_mode.flag"
        existed = flag.is_file()
        try:
            set_safe_mode(True)
            self.assertTrue(safe_mode())
            self.assertEqual(boot_quality(), QUALITY_480)
            set_safe_mode(False)
            self.assertFalse(safe_mode())
        finally:
            if existed:
                set_safe_mode(True)
            elif flag.is_file():
                flag.unlink()
            os.environ.pop("FILM_LAB_SAFE_MODE", None)

    def test_launcher_assets_exist(self) -> None:
        for rel in (
            "START.bat",
            "START_FILM_LAB.bat",
            "INSTALL_FILM_LAB.bat",
            "UNINSTALL_FILM_LAB.bat",
            "REPAIR.bat",
            "scripts/remove_desktop_shortcut.vbs",
            "docs/UNINSTALL.md",
            "assets/film_lab.ico",
            "assets/film_lab.png",
            "scripts/start_desktop.ps1",
            "scripts/run_film_lab.bat",
            "scripts/make_desktop_shortcut.vbs",
            "scripts/repair.ps1",
            "scripts/_common.ps1",
            "scripts/install_desktop_shortcut.ps1",
            "docs/DESKTOP.md",
            "docs/PACKAGING.md",
        ):
            path = ROOT / rel
            self.assertTrue(path.is_file(), rel)
            if path.suffix.lower() in {".bat", ".ps1", ".md"}:
                text = path.read_text(encoding="utf-8", errors="ignore").lower()
                self.assertTrue(
                    "offline" in text or "film lab" in text,
                    rel,
                )
        start = (ROOT / "scripts" / "start_desktop.ps1").read_text(encoding="utf-8")
        common = (ROOT / "scripts" / "_common.ps1").read_text(encoding="utf-8")
        self.assertIn("FILM_LAB_COMFY_CUDA_DEVICE", start)
        self.assertIn("43123", common)
        self.assertIn("8188", common)
        self.assertIn("restart-comfy", (ROOT / "scripts" / "repair.ps1").read_text(encoding="utf-8"))
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        self.assertIn(WORKS_OFFLINE, readme)
        self.assertIn(WORKS_OFFLINE, here)
        src = (ROOT / "app.py").read_text(encoding="utf-8")
        ast.parse(src)
        self.assertIn("Works offline for local generation", src)
        self.assertIn("Safe mode", src)
        self.assertIn("REPAIR.bat", src)
        _no_brands(src.lower())


if __name__ == "__main__":
    unittest.main()
