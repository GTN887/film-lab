#!/usr/bin/env python3
"""Desktop program: START_FILM_LAB, Install on Desktop, no PowerShell daily."""

from __future__ import annotations

import ast
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.desktop import (
    COMPAT_START,
    DAILY_LAUNCHER,
    ICON_ICO,
    ICON_PNG,
    INNO_ISS,
    INSTALLER,
    LOCAL_URL,
    PACKAGING_DOC,
    REPAIR_LAUNCHER,
    SHORTCUT_VBS,
    UNINSTALL_DOC,
    UNINSTALLER,
    ZIP_INSTALL_LNK,
    build_windows_zip,
    daily_launcher_uses_powershell,
    iter_package_files,
)
from film_lab.winlnk import looks_like_lnk, write_install_shortcut
from film_lab.hub import FORBIDDEN_BRANDS, HUB_CARDS
from film_lab.offline import WORKS_OFFLINE
from film_lab.writing import WRITING_MODES


class DesktopProgramTests(unittest.TestCase):
    def test_daily_start_is_cmd_not_powershell(self) -> None:
        start = (ROOT / DAILY_LAUNCHER).read_text(encoding="utf-8", errors="ignore")
        compat = (ROOT / COMPAT_START).read_text(encoding="utf-8", errors="ignore")
        repair = (ROOT / REPAIR_LAUNCHER).read_text(encoding="utf-8", errors="ignore")
        run_lab = (ROOT / "scripts" / "run_film_lab.bat").read_text(encoding="utf-8", errors="ignore")
        self.assertFalse(daily_launcher_uses_powershell(start), start[:200])
        self.assertFalse(daily_launcher_uses_powershell(compat))
        self.assertFalse(daily_launcher_uses_powershell(repair))
        self.assertFalse(daily_launcher_uses_powershell(run_lab))
        self.assertIn("43123", start)
        self.assertIn("127.0.0.1", start)
        self.assertIn(DAILY_LAUNCHER, compat)
        self.assertIn("run_film_lab.bat", start)
        self.assertIn("run_comfyui_amd.bat", start)

    def test_installer_pins_icon(self) -> None:
        install = (ROOT / INSTALLER).read_text(encoding="utf-8", errors="ignore")
        uninstall = (ROOT / UNINSTALLER).read_text(encoding="utf-8", errors="ignore")
        vbs = (ROOT / SHORTCUT_VBS).read_text(encoding="utf-8", errors="ignore")
        remove = (ROOT / "scripts" / "remove_desktop_shortcut.vbs").read_text(
            encoding="utf-8", errors="ignore"
        )
        self.assertIn("Install Film Lab", install)
        self.assertIn("Desktop\\Film Lab", install)
        self.assertIn("make_desktop_shortcut.vbs", install)
        self.assertIn("film_lab.ico", install)
        self.assertIn("patch in place", install.lower())
        self.assertFalse(daily_launcher_uses_powershell(install))
        self.assertFalse(daily_launcher_uses_powershell(uninstall))
        self.assertIn("remove_desktop_shortcut.vbs", uninstall)
        self.assertIn("DELETE", uninstall)
        self.assertIn("START_FILM_LAB.bat", vbs)
        self.assertIn("film_lab.ico", vbs)
        self.assertIn("Film Lab.lnk", vbs)
        self.assertIn("WScript.Shell", vbs)
        self.assertIn("install.json", vbs)
        self.assertIn("Uninstall Film Lab.lnk", vbs)
        self.assertIn("Film Lab.lnk", remove)
        self.assertTrue((ROOT / ICON_ICO).is_file())
        self.assertTrue((ROOT / ICON_PNG).is_file())
        self.assertGreater((ROOT / ICON_ICO).stat().st_size, 400)
        self.assertGreater((ROOT / ICON_PNG).stat().st_size, 400)
        notes = (ROOT / UNINSTALL_DOC).read_text(encoding="utf-8")
        self.assertIn("UNINSTALL_FILM_LAB.bat", notes)
        self.assertIn("patch in place", notes.lower())
        self.assertIn("Grok Bot", notes)

    def test_packaging_zip_and_inno(self) -> None:
        self.assertTrue((ROOT / PACKAGING_DOC).is_file())
        self.assertTrue((ROOT / INNO_ISS).is_file())
        iss = (ROOT / INNO_ISS).read_text(encoding="utf-8")
        self.assertIn(DAILY_LAUNCHER, iss)
        self.assertIn("film_lab.ico", iss)
        doc = (ROOT / PACKAGING_DOC).read_text(encoding="utf-8")
        self.assertIn("INSTALL_FILM_LAB.bat", doc)
        self.assertIn("START_FILM_LAB.bat", doc)
        names = {p.relative_to(ROOT).as_posix() for p in iter_package_files(ROOT)}
        self.assertIn(DAILY_LAUNCHER, names)
        self.assertIn(INSTALLER, names)
        self.assertIn(ICON_ICO, names)
        self.assertNotIn("data/projects", names)
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "film_lab_windows.zip"
            build_windows_zip(ROOT, dest)
            self.assertTrue(dest.is_file())
            with zipfile.ZipFile(dest) as zf:
                inner = set(zf.namelist())
                css = zf.read("film_lab/studio.css").decode("utf-8")
                zf.extract(ZIP_INSTALL_LNK, path=tmp)
            self.assertIn(DAILY_LAUNCHER, inner)
            self.assertIn(INSTALLER, inner)
            self.assertIn(UNINSTALLER, inner)
            self.assertIn(ICON_ICO, inner)
            self.assertIn(ZIP_INSTALL_LNK, inner)
            self.assertIn("PREFINISH.md", inner)
            self.assertIn("CLICK_ME_FIRST.txt", inner)
            self.assertIn("film_lab/studio.css", inner)
            self.assertIn("film_lab/pipeline.py", inner)
            self.assertIn("film_lab/constants.py", inner)
            self.assertTrue(any(n.startswith("film_lab/") for n in inner))
            self.assertFalse(any(".venv" in n for n in inner))
            self.assertIn("--fl-cyan", css)
            self.assertIn("--fl-purple", css)
            self.assertNotIn("#e4c37a", css)
            extracted = Path(tmp) / ZIP_INSTALL_LNK
            self.assertTrue(looks_like_lnk(extracted))
            raw = extracted.read_bytes()
            self.assertIn("INSTALL_FILM_LAB.bat".encode("utf-16le"), raw)
            self.assertIn("film_lab.ico".encode("utf-16le"), raw)

    def test_zip_install_lnk_writer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "Install Film Lab.lnk"
            write_install_shortcut(dest)
            self.assertTrue(looks_like_lnk(dest))
            self.assertGreater(dest.stat().st_size, 80)

    def test_app_copy_hub_lock(self) -> None:
        src = (ROOT / "app.py").read_text(encoding="utf-8")
        ast.parse(src)
        self.assertIn("START_FILM_LAB.bat", src)
        self.assertIn("Install Film Lab", src)
        self.assertIn("INSTALL_FILM_LAB.bat", src)
        self.assertIn("UNINSTALL_FILM_LAB.bat", src)
        self.assertIn("patch in place", src)
        self.assertEqual(len(HUB_CARDS), 15)
        self.assertEqual(len(WRITING_MODES), 5)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        here = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
        self.assertIn(WORKS_OFFLINE, readme)
        self.assertIn(WORKS_OFFLINE, here)
        self.assertIn(DAILY_LAUNCHER, readme)
        self.assertIn(LOCAL_URL, here)
        blob = "\n".join(
            [
                src,
                (ROOT / "film_lab" / "desktop.py").read_text(encoding="utf-8"),
                (ROOT / DAILY_LAUNCHER).read_text(encoding="utf-8", errors="ignore"),
                (ROOT / INSTALLER).read_text(encoding="utf-8", errors="ignore"),
                (ROOT / PACKAGING_DOC).read_text(encoding="utf-8"),
                (ROOT / "film_lab" / "winlnk.py").read_text(encoding="utf-8"),
                (ROOT / UNINSTALLER).read_text(encoding="utf-8", errors="ignore"),
            ]
        ).lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, blob, banned)
        self.assertNotIn("subscription", (ROOT / "film_lab" / "desktop.py").read_text(encoding="utf-8").lower())


if __name__ == "__main__":
    unittest.main()
