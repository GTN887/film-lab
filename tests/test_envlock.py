#!/usr/bin/env python3
"""Environment / Set lock: persist, fold, seed img2vid from locked still."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.director_notes import fold_desk, fold_into_seed, load_notes, strip_note_blocks
from film_lab.envlock import (
    EnvLock,
    apply_env_lock,
    env_markdown,
    env_shot_bits,
    load_env_lock,
    resolve_env_still,
)
from film_lab.hub import FORBIDDEN_BRANDS
from film_lab.motion_path import ensure_motion_still
from film_lab.project import Project
from film_lab.shot_card import ShotCard


def _still(path: Path) -> Path:
    Image.new("RGB", (64, 64), (40, 40, 40)).save(path)
    return path


class EnvLockTests(unittest.TestCase):
    def test_persist_and_fold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("env", data_root=Path(tmp) / "projects")
            plate = _still(Path(tmp) / "street.png")
            lock = apply_env_lock(
                project,
                still=plate,
                geometry="canny",
                strength=0.4,
                note="wet street after the bus",
            )
            self.assertTrue(lock.locked)
            self.assertEqual(lock.geometry, "canny")
            reloaded = load_env_lock(project)
            self.assertEqual(reloaded.still, lock.still)
            self.assertIn("ENV LOCK (set / world):", reloaded.line())
            self.assertIn("wet street", reloaded.line())
            bits = env_shot_bits(reloaded)
            self.assertTrue(any("environment lock" in b for b in bits))
            folded = fold_desk(project, "Slow walk home.")
            self.assertIn("ENV LOCK", folded)
            self.assertIn("Slow walk home", strip_note_blocks(folded))
            again = fold_into_seed(folded + "\nENV LOCK (set / world): old", load_notes(project), env_line=reloaded.line())
            self.assertEqual(again.count("ENV LOCK"), 1)
            resolved = resolve_env_still(project, reloaded)
            self.assertIsNotNone(resolved)
            self.assertTrue(resolved.is_file())

    def test_img2vid_seeds_from_locked_still(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("seed", data_root=Path(tmp) / "projects")
            plate = _still(Path(tmp) / "lamp.png")
            apply_env_lock(project, still=plate, note="same lamp")
            shot = ShotCard(name="Hold", director_intent="hold the room")
            path = ensure_motion_still(project, shot)
            self.assertTrue(path.is_file())
            self.assertEqual(shot.start_frame, load_env_lock(project).still)

    def test_copy_and_no_brands(self) -> None:
        blob = env_markdown(EnvLock()) + consistency_safe()
        low = blob.lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, low, banned)
        self.assertIn("regenerate", low)
        self.assertIn("rx 5600", low)


def consistency_safe() -> str:
    from film_lab.consistency import consistency_program_md

    return consistency_program_md()


if __name__ == "__main__":
    unittest.main()
