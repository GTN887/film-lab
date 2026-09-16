#!/usr/bin/env python3
"""Quality lock: 480p / 720p / 1080p / 4K, AMD native vs export, shot persist."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.project import Project
from film_lab.quality import (
    AMD_NOTE,
    DEBUG_CHECKLIST,
    DEFAULT_QUALITY,
    QUALITY_PRESETS,
    desk_size,
    export_size,
    internal_size,
    native_desk_size,
    native_quality,
    next_lower_quality,
    normalize_quality,
    oom_hint,
    quality_debug_md,
    resize_still,
)
from film_lab.shot_card import ShotCard
from film_lab.variations import fork_take


class QualityLockUnitTests(unittest.TestCase):
    def test_presets_and_aliases(self) -> None:
        self.assertEqual(QUALITY_PRESETS, ("480p", "720p", "1080p", "1440p", "4K"))
        self.assertEqual(normalize_quality("1440"), "1440p")
        self.assertEqual(DEFAULT_QUALITY, "720p")
        self.assertEqual(normalize_quality("720"), "720p")
        self.assertEqual(normalize_quality("1080"), "1080p")
        self.assertEqual(normalize_quality("480"), "480p")
        self.assertEqual(normalize_quality("4k"), "4K")
        self.assertEqual(normalize_quality("2160p"), "4K")
        self.assertEqual(normalize_quality(None), "720p")

    def test_4k_is_export_only(self) -> None:
        self.assertEqual(native_quality("4K"), "720p")
        self.assertEqual(native_quality("1440p"), "720p")
        self.assertEqual(native_quality("1080p"), "1080p")
        self.assertEqual(export_size("1440p", "16:9"), (2560, 1440))
        self.assertEqual(native_desk_size("4K", "16:9"), (1280, 720))
        self.assertEqual(export_size("4K", "16:9"), (3840, 2160))
        self.assertEqual(export_size("4K", "9:16"), (2160, 3840))
        self.assertEqual(desk_size("480p", "16:9"), (854, 480))
        self.assertEqual(internal_size("4K", "16:9"), internal_size("720p", "16:9"))
        self.assertNotIn("4K", {native_quality(q) for q in QUALITY_PRESETS})

    def test_next_lower_and_oom(self) -> None:
        self.assertEqual(next_lower_quality("1080p"), "720p")
        self.assertEqual(next_lower_quality("720p"), "480p")
        self.assertIsNone(next_lower_quality("480p"))
        self.assertEqual(next_lower_quality("4K"), "480p")
        hint = oom_hint("1080p")
        self.assertIn("720p", hint)
        self.assertIn("4K", oom_hint("480p"))
        blob = quality_debug_md()
        self.assertIn("RX 5600 XT", blob)
        self.assertIn("480p", blob)
        self.assertIn("Quality program", blob)
        self.assertIn("DEBUG CHECKLIST", blob)
        self.assertIn("4K", AMD_NOTE)
        self.assertIn("Never force native 4K", DEBUG_CHECKLIST)
        self.assertIn("Shorter duration", DEBUG_CHECKLIST)
        self.assertIn("Retry", DEBUG_CHECKLIST)
        self.assertIn("DEBUG CHECKLIST", hint)

    def test_shot_card_persists_and_fork_keeps_quality(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("quality-lock", data_root=Path(tmp) / "projects")
            self.assertEqual(project.quality, "720p")
            project.set_quality("4K")
            self.assertEqual(project.quality, "4K")
            reloaded = Project.load("quality-lock", data_root=Path(tmp) / "projects")
            self.assertEqual(reloaded.quality, "4K")
            shot = ShotCard(name="Hold", resolution="1080")
            self.assertEqual(shot.resolution, "1080p")
            self.assertIn("quality 1080p", shot.local_prompt())
            project.save_shot(shot)
            loaded = project.load_shot(shot.id)
            self.assertEqual(loaded.resolution, "1080p")
            forked = fork_take(project, loaded, seed=77)
            self.assertEqual(forked.resolution, "1080p")
            self.assertNotEqual(forked.id, loaded.id)

    def test_still_ingest_4k_uses_native_720(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "plate.png"
            Image.new("RGB", (2000, 1200), (20, 20, 20)).save(src)
            dest = Path(tmp) / "out.png"
            resize_still(src, dest, "4K", "16:9")
            with Image.open(dest) as out:
                self.assertEqual(out.size, (1280, 720))

    def test_docs_carry_program_and_checklist(self) -> None:
        for rel in ("README.md", "START_HERE.md", "docs/QUALITY.md", "docs/CRASH_RECOVERY.md"):
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("480p", text, rel)
            self.assertIn("4K", text, rel)
            self.assertIn("RX 5600 XT", text, rel)
            self.assertIn("1080", text, rel)
            low = text.lower()
            self.assertTrue(
                "debug checklist" in low or "drop one" in low,
                rel,
            )


if __name__ == "__main__":
    unittest.main()
