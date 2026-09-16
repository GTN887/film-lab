#!/usr/bin/env python3
"""Any still → Animate. Product beats. No marketplace."""

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

from film_lab.constants import STORY_INTIMACY
from film_lab.hub import FORBIDDEN_BRANDS, HUB_CARDS
from film_lab.motion_scope import (
    DEFAULT_PRODUCT_BEATS,
    SUBJECT_PERSON,
    SUBJECT_POSTER,
    SUBJECT_PRODUCT,
    apply_motion_subject,
    build_product_beats,
    is_object_still,
    likeness_prompt_bits,
    motion_scope_help,
    product_beats_help,
)
from film_lab.project import Project
from film_lab.shot_card import ShotCard
from film_lab.ugc import UGC_ASPECT


class MotionScopeTests(unittest.TestCase):
    def test_hub_motion_is_any_still(self) -> None:
        self.assertEqual(len(HUB_CARDS), 15)
        pipeline = next(c for c in HUB_CARDS if c.tab_id == "pipeline")
        self.assertEqual(pipeline.index, "01")
        self.assertEqual(pipeline.title, "AI Production Pipeline")
        low = (pipeline.blurb + pipeline.kicker + motion_scope_help() + product_beats_help()).lower()
        self.assertIn("any still", low)
        self.assertIn("cans", low)
        self.assertIn("posters", low)
        self.assertIn("no marketplace", low)
        self.assertIn("ugc", low)
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, low, banned)

    def test_object_subject_drops_face_lock(self) -> None:
        self.assertTrue(is_object_still(SUBJECT_PRODUCT))
        self.assertTrue(is_object_still(SUBJECT_POSTER))
        self.assertFalse(is_object_still(SUBJECT_PERSON))
        shot = ShotCard(
            name="Can",
            character_ids=["alison"],
            character_tags=["Alison (blonde late-20s)"],
            face_lock_strength=0.55,
            intimacy_mode="covered sheets",
            content_intensity=0.62,
        )
        apply_motion_subject(shot, SUBJECT_PRODUCT)
        self.assertEqual(shot.character_ids, [])
        self.assertEqual(shot.character_tags, [])
        self.assertEqual(shot.face_lock_strength, 0.0)
        self.assertEqual(shot.intimacy_mode, STORY_INTIMACY)
        bits = likeness_prompt_bits(shot)
        blob = " ".join(bits).lower()
        self.assertIn("object readable", blob)
        self.assertIn("no face lock", blob)
        self.assertNotIn("adult faces", blob)
        person = ShotCard(character_ids=["alison"], face_lock_strength=0.55)
        apply_motion_subject(person, SUBJECT_PERSON)
        self.assertEqual(person.character_ids, ["alison"])
        face = " ".join(likeness_prompt_bits(person)).lower()
        self.assertIn("face lock", face)

    def test_two_beats_can_then_pour(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("beats", data_root=Path(tmp) / "projects")
            can = Path(tmp) / "can.png"
            Image.new("RGB", (64, 64), (180, 40, 40)).save(can)
            written = project.ingest_files([can])
            shots = build_product_beats(
                project,
                stills=[written[0].name, written[0].name],
                product_name="Lamp oil",
                aspect=UGC_ASPECT,
                quality="720p",
                character_ids=["alison"],
            )
            self.assertEqual(len(shots), 2)
            self.assertEqual(len(DEFAULT_PRODUCT_BEATS), 2)
            self.assertIn("Opens alone", shots[0].name)
            self.assertIn("Pick up and pour", shots[1].name)
            self.assertEqual(shots[0].character_ids, [])
            self.assertEqual(shots[1].character_ids, ["alison"])
            self.assertEqual(shots[0].intimacy_mode, STORY_INTIMACY)
            self.assertEqual(shots[1].intimacy_mode, STORY_INTIMACY)
            self.assertIn("lid lifts", shots[0].director_intent.lower())
            self.assertIn("pours", shots[1].director_intent.lower())

    def test_app_copy_locks_scope(self) -> None:
        src = (ROOT / "app.py").read_text(encoding="utf-8")
        ast.parse(src)
        self.assertIn("Any still", src)
        self.assertIn("No marketplace", src)
        self.assertIn("Push two beats → Motion Desk", src)
        self.assertIn("Opens alone", src)
        self.assertIn("Pick up and pour", src)
        self.assertNotIn("marketplace feature", src.lower())
        low = src.lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, low, banned)
        scope = (ROOT / "film_lab" / "motion_scope.py").read_text(encoding="utf-8").lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, scope, banned)


if __name__ == "__main__":
    unittest.main()
