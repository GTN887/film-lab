#!/usr/bin/env python3
"""Dream / Lucid Layer: mark head, child scenes, beat sheet, stitch."""

from __future__ import annotations

import ast
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.characters import CharacterError, CharacterProfile, seed_alison_bradley
from film_lab.dream import (
    DEFAULT_DREAM_TITLES,
    DEFAULT_PRESENTATION,
    INSPIRED_LINE,
    DreamError,
    assert_dream_safe,
    bible_actor_labels,
    dream_beat_sheet,
    dream_board_items,
    dream_markdown,
    draw_thought_bubble,
    enter_dream,
    is_enter_dream,
    load_dream,
    normalize_presentation,
    normalize_text_style,
    normalize_vision,
    parse_dream_titles,
    persist_look_refs,
    steps_from_about,
    stitch_dream_reel,
)
from film_lab.filming import ROLE_TEEN
from film_lab.hub import FORBIDDEN_BRANDS, HUB_CARDS
from film_lab.mark import TARGETS
from film_lab.ffmpeg_support import ffmpeg_available, find_ffmpeg
from film_lab.project import Project
from film_lab.writing import WRITING_MODES


def _still(path: Path) -> Path:
    Image.new("RGB", (320, 240), (28, 24, 20)).save(path, format="PNG")
    return path


class DreamLayerTests(unittest.TestCase):
    def test_head_mark_opens_dream(self) -> None:
        self.assertTrue(is_enter_dream("head", ""))
        self.assertTrue(is_enter_dream("clothing", "Enter dream."))
        self.assertFalse(is_enter_dream("clothing", "jacket stays"))
        self.assertIn("head", TARGETS)
        self.assertEqual(parse_dream_titles(""), list(DEFAULT_DREAM_TITLES))
        self.assertEqual(parse_dream_titles("island, fly"), ["island", "fly"])

    def test_enter_dream_links_children_and_wake(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("dream", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            still = _still(project.stills_dir / "sleep.png")
            layer = enter_dream(
                project,
                parent_still=str(still),
                sleeper_id="alison",
                titles=["island", "meet crush", "talk"],
                character_ids=["alison", "bradley"],
            )
            self.assertEqual(layer.sleeper_id, "alison")
            self.assertEqual([b.title for b in layer.children], ["island", "meet crush", "talk"])
            self.assertIsNotNone(layer.wake)
            self.assertTrue(layer.wake.shot_id)
            self.assertTrue(layer.children[0].shot_id)
            shot = project.load_shot(layer.children[1].shot_id)
            self.assertIn("inspired-only", shot.director_intent.lower())
            self.assertNotIn("luke", shot.director_intent.lower())
            loaded = load_dream(project)
            self.assertEqual(len(loaded.children), 3)
            md = dream_markdown(loaded).lower()
            self.assertIn("dream about", md)
            self.assertIn("island", md)
            self.assertEqual(layer.presentation, "enter dream")
            self.assertEqual(DEFAULT_PRESENTATION, "enter dream")
            self.assertIn("inside the dream", layer.children[0].prompt.lower())
            self.assertFalse(layer.bubble_still)

    def test_beat_sheet_is_director_rewrite_not_sixth_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("sheet", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            body = dream_beat_sheet(
                project,
                sleeper_id="alison",
                titles=["island", "meet crush", "talk"],
                character_ids=["alison", "bradley"],
            )
            self.assertIn("SLEEP", body)
            self.assertIn("island", body)
            self.assertIn("meet crush", body)
            self.assertIn("talk", body)
            self.assertIn("WAKE", body)
            self.assertIn(INSPIRED_LINE.split(".")[0], body)
            self.assertEqual(len(WRITING_MODES), 5)
            self.assertIn("director_rewrite", WRITING_MODES)

    def test_teen_dream_does_not_unlock_intimacy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("kid-dream", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
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
            still = _still(project.stills_dir / "nap.png")
            layer = enter_dream(
                project,
                parent_still=str(still),
                sleeper_id="sam",
                titles=["island"],
                character_ids=["sam"],
                intimacy="covered sheets",
                intensity=0.1,
            )
            self.assertEqual(layer.sleeper_id, "sam")
            with self.assertRaises(CharacterError):
                assert_dream_safe(
                    project,
                    layer,
                    intimacy="intimate sex",
                    intensity=0.8,
                )

    def test_steps_refs_and_parent_child_board(self) -> None:
        chunks = steps_from_about("1. island shore\n2. meet crush\n3. they talk")
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0][0], "island shore")
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("about", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            still = _still(project.stills_dir / "sleep.png")
            ref = _still(Path(tmp) / "look.png")
            saved = persist_look_refs(project, [ref])
            self.assertEqual(len(saved), 1)
            self.assertTrue(Path(saved[0]).is_file())
            labels = bible_actor_labels(project)
            self.assertTrue(any("Actor A" in lab and "alison" in lab for lab in labels))
            layer = enter_dream(
                project,
                parent_still=str(still),
                sleeper_id="alison",
                about="Warm island. Then they talk at a lamp.",
                steps=[{"title": "island", "prompt": "original shoreline"}, {"title": "talk", "prompt": "quiet talk"}],
                look_refs=saved,
                character_ids=["alison", "bradley"],
            )
            self.assertEqual([b.title for b in layer.children], ["island", "talk"])
            self.assertIn("LOOK REF", layer.children[0].prompt)
            board = dream_board_items(project)
            captions = [cap for _path, cap in board]
            self.assertTrue(any(c.startswith("SLEEP ·") for c in captions))
            self.assertTrue(any(c.startswith("DREAM ·") for c in captions))
            self.assertIn("WAKE", captions)

    def test_thought_bubble_and_empty_stitch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = _still(Path(tmp) / "face.png")
            dest = Path(tmp) / "bubble.png"
            out = draw_thought_bubble(src, dest, cx=0.4, cy=0.3)
            self.assertTrue(out.is_file())
            self.assertGreater(out.stat().st_size, 400)
            project = Project.create("nostitch", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            enter_dream(project, parent_still=str(src), sleeper_id="alison")
            with self.assertRaises(DreamError):
                stitch_dream_reel(project)

    def test_style_aliases_vision_and_text(self) -> None:
        self.assertEqual(normalize_presentation("cut"), "enter dream")
        self.assertEqual(normalize_presentation("lucid overlay"), "thought bubble")
        self.assertEqual(normalize_vision("lucid overlay"), "lucid")
        self.assertEqual(normalize_vision(""), "dream")
        self.assertEqual(normalize_text_style("comic"), "comic bubble")
        self.assertEqual(normalize_text_style(""), "none")
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("legacy", data_root=Path(tmp) / "projects")
            project.ensure_dirs()
            (project.root / "dream_layer.json").write_text(
                '{"parent_still": "sleep.png", "presentation": "lucid overlay", '
                '"children": [], "wake": null, "look_refs": []}',
                encoding="utf-8",
            )
            loaded = load_dream(project)
            self.assertEqual(loaded.presentation, "thought bubble")
            self.assertEqual(loaded.inner_vision, "lucid")
            (project.root / "dream_layer.json").write_text(
                '{"parent_still": "sleep.png", "presentation": "cut", '
                '"children": [], "wake": null}',
                encoding="utf-8",
            )
            self.assertEqual(load_dream(project).presentation, "enter dream")

    def test_thought_bubble_caption_and_lucid_vision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = _still(Path(tmp) / "face.png")
            inset = _still(Path(tmp) / "island.png")
            comic = draw_thought_bubble(
                src,
                Path(tmp) / "comic.png",
                caption="island shore",
                content_still=inset,
                text_style="comic bubble",
                vision="dream",
            )
            none = draw_thought_bubble(
                src,
                Path(tmp) / "none.png",
                caption="island shore",
                content_still=inset,
                text_style="none",
                vision="dream",
            )
            diary = draw_thought_bubble(
                src,
                Path(tmp) / "diary.png",
                caption="island shore",
                text_style="diary caption",
                vision="daydream",
            )
            sub = draw_thought_bubble(
                src,
                Path(tmp) / "sub.png",
                caption="island shore",
                text_style="soft subtitle",
            )
            self.assertTrue(comic.is_file())
            self.assertNotEqual(comic.read_bytes(), none.read_bytes())
            self.assertNotEqual(diary.read_bytes(), none.read_bytes())
            self.assertNotEqual(sub.read_bytes(), none.read_bytes())
            project = Project.create("bubble", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            sleep = _still(project.stills_dir / "sleep.png")
            layer = enter_dream(
                project,
                parent_still=str(sleep),
                sleeper_id="alison",
                about="Warm island. Original shoreline.",
                titles=["island"],
                look_refs=[str(inset)],
                presentation="thought bubble",
                inner_vision="lucid",
                text_style="comic bubble",
                character_ids=["alison", "bradley"],
            )
            self.assertEqual(layer.presentation, "thought bubble")
            self.assertEqual(layer.inner_vision, "lucid")
            self.assertEqual(layer.text_style, "comic bubble")
            self.assertIn("they know they are dreaming", layer.children[0].prompt.lower())
            self.assertNotIn("luke", layer.children[0].prompt.lower())
            self.assertTrue(layer.bubble_still)
            self.assertTrue(Path(layer.bubble_still).is_file())
            md = dream_markdown(layer).lower()
            self.assertIn("thought bubble", md)
            self.assertIn("lucid", md)
            board = dream_board_items(project)
            caps = [cap for _path, cap in board]
            self.assertTrue(any("thought bubble" in c.lower() for c in caps))

    def test_app_copy_hub_and_no_brands(self) -> None:
        src = (ROOT / "app.py").read_text(encoding="utf-8")
        ast.parse(src)
        self.assertIn("Enter dream", src)
        self.assertIn("Dream / Lucid", src)
        self.assertIn("sleep → dream → wake", src)
        self.assertIn("Mark the **head**", src)
        self.assertIn("Dream about", src)
        self.assertIn("Actor A / B / C", src)
        self.assertIn("Thought bubble", src)
        self.assertIn("comic bubble", src)
        self.assertIn("Inner vision", src)
        self.assertIn("daydream", src)
        self.assertIn("open_dream_about_ui", src)
        self.assertIn("take_cast_faces.select", src)
        self.assertEqual(len(HUB_CARDS), 15)
        self.assertEqual(len(WRITING_MODES), 5)
        blob = (ROOT / "film_lab" / "dream.py").read_text(encoding="utf-8").lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, blob, banned)
        self.assertNotIn("subscription", blob)
        takes = next(c for c in HUB_CARDS if c.tab_id == "takes")
        self.assertIn("dream about", takes.blurb.lower())


@unittest.skipUnless(ffmpeg_available()[0], "ffmpeg required")
class DreamStitchTests(unittest.TestCase):
    def _color_mp4(self, dest: Path, color: str) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                find_ffmpeg(),
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c={color}:s=320x180:d=1.0",
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

    def test_stitch_sleep_dream_wake(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("reel", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            still = _still(project.stills_dir / "sleep.png")
            layer = enter_dream(
                project,
                parent_still=str(still),
                sleeper_id="alison",
                titles=["island"],
            )
            sleep = self._color_mp4(project.outputs_dir / "sleep.mp4", "navy")
            dream = self._color_mp4(project.outputs_dir / "island.mp4", "teal")
            wake = self._color_mp4(project.outputs_dir / "wake.mp4", "gold")
            layer.parent_clip = str(sleep)
            layer.children[0].clip_path = str(dream)
            layer.wake.clip_path = str(wake)
            dest = stitch_dream_reel(project, layer)
            self.assertTrue(dest.is_file())
            self.assertGreater(dest.stat().st_size, 1000)
            self.assertTrue(dest.name.startswith("dream_"))


if __name__ == "__main__":
    unittest.main()
