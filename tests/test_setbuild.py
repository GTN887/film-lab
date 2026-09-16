#!/usr/bin/env python3
"""LOCKED Environment from photo — local sets / stills / takes."""

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
from film_lab.envlock import load_env_lock
from film_lab.hub import FORBIDDEN_BRANDS, HUB_CARDS
from film_lab.project import Project
from film_lab.setbuild import (
    ENV_CAMERAS,
    SetBuildError,
    build_locked_environment,
    built_set_choices,
    delete_built_set,
    invent_missing_areas,
    place_actors_on_plate,
    storage_help,
)
from film_lab.writing import WRITING_MODES


def _photo(path: Path, size=(80, 48), color=(70, 90, 110)) -> Path:
    Image.new("RGB", size, color).save(path)
    return path


def _no_brands(blob: str) -> None:
    low = blob.lower()
    for banned in FORBIDDEN_BRANDS:
        if banned in low:
            raise AssertionError(banned)


class SetBuildTests(unittest.TestCase):
    def test_invent_is_larger(self) -> None:
        src = Image.new("RGB", (40, 24), (30, 40, 50))
        out = invent_missing_areas(src)
        self.assertGreater(out.size[0], src.size[0])
        self.assertGreater(out.size[1], src.size[1])

    def test_build_stores_sets_stills_and_deletes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("locked-set", data_root=Path(tmp))
            photo = _photo(Path(tmp) / "porch.jpg")
            built = build_locked_environment(
                project,
                photo,
                camera="look-around",
                character_ids=[],
            )
            folder = project.sets_dir / built.id
            self.assertTrue((folder / "expanded.png").is_file())
            self.assertTrue((folder / "env.json").is_file())
            self.assertGreaterEqual(len(built.views), 2)
            stills = list(project.stills_dir.glob(f"{built.id}-*"))
            self.assertTrue(stills)
            lock = load_env_lock(project)
            self.assertTrue(lock.locked)
            self.assertIn("LOCKED Environment", lock.note)
            self.assertTrue(built_set_choices(project))
            help_text = storage_help(project)
            self.assertIn("sets", help_text)
            self.assertIn("stills", help_text)
            self.assertIn("takes", help_text)
            deleted = delete_built_set(project, f"{built.id} — {built.title}")
            self.assertEqual(deleted, built.id)
            self.assertFalse(folder.exists())
            self.assertFalse(list(project.stills_dir.glob(f"{built.id}-*")))

    def test_place_actors_optional(self) -> None:
        plate = Image.new("RGB", (160, 90), (40, 40, 40))
        actor = Image.new("RGB", (40, 80), (200, 160, 140))
        out = place_actors_on_plate(plate, [actor])
        self.assertEqual(out.size, plate.size)
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("with-cast", data_root=Path(tmp))
            seed_alison_bradley(project)
            face = _photo(Path(tmp) / "alison-ref.png", size=(32, 48), color=(210, 180, 150))
            pin_reference(project, "alison", face)
            photo = _photo(Path(tmp) / "room.png", size=(96, 64))
            built = build_locked_environment(
                project,
                photo,
                camera="zoom",
                character_ids=["alison"],
                filming_mode="Regular",
            )
            self.assertIn("alison", built.character_ids)
            self.assertEqual(built.camera, "zoom")

    def test_explicit_blocks_minors_and_bad_camera(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("gate", data_root=Path(tmp))
            seed_alison_bradley(project)
            photo = _photo(Path(tmp) / "bed.png")
            with self.assertRaises(SetBuildError):
                build_locked_environment(project, photo, camera="dolly")
            with self.assertRaises(SetBuildError):
                delete_built_set(project, "")

    def test_modes_hub_ui_and_paths(self) -> None:
        self.assertEqual(ENV_CAMERAS, ("look-around", "zoom", "aerial"))
        self.assertEqual(len(WRITING_MODES), 5)
        self.assertEqual(len(HUB_CARDS), 15)
        src = (ROOT / "app.py").read_text(encoding="utf-8")
        ast.parse(src)
        start = src.find('with gr.Tab("3D Set Desk"')
        chunk = src[start : src.find('with gr.Tab("Mark & Direct"', start)]
        for needle in (
            "LOCKED Environment from photo",
            "look-around",
            "Build locked environment",
            "Delete this set",
            "Place Character Bible actors",
            "data/projects",
            "sets",
            "takes",
        ):
            self.assertIn(needle, chunk)
        _no_brands(src)
        _no_brands((ROOT / "film_lab" / "setbuild.py").read_text(encoding="utf-8"))
        help_text = storage_help()
        self.assertIn("data/projects/<name>/sets", help_text.replace("\\", "/"))


if __name__ == "__main__":
    unittest.main()
