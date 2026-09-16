#!/usr/bin/env python3
"""Local Save Library + optional Drive folder backup."""

from __future__ import annotations

import ast
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.hub import FORBIDDEN_BRANDS, HUB_CARDS
from film_lab.project import Project
from film_lab.savelib import (
    SHELVES,
    backup_project,
    connect_folder,
    folder_status,
    library_help,
    list_shelf,
    load_sync_config,
)
from film_lab.writing import WRITING_MODES


class SaveLibraryTests(unittest.TestCase):
    def test_local_browse_and_optional_backup(self) -> None:
        self.assertEqual(SHELVES, ("Stills", "Takes", "Sets", "Writing", "Exports"))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "projects"
            project = Project.create("lot", data_root=root)
            still = project.stills_dir / "lamp.png"
            Image.new("RGB", (32, 32), (20, 20, 20)).save(still)
            (project.writing_dir / "scene.txt").write_text("INT. BEDROOM", encoding="utf-8")
            (project.takes_dir / "take1.txt").write_text("take", encoding="utf-8")
            (project.sets_dir / "room" / "note.txt").parent.mkdir(parents=True, exist_ok=True)
            (project.sets_dir / "room" / "note.txt").write_text("locked", encoding="utf-8")
            stills = list_shelf(project, "Stills")
            self.assertEqual(len(stills), 1)
            self.assertEqual(stills[0].name, "lamp.png")
            self.assertTrue(list_shelf(project, "Writing"))
            self.assertTrue(list_shelf(project, "Takes"))
            self.assertTrue(list_shelf(project, "Sets"))
            self.assertEqual(list_shelf(project, "Exports"), [])

            missing = backup_project(
                project, onedrive=str(Path(tmp) / "no-drive"), data_root=root
            )
            self.assertIn("missing", missing.lower())
            self.assertTrue(still.is_file())

            dest = Path(tmp) / "OneDrive"
            dest.mkdir()
            saved, note = connect_folder("onedrive", str(dest), data_root=root)
            self.assertEqual(folder_status(saved), "ready")
            self.assertIn("ready", note.lower())
            report = backup_project(project, onedrive=str(dest), data_root=root)
            self.assertIn("copied", report.lower())
            self.assertTrue((dest / "Film Lab" / "lot" / "stills" / "lamp.png").is_file())
            self.assertTrue((dest / "Film Lab" / "lot" / "writing" / "scene.txt").is_file())
            cfg = load_sync_config(root)
            self.assertTrue(cfg.last_backup)
            empty, off = connect_folder("gdrive", "", data_root=root)
            self.assertEqual(empty, "")
            self.assertIn("disconnected", off.lower())

    def test_no_sixteenth_card_and_app_copy(self) -> None:
        self.assertEqual(len(HUB_CARDS), 15)
        self.assertEqual(len(WRITING_MODES), 5)
        help_md = library_help().lower()
        self.assertIn("local", help_md)
        self.assertIn("onedrive", help_md)
        self.assertIn("google drive", help_md)
        self.assertIn("optional", help_md)
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, help_md, banned)
        src = (ROOT / "app.py").read_text(encoding="utf-8")
        ast.parse(src)
        self.assertIn('with gr.Tab("Save Library", id="library"', src)
        self.assertIn('library_btn = gr.Button("Library"', src)
        self.assertIn("OneDrive", src)
        self.assertIn("Google Drive", src)
        self.assertIn("local-first", src.lower())
        self.assertIn("Browse this PC", src)
        self.assertNotIn("file_count", src[src.find("Save Library") : src.find("Still Desk")])
        low = src.lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, low, banned)


if __name__ == "__main__":
    unittest.main()
