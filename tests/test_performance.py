#!/usr/bin/env python3
"""Micro-expressions, full-body behavior, and prop actions."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.characters import CharacterError, CharacterProfile, assert_adult_cast
from film_lab.director_notes import (
    ProjectNotes,
    WorldNote,
    fold_into_seed,
    load_notes,
    save_notes,
    set_world_note,
    upsert_director_note,
)
from film_lab.filming import ROLE_TEEN
from film_lab.hub import FORBIDDEN_BRANDS, HUB_CARDS
from film_lab.mark import TARGETS
from film_lab.performance import (
    BEHAVIORS,
    MICRO_EXPRESSIONS,
    PROP_ACTIONS,
    compose_writing_line,
    fold_micro_into_breath,
    merge_prop_note,
)
from film_lab.project import Project


class PerformanceTests(unittest.TestCase):
    def test_director_note_line_includes_micro_and_behavior(self) -> None:
        notes = ProjectNotes()
        upsert_director_note(
            notes,
            character_id="alison",
            character_name="Alison",
            emotion="tenderness",
            acting_beats="hold the look",
            micro_expression="swallow",
            behavior="weight shift",
        )
        line = notes.director["alison"].line()
        self.assertIn("micro-expression swallow", line)
        self.assertIn("behavior weight shift", line)
        self.assertIn("hold the look", line)

    def test_world_note_pick_up_book_folds_into_seed(self) -> None:
        notes = ProjectNotes()
        set_world_note(
            notes,
            weather="",
            thunder="none",
            earth="",
            wind="",
            setting="thin-wall bedroom",
            placement="",
            outdoor="none",
            prop_action="pick up book",
        )
        self.assertIn("prop pick up book", notes.world.line())
        folded = fold_into_seed("She stands by the lamp.", notes)
        self.assertIn("pick up book", folded)
        self.assertIn("WORLD NOTE", folded)

    def test_merge_prop_note_fills_empty(self) -> None:
        self.assertEqual(merge_prop_note("", "pick up book"), "pick up book")
        self.assertEqual(
            merge_prop_note("jacket stays", "pick up book"),
            "pick up book. jacket stays",
        )
        self.assertEqual(merge_prop_note("pick up book from the table", "pick up book"), "pick up book from the table")
        self.assertEqual(merge_prop_note("hold the lamp", "none"), "hold the lamp")

    def test_character_injection_includes_performance(self) -> None:
        profile = CharacterProfile(
            id="alison",
            name="Alison",
            role="Adult",
            age_band="late 20s (adult)",
            age_years=28,
            emotion_baseline="held warmth",
            micro_expression="soft glance",
            behavior="listen with the body",
        )
        line = profile.injection_line()
        self.assertIn("micro-expression: soft glance", line)
        self.assertIn("behavior: listen with the body", line)

    def test_teen_performance_does_not_unlock_intimacy(self) -> None:
        teen = CharacterProfile(
            id="sam",
            name="Sam",
            role=ROLE_TEEN,
            age_band="teen (story role, non-sexual)",
            age_years=16,
            micro_expression="swallow",
            behavior="pick up then pause",
        )
        self.assertIn("micro-expression: swallow", teen.injection_line())
        self.assertIn("not for intimacy", teen.injection_line().lower())
        with self.assertRaises(CharacterError):
            assert_adult_cast(
                [teen],
                intimacy_mode="intimate sex",
                content_intensity=0.8,
                context="performance test",
            )

    def test_writing_and_voice_helpers(self) -> None:
        self.assertEqual(
            compose_writing_line("swallow", "weight shift", "pick up book"),
            "performance: swallow; weight shift prop action: pick up book",
        )
        self.assertEqual(compose_writing_line("none", "none", "none"), "")
        self.assertEqual(
            fold_micro_into_breath("close-mic, audible inhale", "swallow"),
            "close-mic, audible inhale; micro-expression swallow",
        )
        self.assertEqual(fold_micro_into_breath("already swallow here", "swallow"), "already swallow here")

    def test_catalog_and_mark_target(self) -> None:
        self.assertIn("swallow", MICRO_EXPRESSIONS)
        self.assertIn("weight shift", BEHAVIORS)
        self.assertIn("pick up book", PROP_ACTIONS)
        self.assertIn("prop action", TARGETS)

    def test_persist_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("perf", data_root=Path(tmp) / "projects")
            notes = ProjectNotes()
            upsert_director_note(
                notes,
                character_id="alison",
                character_name="Alison",
                emotion="tenderness",
                acting_beats="",
                micro_expression="jaw set",
                behavior="still breath",
            )
            notes.world = WorldNote(setting="kitchen", prop_action="open book")
            save_notes(project, notes)
            loaded = load_notes(project)
            self.assertEqual(loaded.director["alison"].micro_expression, "jaw set")
            self.assertEqual(loaded.director["alison"].behavior, "still breath")
            self.assertEqual(loaded.world.prop_action, "open book")

    def test_app_copy_hub_and_no_brands(self) -> None:
        src = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("micro-expression", src)
        self.assertIn("pick up book", src)
        self.assertIn("Behavior (full human)", src)
        self.assertEqual(len(HUB_CARDS), 15)
        blob = (ROOT / "film_lab" / "performance.py").read_text(encoding="utf-8").lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, blob, banned)


if __name__ == "__main__":
    unittest.main()
