#!/usr/bin/env python3
"""Pointer / Go-to — Actor A walks to a locked room; Take Board records it."""

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

from film_lab.characters import pin_reference, seed_alison_bradley
from film_lab.ffmpeg_support import ffmpeg_available
from film_lab.hub import FORBIDDEN_BRANDS, HUB_CARDS
from film_lab.mark import SHAPE_POINTER, SHAPES
from film_lab.pointer import (
    PointerError,
    destination_choices,
    generate_go_to,
    guess_room,
    pointer_markdown,
)
from film_lab.project import Project
from film_lab.setbuild import build_locked_environment
from film_lab.writing import WRITING_MODES


def _photo(path: Path, color=(60, 80, 90)) -> Path:
    Image.new("RGB", (96, 64), color).save(path)
    return path


def _no_brands(blob: str) -> None:
    low = blob.lower()
    for banned in FORBIDDEN_BRANDS:
        if banned in low:
            raise AssertionError(banned)


class PointerTests(unittest.TestCase):
    def test_room_guess_and_destinations(self) -> None:
        self.assertEqual(guess_room("guest bathroom still"), "bathroom")
        self.assertIn(SHAPE_POINTER, SHAPES)
        self.assertIn("pointer", pointer_markdown().lower())
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("rooms", data_root=Path(tmp))
            photo = _photo(Path(tmp) / "bath.jpg", (90, 90, 110))
            built = build_locked_environment(
                project, photo, camera="look-around", title="Bathroom"
            )
            choices = destination_choices(project)
            self.assertTrue(any("bathroom" in c.lower() for c in choices))
            self.assertTrue(any(built.id in c for c in choices))

    @unittest.skipUnless(ffmpeg_available()[0], "ffmpeg required for go-to take")
    def test_go_to_records_take(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("goto", data_root=Path(tmp))
            seed_alison_bradley(project)
            face = _photo(Path(tmp) / "alison.png", (200, 170, 150))
            pin_reference(project, "alison", face)
            bath = build_locked_environment(
                project,
                _photo(Path(tmp) / "bath.png", (80, 90, 120)),
                camera="look-around",
                title="Bathroom",
            )
            hall = build_locked_environment(
                project,
                _photo(Path(tmp) / "hall.png", (70, 60, 50)),
                camera="zoom",
                title="Hallway",
            )
            dest = next(c for c in destination_choices(project) if bath.id in c)
            start = next(c for c in destination_choices(project) if hall.id in c)
            take = generate_go_to(
                project,
                "alison — Actor A · Alison",
                dest,
                filming_mode="Regular",
                start_choice=start,
            )
            self.assertTrue(take.take.is_file())
            self.assertEqual(take.destination, "bathroom")
            self.assertTrue(any(c.path == str(take.take.resolve()) for c in project.load_gallery()))
            with self.assertRaises(PointerError):
                generate_go_to(project, "", dest)

    def test_modes_hub_and_ui(self) -> None:
        self.assertEqual(len(WRITING_MODES), 5)
        self.assertEqual(len(HUB_CARDS), 15)
        src = (ROOT / "app.py").read_text(encoding="utf-8")
        ast.parse(src)
        for needle in (
            "Pointer / Go-to",
            "Generate go-to take",
            "Actor A — click to go",
            "bathroom",
            "pointer",
        ):
            self.assertIn(needle, src)
        _no_brands(src)
        _no_brands((ROOT / "film_lab" / "pointer.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
