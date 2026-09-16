#!/usr/bin/env python3
"""Quality lock: polished desks, working Animate path, no branded clones."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.animate_ux import CLOUD_SAFETY_PHRASES, rewrite_cloud_safety
from film_lab.effects import compose_effect_prompt, preset_by_label, preset_detail_md
from film_lab.extend import clips_needed, stitched_length
from film_lab.generators.comfyui_i2v import DEFAULT_NEGATIVE
from film_lab.hub import FORBIDDEN_BRANDS, HUB_CARDS, hub_hero_html
from film_lab.imagine_feed import render_feed
from film_lab.motion_path import generate_motion_mp4, motion_engine_markdown


class QualityLockTests(unittest.TestCase):
    def test_app_parses_and_primary_copy(self) -> None:
        src = (ROOT / "app.py").read_text(encoding="utf-8")
        ast.parse(src)
        self.assertIn("Add Prompt", src)
        self.assertIn("Send", src)
        self.assertIn("Download MP4 (DaVinci / After Effects)", src)
        self.assertIn("Advanced · Ken Burns", src)
        self.assertIn("Effects Desk", src)
        self.assertIn("Pose Desk", src)
        self.assertIn("Pose adjust", src)
        self.assertIn("Director Note", src)
        self.assertIn("World Note", src)
        self.assertIn("3D Set", src)
        self.assertIn("LOCKED Environment", src)
        self.assertIn("look-around", src)
        self.assertIn("data/projects", src)
        self.assertIn("sets/", src)
        self.assertIn("takes/", src)
        self.assertIn("Regular", src)
        self.assertIn("18+ Explicit", src)
        self.assertIn("aerial", src)
        self.assertIn("Mark & Direct", src)
        self.assertIn("Pointer", src)
        self.assertIn("Go-to", src)
        self.assertIn("bathroom", src)
        self.assertIn("undress through motion", src)
        self.assertIn("Revise this take", src)
        self.assertIn("60s reel", src)
        self.assertIn("Regenerate", src)
        self.assertIn("1 min", src)
        self.assertIn("2 min", src)
        self.assertIn("480p", src)
        self.assertIn("1440p", src)
        self.assertIn("4K", src)
        self.assertIn("2.39:1 cinema scope", src)
        self.assertIn("1.85:1", src)
        self.assertIn("4:3", src)
        self.assertIn("frame icon", src)
        self.assertIn("aspect_dropdown_choices", src)
        self.assertIn("RX 5600 XT", src)
        self.assertIn("Quality program", src)
        self.assertIn("AMD, not NVIDIA", src)
        self.assertIn("Environment lock", src)
        self.assertIn("Character sheet", src)
        self.assertIn("Fix this frame", src)
        self.assertIn("Directing — changes will make a new take", src)
        self.assertIn("Exit Direct", src)
        self.assertIn("typed or voice", src)
        self.assertIn("Mic — speak", src)
        self.assertIn("same note", src)
        self.assertIn("4:5", src)
        self.assertIn("21:9", src)
        self.assertIn("3:2", src)
        self.assertIn("2:3", src)
        self.assertIn("Generate still", src)
        self.assertIn("Product still", src)
        self.assertIn("Character Bible", src)
        self.assertIn("Import Word / PDF", src)
        self.assertIn("Export Word / PDF", src)
        self.assertIn("Animate", src)
        self.assertIn("AI Production Pipeline", src)
        self.assertIn("Back to Home", src)
        self.assertIn("same shot", src)
        self.assertIn("no re-upload", src)
        self.assertIn("Any still", src)
        self.assertIn("No marketplace", src)
        self.assertIn("Opens alone", src)
        self.assertIn("Pick up and pour", src)
        self.assertIn("Works offline for local generation", src)
        self.assertIn("Online optional", src)
        self.assertIn("Safe mode", src)
        self.assertIn("Repair", src)
        self.assertIn("START_FILM_LAB.bat", src)
        self.assertIn("Install Film Lab", src)
        self.assertIn("UNINSTALL_FILM_LAB.bat", src)
        self.assertIn("patch in place", src)
        self.assertIn("Fuse", src)
        self.assertIn("Import", src)
        self.assertIn("beat sheet", src)
        self.assertIn("PowerPoint", src)
        self.assertIn("Excel", src)
        self.assertIn("plain text", src)
        self.assertIn(".xlsx", src)
        self.assertIn(".pptx", src)
        self.assertIn("Plan shots", src)
        self.assertIn("Family Genetics", src)
        self.assertIn("What would their kids look like?", src)
        self.assertIn("micro-expression", src)
        self.assertIn("pick up book", src)
        self.assertIn("Behavior (full human)", src)
        self.assertIn("Enter dream", src)
        self.assertIn("Dream / Lucid", src)
        self.assertIn("sleep → dream → wake", src)
        self.assertIn("Dream about", src)
        self.assertIn("Actor A", src)
        self.assertIn("Thought bubble", src)
        self.assertIn("comic bubble", src)
        self.assertIn("Inner vision", src)
        self.assertIn("daydream", src)
        self.assertIn("Rembrandt", src)
        self.assertIn("overcast", src)
        self.assertIn("None — skip", src)
        self.assertIn("neon noir", src)
        self.assertIn("hard noon sun", src)
        self.assertIn("practical bedside lamp", src)
        self.assertIn("pick one", src)
        self.assertIn("Save Library", src)
        self.assertIn("OneDrive", src)
        self.assertIn("Google Drive", src)
        self.assertIn("local-first", src)
        self.assertIn("anamorphic night", src)
        self.assertIn("teal & orange", src)
        self.assertIn("prestige-TV night", src)
        self.assertIn("space-opera rim", src)
        self.assertNotIn("euphoria", src.lower())
        self.assertNotIn("jedi", src.lower())
        self.assertNotIn("Generate video (SVD-XT · AMD)", src)
        self.assertNotIn("#d1fe17", src)
        low = src.lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, low, banned)

    def test_css_is_studio_not_default_gradio(self) -> None:
        css = (ROOT / "film_lab" / "studio.css").read_text(encoding="utf-8")
        self.assertIn("--fl-gold", css)
        self.assertIn("--fl-cyan", css)
        self.assertIn("--fl-purple", css)
        self.assertIn("#7ee8e8", css)
        self.assertIn("#8b6cff", css)
        self.assertIn(".fl-imagine", css)
        self.assertIn(".fl-feed", css)
        self.assertIn(".fl-fx-presets", css)
        self.assertGreater(len(css), 8000)
        self.assertNotIn("#d1fe17", css.lower())
        self.assertNotIn("#e4c37a", css.lower())
        self.assertNotIn("darkroom", css.lower())
        self.assertNotIn("theme-explicit", css.lower())
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, css.lower(), banned)

    def test_hub_has_effects_and_motion(self) -> None:
        titles = [c.title for c in HUB_CARDS]
        self.assertIn("AI Production Pipeline", titles)
        self.assertNotIn("Motion Desk", titles)
        src = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn('with gr.Tab("Motion Desk"', src)
        self.assertIn('with gr.Tab("AI Production Pipeline"', src)
        self.assertIn("Effects Desk", titles)
        self.assertIn("Pose Desk", titles)
        self.assertIn("3D Set Desk", titles)
        self.assertIn("Mark & Direct", titles)
        hero = hub_hero_html().lower()
        self.assertIn("film lab", hero)
        self.assertNotIn("subscription", hero.replace("not a subscription", ""))
        self.assertNotIn("unlimited", hero)

    def test_animate_never_auto_ken_burns(self) -> None:
        self.assertFalse(generate_motion_mp4.__kwdefaults__["allow_fallback"])
        src = (ROOT / "film_lab" / "motion_path.py").read_text(encoding="utf-8")
        self.assertIn("allow_fallback: bool = False", src)
        engine = motion_engine_markdown().lower()
        self.assertIn("advanced", engine)
        self.assertIn("svd", engine)

    def test_no_nsfw_gate(self) -> None:
        low = DEFAULT_NEGATIVE.lower()
        self.assertNotIn("nsfw", low)
        self.assertNotIn("nude", low)
        rewritten = rewrite_cloud_safety(
            "Cannot Animate. Request rejected due to safety guidelines."
        )
        for phrase in CLOUD_SAFETY_PHRASES:
            self.assertNotIn(phrase, rewritten.lower())

    def test_feed_and_effects_and_reel_math(self) -> None:
        empty = render_feed([]).lower()
        self.assertIn("add prompt", empty)
        self.assertIn("send", empty)
        fall = preset_by_label("Floating fall")
        prompt = compose_effect_prompt(fall, extra="keep the bottle", use_extra=True)
        self.assertIn("18+", prompt)
        detail = preset_detail_md("Floating fall").lower()
        self.assertIn("floating fall", detail)
        self.assertGreaterEqual(stitched_length(clips_needed(60)), 60)
        self.assertGreaterEqual(stitched_length(clips_needed(120)), 120)

    def test_character_bible_word_pdf_not_excel(self) -> None:
        src = (ROOT / "app.py").read_text(encoding="utf-8")
        start = src.find('with gr.Tab("Character Consistency"')
        end = src.find('with gr.Tab("Pose Desk"', start + 1)
        self.assertGreater(start, 0)
        self.assertGreater(end, start)
        chunk = src[start:end]
        self.assertIn("Import Word / PDF", chunk)
        self.assertIn("Export Word / PDF", chunk)
        self.assertIn('file_types=[".docx", ".pdf"]', chunk)
        self.assertIn('["Word", "PDF"]', chunk)
        self.assertNotIn(".xlsx", chunk)
        self.assertNotIn(".pptx", chunk)
        self.assertNotIn("plain text", chunk)
        brain = src[src.find('with gr.Tab("Director Brain"') : src.find('with gr.Tab("Motion Desk"')]
        self.assertIn("Excel", brain)
        self.assertIn(".xlsx", brain)


if __name__ == "__main__":
    unittest.main()
