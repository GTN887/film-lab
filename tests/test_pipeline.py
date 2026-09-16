#!/usr/bin/env python3
"""AI Production Pipeline — one desk, same shot, no re-upload."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.hub import FORBIDDEN_BRANDS, HUB_CARDS
from film_lab.pipeline import STEPS, arm_shot, step_visibilities, stepper_html
from film_lab.writing import WRITING_MODES


class PipelineDeskTests(unittest.TestCase):
    def test_three_steps_same_shot(self) -> None:
        self.assertEqual(STEPS, ("Enhance", "Pose", "Animate"))
        self.assertEqual(step_visibilities("Enhance"), (True, False, False))
        self.assertEqual(step_visibilities("Pose"), (False, True, False))
        self.assertEqual(step_visibilities("Animate"), (False, False, True))
        self.assertEqual(step_visibilities("nope"), (True, False, False))
        path, attached, idea, intent = arm_shot("/tmp/shot.png", "slow kiss", "")
        self.assertEqual(path, "/tmp/shot.png")
        self.assertEqual(attached, "/tmp/shot.png")
        self.assertEqual(idea, "slow kiss")
        self.assertEqual(intent, "slow kiss")
        posed, again, _idea, line = arm_shot("/tmp/shot.png", "slow kiss", "dense line")
        self.assertEqual(posed, again)
        self.assertEqual(line, "dense line")
        html = stepper_html("Pose").lower()
        self.assertIn("enhance", html)
        self.assertIn("pose", html)
        self.assertIn("animate", html)
        self.assertIn("same shot", html)
        self.assertIn("no re-upload", html)
        self.assertIn("is-on", html)

    def test_hub_card_opens_pipeline_not_a_sixteenth(self) -> None:
        self.assertEqual(len(HUB_CARDS), 15)
        self.assertEqual(len(WRITING_MODES), 5)
        first = HUB_CARDS[0]
        self.assertEqual(first.tab_id, "pipeline")
        self.assertEqual(first.title, "AI Production Pipeline")
        self.assertEqual(first.button, "Open Pipeline")
        self.assertIn("no re-upload", first.blurb.lower())
        self.assertIn("back to home", first.blurb.lower())
        self.assertFalse(any(c.tab_id == "motion" for c in HUB_CARDS))
        blob = " ".join(f"{c.title} {c.kicker} {c.blurb}" for c in HUB_CARDS)
        blob += stepper_html()
        low = blob.lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, low, banned)

    def test_app_wires_hub_to_same_shot_workspace(self) -> None:
        src = (ROOT / "app.py").read_text(encoding="utf-8")
        ast.parse(src)
        self.assertIn('with gr.Tab("AI Production Pipeline", id="pipeline"', src)
        self.assertIn('with gr.Tab("Motion Desk", id="motion")', src)
        self.assertIn('open_hub_tab("pipeline")', src)
        self.assertIn('hero_motion = gr.Button("Open Pipeline"', src)
        self.assertIn('pipe_home_btn = gr.Button("Back to Home"', src)
        self.assertIn('label="Enhance | Pose | Animate"', src)
        self.assertIn("pipe_still", src)
        self.assertIn("arm_pipeline_shot", src)
        self.assertIn("generate_amd_now", src)
        self.assertIn("same shot", src)
        self.assertIn("no re-upload", src)
        start = src.find('with gr.Tab("AI Production Pipeline"')
        end = src.find('with gr.Tab("Motion Desk"', start + 1)
        self.assertGreater(start, 0)
        self.assertGreater(end, start)
        chunk = src[start:end]
        self.assertIn("pipe_still", chunk)
        self.assertIn("pipe_enhance_btn", chunk)
        self.assertIn("pipe_lighting", chunk)
        self.assertIn("pipe_aspect", chunk)
        self.assertIn("pipe_quality", chunk)
        self.assertIn("filterable=True", chunk)
        self.assertIn("None — skip", chunk)
        self.assertIn("1440p", chunk)
        self.assertIn("2.39:1 cinema scope", chunk)
        self.assertIn("1.85:1", chunk)
        self.assertIn("neon noir", chunk)
        self.assertIn("cinematic pack", chunk)
        self.assertIn("prestige-TV night", chunk)
        self.assertIn("space-opera rim", chunk)
        self.assertNotIn("pipe_aspect = gr.Radio", chunk)
        self.assertNotIn("pipe_quality = gr.Radio", chunk)
        self.assertNotIn("pipe_lighting = gr.Radio", chunk)
        self.assertIn("pipe_apply_pose", chunk)
        self.assertIn("pipe_animate_btn", chunk)
        self.assertEqual(chunk.count("gr.Image("), 2)
        self.assertNotIn("file_count", chunk)
        low = src.lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, low, banned)


if __name__ == "__main__":
    unittest.main()
