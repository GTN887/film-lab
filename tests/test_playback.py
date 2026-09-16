#!/usr/bin/env python3
"""Playback vs Direct: pause never edits; Mark & Direct is the only Fix path."""

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

from film_lab.hub import FORBIDDEN_BRANDS
from film_lab.playback import (
    DIRECT_BANNER,
    ENTER_LABEL,
    EXIT_LABEL,
    FIX_HELPER,
    MODE_DIRECT,
    MODE_PLAYBACK,
    PLAYBACK_HELP,
    banner_html,
    chrome,
    clip_path,
    enter_direct,
    exit_direct,
    freeze_at,
    help_text,
    mark_tools_visible,
    normalize_mode,
    pick_gallery_item,
    play_fix_legend_html,
    playback_copy,
)
from film_lab.project import Project


class PlaybackDirectTests(unittest.TestCase):
    def test_modes_and_banner(self) -> None:
        self.assertEqual(normalize_mode(""), MODE_PLAYBACK)
        self.assertEqual(normalize_mode("fix"), MODE_DIRECT)
        self.assertEqual(enter_direct(), MODE_DIRECT)
        self.assertEqual(exit_direct(), MODE_PLAYBACK)
        self.assertFalse(mark_tools_visible(MODE_PLAYBACK))
        self.assertTrue(mark_tools_visible(MODE_DIRECT))
        self.assertEqual(banner_html(MODE_PLAYBACK), "")
        self.assertIn(DIRECT_BANNER, banner_html(MODE_DIRECT))
        self.assertIn("does not edit", PLAYBACK_HELP)
        self.assertIn("new take", help_text(MODE_DIRECT))
        look = chrome(MODE_PLAYBACK)
        self.assertTrue(look["enter"])
        self.assertFalse(look["exit"])
        self.assertFalse(look["panel"])
        directing = chrome("directing")
        self.assertTrue(directing["panel"])
        self.assertTrue(directing["exit"])
        self.assertFalse(directing["enter"])
        self.assertEqual(directing["mode"], MODE_DIRECT)

    def test_legend_and_labels(self) -> None:
        legend = play_fix_legend_html()
        self.assertIn("Play", legend)
        self.assertIn("Fix", legend)
        self.assertIn(ENTER_LABEL, legend)
        self.assertIn(FIX_HELPER, legend)
        self.assertIn(DIRECT_BANNER, legend)
        copy = playback_copy()
        self.assertIn(EXIT_LABEL, copy)
        self.assertIn("pause never edits", copy.lower())

    def test_pick_and_clip_path(self) -> None:
        items = [("a.mp4", "Take 1"), ("b.mp4", "Take 2")]
        self.assertEqual(pick_gallery_item(items, 1), ("b.mp4", "Take 2"))
        self.assertEqual(pick_gallery_item(items, 99), ("b.mp4", "Take 2"))
        self.assertIsNone(pick_gallery_item([], 0))
        self.assertEqual(clip_path(None), "")
        self.assertEqual(clip_path({"path": "/no/such.mp4"}), "")
        with tempfile.TemporaryDirectory() as tmp:
            clip = Path(tmp) / "take.mp4"
            clip.write_bytes(b"not a real video")
            self.assertEqual(clip_path({"path": str(clip)}), str(clip))

    def test_freeze_still_does_not_need_pause(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("play", data_root=Path(tmp) / "projects")
            src = Path(tmp) / "lead.png"
            Image.new("RGB", (64, 48), (20, 24, 28)).save(src)
            dest = freeze_at(project, str(src), 0)
            self.assertTrue(Path(dest).is_file())
            with self.assertRaises(FileNotFoundError):
                freeze_at(project, None, 0)

    def test_app_wires_play_not_revise_on_take_board(self) -> None:
        src = (ROOT / "app.py").read_text(encoding="utf-8")
        ast.parse(src)
        self.assertIn("play_take_ui", src)
        self.assertIn("enter_direct_ui", src)
        self.assertIn("exit_direct_ui", src)
        self.assertIn(FIX_HELPER, src)
        self.assertIn(DIRECT_BANNER, src)
        self.assertIn(ENTER_LABEL, src)
        idx = src.find("take_clips.select")
        self.assertGreater(idx, 0)
        chunk = src[idx : idx + 500]
        self.assertIn("play_take_ui", chunk)
        self.assertNotIn("open_take_loop_ui", chunk)
        self.assertIn("click to play", src.lower())
        docs = (ROOT / "docs" / "PLAYBACK.md").read_text(encoding="utf-8")
        self.assertIn(FIX_HELPER, docs)
        self.assertIn(DIRECT_BANNER, docs)
        low = (src + docs + playback_copy() + play_fix_legend_html()).lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, low, banned)


if __name__ == "__main__":
    unittest.main()
