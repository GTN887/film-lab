#!/usr/bin/env python3
"""Animate stage copy: Grok-like UX, never a cloud NSFW reject."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.animate_ux import (
    CLOUD_SAFETY_PHRASES,
    default_ref_still,
    generating_label,
    rewrite_cloud_safety,
    sanitize_motion_error,
    toast_html,
)
from film_lab.generators.comfyui_i2v import DEFAULT_NEGATIVE, INSTALL_HINT
from film_lab.hub import FORBIDDEN_BRANDS
from film_lab.motion_path import motion_engine_markdown


class AnimateUxTests(unittest.TestCase):
    def test_toast_is_technical_not_safety_gate(self) -> None:
        html = toast_html("Cannot reach ComfyUI at http://127.0.0.1:8188")
        self.assertIn("fl-toast", html)
        self.assertIn("8188", html)
        lower = html.lower()
        for phrase in CLOUD_SAFETY_PHRASES:
            self.assertNotIn(phrase, lower)
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, lower)

    def test_sanitize_rewrites_cloud_safety_copy(self) -> None:
        rewritten = sanitize_motion_error(
            "Cannot Animate. Request rejected due to safety guidelines."
        )
        lower = rewritten.lower()
        self.assertIn("no nsfw filter", lower)
        self.assertIn("18+", lower)
        self.assertNotIn("cannot animate", lower)
        self.assertNotIn("safety guidelines", lower)

    def test_rewrite_feed_copy_is_not_a_reject(self) -> None:
        rewritten = rewrite_cloud_safety(
            "Cannot Animate. Request rejected due to safety guidelines."
        )
        low = rewritten.lower()
        self.assertIn("cinematic", low)
        self.assertNotIn("cannot animate", low)
        self.assertNotIn("safety guidelines", low)

    def test_generating_pill(self) -> None:
        self.assertEqual(generating_label(12), "Generating… 12%")
        self.assertEqual(generating_label(140), "Generating… 99%")

    def test_negative_is_not_an_nsfw_gate(self) -> None:
        low = DEFAULT_NEGATIVE.lower()
        self.assertNotIn("nsfw", low)
        self.assertNotIn("nude", low)
        self.assertNotIn("explicit", low)
        self.assertIn("child", low)

    def test_install_hint_has_no_safety_reject(self) -> None:
        low = INSTALL_HINT.lower() + motion_engine_markdown().lower()
        for phrase in CLOUD_SAFETY_PHRASES:
            self.assertNotIn(phrase, low)

    def test_default_ref_from_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            still = Path(tmp) / "alison_bradley_ref.jpg"
            still.write_bytes(b"fake")
            import os

            os.environ["FILM_LAB_REF_STILL"] = str(still)
            try:
                found = default_ref_still()
                self.assertEqual(found, still)
            finally:
                os.environ.pop("FILM_LAB_REF_STILL", None)


if __name__ == "__main__":
    unittest.main()
