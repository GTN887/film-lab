#!/usr/bin/env python3
"""Effects Desk: descriptive presets, no credit meter, Comfy stub honesty."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.effects import (
    EFFECT_PRESETS,
    compose_effect_prompt,
    desk_size,
    effects_shelf_html,
    engine_markdown,
    preset_by_label,
    workflow_is_live,
    workflow_stub_note,
)
from film_lab.hub import FORBIDDEN_BRANDS


class EffectsDeskTests(unittest.TestCase):
    def test_descriptive_presets_and_no_brands(self) -> None:
        labels = [p.label.lower() for p in EFFECT_PRESETS]
        self.assertIn("floating fall", labels)
        self.assertIn("high flip", labels)
        self.assertIn("studio slide", labels)
        self.assertTrue(any("melt" in lab for lab in labels))
        blob = effects_shelf_html() + engine_markdown()
        blob += " ".join(f"{p.label} {p.blurb} {p.motion}" for p in EFFECT_PRESETS)
        low = blob.lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, low, banned)
        self.assertIn("no free-gens counter", low)
        self.assertNotIn("credits remaining", low)
        self.assertNotIn("credits left", low)
        self.assertIn("davinci", low)
        self.assertIn("after effects", low)

    def test_prompt_toggle_and_optional_plates(self) -> None:
        preset = preset_by_label("Floating fall")
        base = compose_effect_prompt(preset)
        self.assertIn("floating fall", base.lower())
        self.assertIn("18+", base)
        self.assertNotIn("keep the bottle", base.lower())
        extra = compose_effect_prompt(
            preset,
            extra="Keep the bottle.",
            use_extra=True,
            has_location=True,
            has_product=True,
        )
        self.assertIn("keep the bottle", extra.lower())
        self.assertIn("location plate", extra.lower())
        self.assertIn("product", extra.lower())
        off = compose_effect_prompt(preset, extra="Keep the bottle.", use_extra=False)
        self.assertNotIn("keep the bottle", off.lower())

    def test_stub_workflow_is_not_live(self) -> None:
        fall = preset_by_label("Floating fall")
        self.assertFalse(workflow_is_live(fall))
        note = workflow_stub_note(fall).lower()
        self.assertIn("workflows/effects", note)
        self.assertIn("svd", note)
        self.assertIn("8188", note)

    def test_desk_sizes(self) -> None:
        self.assertEqual(desk_size("9:16", "720"), (720, 1280))
        self.assertEqual(desk_size("16:9", "1080"), (1920, 1080))


if __name__ == "__main__":
    unittest.main()
