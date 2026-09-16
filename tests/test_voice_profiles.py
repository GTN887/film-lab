#!/usr/bin/env python3
"""Per-character Voice profiles, tagged routing, Cinema cue gather."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.characters import load_character, seed_alison_bradley
from film_lab.hub import FORBIDDEN_BRANDS
from film_lab.project import Project
from film_lab.reel import ReelEntry
from film_lab.script import DialogueLine
from film_lab.voice import (
    cues_for_entry,
    default_voice_profile,
    resolve_character_id,
    speak_tagged_lines,
    synthesize_line,
    voice_stack_markdown,
)


def _no_brands(blob: str) -> None:
    lower = blob.lower()
    for banned in FORBIDDEN_BRANDS:
        if banned in lower:
            raise AssertionError(banned)


class VoiceProfileTests(unittest.TestCase):
    def test_alison_bradley_distinct_defaults(self) -> None:
        alison = default_voice_profile("alison")
        bradley = default_voice_profile("bradley")
        self.assertEqual(alison.tts_voice_id, "en+f3")
        self.assertEqual(bradley.tts_voice_id, "en+m3")
        self.assertNotEqual(alison.tts_voice_id, bradley.tts_voice_id)
        self.assertNotEqual(alison.placeholder_hz, bradley.placeholder_hz)
        self.assertGreater(alison.placeholder_hz, bradley.placeholder_hz)

    def test_resolve_character_id(self) -> None:
        self.assertEqual(resolve_character_id(None, "ALISON"), "alison")
        self.assertEqual(resolve_character_id(None, "Bradley"), "bradley")

    def test_seed_fills_distinct_voice_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("voices", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            alison = load_character(project, "alison")
            bradley = load_character(project, "bradley")
            self.assertEqual(alison.voice_id, "en+f3")
            self.assertEqual(bradley.voice_id, "en+m3")
            self.assertNotEqual(alison.voice_id, bradley.voice_id)

    def test_speak_tagged_routes_per_character(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("tagged", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            cues = speak_tagged_lines(
                project,
                [
                    DialogueLine("ALISON", "", "Stay."),
                    DialogueLine("BRADLEY", "", "I'm here."),
                ],
                scene_id="sc1",
                shot_id="sh1",
            )
            self.assertEqual(len(cues), 2)
            self.assertEqual(cues[0].character_id, "alison")
            self.assertEqual(cues[1].character_id, "bradley")
            self.assertEqual(cues[0].voice_id, "en+f3")
            self.assertEqual(cues[1].voice_id, "en+m3")
            self.assertNotEqual(cues[0].path, cues[1].path)
            self.assertTrue(Path(cues[0].path).is_file())
            self.assertTrue(Path(cues[1].path).is_file())
            self.assertGreater(cues[1].start_s, cues[0].start_s)
            entry = ReelEntry(id="r1", order=0, scene_id="sc1", shot_id="sh1")
            gathered = cues_for_entry(project, entry)
            ids = {c.character_id for c in gathered}
            self.assertIn("alison", ids)
            self.assertIn("bradley", ids)

    def test_cues_for_entry_dedupes_attached_wav(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("mux", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            cue = synthesize_line(
                project,
                "Don't move.",
                character_id="alison",
                shot_id="sh9",
                start_s=0.4,
            )
            entry = ReelEntry(
                id="r2",
                order=0,
                shot_id="sh9",
                dialogue_wav=cue.path,
            )
            gathered = cues_for_entry(project, entry)
            paths = [Path(c.path).resolve() for c in gathered]
            self.assertEqual(len(paths), len(set(paths)))
            self.assertEqual(len(gathered), 1)

    def test_stack_copy_local_first_no_credits_or_brands(self) -> None:
        md = voice_stack_markdown().lower()
        self.assertIn("zero", md)
        self.assertIn("character", md)
        self.assertIn("tagged", md)
        self.assertIn("import", md)
        self.assertNotIn("credit meter", md)
        self.assertNotIn("subscription", md)
        _no_brands(md)


if __name__ == "__main__":
    unittest.main()
