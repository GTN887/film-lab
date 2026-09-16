#!/usr/bin/env python3
"""Extended reel: beat sheet, last-frame continue math, crossfade stitch."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.animate_ux import CLOUD_SAFETY_PHRASES
from film_lab.characters import seed_alison_bradley
from film_lab.extend import (
    CLIP_SECONDS,
    OVERLAP,
    clips_needed,
    extract_last_frame,
    last_frame_still,
    load_sequence,
    parse_target,
    plan_beats,
    plan_note,
    build_sequence,
    stitch_sequence,
    stitched_length,
)
from film_lab.ffmpeg_support import ffmpeg_available, find_ffmpeg
from film_lab.hub import FORBIDDEN_BRANDS
from film_lab.project import Project


class ExtendMathTests(unittest.TestCase):
    def test_sixty_and_two_minutes_need_a_chain(self) -> None:
        n60 = clips_needed(60, clip_seconds=CLIP_SECONDS, overlap=OVERLAP)
        n120 = clips_needed(120, clip_seconds=CLIP_SECONDS, overlap=OVERLAP)
        self.assertGreaterEqual(n60, 20)
        self.assertGreaterEqual(n120, 40)
        self.assertGreaterEqual(
            stitched_length(n60, clip_seconds=CLIP_SECONDS, overlap=OVERLAP),
            60,
        )
        self.assertGreaterEqual(
            stitched_length(n120, clip_seconds=CLIP_SECONDS, overlap=OVERLAP),
            120,
        )
        self.assertEqual(parse_target("60s reel"), 60)
        self.assertEqual(parse_target("120s reel"), 120)
        self.assertEqual(parse_target("1 min"), 60)
        self.assertEqual(parse_target("2 min"), 120)
        self.assertEqual(parse_target("30s"), 30)

    def test_note_is_honest_about_seconds(self) -> None:
        note = plan_note(60).lower()
        self.assertIn("seconds", note)
        self.assertIn("chained", note)
        self.assertIn("crossfade", note)
        self.assertIn("ken burns", note)
        self.assertIn("advanced", note)
        self.assertIn("zero credits", note)
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, note)


class BeatSheetTests(unittest.TestCase):
    def test_beats_from_enhanced_paragraph(self) -> None:
        paragraph = (
            "Hold continuity with the still. Alison and Bradley, late-20s adults. "
            "Warm lamp reads on skin. Micro-motions only — breath, a swallow. "
            "Slow kiss. Don't cut."
        )
        beats = plan_beats(paragraph, target_seconds=60, clip_seconds=2.5)
        self.assertEqual(len(beats), clips_needed(60, clip_seconds=2.5))
        blob = " ".join(b.prompt for b in beats).lower()
        self.assertIn("continuity", blob)
        self.assertIn("last frame", blob)
        self.assertIn("adults 18+", blob)
        self.assertIn("kiss", blob)
        for phrase in CLOUD_SAFETY_PHRASES:
            self.assertNotIn(phrase, blob)
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, blob)

    def test_build_sequence_writes_shots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("extend", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            seq = build_sequence(
                project,
                "Lamp, two adults, slow kiss. Lighting on skin. Micro-motions.",
                target_seconds=60,
                clip_seconds=3.0,
            )
            self.assertEqual(len(seq.beats), clips_needed(60, clip_seconds=3.0))
            self.assertTrue(all(b.shot_id for b in seq.beats))
            loaded = load_sequence(project)
            self.assertIsNotNone(loaded)
            self.assertEqual(len(loaded.beats), len(seq.beats))
            shot = project.load_shot(seq.beats[0].shot_id)
            self.assertIn("kiss", shot.director_intent.lower())


@unittest.skipUnless(ffmpeg_available()[0], "ffmpeg required")
class LastFrameStitchTests(unittest.TestCase):
    def _color_mp4(self, dest: Path, color: str, seconds: float = 1.0) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                find_ffmpeg(),
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c={color}:s=320x180:d={seconds:.2f}",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(dest),
            ],
            check=True,
            capture_output=True,
        )
        return dest

    def test_extract_last_frame_and_stitch_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("frames", data_root=Path(tmp) / "projects")
            a = self._color_mp4(project.outputs_dir / "a.mp4", "red", 1.2)
            b = self._color_mp4(project.outputs_dir / "b.mp4", "blue", 1.2)
            still = last_frame_still(project, a)
            self.assertTrue(still.is_file())
            frame = Path(tmp) / "tail.jpg"
            extract_last_frame(b, frame)
            self.assertTrue(frame.is_file())
            seq = build_sequence(project, "Continue the lamp. Adults 18+.", target_seconds=60)
            seq.beats[0].clip_path = str(a)
            seq.beats[1].clip_path = str(b)
            dest = stitch_sequence(project, seq)
            self.assertTrue(dest.is_file())
            self.assertGreater(dest.stat().st_size, 1000)
            self.assertIn("reel_60s", dest.name)


if __name__ == "__main__":
    unittest.main()
