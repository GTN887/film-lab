#!/usr/bin/env python3
"""Home hub cards, looks shelf, take variants — no third-party brand names."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.bridge import TOOL_MANIFEST, bridge_markdown
from film_lab.hub import (
    FORBIDDEN_BRANDS,
    HUB_CARDS,
    EFFECT_LOOKS,
    effect_by_label,
    craft_shelf_html,
    hub_cards_html,
    hub_chrome_html,
    hub_hero_html,
    local_lot_html,
    local_lot_markdown,
    looks_shelf_html,
)
from film_lab.project import Project
from film_lab.shot_card import ShotCard
from film_lab.variations import expand_takes


class HubCopyTests(unittest.TestCase):
    def test_studio_and_craft_desks_and_no_foreign_brands(self) -> None:
        titles = [c.title for c in HUB_CARDS]
        self.assertEqual(
            titles,
            [
                "AI Production Pipeline",
                "Still Desk",
                "Take Board",
                "Director Bridge",
                "Cinema Desk",
                "Director Brain",
                "UGC Ads Desk",
                "Character Consistency",
                "Lighting Desk",
                "Score Desk",
                "Voice Desk",
                "Effects Desk",
                "Pose Desk",
                "3D Set Desk",
                "Mark & Direct",
            ],
        )
        blob = " ".join(
            f"{c.title} {c.kicker} {c.blurb} {c.button} {c.tab_id}" for c in HUB_CARDS
        )
        blob += hub_cards_html()
        blob += hub_hero_html()
        blob += hub_chrome_html()
        blob += looks_shelf_html()
        blob += craft_shelf_html()
        from film_lab.effects import effects_shelf_html, engine_markdown as fx_engine

        blob += effects_shelf_html()
        blob += fx_engine()
        blob += local_lot_html()
        blob += " ".join(f"{e.label} {e.blurb}" for e in EFFECT_LOOKS)
        blob += bridge_markdown()
        lower = blob.lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, lower, banned)
        hero = hub_hero_html().lower()
        self.assertIn("film school", hero)
        self.assertIn("film lab", hero)
        self.assertNotIn("unlimited", hero)
        self.assertNotIn("% off", hero)
        self.assertNotIn("upgrade", hero)
        chrome = hub_chrome_html().lower()
        self.assertIn("local only", chrome)
        self.assertIn("film school", chrome)
        self.assertIn("adults 18+", chrome)
        self.assertIn("no credits", chrome)
        pipeline = next(c for c in HUB_CARDS if c.tab_id == "pipeline")
        self.assertEqual(pipeline.title, "AI Production Pipeline")
        self.assertEqual(pipeline.button, "Open Pipeline")
        self.assertIn("enhance", pipeline.kicker.lower())
        self.assertIn("pose", pipeline.kicker.lower())
        self.assertIn("animate", pipeline.kicker.lower())
        self.assertIn("same still", pipeline.blurb.lower())
        self.assertIn("no re-upload", pipeline.blurb.lower())
        self.assertIn("back to home", pipeline.blurb.lower())
        self.assertNotIn("ken burns", pipeline.blurb.lower())
        self.assertFalse(any(c.tab_id == "motion" for c in HUB_CARDS))
        self.assertEqual(
            [c.index for c in HUB_CARDS],
            ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15"],
        )
        self.assertIn("local finish", looks_shelf_html().lower())
        css = (ROOT / "film_lab" / "studio.css").read_text(encoding="utf-8")
        self.assertIn("--fl-gold", css)
        self.assertIn("--fl-cyan", css)
        self.assertIn("--fl-purple", css)
        self.assertGreater(len(css), 2000)
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, css.lower(), banned)
        self.assertNotIn("#d1fe17", css.lower())
        self.assertNotIn("#e4c37a", css.lower())
        hero = hub_hero_html().lower()
        self.assertIn("filming-mode toggle", hero)
        self.assertIn("one film lab theme", hero)
        takes = next(c for c in HUB_CARDS if c.tab_id == "takes")
        cinema = next(c for c in HUB_CARDS if c.tab_id == "cinema")
        mark = next(c for c in HUB_CARDS if c.tab_id == "mark")
        self.assertEqual(takes.tone, "#3a2468")
        self.assertEqual(cinema.tone, "#322058")
        self.assertEqual(mark.tone, "#2a1848")
        for card in HUB_CARDS:
            self.assertNotIn(card.tone.lower(), {"#2c1c1c", "#241c1c", "#3a2e1c", "#3a2814"})

    def test_effect_shelf(self) -> None:
        look = effect_by_label("Warm lamp hold")
        self.assertTrue(look.lut.endswith(".cube"))
        self.assertEqual(look.vfx, "grain")

    def test_local_lot_lists_folder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "projects"
            Project.create("lot-one", data_root=root, description="Private study")
            md = local_lot_markdown(data_root=root)
            html = local_lot_html(data_root=root)
            self.assertIn("lot-one", md)
            self.assertIn("lot-one", html)
            self.assertIn("this machine", md.lower())
            self.assertIn("this machine", html.lower())
            self.assertNotIn("explore community", md.lower())
            self.assertNotIn("explore community", html.lower())


class TakeBoardTests(unittest.TestCase):
    def test_expand_takes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("takes", data_root=Path(tmp) / "projects")
            source = ShotCard(
                name="Lamp hold",
                camera_move="slow push-in",
                seed=10,
                subject_motion_strength=0.3,
            )
            project.save_shot(source)
            created = expand_takes(
                project,
                source,
                count=3,
                vary_seed=True,
                vary_camera=True,
                vary_motion=True,
            )
            self.assertEqual(len(created), 3)
            self.assertEqual(len({s.id for s in created}), 3)
            self.assertTrue(any(s.camera_move != source.camera_move for s in created))
            self.assertTrue(all(s.seed is not None for s in created))

    def test_bridge_tools(self) -> None:
        names = {t["name"] for t in TOOL_MANIFEST}
        self.assertIn("generate_shot", names)
        self.assertIn("write_draft", names)
        self.assertIn("list_connectors", names)
        self.assertIn("localhost", bridge_markdown().lower() + "127.0.0.1")
        md = bridge_markdown().lower()
        self.assertIn("claude", md)
        self.assertIn("claude code", md)
        self.assertIn("grok bot", md)
        self.assertIn("openclaw", md)
        self.assertIn("hermes", md)
        self.assertIn("cursor", md)
        self.assertIn("mcp", md)
        self.assertIn("cli", md)


if __name__ == "__main__":
    unittest.main()
