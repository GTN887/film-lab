#!/usr/bin/env python3
"""UGC / Product desk: local composite, bible avatar, adult gate."""

from __future__ import annotations

import ast
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.characters import CharacterProfile, pin_reference, save_character
from film_lab.filming import ROLE_TEEN
from film_lab.hub import FORBIDDEN_BRANDS, HUB_CARDS
from film_lab.constants import STORY_INTIMACY
from film_lab.product import (
    PLACEMENTS,
    ProductError,
    build_product_shot,
    compose_product_still,
    product_markdown,
    product_prompt,
    resolve_avatar_still,
)
from film_lab.project import Project
from film_lab.quality import native_desk_size
from film_lab.ugc import UGC_ASPECT


def _swatch(path: Path, color: tuple[int, int, int], size: tuple[int, int] = (80, 80)) -> Path:
    Image.new("RGB", size, color).save(path)
    return path


class ProductTests(unittest.TestCase):
    def test_hub_stays_fifteen_and_product_blurb(self) -> None:
        titles = [c.title for c in HUB_CARDS]
        self.assertEqual(len(HUB_CARDS), 15)
        self.assertEqual(titles[-1], "Mark & Direct")
        self.assertIn("UGC Ads Desk", titles)
        ugc = next(c for c in HUB_CARDS if c.tab_id == "ugc")
        self.assertEqual(ugc.index, "07")
        low = ugc.blurb.lower()
        self.assertIn("product ref", low)
        self.assertIn("avatar", low)
        self.assertIn("enhance", low)
        self.assertIn("animate", low)
        blob = (product_markdown() + ugc.blurb + ugc.kicker).lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, blob, banned)
        self.assertIn("zero", product_markdown().lower())

    def test_compose_and_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("product-ad", data_root=Path(tmp) / "projects")
            person = _swatch(Path(tmp) / "person.png", (40, 80, 140), (200, 320))
            item = _swatch(Path(tmp) / "serum.png", (200, 40, 40), (90, 90))
            dest = compose_product_still(
                project,
                person,
                item,
                aspect=UGC_ASPECT,
                quality="720p",
                placement="in hands",
                name="serum",
            )
            self.assertTrue(dest.is_file())
            self.assertTrue(dest.name.startswith("ugc_"))
            with Image.open(dest) as composed:
                width, height = composed.size
            self.assertEqual((width, height), native_desk_size("720p", UGC_ASPECT))
            line = product_prompt(
                product_name="Warm serum",
                notes="Keep the label readable.",
                direction="She holds the bottle at the lamp.",
                avatar_name="Alison",
                placement="in hands",
            )
            self.assertIn("Warm serum", line)
            self.assertIn("Alison", line)
            self.assertIn("in hands", line)
            self.assertIn("lamp", line.lower())
            self.assertIn("in hands", PLACEMENTS)
            shot = build_product_shot(
                project,
                still_name=dest.name,
                prompt=line,
                aspect=UGC_ASPECT,
                quality="720p",
                product_name="Warm serum",
            )
            self.assertEqual(shot.intimacy_mode, STORY_INTIMACY)
            self.assertEqual(shot.content_intensity, 0.0)
            self.assertEqual(shot.aspect_ratio, UGC_ASPECT)

    def test_bible_or_upload_and_minor_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("avatar-gate", data_root=Path(tmp) / "projects")
            upload = _swatch(Path(tmp) / "upload.png", (20, 20, 20))
            path, label = resolve_avatar_still(project, upload=upload)
            self.assertEqual(path, upload)
            self.assertEqual(label, "upload")
            adult_still = _swatch(Path(tmp) / "alison.png", (180, 160, 140))
            adult = CharacterProfile(id="alison", name="Alison", role="Adult", age_years=28)
            save_character(project, adult)
            pin_reference(project, "alison", adult_still)
            bible, who = resolve_avatar_still(project, character_id="alison")
            self.assertEqual(who, "Alison")
            self.assertTrue(bible.is_file())
            both, both_label = resolve_avatar_still(
                project, character_id="alison", upload=upload
            )
            self.assertEqual(both, upload)
            self.assertEqual(both_label, "upload")
            teen = CharacterProfile(
                id="sam",
                name="Sam",
                role=ROLE_TEEN,
                age_years=16,
                age_band="teen (story role, non-sexual)",
                look_notes="Teen story role. Bus coat.",
            )
            save_character(project, teen)
            pin_reference(project, "sam", _swatch(Path(tmp) / "sam.png", (90, 90, 90)))
            with self.assertRaises(ProductError):
                resolve_avatar_still(project, character_id="sam")
            with self.assertRaises(ProductError):
                resolve_avatar_still(project)

    def test_app_wires_product_desk(self) -> None:
        src = (ROOT / "app.py").read_text(encoding="utf-8")
        ast.parse(src)
        self.assertIn("Generate still", src)
        self.assertIn("Product still", src)
        self.assertIn("Character Bible", src)
        self.assertIn("generate_product_now", src)
        self.assertIn("Mark & Direct this take", src)
        self.assertIn("Spoken ad plan (hook → CTA)", src)
        self.assertNotIn("Generate video (SVD-XT · AMD)", src)
        low = src.lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, low, banned)
        prod = (ROOT / "film_lab" / "product.py").read_text(encoding="utf-8").lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, prod, banned)


if __name__ == "__main__":
    unittest.main()
