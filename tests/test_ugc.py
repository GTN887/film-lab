#!/usr/bin/env python3
"""UGC Ads Desk: local script, 9:16 plan, adult guard."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.hub import FORBIDDEN_BRANDS, HUB_CARDS, hub_cards_html
from film_lab.llm import PROVIDER_CLAUDE, PROVIDER_LOCAL, PROVIDER_OPENAI, UGC_PROVIDERS
from film_lab.project import Project
from film_lab.ugc import (
    UGC_ASPECT,
    UGC_TARGET_SECONDS,
    UgcBrief,
    UgcError,
    assert_ugc_adult,
    build_shot_plan,
    generate_script,
    list_briefs,
    local_script,
    push_plan_to_shots,
    save_brief,
)


class UgcTests(unittest.TestCase):
    def test_seventh_card(self) -> None:
        titles = [c.title for c in HUB_CARDS]
        self.assertIn("UGC Ads Desk", titles)
        self.assertIn("Character Consistency", titles)
        self.assertEqual(titles[-1], "Mark & Direct")
        self.assertEqual(len(HUB_CARDS), 15)
        self.assertIn("3D Set Desk", titles)
        self.assertIn("Pose Desk", titles)
        blob = hub_cards_html().lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, blob, banned)

    def test_local_script_and_plan(self) -> None:
        brief = UgcBrief(
            product_name="Warm lamp oil",
            product_notes="One drop on the bulb ring.",
            creator_name="Alison",
            creator_age=28,
        )
        filled = generate_script(brief, provider=PROVIDER_LOCAL)
        self.assertTrue(filled.hook)
        self.assertTrue(filled.cta)
        self.assertIn("lamp", filled.script_text().lower())
        beats = build_shot_plan(filled)
        total = sum(b.duration for b in beats)
        self.assertGreaterEqual(total, UGC_TARGET_SECONDS[0])
        self.assertLessEqual(total, UGC_TARGET_SECONDS[1])
        self.assertEqual(len(beats), 5)
        self.assertEqual([b.key for b in beats], ["hook", "problem", "product", "proof", "cta"])

    def test_push_shots_are_vertical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("ugc-ad", data_root=Path(tmp) / "projects")
            brief = local_script(
                UgcBrief(product_name="Serum", creator_name="Bradley", creator_age=29)
            )
            shots = push_plan_to_shots(project, brief)
            self.assertEqual(len(shots), 5)
            self.assertTrue(all(s.aspect_ratio == UGC_ASPECT for s in shots))
            self.assertTrue(all(2.0 <= s.duration <= 3.0 for s in shots))
            self.assertEqual(len(list_briefs(project)), 1)

    def test_openai_off_falls_back_to_local(self) -> None:
        import os

        os.environ.pop("FILM_LAB_OPENAI_API_KEY", None)
        os.environ.pop("OPENAI_API_KEY", None)
        self.assertIn(PROVIDER_OPENAI, UGC_PROVIDERS)
        brief = UgcBrief(
            product_name="Warm lamp oil",
            creator_name="Alison",
            creator_age=28,
        )
        filled = generate_script(brief, provider=PROVIDER_OPENAI)
        self.assertTrue(filled.hook)
        self.assertEqual(filled.provider, PROVIDER_LOCAL)
        os.environ.pop("FILM_LAB_ANTHROPIC_API_KEY", None)
        os.environ.pop("ANTHROPIC_API_KEY", None)
        self.assertIn(PROVIDER_CLAUDE, UGC_PROVIDERS)
        claude = generate_script(brief, provider=PROVIDER_CLAUDE)
        self.assertTrue(claude.hook)
        self.assertEqual(claude.provider, PROVIDER_LOCAL)

    def test_minor_blocked(self) -> None:
        with self.assertRaises(UgcError):
            assert_ugc_adult(17)
        with self.assertRaises(UgcError):
            generate_script(UgcBrief(creator_age=16, product_name="x"), provider=PROVIDER_LOCAL)
        path = Path(tempfile.mkdtemp())
        # save_brief also guards
        project = Project.create("guard", data_root=path / "p")
        with self.assertRaises(UgcError):
            save_brief(project, UgcBrief(creator_age=15, product_name="x"))


if __name__ == "__main__":
    unittest.main()
