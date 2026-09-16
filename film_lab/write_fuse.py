"""Import + local Fuse for Writing Studio.

Paste Grok online + Gemini (or any chat) and merge into one screenplay,
novel, or beat sheet. Import PDF, Word (.docx), PowerPoint (.pptx),
Excel (.xlsx), or .txt / .md. RTF later.

No API. Works offline. Not an AI rewrite — beat-aligned local merge.
After edit, Plan shots (cap 8, ~2.5s) hands off to Motion / Take Board.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from film_lab.constants import (
    CHARACTER_TAGS,
    DEFAULT_LIGHTING,
    INTIMACY_MODES,
    STORY_INTIMACY,
)
from film_lab.intensity import clamp_content_intensity
from film_lab.office import (
    ALLOWED_IMPORT_SUFFIXES,
    OfficeError,
    extract_office,
    file_paths,
)
from film_lab.project import Project
from film_lab.shot_card import ShotCard, new_shot_id
from film_lab.writing import WRITING_MODES

FUSE_TARGETS = ("screenplay", "novel", "beat sheet")
FUSE_TARGET_TO_MODE = {
    "screenplay": "screenplay",
    "novel": "novel",
    "beat sheet": "director_rewrite",
}
FUSE_ALIASES = {
    "beat_sheet": "beat sheet",
    "beats": "beat sheet",
    "script": "screenplay",
    "pages": "novel",
}

ALLOWED_SUFFIXES = set(ALLOWED_IMPORT_SUFFIXES)
RTF_LATER = {".rtf"}
SHOT_DURATION = 2.5
SHOT_CAP = 8
PLAN_CAMERAS = ("slow push-in", "static", "pan L", "pull-out", "OTS")

_SLUG_LINE = re.compile(r"^(INT\.|EXT\.|INT/EXT\.|I/E\.)", re.I)
_BEAT_MARK = re.compile(r"^\*\*BEAT\s+\d+", re.I)
_NUMBERED = re.compile(r"^(?:BEAT\s+)?\d+[\.\):]\s+\S", re.I)
_HEADING = re.compile(r"^#{1,3}\s+\S")
_HEADER = re.compile(
    r"^# (?:Fused|Imported) draft \(local\).*?^---\s*\n",
    re.S | re.M,
)
_SENTENCE = re.compile(r"(?<=[.!?])\s+")


class WriteImportError(OfficeError):
    """Could not read an uploaded draft. Not a builtin ImportError."""


class FuseError(RuntimeError):
    """Nothing to merge, or the fuse target is unknown."""


def normalize_fuse_target(raw: str | None) -> str:
    text = (raw or "screenplay").strip().lower()
    text = FUSE_ALIASES.get(text, text)
    if text not in FUSE_TARGETS:
        raise FuseError("Fuse target must be screenplay, novel, or beat sheet.")
    return text


def mode_for_target(target: str) -> str:
    mode = FUSE_TARGET_TO_MODE[normalize_fuse_target(target)]
    return mode if mode in WRITING_MODES else "screenplay"


def strip_fuse_header(text: str) -> str:
    return _HEADER.sub("", text or "", count=1).strip()


def extract_text(path: str | Path) -> str:
    """Read one import: PDF, Word, PowerPoint, Excel, or text."""
    try:
        return extract_office(path)
    except OfficeError as exc:
        raise WriteImportError(str(exc)) from exc


def collect_sources(
    paste_a: str | None,
    paste_b: str | None,
    paste_c: str | None,
    files=None,
) -> tuple[list[tuple[str, str]], list[str]]:
    """Labeled drafts from paste boxes + uploaded files."""
    sources: list[tuple[str, str]] = []
    notes: list[str] = []
    for label, raw in (
        ("Draft A (Grok online)", paste_a),
        ("Draft B (Gemini)", paste_b),
        ("Draft C", paste_c),
    ):
        text = (raw or "").strip()
        if text:
            sources.append((label, text))
    for path in file_paths(files):
        try:
            text = extract_text(path).strip()
        except WriteImportError as exc:
            notes.append(str(exc))
            continue
        if text:
            sources.append((path.name, text))
        else:
            notes.append(f"`{path.name}` had no extractable text.")
    if not sources:
        if notes:
            raise WriteImportError(notes[0])
        raise FuseError(
            "Paste at least one draft (e.g. Grok online + Gemini) or import a "
            "PDF, Word, PowerPoint, Excel, or text file."
        )
    return sources, notes


def split_beats(text: str) -> list[str]:
    """INT./EXT. slugs, numbered beats, ## headings, or blank-line paragraphs."""
    body = strip_fuse_header(text)
    if not body:
        return []
    lines = body.splitlines()
    if any(_SLUG_LINE.match(line) for line in lines):
        return _split_on(_SLUG_LINE, lines)
    if sum(1 for line in lines if _BEAT_MARK.match(line)) >= 2:
        return _split_on(_BEAT_MARK, lines)
    if sum(1 for line in lines if _NUMBERED.match(line)) >= 2:
        return _split_on(_NUMBERED, lines)
    if sum(1 for line in lines if _HEADING.match(line)) >= 2:
        return _split_on(_HEADING, lines)
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    return paras or [body]


def fuse_texts(
    drafts: Iterable[tuple[str, str]],
    target: str = "screenplay",
) -> str:
    """Local merge. Align beats by order, drop near-duplicate sentences."""
    target = normalize_fuse_target(target)
    cleaned: list[tuple[str, str]] = []
    for label, text in drafts:
        body = strip_fuse_header(text or "").strip()
        if body:
            cleaned.append((str(label or "Draft").strip() or "Draft", body))
    if not cleaned:
        raise FuseError(
            "Paste at least one draft (e.g. Grok online + Gemini) or import a file."
        )
    kind = "Fused" if len(cleaned) > 1 else "Imported"
    names = "; ".join(label for label, _ in cleaned)
    header = (
        f"# {kind} draft (local)\n\n"
        f"Sources: {names}\n"
        f"Target: {target}\n\n"
        "Local merge — not an AI rewrite. Edit below, then Plan shots → Motion Desk.\n\n"
        "---\n\n"
    )
    split = [split_beats(text) for _, text in cleaned]
    count = max(len(beats) for beats in split)
    formatter = {
        "screenplay": _format_screenplay,
        "novel": _format_novel,
        "beat sheet": _format_beat_sheet,
    }[target]
    parts: list[str] = []
    for index in range(count):
        pieces = [beats[index] for beats in split if index < len(beats)]
        merged = _merge_blocks(pieces)
        if merged:
            parts.append(formatter(index + 1, merged))
    if not parts:
        raise FuseError("Nothing to fuse — drafts were empty after split.")
    return header + "\n\n".join(parts).strip() + "\n"


def beats_from_pages(body: str, cap: int = SHOT_CAP) -> list[str]:
    beats = [b for b in split_beats(body) if b.strip()]
    if not beats:
        raise FuseError("Draft body is empty. Fuse, import, or paste pages first.")
    limit = max(1, int(cap or SHOT_CAP))
    return beats[:limit]


def push_pages_to_shots(
    project: Project,
    body: str,
    *,
    title: str = "Draft",
    character_ids: list[str] | None = None,
    intimacy: str | None = None,
    intensity: float | None = None,
    cap: int = SHOT_CAP,
) -> list[ShotCard]:
    """Turn fused/edited pages into short ShotCards. Cap 8 for 6GB AMD."""
    beats = beats_from_pages(body, cap=cap)
    ids = _clean_ids(character_ids)
    mode = intimacy if intimacy in INTIMACY_MODES else STORY_INTIMACY
    heat = 0.0 if mode == STORY_INTIMACY else clamp_content_intensity(intensity)
    prefix = (title or "Draft").strip() or "Draft"
    tags = _tags_for(ids)
    created: list[ShotCard] = []
    for index, beat in enumerate(beats):
        shot = ShotCard(
            id=new_shot_id(),
            name=f"{prefix} · beat {index + 1}",
            duration=SHOT_DURATION,
            camera_move=PLAN_CAMERAS[index % len(PLAN_CAMERAS)],
            subject_motion_strength=0.35,
            body_motion_notes=_one_line(beat, 240),
            director_intent=beat.strip()[:800],
            intimacy_mode=mode,
            content_intensity=heat,
            character_ids=list(ids),
            character_tags=list(tags),
            lighting=DEFAULT_LIGHTING,
        )
        project.save_shot(shot)
        created.append(shot)
    return created


def _split_on(pattern: re.Pattern[str], lines: list[str]) -> list[str]:
    chunks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if pattern.match(line) and current:
            chunks.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        chunks.append(current)
    return ["\n".join(block).strip() for block in chunks if "\n".join(block).strip()]


def _sentences(text: str) -> list[str]:
    body = " ".join(line.strip() for line in text.splitlines() if line.strip())
    parts = _SENTENCE.split(body) if body else []
    return [p.strip() for p in parts if p.strip()]


def _jaccard(left: str, right: str) -> float:
    a = set(re.findall(r"[a-z0-9']+", left.lower()))
    b = set(re.findall(r"[a-z0-9']+", right.lower()))
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _similar(left: str, right: str) -> bool:
    a = re.sub(r"\s+", " ", left.lower()).strip()
    b = re.sub(r"\s+", " ", right.lower()).strip()
    if not a or not b:
        return False
    if a == b or a in b or b in a:
        return True
    return _jaccard(a, b) >= 0.72


def _merge_blocks(pieces: list[str]) -> str:
    kept: list[str] = []
    for block in pieces:
        for sent in _sentences(block) or ([block.strip()] if block.strip() else []):
            match = next((i for i, old in enumerate(kept) if _similar(old, sent)), None)
            if match is None:
                kept.append(sent)
            elif len(sent) > len(kept[match]):
                kept[match] = sent
    return " ".join(kept).strip()


def _format_screenplay(index: int, text: str) -> str:
    stripped = text.strip()
    if _SLUG_LINE.match(stripped):
        return stripped
    return f"INT. BEAT {index} — DAY\n\n{stripped}"


def _format_novel(index: int, text: str) -> str:
    stripped = text.strip()
    if _HEADING.match(stripped):
        return stripped
    return f"## {index}\n\n{stripped}"


def _format_beat_sheet(index: int, text: str) -> str:
    stripped = text.strip()
    if _BEAT_MARK.match(stripped):
        return stripped
    first = stripped.splitlines()[0].strip()
    logline = first.split(". ")[0].strip().rstrip(".")
    if len(logline) > 140:
        logline = logline[:137].rstrip() + "…"
    return f"**BEAT {index}** — {logline}\n\n{stripped}"


def _clean_ids(raw) -> list[str]:
    ids: list[str] = []
    for item in raw or []:
        text = str(item or "").strip()
        if " — " in text:
            text = text.split(" — ", 1)[0].strip()
        if text and text not in ids:
            ids.append(text)
    return ids or ["alison", "bradley"]


def _tags_for(ids: list[str]) -> list[str]:
    tags: list[str] = []
    if "alison" in ids and CHARACTER_TAGS:
        tags.append(CHARACTER_TAGS[0])
    if "bradley" in ids and len(CHARACTER_TAGS) > 1:
        tags.append(CHARACTER_TAGS[1])
    return tags


def _one_line(text: str, limit: int) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"
