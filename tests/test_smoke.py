#!/usr/bin/env python3
"""Headless smoke: shot JSON, Ken Burns, queue, stitch."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.examples_import import examples_dir, import_example_shots
from film_lab.ffmpeg_support import ffmpeg_available
from film_lab.generators.ken_burns import KenBurnsGenerator
from film_lab.project import Project
from film_lab.queue import GenerationQueue
from film_lab.shot_card import ShotCard
from film_lab.stitch import stitch_clips


def _still(path: Path, color: tuple[int, int, int], *, w: int = 1280, h: int = 720) -> Path:
    img = Image.new("RGB", (w, h), color)
    # Warm lamp disc + two adult-scale masses so zoompan has something to travel over.
    lamp = Image.new("RGB", (180, 180), (255, 196, 110))
    img.paste(lamp, (980, 40))
    img.paste(Image.new("RGB", (220, 260), (210, 170, 140)), (420, 320))
    img.paste(Image.new("RGB", (240, 300), (90, 70, 60)), (640, 280))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path


class ShotCardTests(unittest.TestCase):
    def test_roundtrip_and_prompt(self) -> None:
        shot = ShotCard(
            name="Test kiss",
            duration=4.5,
            camera_move="OTS",
            intimacy_mode="artistic nude",
            character_tags=["Alison (blonde late-20s)", "wedding bands"],
            body_motion_notes="kiss, breathing",
            seed=7,
        )
        self.assertEqual(
            shot.character_tags,
            ["Alison (blonde late-20s)", "wedding bands"],
        )
        prompt = shot.local_prompt()
        self.assertIn("artistic nude", prompt)
        self.assertIn("OTS", prompt)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "shot.json"
            shot.to_json(path)
            loaded = ShotCard.from_json(path)
            self.assertEqual(loaded.id, shot.id)
            self.assertEqual(loaded.seed, 7)
            self.assertEqual(loaded.camera_move, "OTS")

    def test_examples_parse(self) -> None:
        folder = examples_dir()
        cards = list(folder.glob("*.json"))
        self.assertGreaterEqual(len(cards), 4)
        for path in cards:
            shot = ShotCard.from_json(path)
            self.assertTrue(shot.name)
            self.assertGreaterEqual(shot.duration, 3)


@unittest.skipUnless(ffmpeg_available()[0], "ffmpeg required")
class GenerateStitchTests(unittest.TestCase):
    def test_queue_two_shots_and_stitch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "projects"
            project = Project.create("smoke", data_root=root)
            imported = import_example_shots(project)
            self.assertGreaterEqual(len(imported), 1)

            a = _still(project.stills_dir / "start.jpg", (62, 38, 28))
            b = _still(project.stills_dir / "end.jpg", (90, 48, 32))
            gen = KenBurnsGenerator()
            self.assertTrue(gen.probe().available)

            first = ShotCard(
                name="Push in",
                start_frame=a.name,
                duration=3.0,
                camera_move="slow push-in",
                subject_motion_strength=0.6,
                intimacy_mode="covered sheets",
            )
            second = ShotCard(
                name="Pull with landing",
                start_frame=a.name,
                end_frame=b.name,
                duration=3.5,
                camera_move="pull-out",
                intimacy_mode="artistic nude",
                character_tags=["Alison (blonde late-20s)"],
            )
            queue = GenerationQueue()
            queue.enqueue(first)
            queue.enqueue(second)
            queue.run(project, gen)
            self.assertEqual([i.status for i in queue.items], ["done", "done"])
            clips = [Path(i.output_path) for i in queue.items if i.output_path]
            self.assertEqual(len(clips), 2)
            for clip in clips:
                self.assertGreater(clip.stat().st_size, 2000)

            stitched = project.outputs_dir / "phrase.mp4"
            stitch_clips(clips, stitched)
            self.assertTrue(stitched.is_file())
            self.assertGreater(stitched.stat().st_size, 2000)
            generated = [c for c in project.load_gallery() if Path(c.path).is_file()]
            self.assertGreaterEqual(len(generated), 2)


if __name__ == "__main__":
    unittest.main()
