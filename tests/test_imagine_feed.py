#!/usr/bin/env python3
"""Unified Motion Desk feed: user command, visible enhance, then clip slot."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.animate_ux import CLOUD_SAFETY_PHRASES
from film_lab.hub import FORBIDDEN_BRANDS
from film_lab.imagine_feed import (
    FeedTurn,
    append_turn,
    ref_chip_html,
    render_feed,
)


class ImagineFeedTests(unittest.TestCase):
    def test_empty_feed_explains_add_prompt_and_send(self) -> None:
        html = render_feed([])
        low = html.lower()
        self.assertIn("add prompt", low)
        self.assertIn("send", low)
        self.assertIn("continuity", low)
        self.assertIn("lighting on skin", low)
        self.assertIn("micro-motions", low)
        self.assertIn("underneath", low)

    def test_order_is_user_then_enhancement(self) -> None:
        html = render_feed(
            [
                FeedTurn(
                    user_text="slow kiss",
                    enhanced_paragraph="Hold continuity with the still. Warm lamp on skin.",
                    ref_name="alison_bradley_ref.jpg",
                )
            ],
            generating=True,
        )
        user_at = html.find("slow kiss")
        enhance_at = html.find("Prompt Enhancement")
        para_at = html.find("Hold continuity")
        note_at = html.find("Clip generating")
        self.assertGreater(user_at, 0)
        self.assertGreater(enhance_at, user_at)
        self.assertGreater(para_at, enhance_at)
        self.assertGreater(note_at, para_at)
        self.assertIn("Ref attached", html)
        self.assertIn("alison_bradley_ref.jpg", html)
        self.assertIn("Clip generating", html)

    def test_escapes_html_and_rewrites_safety(self) -> None:
        html = render_feed(
            [
                {
                    "user_text": "<script>alert(1)</script>",
                    "enhanced_paragraph": "Cannot Animate. Request rejected due to safety guidelines.",
                }
            ]
        )
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        low = html.lower()
        for phrase in CLOUD_SAFETY_PHRASES:
            self.assertNotIn(phrase, low)
        self.assertIn("no safety lecture", low)
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, low)

    def test_append_keeps_recent_turns(self) -> None:
        history = []
        for i in range(10):
            history = append_turn(history, user_text=f"cmd {i}", paragraph=f"para {i}")
        self.assertEqual(len(history), 8)
        self.assertEqual(history[0]["user_text"], "cmd 2")
        self.assertEqual(history[-1]["enhanced_paragraph"], "para 9")

    def test_ref_chip(self) -> None:
        empty = ref_chip_html("")
        self.assertIn("Add Prompt", empty)
        chip = ref_chip_html("/tmp/alison_bradley_ref.jpg")
        self.assertIn("Ref attached", chip)
        self.assertIn("alison_bradley_ref.jpg", chip)


if __name__ == "__main__":
    unittest.main()
