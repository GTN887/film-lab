"""Dream / Lucid Layer — parent sleep take → child dream scenes → wake.

Mark the head on a sleeping take to Enter dream. Child scenes can use any
Character Bible cast (island, meet crush, talk, …). Writing Studio fills a
dream beat sheet via director_rewrite — not a sixth writing mode. Stitch
sleep → dream → wake on Take Board.

Movie / Jedi / lucid-dream references are inspired only. Original characters.
Zero credits. Intimate / explicit: adult 18+ ONLY.
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from film_lab.characters import (
    CharacterError,
    assert_adult_cast,
    list_characters,
    load_character,
    load_selected_characters,
)
from film_lab.constants import CHARACTER_TAGS, DEFAULT_LIGHTING, INTIMACY_MODES, STORY_INTIMACY
from film_lab.ffmpeg_support import FFmpegError, ffmpeg_available, run_ffmpeg
from film_lab.filming import role_is_minor
from film_lab.intensity import clamp_content_intensity, intensity_requires_numeric_age
from film_lab.intimacy import is_intimate
from film_lab.project import IMAGE_SUFFIXES, VIDEO_SUFFIXES, Project
from film_lab.shot_card import ShotCard, new_shot_id
from film_lab.stitch import stitch_clips
from film_lab.util import new_id, write_json

DREAM_FILE = "dream_layer.json"
HEAD_TARGET = "head"
HEAD_TARGETS = frozenset({HEAD_TARGET, "head (enter dream)"})
DEFAULT_DREAM_TITLES: tuple[str, ...] = ("island", "meet crush", "talk")
PRESENTATIONS: tuple[str, ...] = ("enter dream", "thought bubble")
DEFAULT_PRESENTATION = "enter dream"
INNER_VISIONS: tuple[str, ...] = ("dream", "daydream", "thinking", "lucid")
DEFAULT_VISION = "dream"
TEXT_STYLES: tuple[str, ...] = ("none", "comic bubble", "soft subtitle", "diary caption")
DEFAULT_TEXT_STYLE = "none"
PHASE_SLEEP = "sleep"
PHASE_DREAM = "dream"
PHASE_WAKE = "wake"
SHOT_DURATION = 2.5
PLAN_CAMERAS = ("slow push-in", "static", "pan L", "pull-out", "OTS")

INSPIRED_LINE = (
    "Inspired-only original characters. Movie / Jedi / lucid-dream references "
    "are lighting and structure notes — never franchise likenesses or plots."
)

DREAM_HELP = (
    "**Dream / Lucid Layer.** Pause the sleeping take on Take Board. "
    "Click the person → **Dream about…** — Character Bible multi-select "
    "(Actor A / B / C) plus free text. Add dream beats layer by layer. "
    "Drop image or video look-refs. Pick **Dream style** on the popup: "
    "**Enter dream** (they are inside the sequence) or **Thought bubble** "
    "(overlay on the sleeping shot — still, mini-clip, or styled text). "
    "Inner vision: dream / daydream / thinking / lucid. "
    "Text stylize: comic bubble / soft subtitle / diary caption / none. "
    "Animate the dream takes, then **Stitch sleep → dream → wake**. "
    "Movie / Jedi refs are inspired only. Original characters. "
    "Regular / story for under-18 roles. Intimate / explicit: adult 18+ ONLY. "
    "Zero credits."
)
ACTOR_LETTERS = "ABCDEFGH"
_NUMBERED_STEP = re.compile(
    r"^(?:(?:beat|layer|step)\s*)?\d+[\.\):]\s+",
    re.I,
)

_ENTER_WORDS = ("enter dream", "dream take", "lucid layer", "open dream")
_PRESENTATION_ALIASES = {
    "cut": "enter dream",
    "inside": "enter dream",
    "enter": "enter dream",
    "enter dream": "enter dream",
    "thought bubble": "thought bubble",
    "thought-bubble": "thought bubble",
    "bubble": "thought bubble",
    "lucid overlay": "thought bubble",
}
_TEXT_ALIASES = {
    "none": "none",
    "off": "none",
    "comic": "comic bubble",
    "comic bubble": "comic bubble",
    "subtitle": "soft subtitle",
    "soft subtitle": "soft subtitle",
    "diary": "diary caption",
    "diary caption": "diary caption",
}
VISION_LINES = {
    "dream": (
        "They are inside the dream. Full inner vision, not a bedroom cutaway. "
        + INSPIRED_LINE
    ),
    "daydream": (
        "Waking daydream. Eyes soft. The room stays; the picture blooms. "
        + INSPIRED_LINE
    ),
    "thinking": (
        "Inner thought, not a cutaway world. Face stays on the sleeper. "
        + INSPIRED_LINE
    ),
    "lucid": (
        "Lucid: they know they are dreaming. Original characters only. "
        + INSPIRED_LINE
    ),
}
VISION_MARKERS = {
    "dream": "inside the dream",
    "daydream": "waking daydream",
    "thinking": "inner thought",
    "lucid": "they know they are dreaming",
}


class DreamError(ValueError):
    """No sleeping parent, empty beats, or not enough clips to stitch."""


@dataclass
class DreamBeat:
    id: str
    title: str
    phase: str
    prompt: str
    character_ids: list[str] = field(default_factory=list)
    shot_id: str = ""
    clip_path: str = ""
    look_refs: list[str] = field(default_factory=list)
    card_still: str = ""

    def label(self) -> str:
        name = (self.title or self.phase or "beat").strip()
        return f"{self.phase} · {name}" if self.phase != name else name


@dataclass
class DreamLayer:
    parent_shot_id: str = ""
    parent_clip: str = ""
    parent_still: str = ""
    sleeper_id: str = ""
    about: str = ""
    presentation: str = DEFAULT_PRESENTATION
    inner_vision: str = DEFAULT_VISION
    text_style: str = DEFAULT_TEXT_STYLE
    inspired: str = INSPIRED_LINE
    bubble_still: str = ""
    bubble_clip: str = ""
    look_refs: list[str] = field(default_factory=list)
    children: list[DreamBeat] = field(default_factory=list)
    wake: DreamBeat | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "parent_shot_id": self.parent_shot_id,
            "parent_clip": self.parent_clip,
            "parent_still": self.parent_still,
            "sleeper_id": self.sleeper_id,
            "about": self.about,
            "presentation": normalize_presentation(self.presentation),
            "inner_vision": normalize_vision(self.inner_vision),
            "text_style": normalize_text_style(self.text_style),
            "inspired": self.inspired,
            "bubble_still": self.bubble_still,
            "bubble_clip": self.bubble_clip,
            "look_refs": list(self.look_refs),
            "children": [asdict(b) for b in self.children],
            "wake": asdict(self.wake) if self.wake else None,
        }

    def ordered_beats(self) -> list[DreamBeat]:
        sleep = DreamBeat(
            id="sleep",
            title="sleep",
            phase=PHASE_SLEEP,
            prompt="Asleep. Breath. The room holds.",
            character_ids=[self.sleeper_id] if self.sleeper_id else [],
            shot_id=self.parent_shot_id,
            clip_path=self.parent_clip,
        )
        tail = [self.wake] if self.wake else []
        return [sleep, *self.children, *tail]


def dream_path(project: Project) -> Path:
    return project.root / DREAM_FILE


def load_dream(project: Project) -> DreamLayer:
    path = dream_path(project)
    if not path.is_file():
        return DreamLayer()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DreamLayer()
    if not isinstance(data, dict):
        return DreamLayer()
    children: list[DreamBeat] = []
    for item in data.get("children") or []:
        beat = _beat_from_dict(item)
        if beat:
            children.append(beat)
    wake = _beat_from_dict(data.get("wake")) if data.get("wake") else None
    raw_pres = str(data.get("presentation") or "")
    vision = data.get("inner_vision")
    if not vision and raw_pres.strip().lower() == "lucid overlay":
        vision = "lucid"
    return DreamLayer(
        parent_shot_id=str(data.get("parent_shot_id") or ""),
        parent_clip=str(data.get("parent_clip") or ""),
        parent_still=str(data.get("parent_still") or ""),
        sleeper_id=str(data.get("sleeper_id") or ""),
        about=str(data.get("about") or ""),
        presentation=normalize_presentation(raw_pres),
        inner_vision=normalize_vision(vision),
        text_style=normalize_text_style(data.get("text_style")),
        inspired=str(data.get("inspired") or INSPIRED_LINE),
        bubble_still=str(data.get("bubble_still") or ""),
        bubble_clip=str(data.get("bubble_clip") or ""),
        look_refs=[str(x).strip() for x in (data.get("look_refs") or []) if str(x).strip()],
        children=children,
        wake=wake,
    )


def save_dream(project: Project, layer: DreamLayer) -> Path:
    project.ensure_dirs()
    path = dream_path(project)
    write_json(path, layer.to_dict())
    return path


def _beat_from_dict(item: Any) -> DreamBeat | None:
    if not isinstance(item, dict):
        return None
    title = str(item.get("title") or "").strip()
    phase = str(item.get("phase") or PHASE_DREAM).strip() or PHASE_DREAM
    ids = [str(x).strip() for x in (item.get("character_ids") or []) if str(x).strip()]
    return DreamBeat(
        id=str(item.get("id") or new_id()),
        title=title or phase,
        phase=phase,
        prompt=str(item.get("prompt") or ""),
        character_ids=ids,
        shot_id=str(item.get("shot_id") or ""),
        clip_path=str(item.get("clip_path") or ""),
        look_refs=[str(x).strip() for x in (item.get("look_refs") or []) if str(x).strip()],
        card_still=str(item.get("card_still") or ""),
    )


def normalize_presentation(raw: str | None) -> str:
    text = (raw or "").strip().lower()
    if text in PRESENTATIONS:
        return text
    return _PRESENTATION_ALIASES.get(text, DEFAULT_PRESENTATION)


def normalize_vision(raw: str | None) -> str:
    text = (raw or "").strip().lower()
    if text in INNER_VISIONS:
        return text
    if "lucid" in text:
        return "lucid"
    if "daydream" in text or "day dream" in text:
        return "daydream"
    if "think" in text:
        return "thinking"
    return DEFAULT_VISION


def normalize_text_style(raw: str | None) -> str:
    text = (raw or "").strip().lower()
    if text in TEXT_STYLES:
        return text
    return _TEXT_ALIASES.get(text, DEFAULT_TEXT_STYLE)


def parse_dream_titles(raw: str | None) -> list[str]:
    text = (raw or "").strip()
    if not text:
        return list(DEFAULT_DREAM_TITLES)
    parts = [p.strip() for p in text.replace(";", ",").split(",")]
    titles = [p for p in parts if p]
    return titles[:8] or list(DEFAULT_DREAM_TITLES)


def title_from_chunk(chunk: str) -> str:
    words = " ".join((chunk or "").split())
    if not words:
        return "layer"
    bits = words.split()
    return " ".join(bits[:4]).strip(".,;:") or "layer"


def steps_from_about(about: str | None) -> list[tuple[str, str]]:
    """Turn free text into layer-by-layer dream beats."""
    text = (about or "").strip()
    if not text:
        return [(title, "") for title in DEFAULT_DREAM_TITLES]
    chunks = [c.strip() for c in re.split(r"\n\s*\n", text) if c.strip()]
    if len(chunks) == 1:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        numbered = [_NUMBERED_STEP.sub("", ln).strip() for ln in lines if _NUMBERED_STEP.match(ln)]
        if len(numbered) >= 2:
            chunks = numbered
        elif len(lines) >= 3:
            chunks = lines
        else:
            chunks = [text]
    out: list[tuple[str, str]] = []
    for chunk in chunks[:8]:
        out.append((title_from_chunk(chunk), chunk))
    return out or [(title, "") for title in DEFAULT_DREAM_TITLES]


def normalize_steps(raw) -> list[dict[str, str]]:
    steps: list[dict[str, str]] = []
    for item in raw or []:
        if isinstance(item, dict):
            title = str(item.get("title") or "").strip()
            prompt = str(item.get("prompt") or item.get("text") or "").strip()
        elif isinstance(item, (list, tuple)) and item:
            title = str(item[0] or "").strip()
            prompt = str(item[1] if len(item) > 1 else "").strip()
        else:
            continue
        if not title and not prompt:
            continue
        steps.append({"title": title or title_from_chunk(prompt), "prompt": prompt})
    return steps[:8]


def steps_markdown(steps) -> str:
    rows = normalize_steps(steps)
    if not rows:
        return "No dream layers yet. Add a beat, or type **Dream about…** and Open dream sequence."
    lines = ["**Dream layers (step by step)**"]
    for index, row in enumerate(rows, start=1):
        lines.append(f"{index}. **{row['title']}** — {row['prompt'][:160]}")
    return "\n".join(lines)


def bible_actor_labels(project: Project) -> list[str]:
    labels: list[str] = []
    for index, profile in enumerate(list_characters(project)):
        letter = ACTOR_LETTERS[index] if index < len(ACTOR_LETTERS) else str(index + 1)
        labels.append(f"{profile.id} — Actor {letter} · {profile.name}")
    return labels


def persist_look_refs(project: Project, files) -> list[str]:
    """Copy image + video look-refs into the project. Not a hosted asset library."""
    project.ensure_dirs()
    dest_dir = project.root / "dream_refs"
    dest_dir.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    for item in _iter_upload_paths(files):
        suffix = item.suffix.lower()
        if suffix not in IMAGE_SUFFIXES and suffix not in VIDEO_SUFFIXES:
            continue
        dest = dest_dir / f"{new_id()[:8]}_{item.name}"
        shutil.copy2(item, dest)
        saved.append(str(dest))
    return saved


def _iter_upload_paths(files) -> list[Path]:
    if not files:
        return []
    if not isinstance(files, list):
        files = [files]
    out: list[Path] = []
    for item in files:
        if item is None:
            continue
        if isinstance(item, dict):
            raw = item.get("path") or item.get("name") or ""
            path = Path(raw) if raw else None
        elif isinstance(item, (str, Path)):
            path = Path(item)
        elif hasattr(item, "name"):
            path = Path(item.name)
        else:
            continue
        if path is not None and path.is_file():
            out.append(path)
    return out


def look_ref_line(refs: list[str]) -> str:
    bits: list[str] = []
    for raw in refs or []:
        path = Path(raw)
        if not path.is_file():
            continue
        kind = "video" if _is_video(path) else "image"
        bits.append(f"LOOK REF ({kind}): {path.name}")
    return " ".join(bits)


def dream_placeholder_still(project: Project, label: str) -> Path:
    project.ensure_dirs()
    dest = project.stills_dir / f"dream_card_{new_id()[:8]}.png"
    img = Image.new("RGB", (640, 360), (16, 10, 28))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([18, 18, 622, 342], radius=22, outline=(139, 108, 255), width=3)
    draw.ellipse([48, 120, 168, 240], outline=(126, 232, 232), width=3)
    text = (label or "DREAM").strip()[:42]
    draw.text((200, 150), text, fill=(242, 238, 248))
    img.save(dest, format="PNG")
    return dest


def dream_board_items(project: Project) -> list[tuple[str, str]]:
    """Parent/child Take Board: SLEEP → DREAM layers → WAKE, then other takes."""
    layer = refresh_dream_clips(project, load_dream(project))
    items: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(path: str, label: str) -> None:
        if not path:
            return
        raw = Path(path)
        if not raw.is_file():
            return
        try:
            key = str(raw.resolve())
        except OSError:
            key = str(raw)
        if key in seen:
            return
        seen.add(key)
        items.append((str(raw), label))

    sleeper = sleeper_name(project, layer.sleeper_id) if layer.sleeper_id else "sleeper"
    if (
        normalize_presentation(layer.presentation) == "thought bubble"
        and layer.bubble_still
        and Path(layer.bubble_still).is_file()
    ):
        add(layer.bubble_still, f"SLEEP · {sleeper} · thought bubble")
        if layer.bubble_clip and Path(layer.bubble_clip).is_file():
            add(layer.bubble_clip, f"BUBBLE · {sleeper}")
    if layer.parent_clip or layer.parent_still:
        add(layer.parent_clip or layer.parent_still, f"SLEEP · {sleeper}")
    for beat in layer.children:
        path = beat.clip_path or beat.card_still
        if not path or not Path(path).is_file():
            card = dream_placeholder_still(project, f"DREAM · {beat.title}")
            beat.card_still = str(card)
            path = str(card)
        add(path, f"DREAM · {beat.title}")
    if layer.wake:
        path = layer.wake.clip_path or layer.wake.card_still
        if not path or not Path(path).is_file():
            card = dream_placeholder_still(project, "WAKE")
            layer.wake.card_still = str(card)
            path = str(card)
        add(path, "WAKE")
    if layer.children or layer.wake:
        save_dream(project, layer)
    for clip in project.load_gallery():
        label = clip.shot_name or Path(clip.path).name
        add(clip.path, label)
    return items


def is_enter_dream(target: str | None, note: str | None = "") -> bool:
    tgt = (target or "").strip().lower()
    text = (note or "").strip().lower()
    if tgt in HEAD_TARGETS:
        return True
    if any(word in text for word in _ENTER_WORDS):
        return True
    return False


def hint_head_note(target: str | None, note: str | None) -> str:
    current = (note or "").strip()
    if (target or "").strip().lower() in HEAD_TARGETS and not current:
        return "Enter dream."
    return current


def dream_about_heading(name: str) -> str:
    who = (name or "this person").strip() or "this person"
    return (
        f"### Dream about… — {who}\n"
        "Pause the take. Pick Dream style (Enter dream / Thought bubble), "
        "inner vision, and text stylize. Actor A / B / C. Type the dream. "
        "Add layers one by one. Image + video look-refs optional."
    )


def sleeper_name(project: Project, sleeper_id: str) -> str:
    cid = (sleeper_id or "").strip()
    if not cid:
        return "the sleeper"
    try:
        return load_character(project, cid).name
    except (OSError, ValueError, FileNotFoundError, CharacterError):
        return cid


def dream_beat_sheet(
    project: Project,
    *,
    sleeper_id: str = "",
    titles: list[str] | None = None,
    character_ids: list[str] | None = None,
) -> str:
    sleeper = sleeper_name(project, sleeper_id)
    kids = titles or list(DEFAULT_DREAM_TITLES)
    names = _cast_names(project, character_ids or [])
    cast_line = ", ".join(names) if names else "Character Bible cast"
    lines = [
        "# Dream beat sheet (local · director rewrite)",
        INSPIRED_LINE,
        "",
        f"**BEAT 1 — SLEEP**",
        f"{sleeper} asleep. Breath. The room holds. Parent take.",
        "",
    ]
    for index, title in enumerate(kids, start=2):
        prompt = _dream_prompt(title, sleeper, cast_line)
        lines.append(f"**BEAT {index} — DREAM · {title}**")
        lines.append(prompt)
        lines.append("")
    wake_n = len(kids) + 2
    lines.append(f"**BEAT {wake_n} — WAKE**")
    lines.append(f"Back to the bed. {sleeper} opens their eyes. The room is the room.")
    lines.append("")
    return "\n".join(lines).strip() + "\n"


def _dream_prompt(title: str, sleeper: str, cast_line: str) -> str:
    key = title.strip().lower()
    stock = {
        "island": (
            f"Dream island. Warm water, original shoreline. {sleeper} with {cast_line}. "
            f"{INSPIRED_LINE}"
        ),
        "meet crush": (
            f"Dream: {sleeper} meets a crush — an original Character Bible adult, "
            f"not a celebrity or franchise face. Held look. {INSPIRED_LINE}"
        ),
        "talk": (
            f"Dream talk. {sleeper} and {cast_line} speak quietly. "
            f"No copied movie dialogue. {INSPIRED_LINE}"
        ),
    }
    if key in stock:
        return stock[key]
    return (
        f"Dream · {title}. Original Character Bible bodies ({cast_line}). "
        f"{sleeper} is the sleeper. {INSPIRED_LINE}"
    )


def _cast_names(project: Project, ids: list[str]) -> list[str]:
    names: list[str] = []
    for profile in list_characters(project):
        if profile.id in ids:
            names.append(profile.name)
    if names:
        return names
    return [cid for cid in ids if cid]


def _tags_for(ids: list[str]) -> list[str]:
    tags: list[str] = []
    for cid in ids:
        if cid in CHARACTER_TAGS and cid not in tags:
            tags.append(cid)
    return tags


def _is_video(path: str | Path) -> bool:
    return Path(path).suffix.lower() in VIDEO_SUFFIXES


def _is_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in IMAGE_SUFFIXES


def resolve_sleeper_id(project: Project, raw: str | None) -> str:
    text = (raw or "").strip()
    if " — " in text:
        text = text.split(" — ", 1)[0].strip()
    if text:
        return text
    for cid in project.active_cast or []:
        try:
            profile = load_character(project, cid)
        except (OSError, ValueError, FileNotFoundError, CharacterError):
            continue
        if not role_is_minor(getattr(profile, "role", "Adult")):
            return profile.id
    if project.active_cast:
        return project.active_cast[0]
    faces = list_characters(project)
    return faces[0].id if faces else "alison"


def assert_dream_safe(
    project: Project,
    layer: DreamLayer,
    *,
    intimacy: str = "",
    intensity: float = 0,
) -> None:
    ids: list[str] = []
    if layer.sleeper_id:
        ids.append(layer.sleeper_id)
    for beat in layer.children:
        ids.extend(beat.character_ids)
    if layer.wake:
        ids.extend(layer.wake.character_ids)
    unique = list(dict.fromkeys(i for i in ids if i))
    if not unique:
        return
    mode = intimacy if intimacy in INTIMACY_MODES else STORY_INTIMACY
    heat = clamp_content_intensity(intensity)
    if not (is_intimate(mode) or intensity_requires_numeric_age(heat)):
        return
    try:
        profiles = load_selected_characters(project, unique)
    except (OSError, ValueError, FileNotFoundError, CharacterError):
        profiles = []
    assert_adult_cast(
        profiles,
        intimacy_mode=mode,
        content_intensity=heat,
        context="Dream / Lucid Layer",
    )


def enter_dream(
    project: Project,
    *,
    parent_clip: str = "",
    parent_still: str = "",
    parent_shot_id: str = "",
    sleeper_id: str = "",
    titles: list[str] | None = None,
    about: str = "",
    steps=None,
    look_refs: list[str] | None = None,
    character_ids: list[str] | None = None,
    presentation: str = DEFAULT_PRESENTATION,
    inner_vision: str = DEFAULT_VISION,
    text_style: str = DEFAULT_TEXT_STYLE,
    intimacy: str = "",
    intensity: float = 0,
    cx: float = 0.50,
    cy: float = 0.28,
) -> DreamLayer:
    """Open or refresh the lucid layer from a sleeping parent take / still."""
    project.ensure_dirs()
    clip = (parent_clip or "").strip()
    still = (parent_still or "").strip()
    if clip and not Path(clip).is_file():
        clip = ""
    if still and not Path(still).is_file():
        still = ""
    if clip and _is_image(clip) and not still:
        still = clip
        clip = ""
    if still and _is_video(still) and not clip:
        clip = still
        still = ""
    existing = load_dream(project)
    if not clip and not still:
        clip = existing.parent_clip if existing.parent_clip and Path(existing.parent_clip).is_file() else ""
        still = existing.parent_still if existing.parent_still and Path(existing.parent_still).is_file() else ""
    if not clip and not still:
        raise DreamError(
            "Pause a sleeping take on Take Board, then click the person (Dream about…)."
        )

    sleeper = resolve_sleeper_id(project, sleeper_id)
    ids = [str(x).strip() for x in (character_ids or project.active_cast or []) if str(x).strip()]
    if sleeper and sleeper not in ids:
        ids = [sleeper, *ids]
    refs = [str(x).strip() for x in (look_refs or []) if str(x).strip()]
    planned = normalize_steps(steps)
    if not planned and (about or "").strip():
        planned = [{"title": t, "prompt": p} for t, p in steps_from_about(about)]
    if not planned:
        planned = [{"title": t, "prompt": ""} for t in (titles or list(DEFAULT_DREAM_TITLES))]
    titles = [row["title"] for row in planned]
    shot_id = (parent_shot_id or "").strip() or existing.parent_shot_id
    layer = DreamLayer(
        parent_shot_id=shot_id,
        parent_clip=clip or existing.parent_clip,
        parent_still=still or existing.parent_still,
        sleeper_id=sleeper,
        about=(about or existing.about or "").strip(),
        presentation=normalize_presentation(presentation or existing.presentation),
        inner_vision=normalize_vision(inner_vision or existing.inner_vision),
        text_style=normalize_text_style(
            text_style if text_style is not None else existing.text_style
        ),
        inspired=INSPIRED_LINE,
        bubble_still=existing.bubble_still,
        bubble_clip=existing.bubble_clip,
        look_refs=refs or list(existing.look_refs),
        children=list(existing.children),
        wake=existing.wake,
    )
    same_parent = bool(
        (clip and clip == existing.parent_clip)
        or (still and still == existing.parent_still)
        or (shot_id and shot_id == existing.parent_shot_id)
    )
    wanted = [t.strip().lower() for t in titles]
    have = [b.title.strip().lower() for b in existing.children]
    if not layer.children or not same_parent or wanted != have:
        layer.children = _make_child_beats(
            project,
            titles,
            ids,
            sleeper,
            prompts=[row["prompt"] for row in planned],
            look_refs=layer.look_refs,
        )
        layer.wake = _make_wake_beat(project, sleeper, ids, look_refs=layer.look_refs)
    layer = apply_vision_prompt(layer)
    if layer.presentation == "thought bubble":
        layer = apply_thought_bubble_overlay(project, layer, cx=cx, cy=cy)
    assert_dream_safe(project, layer, intimacy=intimacy, intensity=intensity)
    save_dream(project, layer)
    return layer


def _first_existing(*paths: str) -> str:
    for path in paths:
        if path and Path(path).is_file():
            return path
    return ""


def _first_look_still(refs: list[str]) -> str:
    for raw in refs or []:
        if raw and Path(raw).is_file() and _is_image(raw):
            return raw
    return ""


def _apply_look_still(project: Project, shot: ShotCard, refs: list[str]) -> ShotCard:
    plate = _first_look_still(refs)
    if not plate:
        return shot
    dest = project.stills_dir / f"dream_look_{new_id()[:8]}{Path(plate).suffix.lower()}"
    shutil.copy2(plate, dest)
    shot.start_frame = dest.name
    extra = look_ref_line(refs)
    if extra and extra not in (shot.director_intent or ""):
        shot.director_intent = f"{shot.director_intent} {extra}".strip()[:800]
    return shot


def _make_child_beats(
    project: Project,
    titles: list[str],
    ids: list[str],
    sleeper: str,
    prompts: list[str] | None = None,
    look_refs: list[str] | None = None,
) -> list[DreamBeat]:
    sleeper_label = sleeper_name(project, sleeper)
    cast_line = ", ".join(_cast_names(project, ids)) or "Character Bible cast"
    tags = _tags_for(ids)
    refs = [str(x) for x in (look_refs or []) if str(x).strip()]
    beats: list[DreamBeat] = []
    for index, title in enumerate(titles):
        custom = ""
        if prompts and index < len(prompts):
            custom = (prompts[index] or "").strip()
        prompt = custom or _dream_prompt(title, sleeper_label, cast_line)
        if refs:
            extra = look_ref_line(refs)
            if extra and extra not in prompt:
                prompt = f"{prompt} {extra}".strip()
        shot = ShotCard(
            id=new_shot_id(),
            name=f"dream · {title}",
            duration=SHOT_DURATION,
            camera_move=PLAN_CAMERAS[index % len(PLAN_CAMERAS)],
            subject_motion_strength=0.32,
            body_motion_notes=f"Dream · {title}. {INSPIRED_LINE}",
            director_intent=prompt[:800],
            intimacy_mode=STORY_INTIMACY,
            content_intensity=0.0,
            character_ids=list(ids),
            character_tags=list(tags),
            lighting=DEFAULT_LIGHTING,
        )
        shot = _apply_look_still(project, shot, refs)
        project.save_shot(shot)
        card = dream_placeholder_still(project, f"DREAM · {title}")
        beats.append(
            DreamBeat(
                id=new_id(),
                title=title,
                phase=PHASE_DREAM,
                prompt=prompt,
                character_ids=list(ids),
                shot_id=shot.id,
                look_refs=list(refs),
                card_still=str(card),
            )
        )
    return beats


def _make_wake_beat(
    project: Project,
    sleeper: str,
    ids: list[str],
    look_refs: list[str] | None = None,
) -> DreamBeat:
    name = sleeper_name(project, sleeper)
    prompt = f"Wake. {name} opens their eyes. The room is the room. {INSPIRED_LINE}"
    shot = ShotCard(
        id=new_shot_id(),
        name="wake",
        duration=SHOT_DURATION,
        camera_move="slow push-in",
        subject_motion_strength=0.22,
        body_motion_notes="Eyes open. Back to the bed.",
        director_intent=prompt[:800],
        intimacy_mode=STORY_INTIMACY,
        content_intensity=0.0,
        character_ids=list(ids),
        character_tags=_tags_for(ids),
        lighting=DEFAULT_LIGHTING,
    )
    project.save_shot(shot)
    card = dream_placeholder_still(project, "WAKE")
    return DreamBeat(
        id=new_id(),
        title="wake",
        phase=PHASE_WAKE,
        prompt=prompt,
        character_ids=list(ids),
        shot_id=shot.id,
        look_refs=list(look_refs or []),
        card_still=str(card),
    )


def apply_lucid_line(layer: DreamLayer) -> DreamLayer:
    """Back-compat: old lucid overlay is thought bubble + lucid vision."""
    layer.presentation = "thought bubble"
    layer.inner_vision = "lucid"
    return apply_vision_prompt(layer)


def apply_vision_prompt(layer: DreamLayer) -> DreamLayer:
    vision = normalize_vision(layer.inner_vision)
    extra = VISION_LINES[vision]
    if normalize_presentation(layer.presentation) == "enter dream" and vision == "dream":
        extra = (
            "Enter dream: they leave the bedroom and are inside the dream. "
            + INSPIRED_LINE
        )
    marker = VISION_MARKERS[vision]
    for beat in layer.children:
        body = (beat.prompt or "").lower()
        if marker not in body:
            beat.prompt = f"{beat.prompt} {extra}".strip()
    return layer


def caption_for_layer(layer: DreamLayer) -> str:
    about = (layer.about or "").strip()
    if about:
        return about
    if layer.children:
        first = layer.children[0]
        return (first.prompt or first.title or "").strip()
    return ""


def extract_clip_frame(src: Path, dest: Path) -> Path | None:
    """First frame of a look-ref clip. Honest no-op if ffmpeg is missing."""
    ok, _msg = ffmpeg_available()
    if not ok:
        return None
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        run_ffmpeg(["-y", "-i", str(src), "-vframes", "1", str(dest)])
    except FFmpegError:
        return None
    return dest if dest.is_file() else None


def resolve_bubble_content(project: Project, refs: list[str]) -> tuple[str, str]:
    """Still + optional mini-clip for the thought-bubble plate."""
    video = ""
    for raw in refs or []:
        if raw and Path(raw).is_file() and _is_video(raw):
            video = raw
            break
    if video:
        dest = project.stills_dir / f"dream_clipframe_{new_id()[:8]}.png"
        frame = extract_clip_frame(Path(video), dest)
        if frame:
            return str(frame), video
    still = _first_look_still(refs)
    return still, video if video else ""


def apply_thought_bubble_overlay(
    project: Project,
    layer: DreamLayer,
    *,
    cx: float = 0.50,
    cy: float = 0.28,
) -> DreamLayer:
    plate = _first_existing(layer.parent_still, layer.bubble_still)
    if (not plate or not _is_image(plate)) and layer.parent_clip and _is_video(layer.parent_clip):
        dest = project.stills_dir / f"dream_sleepframe_{new_id()[:8]}.png"
        frame = extract_clip_frame(Path(layer.parent_clip), dest)
        if frame:
            layer.parent_still = str(frame)
            plate = str(frame)
    if not plate or not Path(plate).is_file() or not _is_image(plate):
        return layer
    content, clip = resolve_bubble_content(project, layer.look_refs)
    if clip:
        layer.bubble_clip = clip
    caption = caption_for_layer(layer)
    dest = project.stills_dir / f"dream_bubble_{new_id()[:8]}.png"
    layer.bubble_still = str(
        draw_thought_bubble(
            Path(plate),
            dest,
            cx=cx,
            cy=cy,
            caption=caption,
            content_still=Path(content) if content else None,
            text_style=layer.text_style,
            vision=layer.inner_vision,
        )
    )
    return layer


def refresh_dream_clips(project: Project, layer: DreamLayer) -> DreamLayer:
    """Attach gallery MP4s onto child / wake beats when Animate has landed."""
    by_shot: dict[str, str] = {}
    for clip in project.load_gallery():
        if clip.shot_id and Path(clip.path).is_file():
            by_shot[clip.shot_id] = clip.path
    if layer.parent_shot_id and layer.parent_shot_id in by_shot:
        layer.parent_clip = by_shot[layer.parent_shot_id]
    for beat in layer.children:
        if beat.shot_id and beat.shot_id in by_shot:
            beat.clip_path = by_shot[beat.shot_id]
    if layer.wake and layer.wake.shot_id and layer.wake.shot_id in by_shot:
        layer.wake.clip_path = by_shot[layer.wake.shot_id]
    return layer


def stitch_paths(layer: DreamLayer) -> list[Path]:
    paths: list[Path] = []
    seen: set[str] = set()
    for beat in layer.ordered_beats():
        raw = (beat.clip_path or "").strip()
        if not raw:
            continue
        path = Path(raw)
        key = str(path.resolve()) if path.is_file() else ""
        if not key or key in seen:
            continue
        seen.add(key)
        paths.append(path)
    return paths


def stitch_dream_reel(project: Project, layer: DreamLayer | None = None) -> Path:
    current = refresh_dream_clips(project, layer or load_dream(project))
    clips = stitch_paths(current)
    if len(clips) < 2:
        raise DreamError(
            "Need at least two animated clips (sleep + a dream, or dream + wake) "
            "before Stitch sleep → dream → wake."
        )
    dest = project.outputs_dir / f"dream_{new_id()[:8]}.mp4"
    stitch_clips(clips, dest)
    project.register_output(dest, generator="dream-stitch")
    save_dream(project, current)
    return dest


def dream_markdown(layer: DreamLayer | None = None) -> str:
    head = (
        "### Dream / Lucid Layer\n"
        "Pause the sleeping take. Click the person → **Dream about…** "
        "(Dream style + Actor A / B / C + free text + look-refs). "
        "Linked child scenes sit under that sleeper. "
        f"{INSPIRED_LINE} Animate, then **Stitch sleep → dream → wake**."
    )
    if not layer or (not layer.parent_clip and not layer.parent_still and not layer.children):
        return head + "\n\nNo dream yet. Pause a take, click the person, Dream about…"
    sleeper = layer.sleeper_id or "sleeper"
    about = (layer.about or "").strip()
    style = normalize_presentation(layer.presentation)
    vision = normalize_vision(layer.inner_vision)
    text = normalize_text_style(layer.text_style)
    parent_name = (
        Path(layer.parent_clip).name
        if layer.parent_clip
        else (Path(layer.parent_still).name if layer.parent_still else "—")
    )
    lines = [
        head,
        "",
        f"**Parent (sleep):** `{parent_name}` · {sleeper}",
        f"**Dream style:** {style} · **Inner vision:** {vision} · **Text:** {text}",
    ]
    if style == "enter dream":
        lines.append("Enter dream — they leave the sleeping shot and are inside the sequence.")
    else:
        lines.append(
            "Thought bubble — overlay stays on the sleeping shot "
            "(still, mini-clip, or styled text)."
        )
    if about:
        lines.append(f"**Dream about:** {about[:240]}")
    if layer.look_refs:
        lines.append("**Look-refs:** " + ", ".join(Path(r).name for r in layer.look_refs if r))
    if layer.children:
        lines.append("**Dream children:**")
        for beat in layer.children:
            shot = f" `{beat.shot_id}`" if beat.shot_id else ""
            clip = " · clip ready" if beat.clip_path and Path(beat.clip_path).is_file() else ""
            lines.append(f"- {beat.label()}{shot}{clip}")
    if layer.wake:
        clip = " · clip ready" if layer.wake.clip_path and Path(layer.wake.clip_path).is_file() else ""
        lines.append(f"**Wake:** `{layer.wake.shot_id or '—'}`{clip}")
    if layer.bubble_still and Path(layer.bubble_still).is_file():
        lines.append(f"Thought-bubble plate: `{Path(layer.bubble_still).name}`")
    if layer.bubble_clip and Path(layer.bubble_clip).is_file():
        lines.append(f"Thought-bubble mini-clip: `{Path(layer.bubble_clip).name}`")
    return "\n".join(lines)


def _load_font(size: int, *, italic: bool = False) -> ImageFont.ImageFont:
    names = (
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        )
        if italic
        else (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        )
    )
    for path in names:
        if Path(path).is_file():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int, limit: int = 6) -> list[str]:
    words = (text or "").split()
    if not words:
        return []
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
            if len(lines) >= limit:
                return lines
    if current and len(lines) < limit:
        lines.append(current)
    return lines


def _paste_inset(base: Image.Image, content: Path, box: tuple[int, int, int, int], pad: int) -> None:
    if not content or not Path(content).is_file():
        return
    try:
        inset = Image.open(content).convert("RGB")
    except OSError:
        return
    x0, y0, x1, y1 = box
    tw = max(8, x1 - x0 - pad * 2)
    th = max(8, y1 - y0 - pad * 2)
    inset.thumbnail((tw, th), Image.Resampling.LANCZOS)
    px = x0 + (x1 - x0 - inset.width) // 2
    py = y0 + pad
    base.paste(inset, (px, py))


def draw_thought_bubble(
    src: Path,
    dest: Path,
    *,
    cx: float = 0.50,
    cy: float = 0.32,
    caption: str = "",
    content_still: Path | None = None,
    text_style: str = DEFAULT_TEXT_STYLE,
    vision: str = DEFAULT_VISION,
) -> Path:
    """Local plate on the sleeping shot — still, mini-clip frame, or styled text."""
    img = Image.open(src).convert("RGBA")
    width, height = img.size
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    head_x = int(width * min(0.95, max(0.05, cx)))
    head_y = int(height * min(0.95, max(0.05, cy)))
    if cx >= 0.55:
        bx0, bx1 = int(width * 0.04), int(width * 0.46)
    else:
        bx0, bx1 = int(width * 0.54), int(width * 0.96)
    by0, by1 = int(height * 0.05), int(height * 0.46)
    stroke = max(2, width // 180)
    style = normalize_text_style(text_style)
    vis = normalize_vision(vision)
    label = (caption or "").strip()
    if style != "none" and vis != "dream":
        label = f"{vis} — {label}" if label else vis
    draw.ellipse(
        [bx0, by0, bx1, by1],
        fill=(232, 226, 248, 205),
        outline=(139, 108, 255, 240),
        width=stroke,
    )
    mid_x = (bx0 + bx1) // 2
    mid_y = by1
    r1 = max(6, width // 55)
    r2 = max(4, width // 80)
    c1x = int(mid_x * 0.7 + head_x * 0.3)
    c1y = int(mid_y * 0.55 + head_y * 0.45)
    c2x = int(mid_x * 0.35 + head_x * 0.65)
    c2y = int(mid_y * 0.25 + head_y * 0.75)
    draw.ellipse(
        [c1x - r1, c1y - r1, c1x + r1, c1y + r1],
        fill=(232, 226, 248, 200),
        outline=(139, 108, 255, 230),
        width=max(1, stroke - 1),
    )
    draw.ellipse(
        [c2x - r2, c2y - r2, c2x + r2, c2y + r2],
        fill=(232, 226, 248, 190),
        outline=(126, 232, 232, 220),
        width=max(1, stroke - 1),
    )
    composed = Image.alpha_composite(img, overlay)
    pad = max(10, width // 48)
    inset_bottom = by1 - (height // 10 if style == "comic bubble" and label else pad)
    if content_still:
        _paste_inset(composed, Path(content_still), (bx0, by0, bx1, inset_bottom), pad)
    ink = ImageDraw.Draw(composed)
    font = _load_font(max(12, width // 42), italic=style == "diary caption")
    max_w = max(24, bx1 - bx0 - pad * 2)
    if style == "comic bubble" and label:
        lines = _wrap_text(ink, label, font, max_w)
        ty = inset_bottom - 4 if content_still else by0 + pad + (by1 - by0) // 3
        for line in lines:
            ink.text((bx0 + pad, ty), line, fill=(40, 28, 64, 255), font=font)
            ty += max(14, width // 36)
    elif style == "soft subtitle" and label:
        bar_h = max(28, height // 9)
        bar = Image.new("RGBA", (width, bar_h), (16, 10, 28, 170))
        composed.paste(bar, (0, height - bar_h), bar)
        ink = ImageDraw.Draw(composed)
        lines = _wrap_text(ink, label, font, width - pad * 2, limit=2)
        ty = height - bar_h + 6
        for line in lines:
            bbox = ink.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            ink.text(((width - tw) // 2, ty), line, fill=(242, 238, 248, 255), font=font)
            ty += max(14, width // 36)
    elif style == "diary caption" and label:
        scrap_h = max(36, height // 7)
        sx0, sy0 = bx0 + pad // 2, min(height - scrap_h - pad, by1 - scrap_h // 3)
        sx1, sy1 = bx1 - pad // 2, sy0 + scrap_h
        ink.rounded_rectangle(
            [sx0, sy0, sx1, sy1],
            radius=6,
            fill=(236, 230, 252, 230),
            outline=(139, 108, 255, 240),
            width=max(1, stroke - 1),
        )
        lines = _wrap_text(ink, label, font, max(24, sx1 - sx0 - pad), limit=3)
        ty = sy0 + 6
        for line in lines:
            ink.text((sx0 + 8, ty), line, fill=(40, 28, 64, 255), font=font)
            ty += max(14, width // 38)
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    composed.convert("RGB").save(dest, format="PNG")
    return dest


def link_planned_shots(
    layer: DreamLayer,
    shots: list[ShotCard],
    *,
    sleeper_id: str = "",
) -> DreamLayer:
    """Map Plan shots cards onto sleep / dream / wake when the body is a dream sheet."""
    if not shots:
        return layer
    rest = list(shots)
    first = rest[0]
    if "sleep" in (first.name + " " + first.director_intent).lower():
        layer.parent_shot_id = first.id
        rest = rest[1:]
    if rest and "wake" in (rest[-1].name + " " + rest[-1].director_intent).lower():
        last = rest[-1]
        layer.wake = DreamBeat(
            id=new_id(),
            title="wake",
            phase=PHASE_WAKE,
            prompt=last.director_intent or last.body_motion_notes,
            character_ids=list(last.character_ids),
            shot_id=last.id,
        )
        rest = rest[:-1]
    children: list[DreamBeat] = []
    for shot in rest:
        title = shot.name.split("·")[-1].strip() if "·" in shot.name else shot.name
        title = title.replace("dream", "").replace("DREAM", "").strip(" ·") or shot.name
        children.append(
            DreamBeat(
                id=new_id(),
                title=title,
                phase=PHASE_DREAM,
                prompt=shot.director_intent or shot.body_motion_notes,
                character_ids=list(shot.character_ids),
                shot_id=shot.id,
            )
        )
    if children:
        layer.children = children
    if sleeper_id:
        layer.sleeper_id = sleeper_id
    return layer
