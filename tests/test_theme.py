#!/usr/bin/env python3
"""One Film Lab theme: purple + soft cyan. Regular vs 18+ is mode, not a skin."""

from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.effects import EFFECT_PRESETS
from film_lab.filming import SAFETY_COPY
from film_lab.hub import HUB_CARDS, hub_hero_html
from film_lab.mark import FILL, STROKE
from film_lab.pose import JOINT_COLOR, LIMB_COLOR
from film_lab.product import STROKE as PRODUCT_STROKE
from film_lab.prompt_still import GOLD
from film_lab.ui_handlers import apply_filming_mode_ui


class ThemeLockTests(unittest.TestCase):
    def test_one_purple_cyan_theme(self) -> None:
        css = (ROOT / "film_lab" / "studio.css").read_text(encoding="utf-8")
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("--fl-purple: #8b6cff", css)
        self.assertIn("--fl-cyan: #7ee8e8", css)
        self.assertIn("--fl-gold: #7ee8e8", css)
        self.assertIn('primary_hue="violet"', app)
        self.assertIn('button_primary_background_fill="#7ee8e8"', app)
        self.assertNotIn('primary_hue="amber"', app)
        self.assertNotIn("#e4c37a", app)
        self.assertNotIn("#e4c37a", css)
        for banned in ("darkroom", "theme-explicit", "fl-explicit-skin", "theme-regular"):
            self.assertNotIn(banned, css.lower())
            self.assertNotIn(banned, app.lower())

    def test_regular_vs_explicit_is_mode_not_theme(self) -> None:
        src = inspect.getsource(apply_filming_mode_ui)
        self.assertIn("Never swap CSS", src)
        self.assertNotIn("studio.css", src)
        self.assertNotIn("primary_hue", src)
        self.assertNotIn("elem_classes", src)
        self.assertIn("filming-mode toggle", SAFETY_COPY.lower())
        self.assertIn("one purple", SAFETY_COPY.lower())
        hero = hub_hero_html().lower()
        self.assertIn("filming-mode toggle", hero)
        self.assertIn("not two apps", hero)

    def test_desks_share_purple_not_red_darkroom(self) -> None:
        red_darkroom = {
            "#2c1c1c",
            "#241c1c",
            "#3a2e1c",
            "#3a2814",
            "#281c1c",
            "#2a2418",
            "#32281c",
        }
        for card in HUB_CARDS:
            self.assertNotIn(card.tone.lower(), red_darkroom, card.title)
            hex6 = card.tone.lstrip("#")
            r, g, b = int(hex6[0:2], 16), int(hex6[2:4], 16), int(hex6[4:6], 16)
            self.assertGreaterEqual(b, r, f"{card.title} tone {card.tone} reads red, not purple")
        for preset in EFFECT_PRESETS:
            self.assertNotIn(preset.tone.lower(), red_darkroom, preset.label)
            hex6 = preset.tone.lstrip("#")
            r, g, b = int(hex6[0:2], 16), int(hex6[2:4], 16), int(hex6[4:6], 16)
            self.assertGreaterEqual(b, r, f"{preset.label} tone {preset.tone} reads red, not purple")

    def test_overlays_use_cyan_purple(self) -> None:
        self.assertEqual(LIMB_COLOR[:3], (139, 108, 255))
        self.assertEqual(JOINT_COLOR[:3], (126, 232, 232))
        self.assertEqual(STROKE[:3], (139, 108, 255))
        self.assertEqual(FILL[:3], (126, 232, 232))
        self.assertEqual(PRODUCT_STROKE[:3], (126, 232, 232))
        self.assertEqual(GOLD[:3], (126, 232, 232))
