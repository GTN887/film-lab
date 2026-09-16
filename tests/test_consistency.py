#!/usr/bin/env python3
"""Character bible injection + local consistency stack."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.characters import (
    CharacterError,
    compose_local_prompt,
    ensure_studio_library,
    export_to_studio_library,
    load_studio_library,
    seed_alison_bradley,
    studio_characters_root,
)
from film_lab.consistency import (
    CONSISTENCY_DEBUG,
    CONSISTENCY_PROGRAM,
    CONSISTENCY_STACK,
    DEFAULT_FACE_LOCK,
    FACE_METHODS,
    consistency_program_md,
    detect_env_nodes,
    detect_face_nodes,
    face_lock_plan,
    normalize_face_method,
)
from film_lab.hub import FORBIDDEN_BRANDS, HUB_CARDS
from film_lab.project import Project
from film_lab.shot_card import ShotCard
from film_lab.ugc import apply_cast_to_brief, UgcBrief
from film_lab.writing import bible_block


class ConsistencyTests(unittest.TestCase):
    def test_stack_and_hub_card(self) -> None:
        keys = [m.key for m in CONSISTENCY_STACK]
        self.assertEqual(keys[0], "start_still_i2v")
        self.assertIn("ipadapter_faceid_plus_v2", keys)
        self.assertIn("instantid", keys)
        self.assertIn("openpose", keys)
        self.assertIn("reactor", keys)
        self.assertIn("Character Consistency", [c.title for c in HUB_CARDS])
        program = consistency_program_md()
        self.assertIn("InstantID", program)
        self.assertIn("Environment", program)
        self.assertIn("DEBUG CHECKLIST", CONSISTENCY_DEBUG)
        self.assertIn("RX 5600 XT", CONSISTENCY_PROGRAM)
        self.assertEqual(normalize_face_method("instantid"), "instantid")
        self.assertEqual(normalize_face_method("nope"), "start_still_i2v")
        self.assertIn("instantid", FACE_METHODS)
        self.assertEqual(detect_face_nodes({"ApplyInstantID": {}}), ["ApplyInstantID"])
        self.assertEqual(detect_env_nodes({"ControlNetLoader": {}}), ["ControlNetLoader"])
        blob = " ".join(m.title + m.notes for m in CONSISTENCY_STACK).lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, blob, banned)

    def test_alison_bradley_inject(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("cast", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            shot = ShotCard(
                name="Lamp",
                character_ids=["alison", "bradley"],
                face_lock_strength=0.55,
            )
            prompt = compose_local_prompt(shot, project)
            self.assertIn("Alison", prompt)
            self.assertIn("blonde", prompt.lower())
            self.assertIn("Bradley", prompt)
            self.assertIn("wedding band", prompt.lower())
            self.assertIn("personality", prompt.lower())
            self.assertIn("face lock 0.55", prompt)
            bible = bible_block(project, ["alison", "bradley"])
            self.assertIn("Tenderness", bible)
            self.assertIn("18+", bible)

    def test_studio_library_json(self) -> None:
        ensure_studio_library()
        root = studio_characters_root()
        self.assertTrue((root / "alison.json").is_file())
        self.assertTrue((root / "bradley.json").is_file())
        lib = load_studio_library()
        names = {p.name for p in lib}
        self.assertIn("Alison", names)
        self.assertIn("Bradley", names)
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("lib", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            from film_lab.characters import load_character

            path = export_to_studio_library(load_character(project, "alison"))
            self.assertEqual(path.suffix, ".json")
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("sk-", text)
            self.assertIn("alison", text.lower())

    def test_ugc_picks_up_cast(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("ad", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            brief = apply_cast_to_brief(
                project, UgcBrief(creator_name="Alison", creator_age=28, product_name="Lamp")
            )
            self.assertIn("blonde", brief.creator_look.lower())

    def test_minor_still_blocked(self) -> None:
        with self.assertRaises(CharacterError):
            from film_lab.characters import CharacterProfile

            CharacterProfile(id="x", name="X", age_years=16, age_band="late 20s (adult)")

    def test_face_lock_plan(self) -> None:
        plan = face_lock_plan(strength=DEFAULT_FACE_LOCK, ref_count=4)
        self.assertEqual(plan["status"], "wired")
        self.assertAlmostEqual(plan["strength"], 0.55)


if __name__ == "__main__":
    unittest.main()
