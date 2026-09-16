#!/usr/bin/env python3
"""Prompt + optional still must write a real MP4, or block honestly."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.ffmpeg_support import ffmpeg_available
from film_lab.hub import FORBIDDEN_BRANDS
from film_lab.motion_path import (
    MotionBlocked,
    generate_motion_mp4,
    motion_engine_markdown,
)
from film_lab.project import Project
from film_lab.shot_card import ShotCard


def _no_brands(blob: str) -> None:
    lower = blob.lower()
    for banned in FORBIDDEN_BRANDS:
        if banned in lower:
            raise AssertionError(banned)


class MotionPathTests(unittest.TestCase):
    def test_engine_copy_is_honest(self) -> None:
        md = motion_engine_markdown()
        self.assertIn("img2vid", md.lower())
        self.assertIn("zero", md.lower())
        self.assertIn("Advanced", md)
        self.assertIn("Ken Burns", md)
        self.assertNotIn("will still work", md.lower())
        self.assertNotIn("auto-fallback", md.lower())
        self.assertNotIn("auto-falls", md.lower())
        _no_brands(md)

    def test_primary_without_sidecar_blocks(self) -> None:
        os.environ["FILM_LAB_COMFY_URL"] = "http://127.0.0.1:1"
        try:
            with tempfile.TemporaryDirectory() as tmp:
                project = Project.create("blocked", data_root=Path(tmp) / "projects")
                shot = ShotCard(
                    name="Need sidecar",
                    director_intent="Warm lamp, two late-20s adults, slow push-in",
                    duration=2.0,
                )
                with self.assertRaises(MotionBlocked) as ctx:
                    generate_motion_mp4(project, shot)
                msg = str(ctx.exception).lower()
                self.assertIn("run_comfyui_amd", msg)
                self.assertIn("svd_xt", msg)
                self.assertNotIn("ken burns still produced", msg)
                self.assertNotIn("will still work", msg)
        finally:
            os.environ.pop("FILM_LAB_COMFY_URL", None)

    def test_prompt_only_writes_mp4(self) -> None:
        ok, _ = ffmpeg_available()
        if not ok:
            self.skipTest("ffmpeg missing on this box")
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("motion", data_root=Path(tmp) / "projects")
            shot = ShotCard(
                name="Prompt hold",
                director_intent="Warm lamp, two late-20s adults, slow push-in",
                duration=2.0,
                aspect_ratio="16:9",
            )
            dest, note = generate_motion_mp4(project, shot, generator_id="ken_burns", allow_fallback=False)
            self.assertTrue(dest.is_file(), dest)
            self.assertGreater(dest.stat().st_size, 1000)
            self.assertTrue(dest.name.endswith(".mp4"))
            self.assertIn("Ken Burns", note)
            self.assertTrue(project.resolve_still(shot.start_frame))

    def test_image_and_nine_sixteen(self) -> None:
        ok, _ = ffmpeg_available()
        if not ok:
            self.skipTest("ffmpeg missing on this box")
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("vert", data_root=Path(tmp) / "projects")
            still = Path(tmp) / "phone.png"
            Image.new("RGB", (360, 640), (40, 28, 18)).save(still)
            shot = ShotCard(
                name="UGC beat",
                director_intent="phone-light kitchen, adult creator, hook",
                duration=2.0,
                aspect_ratio="9:16",
            )
            dest, note = generate_motion_mp4(
                project,
                shot,
                generator_id="ken_burns",
                uploaded=[still],
                allow_fallback=False,
            )
            self.assertTrue(dest.is_file())
            self.assertGreater(dest.stat().st_size, 1000)
            self.assertIn("mp4", note.lower())

    def test_empty_prompt_without_still_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("empty", data_root=Path(tmp) / "projects")
            shot = ShotCard(name="Blank", director_intent="", body_motion_notes="")
            with self.assertRaises(MotionBlocked):
                generate_motion_mp4(project, shot, generator_id="ken_burns", allow_fallback=False)


if __name__ == "__main__":
    unittest.main()
