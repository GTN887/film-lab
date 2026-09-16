#!/usr/bin/env python3
"""Provider menus: Liam's picker words, Local default, fail-soft, no secrets."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.llm import (
    DEFAULT_PROVIDER,
    NO_CREDITS,
    PROVIDER_CLAUDE,
    PROVIDER_GROK,
    PROVIDER_LOCAL,
    PROVIDER_OPENAI,
)
from film_lab.providers import (
    IMAGE_FAMILIES,
    IMAGE_FAMILY_DEFAULT,
    IMAGE_GROK,
    IMAGE_LOCAL,
    IMAGE_NANO,
    IMAGE_OPENAI,
    IMAGE_SEEDREAM,
    VIDEO_FAMILIES,
    VIDEO_FAMILY_DEFAULT,
    VIDEO_FEATURED,
    VIDEO_HAILUO,
    VIDEO_LOCAL,
    TEXT_CLAUDE,
    TEXT_FAMILY_DEFAULT,
    TEXT_GROK,
    TEXT_OPENAI,
    VOICE_DEFAULT,
    VOICE_ELEVENLABS,
    VOICE_PROVIDERS,
    family_to_provider,
    image_models_for,
    providers_markdown,
    resolve_image_pick,
    resolve_text_pick,
    resolve_video_pick,
    resolve_voice_provider,
    text_models_for,
    video_models_for,
)


class ProviderMenuTests(unittest.TestCase):
    def test_voice_words_and_local_default(self) -> None:
        self.assertEqual(VOICE_DEFAULT, "Local TTS")
        self.assertEqual(
            list(VOICE_PROVIDERS),
            ["Local TTS", "ElevenLabs", "Seed Audio", "Seed Speech"],
        )
        local = resolve_voice_provider("Local TTS")
        self.assertTrue(local.local)
        self.assertTrue(local.wired)
        cloud = resolve_voice_provider(VOICE_ELEVENLABS)
        self.assertFalse(cloud.wired)
        self.assertIn("coming soon", cloud.message.lower())
        self.assertIn("will not fake", cloud.message.lower())

    def test_image_nested_words(self) -> None:
        self.assertEqual(IMAGE_FAMILY_DEFAULT, IMAGE_LOCAL)
        self.assertEqual(IMAGE_FAMILIES[0], IMAGE_LOCAL)
        self.assertIn(IMAGE_NANO, IMAGE_FAMILIES)
        self.assertIn(IMAGE_GROK, IMAGE_FAMILIES)
        self.assertIn("Ideogram", IMAGE_FAMILIES)
        self.assertIn(IMAGE_OPENAI, IMAGE_FAMILIES)
        self.assertIn(IMAGE_SEEDREAM, IMAGE_FAMILIES)
        nano = image_models_for(IMAGE_NANO)
        self.assertEqual(
            nano,
            [
                "Nano Banana Pro",
                "Nano Banana",
                "Nano Banana 2",
                "Nano Banana 2 Lite",
            ],
        )
        grok = image_models_for(IMAGE_GROK)
        self.assertIn("Grok Imagine", grok)
        self.assertIn("Grok Imagine 2.0 Edit", grok)
        ideo = image_models_for("Ideogram")
        self.assertIn("Ideogram 2.0 Turbo", ideo)
        seed = image_models_for(IMAGE_SEEDREAM)
        self.assertIn("Seedream 5.0 Pro", seed)
        local = resolve_image_pick(IMAGE_LOCAL)
        self.assertTrue(local.local_i2v)
        self.assertTrue(local.wired)
        blocked = resolve_image_pick(IMAGE_NANO, "Nano Banana Pro")
        self.assertFalse(blocked.wired)
        self.assertFalse(blocked.local_i2v)
        self.assertIn("coming soon", blocked.message.lower())

    def test_video_nested_local_default_and_featured_alias(self) -> None:
        self.assertEqual(VIDEO_FAMILY_DEFAULT, VIDEO_LOCAL)
        self.assertEqual(VIDEO_FAMILIES[0], VIDEO_LOCAL)
        self.assertIn(VIDEO_FEATURED, VIDEO_FAMILIES)
        self.assertIn(VIDEO_HAILUO, VIDEO_FAMILIES)
        hailuo = video_models_for(VIDEO_HAILUO)
        self.assertIn("Minimax H3 Max", hailuo)
        self.assertIn("Hailuo 3.0", hailuo)
        self.assertIn("Hailuo G2", hailuo)
        featured = video_models_for(VIDEO_FEATURED)
        self.assertEqual(featured, ["Multi-Version", "Reality Mix"])
        local = resolve_video_pick(VIDEO_LOCAL)
        self.assertTrue(local.local_i2v)
        mix = resolve_video_pick(VIDEO_FEATURED, "Reality Mix")
        self.assertTrue(mix.local_i2v)
        self.assertIn("film lab", mix.message.lower())
        self.assertNotIn("genjutsu", mix.message.lower())
        cloud = resolve_video_pick(VIDEO_HAILUO, "Hailuo 3.0")
        self.assertFalse(cloud.local_i2v)
        self.assertIn("coming soon", cloud.message.lower())
        self.assertNotIn("sk-", cloud.message.lower())

    def test_text_nested_and_wired_backends(self) -> None:
        self.assertEqual(TEXT_FAMILY_DEFAULT, "Local templates only")
        self.assertEqual(family_to_provider(TEXT_FAMILY_DEFAULT), PROVIDER_LOCAL)
        self.assertEqual(family_to_provider(TEXT_GROK), PROVIDER_GROK)
        self.assertEqual(family_to_provider(TEXT_OPENAI), PROVIDER_OPENAI)
        self.assertEqual(family_to_provider(TEXT_CLAUDE), PROVIDER_CLAUDE)
        self.assertEqual(
            text_models_for(TEXT_GROK),
            ["Grok 2", "Grok mini", "Grok Beta"],
        )
        self.assertIn("GPT-4o", text_models_for(TEXT_OPENAI))
        self.assertIn("o1-mini", text_models_for(TEXT_OPENAI))
        local = resolve_text_pick(TEXT_FAMILY_DEFAULT)
        self.assertTrue(local.wired)
        self.assertEqual(local.backend, PROVIDER_LOCAL)
        os.environ.pop("FILM_LAB_XAI_API_KEY", None)
        os.environ.pop("XAI_API_KEY", None)
        grok = resolve_text_pick(TEXT_GROK, "Grok 2")
        self.assertFalse(grok.wired)
        self.assertEqual(grok.api_id, "grok-2")
        self.assertIn("FILM_LAB_XAI_API_KEY", grok.message)
        openai = resolve_text_pick(TEXT_OPENAI, "GPT-4o")
        self.assertEqual(openai.api_id, "gpt-4o")
        self.assertFalse(openai.wired)
        os.environ.pop("FILM_LAB_ANTHROPIC_API_KEY", None)
        os.environ.pop("ANTHROPIC_API_KEY", None)
        claude = resolve_text_pick(TEXT_CLAUDE, "Claude Sonnet")
        self.assertEqual(claude.backend, PROVIDER_CLAUDE)
        self.assertEqual(claude.api_id, "claude-sonnet-4-5")
        self.assertFalse(claude.wired)
        self.assertIn("ANTHROPIC", claude.message.upper())

    def test_no_secrets_or_credits_or_required_paid(self) -> None:
        md = providers_markdown().lower()
        self.assertIn("local is the default", md)
        self.assertIn("zero", md)
        self.assertNotIn("sk-", md)
        self.assertNotIn("api_key=", md)
        self.assertNotIn("credit meter", md)
        self.assertIn("film", NO_CREDITS.lower())
        for route in (
            resolve_voice_provider("Seed Speech"),
            resolve_image_pick("Seedream", "Seedream 4.5"),
            resolve_text_pick(TEXT_OPENAI, "GPT-3.5 Turbo"),
        ):
            blob = route.message.lower()
            self.assertNotIn("sk-", blob)
            self.assertTrue("credit" in blob or "zero" in blob)

    def test_app_source_has_no_forbidden_hub_brands(self) -> None:
        from film_lab.hub import FORBIDDEN_BRANDS

        src = (ROOT / "app.py").read_text(encoding="utf-8").lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, src, banned)
        self.assertEqual(DEFAULT_PROVIDER, PROVIDER_LOCAL)


if __name__ == "__main__":
    unittest.main()
