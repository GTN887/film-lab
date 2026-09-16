#!/usr/bin/env python3
"""Voice notes: typed + mic land in the same Director / Mark note."""

from __future__ import annotations

import ast
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.hub import FORBIDDEN_BRANDS
from film_lab.ui_handlers import transcribe_into_note_ui
from film_lab.voice_notes import (
    NOTE_HELP,
    VoiceNoteError,
    audio_path,
    merge_note,
    probe_stt,
    set_transcribe_override,
    transcribe,
    voice_note_markdown,
)
from film_lab.wavutil import sine_tone, write_mono_wav


class VoiceNoteTests(unittest.TestCase):
    def tearDown(self) -> None:
        set_transcribe_override(None)

    def test_merge_same_box(self) -> None:
        self.assertEqual(merge_note("", "Hold the look."), "Hold the look.")
        self.assertEqual(
            merge_note("Jacket stays.", "Don't rush the face."),
            "Jacket stays. Don't rush the face.",
        )
        self.assertEqual(
            merge_note("Jacket stays. Don't rush.", "Don't rush"),
            "Jacket stays. Don't rush.",
        )

    def test_override_transcribe_and_ui(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "note.wav"
            write_mono_wav(wav, sine_tone(0.6, 180))
            set_transcribe_override(lambda _p: "Glass stays in her left hand.")
            self.assertEqual(transcribe(str(wav)), "Glass stays in her left hand.")
            text, toast, status = transcribe_into_note_ui(
                str(wav), "Actor: hold the pour."
            )
            self.assertIn("hold the pour", text)
            self.assertIn("Glass stays in her left hand.", text)
            self.assertEqual(toast, "")
            self.assertIn("same note", status)
            self.assertEqual(audio_path({"path": str(wav)}), str(wav))

    def test_missing_audio_keeps_typed(self) -> None:
        with self.assertRaises(VoiceNoteError):
            transcribe(None)
        text, toast, _status = transcribe_into_note_ui(None, "Typed already.")
        self.assertEqual(text, "Typed already.")
        self.assertEqual(toast, "")
        set_transcribe_override(lambda _p: "")
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "empty.wav"
            write_mono_wav(wav, sine_tone(0.6, 90))
            kept, toast, _status = transcribe_into_note_ui(str(wav), "Keep this.")
            self.assertEqual(kept, "Keep this.")
            self.assertTrue(toast)

    def test_app_wires_mic_on_notes(self) -> None:
        src = (ROOT / "app.py").read_text(encoding="utf-8")
        ast.parse(src)
        self.assertIn("transcribe_into_note_ui", src)
        self.assertIn("note_mic", src)
        self.assertIn("mk_mark_mic", src)
        self.assertIn("md_mark_mic", src)
        self.assertIn("tk_mark_mic", src)
        self.assertIn("typed or voice", src)
        self.assertIn("Mic — speak", src)
        self.assertIn("prop / object", src)
        status, detail = probe_stt()
        self.assertTrue(status)
        md = voice_note_markdown().lower()
        self.assertIn("typed or spoken", md)
        self.assertIn("same note", NOTE_HELP.lower())
        docs = (ROOT / "docs" / "VOICE_NOTES.md").read_text(encoding="utf-8")
        self.assertIn("Apply / Regenerate", docs)
        low = (src + docs + NOTE_HELP + md).lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, low, banned)


if __name__ == "__main__":
    unittest.main()
