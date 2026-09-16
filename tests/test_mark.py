#!/usr/bin/env python3
"""Mark & Direct: region stack, clip frame, Regular vs 18+ gate."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.characters import CharacterProfile, seed_alison_bradley
from film_lab.filming import MODE_EXPLICIT, MODE_REGULAR, ROLE_TEEN
from film_lab.hub import FORBIDDEN_BRANDS, HUB_CARDS
from film_lab.mark import (
    MarkError,
    apply_region,
    assert_marks_safe,
    fold_marks_into_seed,
    load_marks,
    marks_markdown,
    region_asks_sex,
    still_from_source,
)
from film_lab.project import Project


def _still(path: Path) -> Path:
    Image.new("RGB", (320, 240), (40, 32, 24)).save(path, format="PNG")
    return path


class MarkDirectTests(unittest.TestCase):
    def test_circle_stacks_and_folds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("mark", data_root=Path(tmp) / "projects")
            src = _still(Path(tmp) / "lead.png")
            dest, marks, region = apply_region(
                project,
                src,
                shape="circle",
                target="clothing",
                note="Jacket stays zipped.",
                cx=0.4,
                cy=0.5,
                size=0.3,
            )
            self.assertTrue(dest.is_file())
            self.assertTrue(dest.with_name(dest.stem + ".mark.json").is_file())
            self.assertEqual(len(marks.regions), 1)
            self.assertIn("MARK NOTE (clothing):", region.line())
            folded = fold_marks_into_seed("Slow walk home.", marks)
            self.assertIn("MARK NOTE", folded)
            self.assertIn("Jacket stays zipped", folded)
            apply_region(
                project,
                dest,
                shape="square",
                target="face emotion",
                note="Hold the look. Don't rush.",
                cx=0.5,
                cy=0.22,
                size=0.2,
            )
            stacked = load_marks(project)
            self.assertEqual(len(stacked.regions), 2)

    def test_lasso_needs_brush(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("lasso", data_root=Path(tmp) / "projects")
            src = _still(Path(tmp) / "lead.png")
            with self.assertRaises(MarkError):
                apply_region(
                    project,
                    src,
                    shape="lasso",
                    target="body",
                    note="Soften the shoulder.",
                )

    def test_regular_blocks_sexual_region(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("safe", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            project.set_filming_mode(MODE_REGULAR)
            marks = load_marks(project)
            from film_lab.mark import RegionMark

            dirty = RegionMark(id="x", target="clothing", note="undress through motion")
            self.assertTrue(region_asks_sex(dirty))
            marks.regions.append(dirty)
            with self.assertRaises(MarkError):
                assert_marks_safe(
                    project,
                    marks,
                    extra_note="undress through motion",
                    context="Mark & Direct",
                )
            project.set_filming_mode(MODE_EXPLICIT)
            assert_marks_safe(
                project,
                marks,
                intimacy="intimate sex",
                intensity=1.0,
                extra_note="undress through motion",
            )
            teen = CharacterProfile(
                id="sam",
                name="Sam",
                role=ROLE_TEEN,
                age_years=16,
                age_band="teen (story role, non-sexual)",
                look_notes="Teen story role. Bus coat.",
            )
            from film_lab.characters import save_character

            save_character(project, teen)
            project.set_cast(["sam"])
            with self.assertRaises(MarkError):
                assert_marks_safe(
                    project,
                    marks,
                    intimacy="intimate sex",
                    intensity=1.0,
                    extra_note="undress",
                )

    def test_clip_frame_and_hub(self) -> None:
        titles = [c.title for c in HUB_CARDS]
        self.assertIn("Mark & Direct", titles)
        mark = next(c for c in HUB_CARDS if c.tab_id == "mark")
        self.assertEqual(mark.index, "15")
        low = (marks_markdown() + mark.blurb).lower()
        self.assertIn("lasso", low)
        self.assertIn("regenerate", low)
        docs = (ROOT / "docs" / "MARK.md").read_text(encoding="utf-8").lower()
        self.assertIn("will not fake", docs)
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, low, banned)
            self.assertNotIn(banned, docs, banned)
        with tempfile.TemporaryDirectory() as tmp:
            src = _still(Path(tmp) / "frame.png")
            dest = Path(tmp) / "copy.png"
            out = still_from_source(src, dest)
            self.assertTrue(out.is_file())


if __name__ == "__main__":
    unittest.main()
