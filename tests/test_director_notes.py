#!/usr/bin/env python3
"""Director Note + World Note: fold into enhance, adult-only intimate route."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.characters import seed_alison_bradley
from film_lab.constants import EXPLICIT_INTIMACY
from film_lab.director_notes import (
    CastFace,
    DirectorNote,
    DirectorNoteError,
    ProjectNotes,
    SAFETY_LINE,
    WorldNote,
    assert_notes_safe,
    face_is_adult,
    fold_into_seed,
    load_notes,
    notes_ask_undress,
    notes_need_adult,
    save_notes,
    strip_note_blocks,
    upsert_director_note,
)
from film_lab.enhance import enhance_prompt
from film_lab.hub import FORBIDDEN_BRANDS
from film_lab.intensity import intensity_ui_help
from film_lab.llm import PROVIDER_LOCAL
from film_lab.project import Project
from film_lab.shot_card import ShotCard
from film_lab.variations import base_take_name, fork_take


class DirectorNotesTests(unittest.TestCase):
    def test_fold_and_strip(self) -> None:
        notes = ProjectNotes()
        upsert_director_note(
            notes,
            character_id="alison",
            character_name="Alison",
            emotion="tenderness",
            acting_beats="hold the look",
        )
        notes.world = WorldNote(
            weather="storm",
            thunder="overhead",
            earth="wet earth",
            wind="gust",
            setting="thin-wall bedroom",
            placement="she at the window",
        )
        folded = fold_into_seed("Slow kiss. Don't cut.", notes)
        self.assertIn("DIRECTOR NOTE (Alison — performance):", folded)
        self.assertIn("hold the look", folded)
        self.assertIn("WORLD NOTE (mise-en-scène):", folded)
        self.assertIn("thunder overhead", folded)
        again = fold_into_seed(folded + "\nDIRECTOR NOTE (Alison — performance): old", notes)
        self.assertEqual(again.count("DIRECTOR NOTE"), 1)
        self.assertIn("Slow kiss", strip_note_blocks(folded))

    def test_adult_gate_copy(self) -> None:
        self.assertFalse(notes_need_adult("covered sheets", 0.2))
        self.assertTrue(notes_need_adult("intimate sex", 0.2))
        self.assertTrue(notes_need_adult("covered sheets", 0.5))
        self.assertTrue(notes_need_adult(EXPLICIT_INTIMACY, 0.1))
        kid = CastFace(id="sam", name="Sam", age_years=16)
        self.assertFalse(face_is_adult(kid))
        self.assertTrue(face_is_adult(CastFace(id="alison", name="Alison", age_years=28)))
        help_text = intensity_ui_help().lower()
        self.assertIn("adult 18+ only", help_text)
        self.assertIn("director notes", help_text)
        self.assertIn("never route minors", help_text)
        self.assertIn("18+", SAFETY_LINE)

    def test_persist_and_enhance_fold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("notes", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            notes = load_notes(project)
            upsert_director_note(
                notes,
                character_id="alison",
                character_name="Alison",
                emotion="longing",
                acting_beats="don't rush the kiss",
            )
            notes.world = WorldNote(weather="rain", setting="bedroom lamp")
            save_notes(project, notes)
            assert_notes_safe(
                project,
                notes,
                intimacy="intimate sex",
                intensity=0.62,
            )
            result = enhance_prompt(
                project,
                "lamp, slow kiss",
                provider=PROVIDER_LOCAL,
                character_ids=["alison", "bradley"],
                intimacy="intimate sex",
                content_intensity=0.62,
            )
            blob = (result.seed + " " + result.prompt).lower()
            self.assertIn("director note", blob)
            self.assertIn("longing", blob)
            self.assertIn("world note", blob)
            ghost = ProjectNotes(
                director={
                    "kid": DirectorNote(
                        character_id="kid",
                        character_name="Kid",
                        emotion="hope",
                        acting_beats="wave from the porch",
                    )
                }
            )
            with self.assertRaises(DirectorNoteError):
                assert_notes_safe(
                    project,
                    ghost,
                    intimacy=EXPLICIT_INTIMACY,
                    intensity=1.0,
                    context="Animate",
                )
            assert_notes_safe(project, ghost, intimacy="covered sheets", intensity=0.2)

    def test_undress_needs_explicit_adults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("undress", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            notes = ProjectNotes()
            upsert_director_note(
                notes,
                character_id="alison",
                character_name="Alison",
                emotion="desire",
                acting_beats="don't cut",
                wardrobe_motion="undress through motion",
            )
            self.assertTrue(notes_ask_undress(notes))
            with self.assertRaises(DirectorNoteError):
                assert_notes_safe(
                    project, notes, intimacy="covered sheets", intensity=0.22
                )
            assert_notes_safe(
                project, notes, intimacy="covered sheets", intensity=1.0
            )
            save_notes(project, notes)
            result = enhance_prompt(
                project,
                "clothed still, slow kiss",
                provider=PROVIDER_LOCAL,
                character_ids=["alison", "bradley"],
                intimacy="covered sheets",
                content_intensity=1.0,
            )
            para = result.paragraph.lower()
            self.assertIn("clothes come off", para)
            self.assertNotIn("same wardrobe", para)
            self.assertIn("adult", para)

    def test_fork_keeps_source_take(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("fork", data_root=Path(tmp) / "projects")
            source = ShotCard(name="Lamp hold", seed=10)
            project.save_shot(source)
            forked = fork_take(project, source, seed=99)
            self.assertNotEqual(forked.id, source.id)
            self.assertEqual(base_take_name(forked.name), "Lamp hold")
            self.assertIn("take", forked.name)
            self.assertEqual(forked.seed, 99)
            self.assertEqual(len(project.list_shots()), 2)
            self.assertTrue(any(s.id == source.id for s in project.list_shots()))

    def test_no_forbidden_brands(self) -> None:
        blob = SAFETY_LINE + intensity_ui_help()
        src = (ROOT / "film_lab" / "director_notes.py").read_text(encoding="utf-8")
        low = (blob + src).lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, low, banned)


if __name__ == "__main__":
    unittest.main()
