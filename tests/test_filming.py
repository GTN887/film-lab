#!/usr/bin/env python3
"""Regular | 18+ Explicit split, family roles, 3D Set notes."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.characters import CharacterError, CharacterProfile, seed_alison_bradley
from film_lab.constants import CAMERA_MOVES, EXPLICIT_INTIMACY, STORY_INTIMACY
from film_lab.director_notes import (
    DirectorNote,
    DirectorNoteError,
    ProjectNotes,
    assert_notes_safe,
)
from film_lab.enhance import EnhanceError, enhance_prompt
from film_lab.filming import (
    MODE_EXPLICIT,
    MODE_REGULAR,
    ROLE_CHILD,
    ROLE_TEEN,
    FilmingError,
    assert_filming_safe,
    asks_sex_tools,
    profile_is_adult,
)
from film_lab.hub import FORBIDDEN_BRANDS, HUB_CARDS
from film_lab.llm import PROVIDER_LOCAL
from film_lab.project import Project
from film_lab.setdesk import (
    SET_CAMERAS,
    CharacterMark,
    build_set_note,
    load_set_note,
    save_set_note,
    set_markdown,
)


class FilmingModeTests(unittest.TestCase):
    def test_regular_blocks_sex_tools(self) -> None:
        self.assertTrue(asks_sex_tools("intimate sex", 0.2))
        self.assertTrue(asks_sex_tools("covered sheets", 0.62))
        self.assertTrue(asks_sex_tools("covered sheets", 0.2, "undress through motion"))
        self.assertFalse(asks_sex_tools(STORY_INTIMACY, 0.22))
        adult = CharacterProfile(id="alison", name="Alison", age_years=28)
        with self.assertRaises(FilmingError):
            assert_filming_safe(
                MODE_REGULAR,
                [adult],
                intimacy="intimate sex",
                intensity=0.2,
            )
        assert_filming_safe(
            MODE_REGULAR,
            [adult],
            intimacy=STORY_INTIMACY,
            intensity=0.22,
        )

    def test_teen_role_allowed_in_regular_blocked_in_explicit(self) -> None:
        teen = CharacterProfile(
            id="sam",
            name="Sam",
            role=ROLE_TEEN,
            age_years=16,
            age_band="teen (story role, non-sexual)",
            look_notes="Teen story role. School bag. Non-sexual.",
        )
        self.assertFalse(profile_is_adult(teen))
        assert_filming_safe(
            MODE_REGULAR,
            [teen],
            intimacy=STORY_INTIMACY,
            intensity=0.2,
        )
        with self.assertRaises(FilmingError):
            assert_filming_safe(
                MODE_EXPLICIT,
                [teen],
                intimacy=EXPLICIT_INTIMACY,
                intensity=1.0,
            )
        with self.assertRaises(CharacterError):
            CharacterProfile(
                id="bad",
                name="Bad",
                role=ROLE_TEEN,
                age_years=19,
                age_band="teen (story role, non-sexual)",
            )
        with self.assertRaises(CharacterError):
            CharacterProfile(id="kid", name="No", age_band="late 20s (adult)", age_years=17)

    def test_child_injection_is_nonsexual(self) -> None:
        child = CharacterProfile(
            id="lea",
            name="Lea",
            role=ROLE_CHILD,
            age_years=8,
            age_band="child (story role, non-sexual)",
            look_notes="Child story role. Coat. Bus window.",
        )
        line = child.injection_line().lower()
        self.assertIn("non-sexual", line)
        self.assertIn("child", line)
        self.assertNotIn("adult 18+", line)

    def test_notes_and_enhance_respect_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("modes", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            self.assertEqual(project.filming_mode, MODE_EXPLICIT)
            notes = ProjectNotes(
                director={
                    "alison": DirectorNote(
                        character_id="alison",
                        character_name="Alison",
                        emotion="tenderness",
                    )
                }
            )
            assert_notes_safe(project, notes, intimacy="intimate sex", intensity=0.62)
            project.set_filming_mode(MODE_REGULAR)
            with self.assertRaises(DirectorNoteError):
                assert_notes_safe(project, notes, intimacy="intimate sex", intensity=0.62)
            with self.assertRaises(EnhanceError):
                enhance_prompt(
                    project,
                    "bus, walk home",
                    provider=PROVIDER_LOCAL,
                    character_ids=["alison"],
                    intimacy="intimate sex",
                    content_intensity=0.62,
                )
            result = enhance_prompt(
                project,
                "bus, walk home",
                provider=PROVIDER_LOCAL,
                character_ids=["alison"],
                intimacy=STORY_INTIMACY,
                content_intensity=0.22,
            )
            self.assertIn("bus", result.prompt.lower())

    def test_set_note_folds_and_hub(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("set", data_root=Path(tmp) / "projects")
            note = build_set_note(
                camera="aerial",
                outdoor="bus stop",
                set_description="After the bus. Walk home.",
                placements=[
                    CharacterMark(
                        character_id="sam",
                        character_name="Sam",
                        role=ROLE_TEEN,
                        mark="the bus door",
                    )
                ],
            )
            save_set_note(project, note)
            loaded = load_set_note(project)
            line = loaded.line().lower()
            self.assertIn("set note", line)
            self.assertIn("aerial", line)
            self.assertIn("bus stop", line)
            self.assertIn("teen", line)
        for cam in SET_CAMERAS:
            self.assertIn(cam, CAMERA_MOVES)
        titles = [c.title for c in HUB_CARDS]
        self.assertIn("3D Set Desk", titles)
        docs = (ROOT / "docs" / "SET.md").read_text(encoding="utf-8").lower()
        self.assertIn("not a realtime 3d engine", docs)
        self.assertIn("aerial", docs)
        blob = set_markdown() + " ".join(c.blurb for c in HUB_CARDS)
        low = blob.lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, low, banned)


if __name__ == "__main__":
    unittest.main()
