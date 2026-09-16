#!/usr/bin/env python3
"""Writing Studio office import / export — local files, no extra hub card."""

from __future__ import annotations

import ast
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.hub import FORBIDDEN_BRANDS, HUB_CARDS
from film_lab.office import (
    EXPORT_LABELS,
    OfficeError,
    ext_for_export_label,
    extract_office,
    export_typed,
    import_files_as_text,
    pages_from_text,
    write_pptx,
    write_word,
    write_xlsx,
)
from film_lab.project import Project
from film_lab.writing import WRITING_MODES, export_draft, new_draft, save_draft


def _no_brands(blob: str) -> None:
    low = blob.lower()
    for banned in FORBIDDEN_BRANDS:
        if banned in low:
            raise AssertionError(banned)


class OfficeFileTests(unittest.TestCase):
    def test_labels_and_pages(self) -> None:
        self.assertEqual(
            EXPORT_LABELS,
            ("Word", "PDF", "PowerPoint", "Excel", "plain text"),
        )
        self.assertEqual(ext_for_export_label("Word"), ".docx")
        self.assertEqual(ext_for_export_label("PDF"), ".pdf")
        self.assertEqual(ext_for_export_label("PowerPoint"), ".pptx")
        self.assertEqual(ext_for_export_label("Excel"), ".xlsx")
        self.assertEqual(ext_for_export_label("plain text"), ".txt")
        pages = pages_from_text(
            "INT. KITCHEN — NIGHT\n\nAlison lights the lamp.\n\n"
            "EXT. STREET — DAWN\n\nBradley waits."
        )
        self.assertEqual(len(pages), 2)
        self.assertTrue(pages[0][0].startswith("INT."))
        self.assertIn("lamp", pages[0][1])

    def test_roundtrip_typed_office_files(self) -> None:
        body = (
            "INT. KITCHEN — NIGHT\n\n"
            "Alison lights the lamp. The kettle ticks.\n\n"
            "EXT. STREET — DAWN\n\n"
            "Bradley waits by the door."
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            word = export_typed(body, root / "pages.docx", title="Kitchen study")
            pdf = export_typed(body, root / "pages.pdf", title="Kitchen study")
            ppt = export_typed(body, root / "pages.pptx", title="Kitchen study")
            xls = export_typed(body, root / "pages.xlsx", title="Kitchen study")
            txt = export_typed(body, root / "pages.txt", title="Kitchen study")
            self.assertTrue(word.is_file())
            self.assertTrue(pdf.read_bytes().startswith(b"%PDF"))
            self.assertTrue(ppt.is_file())
            self.assertTrue(xls.is_file())
            self.assertIn("Alison", txt.read_text(encoding="utf-8"))
            self.assertIn("Alison", extract_office(word))
            self.assertIn("Alison", extract_office(pdf))
            self.assertIn("Alison", extract_office(ppt))
            self.assertIn("Alison", extract_office(xls))
            self.assertIn("Bradley", extract_office(ppt))
            self.assertIn("Kitchen study", extract_office(ppt))
            viewed, names = import_files_as_text([str(word)])
            self.assertEqual(names, ["pages.docx"])
            self.assertIn("lamp", viewed)
            with self.assertRaises(OfficeError):
                import_files_as_text(None)
            with self.assertRaises(OfficeError):
                extract_office(root / "missing.pptx")

    def test_import_native_pptx_xlsx(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ppt = root / "deck.pptx"
            write_pptx(
                "INT. BEDROOM — NIGHT\n\nAlison does not move.",
                ppt,
                title="Bedroom",
            )
            self.assertIn("Alison", extract_office(ppt))
            xls = root / "beats.xlsx"
            write_xlsx(
                "INT. BEDROOM — NIGHT\n\nBradley stays in the doorway.",
                xls,
                title="Beats",
            )
            self.assertIn("Bradley", extract_office(xls))
            word = root / "note.docx"
            write_word("The sheet slips.", word, title="Note")
            self.assertIn("sheet slips", extract_office(word))

    def test_export_draft_office_suffixes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("office-pages", data_root=Path(tmp))
            draft = new_draft("Lamp pages", "screenplay")
            draft.body = "INT. BEDROOM — NIGHT\n\nAlison stays."
            save_draft(project, draft)
            dest = project.writing_dir / "lamp.docx"
            export_draft(project, draft, dest)
            self.assertIn("Alison", extract_office(dest))
            xls = project.writing_dir / "lamp.xlsx"
            export_draft(project, draft, xls)
            self.assertIn("Alison", extract_office(xls))

    def test_modes_and_hub_and_ui_strings(self) -> None:
        self.assertEqual(len(WRITING_MODES), 5)
        self.assertEqual(len(HUB_CARDS), 15)
        src = (ROOT / "app.py").read_text(encoding="utf-8")
        ast.parse(src)
        for needle in (
            "PowerPoint",
            "Excel",
            "plain text",
            ".pptx",
            ".xlsx",
            'gr.Button("Import")',
            "Export draft",
            "Upload PDF / Word / PowerPoint / Excel / text",
        ):
            self.assertIn(needle, src)
        _no_brands(src)
        _no_brands((ROOT / "film_lab" / "office.py").read_text(encoding="utf-8"))
        _no_brands((ROOT / "film_lab" / "write_fuse.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
