#!/usr/bin/env python3
"""Import + Fuse + Plan shots — local Writing Studio, no extra hub card."""

from __future__ import annotations

import ast
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.constants import STORY_INTIMACY
from film_lab.hub import FORBIDDEN_BRANDS, HUB_CARDS
from film_lab.pdf_export import write_simple_pdf
from film_lab.project import Project
from film_lab.write_fuse import (
    FUSE_TARGETS,
    FuseError,
    WriteImportError,
    beats_from_pages,
    collect_sources,
    extract_text,
    fuse_texts,
    mode_for_target,
    push_pages_to_shots,
    split_beats,
)


def _no_brands(blob: str) -> None:
    low = blob.lower()
    for banned in FORBIDDEN_BRANDS:
        if banned in low:
            raise AssertionError(banned)


class WriteFuseTests(unittest.TestCase):
    def test_fuse_two_drafts_keeps_both(self) -> None:
        grok = (
            "INT. KITCHEN — NIGHT\n\n"
            "Alison sets the lamp. The kettle ticks.\n"
        )
        gemini = (
            "INT. KITCHEN — NIGHT\n\n"
            "Alison sets the lamp. Bradley watches from the door.\n"
        )
        body = fuse_texts(
            [("Draft A (Grok online)", grok), ("Draft B (Gemini)", gemini)],
            "screenplay",
        )
        self.assertIn("# Fused draft (local)", body)
        self.assertIn("Grok online", body)
        self.assertIn("Gemini", body)
        self.assertIn("kettle", body)
        self.assertIn("Bradley", body)
        self.assertIn("INT.", body)
        self.assertNotIn("AI rewrite", body.lower().replace("not an ai rewrite", ""))
        _no_brands(body)

    def test_fuse_beat_sheet_and_novel(self) -> None:
        a = "She opens the can.\n\nShe pours."
        b = "The can sits alone.\n\nShe picks it up and pours."
        beats = fuse_texts([("A", a), ("B", b)], "beat sheet")
        self.assertIn("**BEAT 1**", beats)
        self.assertIn("Target: beat sheet", beats)
        novel = fuse_texts([("A", a), ("B", b)], "novel")
        self.assertIn("## 1", novel)
        self.assertEqual(mode_for_target("beat sheet"), "director_rewrite")
        self.assertEqual(mode_for_target("novel"), "novel")
        self.assertEqual(FUSE_TARGETS, ("screenplay", "novel", "beat sheet"))

    def test_extract_txt_and_empty_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "draft.md"
            path.write_text("# Scene\n\nThe lamp holds.", encoding="utf-8")
            self.assertIn("lamp holds", extract_text(path))
            rtf = Path(tmp) / "old.rtf"
            rtf.write_text("nope", encoding="utf-8")
            with self.assertRaises(WriteImportError) as ctx:
                extract_text(rtf)
            self.assertIn("RTF later", str(ctx.exception))
            with self.assertRaises(FuseError):
                fuse_texts([], "screenplay")
            with self.assertRaises(FuseError):
                collect_sources("", "", "", None)

    def test_extract_pdf_and_docx(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "pages.pdf"
            write_simple_pdf("INT. BEDROOM — NIGHT\n\nAlison does not move.", pdf)
            self.assertIn("Alison", extract_text(pdf))
            from docx import Document

            docx_path = Path(tmp) / "pages.docx"
            doc = Document()
            doc.add_paragraph("Bradley stays in the doorway.")
            doc.save(docx_path)
            self.assertIn("Bradley", extract_text(docx_path))
            from film_lab.office import write_pptx, write_xlsx

            pptx_path = Path(tmp) / "deck.pptx"
            write_pptx("The lamp holds on the table.", pptx_path, title="Deck")
            self.assertIn("lamp holds", extract_text(pptx_path))
            xlsx_path = Path(tmp) / "beats.xlsx"
            write_xlsx("INT. KITCHEN — NIGHT\n\nShe pours.", xlsx_path, title="Beats")
            self.assertIn("pours", extract_text(xlsx_path))
            sources, notes = collect_sources(
                "Grok: the lamp.",
                "",
                "",
                [str(docx_path)],
            )
            self.assertEqual(len(sources), 2)
            self.assertEqual(notes, [])

    def test_plan_shots_capped(self) -> None:
        body = "\n\n".join(f"Beat {i}. The room waits {i}." for i in range(1, 12))
        beats = beats_from_pages(body, cap=8)
        self.assertEqual(len(beats), 8)
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("fuse-plan", data_root=Path(tmp))
            shots = push_pages_to_shots(
                project,
                body,
                title="Kitchen study",
                character_ids=["alison", "bradley"],
                intimacy=STORY_INTIMACY,
                intensity=0,
            )
            self.assertEqual(len(shots), 8)
            self.assertAlmostEqual(shots[0].duration, 2.5)
            self.assertIn("Kitchen study", shots[0].name)
            self.assertEqual(shots[0].character_ids, ["alison", "bradley"])
            self.assertTrue((project.shots_dir / f"{shots[0].id}.json").is_file())

    def test_split_slugs(self) -> None:
        pages = (
            "INT. BEDROOM — NIGHT\n\nShe waits.\n\n"
            "EXT. STREET — DAWN\n\nHe walks."
        )
        beats = split_beats(pages)
        self.assertEqual(len(beats), 2)
        self.assertTrue(beats[0].startswith("INT."))

    def test_app_has_import_fuse_ui_and_15_cards(self) -> None:
        src = (ROOT / "app.py").read_text(encoding="utf-8")
        ast.parse(src)
        for needle in (
            "Fuse",
            "Import",
            "beat sheet",
            "Plan shots",
            "Import & Fuse",
            "Fuse into one draft",
            "Open Take Board",
            "PowerPoint",
            "Excel",
            "plain text",
        ):
            self.assertIn(needle, src)
        self.assertEqual(len(HUB_CARDS), 15)
        titles = [c.title for c in HUB_CARDS]
        self.assertIn("Director Brain", titles)
        self.assertNotIn("Writing Studio", titles)
        brain = next(c for c in HUB_CARDS if c.tab_id == "brain")
        self.assertIn("Fuse", brain.blurb)
        _no_brands(src)
        _no_brands((ROOT / "film_lab" / "write_fuse.py").read_text(encoding="utf-8"))
        modes = (
            ROOT / "film_lab" / "writing.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            '"screenplay",\n    "novel",\n    "book_to_screenplay",\n    "roleplay",\n    "director_rewrite"',
            modes,
        )


if __name__ == "__main__":
    unittest.main()
