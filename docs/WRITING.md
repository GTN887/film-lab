# Writing Studio — Import, Fuse, Plan shots

Director Brain is the Writing Studio. No extra hub card. **Works offline.** Optional Grok / Gemini / ChatGPT / Claude keys you own. Zero Film Lab credits.

## Flow

1. **Import** PDF, Word (`.docx`), PowerPoint (`.pptx`), Excel (`.xlsx`), or `.txt` / `.md` (RTF later), and/or paste **Draft A** (e.g. Grok online) + **Draft B** (e.g. Gemini) + optional Draft C. Use **Import** to view the file in the draft body.
2. Pick a **Fuse target**: screenplay, novel, or **beat sheet**.
3. **Fuse into one draft** — local merge. Not an API rewrite. Fills the draft body and sets Mode (`beat sheet` → director rewrite).
4. **Edit** the body.
5. **Plan shots → Motion Desk** — up to **8** ShotCards at ~2.5s (6GB AMD). First shot is selected on Motion. Animate there.
6. **Open Take Board** to play the take. Pause never edits. Mark & Direct · Fix this frame.

**Micro-expression & behavior** accordion injects a performance + prop-action line into director notes. Same catalog as Director Note / Pose / Mark. Does not add a sixth writing mode. See [PERFORMANCE.md](PERFORMANCE.md).

**Dream beat sheet** accordion fills a sleep → dream → wake director-rewrite (still five modes). **Plan dream shots → Take Board** links child scenes. Dream style on the Take Board popup: Enter dream or Thought bubble (inner vision + text stylize). Movie / Jedi refs are inspired only. See [DREAM.md](DREAM.md).

Existing buttons stay: Build prompt pack, Generate pages, Push body → Script scene, Save takes → Voice, **Export** (Word, PDF, PowerPoint, Excel, plain text, plus fountain / md).

## Fuse (honest)

Beats align by order (INT./EXT. slugs, numbered beats, `##` headings, or blank-line paragraphs). Near-duplicate sentences drop. A header records sources. One file or one paste is an **import**; two or more is a **fuse**.

Intimate / explicit pages are allowed for **adult 18+ ONLY**. Fuse does not unlock minors. Save / Generate still run the genre + age guard.

## Libraries

`pypdf`, `python-docx`, `python-pptx`, and `openpyxl` are in `requirements.txt`. Missing library → toast, not a crash. Scanned PDFs have no OCR yet. Nothing leaves this machine.
