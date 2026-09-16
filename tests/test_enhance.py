#!/usr/bin/env python3
"""Prompt Enhancement: local cinematic expand, bible inject, no adult NSFW refuse."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.animate_ux import CLOUD_SAFETY_PHRASES
from film_lab.characters import seed_alison_bradley
from film_lab.constants import EXPLICIT_INTIMACY
from film_lab.enhance import EnhanceError, enhance_prompt
from film_lab.hub import FORBIDDEN_BRANDS
from film_lab.llm import DEFAULT_PROVIDER, PROVIDER_LOCAL, UGC_PROVIDERS
from film_lab.project import Project


class EnhanceTests(unittest.TestCase):
    def test_local_expands_and_injects_bible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("enhance", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            result = enhance_prompt(
                project,
                "lamp, slow kiss",
                provider=PROVIDER_LOCAL,
                character_ids=["alison", "bradley"],
                aspect="9:16",
                camera="slow push-in",
                lighting="warm lamp bedroom",
                intimacy="intimate sex",
            )
            blob = (result.prompt + " " + result.packed()).lower()
            self.assertEqual(result.provider, PROVIDER_LOCAL)
            self.assertIn("alison", blob)
            self.assertIn("bradley", blob)
            self.assertIn("kiss", blob)
            self.assertIn("9:16", blob)
            self.assertIn("push-in", blob)
            self.assertIn("warm lamp", blob)
            self.assertIn("adult", blob)
            self.assertIn("child", result.negative.lower())
            self.assertNotIn("nsfw", result.negative.lower())
            self.assertNotIn("nude", result.negative.lower())
            self.assertIn("no credits", result.note.lower())
            para = result.paragraph.lower()
            self.assertIn("continuity", para)
            self.assertIn("skin", para)
            self.assertIn("micro-motions", para)
            self.assertIn("kiss", para)
            for banned in FORBIDDEN_BRANDS:
                self.assertNotIn(banned, blob)
                self.assertNotIn(banned, para)

    def test_explicit_adult_is_not_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("explicit", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            result = enhance_prompt(
                project,
                "they don't stop, mouths, hips",
                character_ids=["alison", "bradley"],
                intimacy=EXPLICIT_INTIMACY,
            )
            low = result.prompt.lower()
            self.assertIn("adult", low)
            for phrase in CLOUD_SAFETY_PHRASES:
                self.assertNotIn(phrase, low)

    def test_skip_lighting_is_not_forced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("skiplight", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            result = enhance_prompt(
                project,
                "they sit on the bed",
                lighting="",
                character_ids=["alison", "bradley"],
            )
            self.assertIn("no forced lighting", result.paragraph.lower())
            self.assertNotIn("lighting: warm lamp bedroom, tungsten practical, amber falloff, soft shadow", result.prompt.lower())
            rem = enhance_prompt(
                project,
                "they sit on the bed",
                lighting="Rembrandt",
                character_ids=["alison", "bradley"],
            )
            self.assertIn("triangle", rem.prompt.lower())

    def test_empty_seed_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("empty", data_root=Path(tmp) / "projects")
            with self.assertRaises(EnhanceError):
                enhance_prompt(project, "   ")

    def test_providers_are_user_owned_set(self) -> None:
        self.assertEqual(DEFAULT_PROVIDER, PROVIDER_LOCAL)
        self.assertEqual(
            list(UGC_PROVIDERS),
            [
                "Local templates only",
                "Grok (xAI)",
                "Gemini (Google)",
                "ChatGPT (OpenAI)",
                "Claude (Anthropic)",
            ],
        )


if __name__ == "__main__":
    unittest.main()
