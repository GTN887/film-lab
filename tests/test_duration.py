#!/usr/bin/env python3
"""Motion Desk duration lock + regenerate seed helper."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.constants import DEFAULT_DURATION, MAX_DURATION, MIN_DURATION
from film_lab.duration import (
    DEFAULT_DURATION_PRESET,
    DURATION_PRESETS,
    is_long_duration,
    parse_duration_preset,
)
from film_lab.hub import FORBIDDEN_BRANDS
from film_lab.ui_handlers import _form_with_duration, _new_regen_seed


class DurationLockTests(unittest.TestCase):
    def test_presets_and_long_flag(self) -> None:
        self.assertEqual(
            list(DURATION_PRESETS),
            ["5s", "10s", "15s", "20s", "30s", "1 min", "2 min"],
        )
        self.assertEqual(DEFAULT_DURATION_PRESET, "5s")
        self.assertEqual(DEFAULT_DURATION, 5.0)
        self.assertEqual(MIN_DURATION, 2.0)
        self.assertEqual(MAX_DURATION, 30.0)
        self.assertFalse(parse_duration_preset("5s").is_long)
        self.assertFalse(parse_duration_preset("30s").is_long)
        self.assertTrue(parse_duration_preset("1 min").is_long)
        self.assertTrue(parse_duration_preset("2 min").is_long)
        self.assertTrue(is_long_duration("60s reel"))
        self.assertEqual(parse_duration_preset("1 min").seconds, 60)
        self.assertEqual(parse_duration_preset("2 min").seconds, 120)

    def test_form_applies_short_not_long(self) -> None:
        form = [None] * 28
        form[4] = 3.0
        short = _form_with_duration(form, "20s")
        self.assertEqual(short[4], 20.0)
        long = _form_with_duration(form, "1 min")
        self.assertEqual(long[4], 3.0)

    def test_regen_seed_changes(self) -> None:
        seeds = {_new_regen_seed() for _ in range(8)}
        self.assertTrue(all(1 <= n <= 2_147_483_647 for n in seeds))
        self.assertGreaterEqual(len(seeds), 2)

    def test_docs_mention_recovery(self) -> None:
        crash = (ROOT / "docs" / "CRASH_RECOVERY.md").read_text(encoding="utf-8").lower()
        self.assertIn("8188", crash)
        self.assertIn("oom", crash)
        self.assertIn("regenerate", crash)
        self.assertIn("cinema desk", crash)
        self.assertIn("davinci", crash)
        self.assertIn("launcher", crash)
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, crash)


if __name__ == "__main__":
    unittest.main()
