#!/usr/bin/env python3
"""Aspect picker: full ratio list, persist on shot, Regenerate keeps unless changed."""

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

from film_lab.constants import (
    ASPECT_RATIOS,
    DEFAULT_ASPECT,
    FRAME_LANDSCAPE,
    FRAME_SQUARE,
    FRAME_TALL,
    FRAME_ULTRAWIDE,
    aspect_choice_label,
    aspect_dropdown_choices,
    aspect_frame_kind,
    normalize_aspect,
)
from film_lab.hub import FORBIDDEN_BRANDS
from film_lab.project import Project
from film_lab.quality import desk_size, internal_size, resize_still
from film_lab.shot_card import ShotCard
from film_lab.variations import fork_take
from film_lab.generators.comfyui_i2v import i2v_size


class AspectLockTests(unittest.TestCase):
    def test_seven_ratios_and_aliases(self) -> None:
        self.assertEqual(
            ASPECT_RATIOS,
            (
                "16:9",
                "9:16",
                "1:1",
                "4:5",
                "3:2",
                "2:3",
                "4:3",
                "3:4",
                "21:9",
                "2.39:1 cinema scope",
                "1.85:1",
            ),
        )
        self.assertEqual(DEFAULT_ASPECT, "16:9")
        self.assertEqual(normalize_aspect("vertical"), "9:16")
        self.assertEqual(normalize_aspect("ultrawide"), "21:9")
        self.assertEqual(normalize_aspect("4/5"), "4:5")
        self.assertEqual(normalize_aspect("nope"), "16:9")
        self.assertEqual(aspect_frame_kind("1:1"), "square")
        for tall in ("9:16", "4:5", "2:3", "3:4"):
            self.assertEqual(aspect_frame_kind(tall), "tall", tall)
        for wide in ("16:9", "3:2", "4:3", "1.85:1"):
            self.assertEqual(aspect_frame_kind(wide), "landscape", wide)
        for ultra in ("21:9", "2.39:1 cinema scope"):
            self.assertEqual(aspect_frame_kind(ultra), "ultrawide", ultra)
        pairs = aspect_dropdown_choices()
        self.assertEqual([value for _label, value in pairs], list(ASPECT_RATIOS))
        labels = {value: label for label, value in pairs}
        self.assertTrue(labels["1:1"].startswith(FRAME_SQUARE))
        self.assertTrue(labels["9:16"].startswith(FRAME_TALL))
        self.assertTrue(labels["16:9"].startswith(FRAME_LANDSCAPE))
        self.assertTrue(labels["21:9"].startswith(FRAME_ULTRAWIDE))
        self.assertIn("1:1", labels["1:1"])
        self.assertEqual(normalize_aspect(aspect_choice_label("9:16")), "9:16")
        self.assertEqual(normalize_aspect(f"{FRAME_LANDSCAPE}  16:9"), "16:9")

    def test_sizes_and_still_fit(self) -> None:
        self.assertEqual(desk_size("720p", "16:9"), (1280, 720))
        self.assertEqual(desk_size("720p", "9:16"), (720, 1280))
        self.assertEqual(desk_size("720p", "21:9"), (1680, 720))
        self.assertEqual(desk_size("720p", "4:5"), (720, 900))
        self.assertEqual(desk_size("720p", "3:2"), (1080, 720))
        self.assertEqual(desk_size("720p", "2:3"), (720, 1080))
        self.assertEqual(desk_size("720p", "4:3"), (960, 720))
        self.assertEqual(desk_size("720p", "3:4"), (720, 960))
        self.assertEqual(desk_size("720p", "2.39:1 cinema scope")[1], 720)
        self.assertEqual(desk_size("720p", "1.85:1")[1], 720)
        self.assertEqual(normalize_aspect("scope"), "2.39:1 cinema scope")
        self.assertEqual(normalize_aspect("2.39:1"), "2.39:1 cinema scope")
        self.assertEqual(normalize_aspect("1.85"), "1.85:1")
        self.assertEqual(internal_size("720p", "16:9"), (512, 288))
        self.assertEqual(i2v_size("21:9")[0] % 32, 0)
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "plate.png"
            Image.new("RGB", (1200, 800), (18, 18, 18)).save(src)
            dest = Path(tmp) / "out.png"
            resize_still(src, dest, "720p", "4:5")
            with Image.open(dest) as out:
                self.assertEqual(out.size, (720, 900))

    def test_shot_and_project_persist_and_fork(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("aspect-lock", data_root=Path(tmp) / "projects")
            self.assertEqual(project.aspect, "16:9")
            project.set_aspect("21:9")
            reloaded = Project.load("aspect-lock", data_root=Path(tmp) / "projects")
            self.assertEqual(reloaded.aspect, "21:9")
            shot = ShotCard(name="Wide", aspect_ratio="21:9", resolution="720p")
            self.assertEqual(shot.aspect_ratio, "21:9")
            project.save_shot(shot)
            loaded = project.load_shot(shot.id)
            self.assertEqual(loaded.aspect_ratio, "21:9")
            forked = fork_take(project, loaded, seed=11)
            self.assertEqual(forked.aspect_ratio, "21:9")
            changed = ShotCard.from_dict({**forked.to_dict(), "aspect_ratio": "9:16"})
            self.assertEqual(changed.aspect_ratio, "9:16")

    def test_app_picker_next_to_quality(self) -> None:
        src = (ROOT / "app.py").read_text(encoding="utf-8")
        ast.parse(src)
        self.assertIn("4:5", src)
        self.assertIn("21:9", src)
        self.assertIn("still_aspect", src)
        self.assertIn("aspect_dropdown_choices()", src)
        self.assertIn("pipe_aspect", src)
        self.assertIn("fl-aspect-dd", src)
        self.assertIn("frame icon", src)
        quality = src.find("motion_quality = gr.Dropdown")
        aspect = src.find("\n                            aspect = gr.Dropdown")
        buried = src.find('label="Aspect — 9:16 is UGC"')
        self.assertGreater(quality, 0)
        self.assertGreater(aspect, quality)
        self.assertEqual(buried, -1)
        docs = (ROOT / "docs" / "ASPECT.md").read_text(encoding="utf-8")
        self.assertIn("Regenerate", docs)
        low = (src + docs).lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, low, banned)


if __name__ == "__main__":
    unittest.main()
