#!/usr/bin/env python3
"""Character Bible Word / PDF sheets — not Excel."""

from __future__ import annotations

import ast
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.char_sheet import (
    BIBLE_EXPORT_LABELS,
    BIBLE_IMPORT_SUFFIXES,
    BibleSheetError,
    export_bible_sheet,
    ext_for_bible_export,
    format_sheet,
    import_bible_files,
    parse_sheet_text,
)
from film_lab.hub import FORBIDDEN_BRANDS, HUB_CARDS
from film_lab.project import Project
from film_lab.writing import WRITING_MODES


def _no_brands(blob: str) -> None:
    low = blob.lower()
    for banned in FORBIDDEN_BRANDS:
        if banned in low:
            raise AssertionError(banned)


class CharSheetTests(unittest.TestCase):
    def test_labels_and_parse(self) -> None:
        self.assertEqual(BIBLE_EXPORT_LABELS, ("Word", "PDF"))
        self.assertEqual(BIBLE_IMPORT_SUFFIXES, {".docx", ".pdf"})
        self.assertEqual(ext_for_bible_export("Word"), ".docx")
        self.assertEqual(ext_for_bible_export("PDF"), ".pdf")
        with self.assertRaises(BibleSheetError):
            ext_for_bible_export("Excel")
        text = format_sheet(
            {
                "name": "Alison",
                "role": "Adult",
                "age_years": 28,
                "look_notes": "Blonde, late-20s adult woman.",
                "personality": "Direct, tender.",
            }
        )
        self.assertIn("Character sheet — Alison", text)
        self.assertIn("Look / appearance: Blonde", text)
        parsed = parse_sheet_text(text)
        self.assertEqual(parsed["name"], "Alison")
        self.assertEqual(parsed["role"], "Adult")
        self.assertIn("Blonde", parsed["look_notes"])
        loose = parse_sheet_text("Bradley\n\nDark hair, athletic late-20s adult man.")
        self.assertEqual(loose["name"], "Bradley")
        self.assertIn("Dark hair", loose["look_notes"])

    def test_roundtrip_word_and_pdf(self) -> None:
        fields = {
            "id": "alison",
            "name": "Alison",
            "role": "Adult",
            "age_band": "late 20s (adult)",
            "age_years": 28,
            "look_notes": "Blonde, late-20s adult woman. Soft jaw.",
            "wardrobe": "Fallen sheet, never costume-y.",
            "rings_props": "Wedding band on the left hand.",
            "personality": "Direct, tender.",
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            word = export_bible_sheet(fields, root / "alison.docx")
            pdf = export_bible_sheet(fields, root / "alison.pdf")
            self.assertTrue(word.is_file())
            self.assertTrue(pdf.read_bytes().startswith(b"%PDF"))
            back_word, names = import_bible_files([str(word)])
            self.assertEqual(names, ["alison.docx"])
            self.assertEqual(back_word["name"], "Alison")
            self.assertIn("Blonde", back_word["look_notes"])
            self.assertIn("Wedding band", back_word["rings_props"])
            back_pdf, _ = import_bible_files([str(pdf)])
            self.assertEqual(back_pdf["name"], "Alison")
            self.assertIn("tender", back_pdf["personality"])
            xls = root / "nope.xlsx"
            xls.write_bytes(b"not-excel")
            with self.assertRaises(BibleSheetError) as ctx:
                import_bible_files([str(xls)])
            self.assertIn("Writing Studio", str(ctx.exception))
            with self.assertRaises(BibleSheetError):
                export_bible_sheet(fields, root / "nope.xlsx")

    def test_export_into_project_bible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("bible-sheet", data_root=Path(tmp))
            dest = (
                project.root
                / "characters"
                / "bradley"
                / "bradley-character-sheet.pdf"
            )
            export_bible_sheet(
                {
                    "id": "bradley",
                    "name": "Bradley",
                    "role": "Adult",
                    "look_notes": "Dark hair, athletic late-20s adult man.",
                },
                dest,
            )
            parsed, _ = import_bible_files([str(dest)])
            self.assertEqual(parsed["name"], "Bradley")
            self.assertIn("athletic", parsed["look_notes"])

    def test_modes_hub_and_ui(self) -> None:
        self.assertEqual(len(WRITING_MODES), 5)
        self.assertEqual(len(HUB_CARDS), 15)
        src = (ROOT / "app.py").read_text(encoding="utf-8")
        ast.parse(src)
        start = src.find('with gr.Tab("Character Consistency"')
        chunk = src[start : src.find('with gr.Tab("Pose Desk"', start)]
        self.assertIn("Import Word / PDF", chunk)
        self.assertIn("Export Word / PDF", chunk)
        self.assertIn(".docx", chunk)
        self.assertNotIn(".xlsx", chunk)
        _no_brands(src)
        _no_brands((ROOT / "film_lab" / "char_sheet.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
