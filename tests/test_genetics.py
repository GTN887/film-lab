#!/usr/bin/env python3
"""Family Genetics — Regular/story kids from two adult bible faces."""

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

from film_lab.characters import (
    CharacterError,
    CharacterProfile,
    assert_adult_cast,
    pin_reference,
    seed_alison_bradley,
)
from film_lab.filming import ROLE_CHILD, ROLE_INFANT, ROLE_TEEN
from film_lab.genetics import (
    KID_AGES,
    GeneticsError,
    belongs_line,
    blend_parent_refs,
    generate_kids,
)
from film_lab.hub import FORBIDDEN_BRANDS, HUB_CARDS
from film_lab.project import Project


def _face(path: Path, color: tuple[int, int, int]) -> Path:
    Image.new("RGB", (640, 800), color).save(path)
    return path


def _parents(root: Path) -> tuple:
    project = Project.create("genetics", data_root=root / "projects")
    seed_alison_bradley(project)
    pink = _face(root / "a.png", (210, 170, 150))
    blue = _face(root / "b.png", (90, 110, 140))
    pin_reference(project, "alison", pink)
    pin_reference(project, "bradley", blue)
    return project, pink, blue


class GeneticsTests(unittest.TestCase):
    def test_blend_and_bible_card(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, _, _ = _parents(root)
            child, stills = generate_kids(project, "bradley", "alison", "child")
            self.assertEqual(child.role, ROLE_CHILD)
            self.assertEqual(child.age_years, 8)
            self.assertEqual(child.parent_ids, ["bradley", "alison"])
            self.assertIn("Belongs to", belongs_line(child, project))
            self.assertIn("Alison", belongs_line(child, project))
            self.assertEqual(len(stills), 2)
            for path in stills:
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size, 800)
            self.assertGreaterEqual(len(child.reference_stills), 2)
            self.assertNotRegex(child.wardrobe, r"bare skin|nude|sheet")
            self.assertIn("non-sexual", child.look_notes.lower())
            self.assertIn("not for intimacy", child.injection_line().lower())
            with self.assertRaises(CharacterError):
                assert_adult_cast(
                    [child],
                    intimacy_mode="intimate sex",
                    content_intensity=0.8,
                    context="genetics test",
                )

    def test_infant_teen_and_guards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, pink, blue = _parents(root)
            infant, _ = generate_kids(project, "alison", "bradley", "infant", name="Lamp kid")
            self.assertEqual(infant.role, ROLE_INFANT)
            self.assertEqual(infant.name, "Lamp kid")
            teen, _ = generate_kids(project, "alison", "bradley", "teen")
            self.assertEqual(teen.role, ROLE_TEEN)
            self.assertEqual(teen.age_years, 16)
            self.assertEqual(KID_AGES, ("infant", "child", "teen"))
            with self.assertRaises(GeneticsError):
                generate_kids(project, "alison", "alison", "child")
            kid = CharacterProfile(
                id="solo-kid",
                name="Solo",
                role=ROLE_CHILD,
                age_years=8,
                look_notes="story child, non-sexual",
            )
            save = project.root / "characters" / kid.id
            save.mkdir(parents=True)
            from film_lab.characters import save_character

            save_character(project, kid)
            pin_reference(project, kid.id, pink)
            with self.assertRaises(GeneticsError) as ctx:
                generate_kids(project, kid.id, "alison", "child")
            self.assertIn("18+", str(ctx.exception))
            empty = Project.create("noref", data_root=root / "empty")
            seed_alison_bradley(empty)
            with self.assertRaises(GeneticsError):
                generate_kids(empty, "alison", "bradley", "child")
            blended = blend_parent_refs(pink, blue, "child", bias=0.4)
            self.assertEqual(blended.size, (720, 900))

    def test_app_ui_and_fifteen_cards(self) -> None:
        src = (ROOT / "app.py").read_text(encoding="utf-8")
        ast.parse(src)
        for needle in (
            "Family Genetics",
            "What would their kids look like?",
            "Actor A",
            "Actress B",
            "infant",
            "child",
            "teen",
        ):
            self.assertIn(needle, src)
        self.assertEqual(len(HUB_CARDS), 15)
        titles = [c.title for c in HUB_CARDS]
        self.assertIn("Character Consistency", titles)
        self.assertNotIn("Family Genetics", titles)
        bible = next(c for c in HUB_CARDS if c.tab_id == "characters")
        self.assertIn("Family Genetics", bible.blurb)
        low = (src + (ROOT / "film_lab" / "genetics.py").read_text(encoding="utf-8")).lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, low, banned)


if __name__ == "__main__":
    unittest.main()
