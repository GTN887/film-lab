#!/usr/bin/env python3
"""Lighting chips, score cues, cinematic voice, local video-path notes."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.characters import compose_local_prompt, seed_alison_bradley
from film_lab.hub import FORBIDDEN_BRANDS
from film_lab.lighting import (
    CINEMA_TITLES,
    LIGHTING_PRESETS,
    SKIP_LABEL,
    STUDIO_TITLES,
    expand_lighting,
    find_preset,
    is_lighting_skipped,
    lighting_bible_line,
    lighting_prompt_bit,
    mentor_markdown,
    preset_choices,
)
from film_lab.music import new_cue, render_bed, score_stack_markdown
from film_lab.project import Project
from film_lab.shot_card import ShotCard
from film_lab.video_tools import VIDEO_PATHS, video_tools_markdown
from film_lab.voice import expand_pause_markup, synthesize_line, synthesize_takes, voice_stack_markdown
from film_lab.writing import bible_block


def _no_brands(blob: str) -> None:
    lower = blob.lower()
    for banned in FORBIDDEN_BRANDS:
        if banned in lower:
            raise AssertionError(banned)


class CraftDeskTests(unittest.TestCase):
    def test_lighting_presets_and_injection(self) -> None:
        self.assertGreaterEqual(len(LIGHTING_PRESETS), 24)
        titles = {p.title.lower() for p in LIGHTING_PRESETS}
        for needed in (*STUDIO_TITLES, *CINEMA_TITLES):
            self.assertIn(needed.lower(), titles)
        for needed in (
            "key",
            "fill",
            "three-point",
            "day",
            "night",
            "motivated practicals",
            "warm lamp bedroom",
            "practical bedside lamp",
        ):
            self.assertIn(needed, titles)
        blob = " ".join(f"{p.title} {p.chip} {p.mentor}" for p in LIGHTING_PRESETS).lower()
        for stolen in ("euphoria", "jedi", "star wars", "lightsaber", "sora", "kling"):
            self.assertNotIn(stolen, blob, stolen)
        self.assertTrue(is_lighting_skipped(SKIP_LABEL))
        self.assertEqual(expand_lighting(SKIP_LABEL), "")
        self.assertEqual(expand_lighting(""), "")
        self.assertEqual(lighting_bible_line(""), "")
        self.assertEqual(preset_choices()[0], SKIP_LABEL)
        self.assertIn("none — skip", preset_choices()[0].lower())
        self.assertEqual(expand_lighting("Hard noon sun"), expand_lighting("hard noon"))
        self.assertIn("overhead", expand_lighting("Hard noon sun").lower())
        self.assertIn("cobalt", expand_lighting("Blue hour / twilight").lower())
        self.assertIn("nightstand", mentor_markdown("Practical bedside lamp").lower())
        self.assertIn("magenta", expand_lighting("Neon noir").lower())
        self.assertIn("wet", expand_lighting("Rain / wet overcast").lower())
        self.assertEqual(find_preset("candle").key, "candle")
        self.assertEqual(find_preset("low-key").key, "low_key")
        self.assertEqual(find_preset("rim").key, "rim")
        self.assertIn("optional", mentor_markdown(SKIP_LABEL).lower())
        self.assertIn("skip", mentor_markdown(SKIP_LABEL).lower())
        chip = expand_lighting("Rembrandt")
        self.assertIn("triangle", chip.lower())
        note = mentor_markdown("Warm lamp bedroom")
        self.assertIn("18+", note)
        self.assertEqual(find_preset("moonlight").key, "moonlight")
        self.assertEqual(find_preset("teal & orange").key, "teal_orange")
        self.assertEqual(find_preset("prestige-TV night").key, "prestige_night")
        self.assertEqual(find_preset("space-opera rim").key, "space_opera_rim")
        self.assertIn("shafts", expand_lighting("Volumetric god-rays").lower())
        _no_brands(note + chip + lighting_bible_line("moonlight"))
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("lamp", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            project.set_lighting("Low-key")
            shot = ShotCard(name="Hold", lighting="Low-key", character_ids=["alison"])
            prompt = compose_local_prompt(shot, project)
            self.assertIn("low-key", prompt.lower())
            bible = bible_block(project, ["alison"])
            self.assertIn("Lighting lock", bible)
            self.assertIn("low-key", bible.lower())
            bare = ShotCard(name="Skip", lighting="", character_ids=["alison"])
            self.assertEqual(lighting_prompt_bit(bare.lighting), "")
            self.assertNotIn("lighting: key light only", compose_local_prompt(bare, project).lower())
            project.set_lighting(SKIP_LABEL)
            self.assertEqual(project.active_lighting, "")
            self.assertEqual(lighting_bible_line(project.active_lighting), "")

    def test_score_import_first_and_synth(self) -> None:
        md = score_stack_markdown().lower()
        self.assertIn("import", md)
        self.assertIn("zero", md)
        self.assertNotIn("suno", md)
        _no_brands(md)
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("score", data_root=Path(tmp) / "projects")
            cue = new_cue("after", mood="afterglow", length=1.0, intensity=0.2)
            path = render_bed(project, cue)
            self.assertTrue(path.is_file())
            self.assertGreater(path.stat().st_size, 44)

    def test_voice_pauses_and_takes(self) -> None:
        spoken = expand_pause_markup("Stay. [2s] Don't / move...")
        self.assertIn(".", spoken)
        md = voice_stack_markdown().lower()
        self.assertIn("intention", md)
        self.assertIn("import", md)
        self.assertIn("alison", md)
        self.assertIn("en+f3", md)
        _no_brands(md)
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("vo", data_root=Path(tmp) / "projects")
            cue = synthesize_line(project, "Stay like that. [1s] Breathe.", character_id="alison")
            self.assertTrue(Path(cue.path).is_file())
            self.assertEqual(cue.character_id, "alison")
            takes = synthesize_takes(project, "Don't move.", character_id="bradley", count=2)
            self.assertEqual(len(takes), 2)
            self.assertNotEqual(takes[0].intensity, takes[1].intensity)

    def test_video_tools_order(self) -> None:
        keys = [p.key for p in VIDEO_PATHS]
        self.assertEqual(keys[0], "amd_i2v")
        self.assertIn("ken_burns", keys)
        md = video_tools_markdown().lower()
        self.assertIn("comfyui", md)
        self.assertIn("ken burns", md)
        self.assertIn("advanced", md)
        self.assertIn("not the product", md)
        _no_brands(md)


if __name__ == "__main__":
    unittest.main()
