"""Director Note (performance) + World Note (mise-en-scène).

Click a Character Bible face → Director Note (emotion, micro-expression,
full human behavior, acting beats). World Note is a separate environment
control (weather, thunder, earth, wind, setting, placement, prop action).
Apply folds both into Enhance → Pose → Animate.

Intimate / explicit intensity is adult 18+ ONLY. The picker may include
any age for non-sexual acting, emotion, and placement. Never route
minors into intimacy or porn intensity. Zero credits.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from film_lab.characters import (
    CharacterError,
    assert_adult_cast,
    list_characters,
    load_selected_characters,
    parse_age_years,
    resolve_age_years,
    resolve_refs,
    years_from_age_band,
)
from film_lab.intensity import intensity_requires_numeric_age
from film_lab.intimacy import is_intimate
from film_lab.project import Project
from film_lab.performance import (
    DEFAULT_BEHAVIOR,
    DEFAULT_MICRO,
    DEFAULT_PROP,
    active as perf_active,
    compose_performance,
    compose_prop_action,
)
from film_lab.senses import EMOTIONS, WEATHERS
from film_lab.util import write_json

NOTES_FILE = "director_notes.json"

THUNDER_CHOICES: tuple[str, ...] = ("none", "distant", "overhead", "rolling")
EARTH_CHOICES: tuple[str, ...] = (
    "dry ground",
    "wet earth",
    "mud",
    "dust",
    "grass",
    "pavement",
    "floorboards",
)
WIND_CHOICES: tuple[str, ...] = ("still", "breeze", "gust", "gale")
OUTDOOR_CHOICES: tuple[str, ...] = (
    "none",
    "street",
    "sky",
    "wide outdoor",
    "bus stop",
    "walk home",
    "drone aerial",
)
DEFAULT_OUTDOOR = "none"

DEFAULT_EMOTION = "tenderness"
DEFAULT_WEATHER = "clear"
DEFAULT_THUNDER = "none"
DEFAULT_EARTH = "floorboards"
DEFAULT_WIND = "still"
DEFAULT_WARDROBE = "clothes stay"

WARDROBE_MOTIONS: tuple[str, ...] = (
    "clothes stay",
    "undress through motion",
    "into explicit sex",
)
UNDRESS_MOTIONS: frozenset[str] = frozenset(
    {"undress through motion", "into explicit sex"}
)
EXPLICIT_INTENSITY_MIN = 0.90

SAFETY_LINE = (
    "Intimate / explicit modes: adult 18+ ONLY. "
    "Director Notes on any age are performance / placement. "
    "Never route minors into intimacy or porn intensity. "
    "Undress through motion / into explicit sex needs the Explicit dial "
    "and an adult 18+ cast. "
    "Regular / story filming may include Teen / Child / Infant for non-sexual "
    "everyday scenes only. Intimate tools stay locked unless mode is 18+ Explicit."
)

_DIR_LINE = re.compile(r"^DIRECTOR NOTE \([^)]+\):.*$", re.M)
_WORLD_LINE = re.compile(r"^WORLD NOTE \(mise-en-scène\):.*$", re.M)
_SET_LINE = re.compile(r"^SET NOTE \(3D set / camera\):.*$", re.M)
_MARK_LINE = re.compile(r"^MARK NOTE \([^)]+\):.*$", re.M)
_ENV_LINE = re.compile(r"^ENV LOCK \(set / world\):.*$", re.M)


class DirectorNoteError(ValueError):
    """Blocked note apply — usually a minor on an intimate route."""


@dataclass
class CastFace:
    id: str
    name: str
    age_years: int | None
    age_band: str = ""
    role: str = "Adult"
    thumb: str = ""

    @property
    def adult(self) -> bool:
        return face_is_adult(self)

    @property
    def caption(self) -> str:
        years = self.age_years
        role = (self.role or "Adult").strip() or "Adult"
        if years is None:
            return f"{self.name} · {role} · age unset"
        return f"{self.name} · {role} · {years}"


@dataclass
class DirectorNote:
    character_id: str
    character_name: str
    emotion: str = DEFAULT_EMOTION
    acting_beats: str = ""
    wardrobe_motion: str = DEFAULT_WARDROBE
    micro_expression: str = DEFAULT_MICRO
    behavior: str = DEFAULT_BEHAVIOR

    def line(self) -> str:
        emotion = (self.emotion or DEFAULT_EMOTION).strip() or DEFAULT_EMOTION
        wardrobe = (self.wardrobe_motion or DEFAULT_WARDROBE).strip() or DEFAULT_WARDROBE
        beats = " ".join((self.acting_beats or "").split())
        parts = [emotion]
        face = perf_active(self.micro_expression)
        body = perf_active(self.behavior)
        if face:
            parts.append(f"micro-expression {face}")
        if body:
            parts.append(f"behavior {body}")
        if wardrobe and wardrobe != "clothes stay":
            parts.append(wardrobe)
        if beats:
            parts.append(beats)
        return f"DIRECTOR NOTE ({self.character_name} — performance): {'; '.join(parts)}"


@dataclass
class WorldNote:
    weather: str = ""
    thunder: str = ""
    earth: str = ""
    wind: str = ""
    setting: str = ""
    placement: str = ""
    outdoor: str = ""
    prop_action: str = DEFAULT_PROP

    def line(self) -> str:
        bits = [
            f"weather {self.weather}" if self.weather else "",
            f"thunder {self.thunder}" if self.thunder and self.thunder != "none" else "",
            f"earth {self.earth}" if self.earth else "",
            f"wind {self.wind}" if self.wind else "",
            f"outdoor plate {self.outdoor}" if self.outdoor and self.outdoor != "none" else "",
            f"setting {self.setting.strip()}" if self.setting.strip() else "",
            f"placement {self.placement.strip()}" if self.placement.strip() else "",
            compose_prop_action(self.prop_action).replace("prop action: ", "prop ")
            if perf_active(self.prop_action)
            else "",
        ]
        body = "; ".join(b for b in bits if b)
        if not body:
            return ""
        return f"WORLD NOTE (mise-en-scène): {body}"

    def is_empty(self) -> bool:
        return not self.line()


@dataclass
class ProjectNotes:
    director: dict[str, DirectorNote] = field(default_factory=dict)
    world: WorldNote = field(default_factory=WorldNote)

    def render_block(self) -> str:
        lines = [note.line() for note in self.director.values() if note.line()]
        world = self.world.line()
        if world:
            lines.append(world)
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "director": {k: asdict(v) for k, v in self.director.items()},
            "world": asdict(self.world),
        }


def notes_path(project: Project) -> Path:
    return project.root / NOTES_FILE


def load_notes(project: Project) -> ProjectNotes:
    path = notes_path(project)
    if not path.is_file():
        return ProjectNotes()
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return ProjectNotes()
    import json

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return ProjectNotes()
    if not isinstance(data, dict):
        return ProjectNotes()
    director: dict[str, DirectorNote] = {}
    blob = data.get("director") or {}
    if isinstance(blob, dict):
        for key, item in blob.items():
            if not isinstance(item, dict):
                continue
            cid = str(item.get("character_id") or key).strip()
            if not cid:
                continue
            director[cid] = DirectorNote(
                character_id=cid,
                character_name=str(item.get("character_name") or cid),
                emotion=str(item.get("emotion") or DEFAULT_EMOTION),
                acting_beats=str(item.get("acting_beats") or ""),
                wardrobe_motion=str(item.get("wardrobe_motion") or DEFAULT_WARDROBE),
                micro_expression=str(item.get("micro_expression") or DEFAULT_MICRO),
                behavior=str(item.get("behavior") or DEFAULT_BEHAVIOR),
            )
    world_raw = data.get("world") if isinstance(data.get("world"), dict) else {}
    world = WorldNote(
        weather=str(world_raw.get("weather") or ""),
        thunder=str(world_raw.get("thunder") or ""),
        earth=str(world_raw.get("earth") or ""),
        wind=str(world_raw.get("wind") or ""),
        setting=str(world_raw.get("setting") or ""),
        placement=str(world_raw.get("placement") or ""),
        outdoor=str(world_raw.get("outdoor") or ""),
        prop_action=str(world_raw.get("prop_action") or DEFAULT_PROP),
    )
    return ProjectNotes(director=director, world=world)


def save_notes(project: Project, notes: ProjectNotes) -> Path:
    project.ensure_dirs()
    path = notes_path(project)
    write_json(path, notes.to_dict())
    return path


def face_is_adult(face: CastFace) -> bool:
    years = parse_age_years(face.age_years)
    if years is not None:
        return years >= 18
    band = years_from_age_band(face.age_band)
    if band is not None:
        return band >= 18
    return True


def notes_need_adult(intimacy: str | None, intensity: float | int | str | None) -> bool:
    return is_intimate(intimacy) or intensity_requires_numeric_age(intensity)


def wardrobe_is_undress(motion: str | None) -> bool:
    return (motion or "").strip().lower() in UNDRESS_MOTIONS


def notes_ask_undress(notes: ProjectNotes | None = None, text: str = "") -> bool:
    blob = (text or "").lower()
    if any(key in blob for key in UNDRESS_MOTIONS):
        return True
    if notes is None:
        return False
    return any(wardrobe_is_undress(n.wardrobe_motion) for n in notes.director.values())


def strip_note_blocks(text: str) -> str:
    cleaned = _DIR_LINE.sub("", text or "")
    cleaned = _WORLD_LINE.sub("", cleaned)
    cleaned = _SET_LINE.sub("", cleaned)
    cleaned = _MARK_LINE.sub("", cleaned)
    cleaned = _ENV_LINE.sub("", cleaned)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def fold_into_seed(
    seed: str,
    notes: ProjectNotes,
    set_line: str = "",
    mark_line: str = "",
    env_line: str = "",
) -> str:
    base = strip_note_blocks(seed)
    parts = [
        p
        for p in (
            notes.render_block(),
            (set_line or "").strip(),
            (mark_line or "").strip(),
            (env_line or "").strip(),
        )
        if p
    ]
    block = "\n".join(parts)
    if not block:
        return base
    if not base:
        return block
    return f"{base}\n\n{block}"


def fold_desk(project: Project, seed: str) -> str:
    """Fold Director / World / Set / Mark / Environment lock into one seed."""
    from film_lab.envlock import load_env_lock
    from film_lab.mark import load_marks
    from film_lab.setdesk import load_set_note

    notes = load_notes(project)
    set_note = load_set_note(project)
    marks = load_marks(project)
    env = load_env_lock(project)
    return fold_into_seed(
        seed,
        notes,
        set_note.line() if not set_note.is_empty() else "",
        marks.render_block(),
        env.line() if env.locked else "",
    )


def notes_shot_bits(notes: ProjectNotes) -> list[str]:
    bits: list[str] = []
    for note in notes.director.values():
        emotion = (note.emotion or "").strip()
        beats = " ".join((note.acting_beats or "").split())
        perf = compose_performance(note.micro_expression, note.behavior)
        if emotion or beats or perf:
            extra = "; ".join(p for p in (beats, perf) if p)
            bits.append(
                f"performance {note.character_name}: {emotion}"
                + (f"; {extra}" if extra else "")
            )
    world = notes.world.line()
    if world:
        bits.append(world.replace("WORLD NOTE (mise-en-scène): ", "mise-en-scène: "))
    return bits


def list_cast_faces(project: Project) -> list[CastFace]:
    """Every bible face. No adult filter — intimate routes gate later."""
    faces: list[CastFace] = []
    for profile in list_characters(project):
        refs = resolve_refs(project, profile)
        thumb = str(refs[0]) if refs else str(_placeholder_thumb(project, profile.id, profile.name))
        faces.append(
            CastFace(
                id=profile.id,
                name=profile.name,
                age_years=resolve_age_years(profile),
                age_band=profile.age_band,
                role=getattr(profile, "role", "Adult") or "Adult",
                thumb=thumb,
            )
        )
    return faces


def cast_gallery_items(project: Project) -> list[tuple[str, str]]:
    return [(face.thumb, face.caption) for face in list_cast_faces(project)]


def notes_markdown(notes: ProjectNotes) -> str:
    block = notes.render_block()
    if not block:
        return (
            "No Director Note or World Note yet. Click a cast face for "
            "**Director Note** (performance). Use **World Note** for mise-en-scène. "
            f"{SAFETY_LINE}"
        )
    return f"{block}\n\n{SAFETY_LINE}"


def assert_notes_safe(
    project: Project,
    notes: ProjectNotes,
    *,
    intimacy: str = "",
    intensity: float = 0.0,
    context: str = "Enhance → Pose → Animate",
) -> None:
    """Block minors on intimate / porn intensity. Performance-only otherwise."""
    from film_lab.filming import FilmingError, assert_filming_safe

    undress = notes_ask_undress(notes)
    if undress:
        try:
            intensity_f = float(intensity or 0)
        except (TypeError, ValueError):
            intensity_f = 0.0
        if intensity_f < EXPLICIT_INTENSITY_MIN:
            raise DirectorNoteError(
                "Undress through motion / into explicit sex needs the intensity "
                "dial at Explicit / adult study. Adult 18+ cast only. "
                "The start still may stay clothed — clothes come off in the clip."
            )
        intensity = 1.0
        if not intimacy:
            intimacy = "intimate sex"
    if not notes_need_adult(intimacy, intensity) and not undress:
        return
    faces = {face.id: face for face in list_cast_faces(project)}
    for cid, note in notes.director.items():
        face = faces.get(cid)
        if face is None:
            profiles = load_selected_characters(project, [cid])
            if profiles:
                years = resolve_age_years(profiles[0])
                face = CastFace(cid, note.character_name, years, profiles[0].age_band)
        if face is not None and not face.adult:
            raise DirectorNoteError(
                f"{note.character_name} is under 18 or not a confirmed adult. "
                f"Intimate / explicit intensity is adult 18+ ONLY. "
                f"Keep this Director Note to non-sexual acting and placement. "
                f"Cannot apply into {context}."
            )
    ids = list(notes.director) or list(project.active_cast or [])
    profiles = load_selected_characters(project, ids)
    wardrobe = ""
    if undress:
        wardrobe = "undress through motion"
    try:
        assert_filming_safe(
            getattr(project, "filming_mode", None),
            profiles,
            intimacy=intimacy,
            intensity=intensity,
            wardrobe=wardrobe,
            context=context,
        )
        assert_adult_cast(
            profiles,
            intimacy_mode=intimacy,
            content_intensity=intensity,
            context=context,
        )
    except (CharacterError, FilmingError) as exc:
        raise DirectorNoteError(str(exc)) from exc


def upsert_director_note(
    notes: ProjectNotes,
    *,
    character_id: str,
    character_name: str,
    emotion: str,
    acting_beats: str,
    wardrobe_motion: str = DEFAULT_WARDROBE,
    micro_expression: str = DEFAULT_MICRO,
    behavior: str = DEFAULT_BEHAVIOR,
) -> ProjectNotes:
    cid = (character_id or "").strip()
    if not cid:
        raise DirectorNoteError("Click a character face first.")
    notes.director[cid] = DirectorNote(
        character_id=cid,
        character_name=(character_name or cid).strip() or cid,
        emotion=(emotion or DEFAULT_EMOTION).strip() or DEFAULT_EMOTION,
        acting_beats=(acting_beats or "").strip(),
        wardrobe_motion=(wardrobe_motion or DEFAULT_WARDROBE).strip() or DEFAULT_WARDROBE,
        micro_expression=(micro_expression or DEFAULT_MICRO).strip() or DEFAULT_MICRO,
        behavior=(behavior or DEFAULT_BEHAVIOR).strip() or DEFAULT_BEHAVIOR,
    )
    return notes


def wardrobe_choices() -> list[str]:
    return list(WARDROBE_MOTIONS)


def set_world_note(
    notes: ProjectNotes,
    *,
    weather: str,
    thunder: str,
    earth: str,
    wind: str,
    setting: str,
    placement: str,
    outdoor: str = DEFAULT_OUTDOOR,
    prop_action: str = DEFAULT_PROP,
) -> ProjectNotes:
    notes.world = WorldNote(
        weather=(weather or DEFAULT_WEATHER).strip() or DEFAULT_WEATHER,
        thunder=(thunder or DEFAULT_THUNDER).strip() or DEFAULT_THUNDER,
        earth=(earth or DEFAULT_EARTH).strip() or DEFAULT_EARTH,
        wind=(wind or DEFAULT_WIND).strip() or DEFAULT_WIND,
        setting=(setting or "").strip(),
        placement=(placement or "").strip(),
        outdoor=(outdoor or DEFAULT_OUTDOOR).strip() or DEFAULT_OUTDOOR,
        prop_action=(prop_action or DEFAULT_PROP).strip() or DEFAULT_PROP,
    )
    return notes


def _placeholder_thumb(project: Project, character_id: str, name: str) -> Path:
    folder = project.root / "note_thumbs"
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / f"{character_id}.png"
    if dest.is_file():
        return dest
    img = Image.new("RGB", (256, 256), (28, 26, 22))
    draw = ImageDraw.Draw(img)
    draw.ellipse((28, 28, 228, 228), fill=(40, 28, 64), outline=(139, 108, 255), width=3)
    initial = (name or character_id or "?").strip()[:1].upper() or "?"
    try:
        font = ImageFont.load_default()
    except OSError:
        font = None
    draw.text((118, 108), initial, fill=(126, 232, 232), font=font)
    img.save(dest, format="PNG")
    return dest


def emotion_choices() -> list[str]:
    return [e for e in EMOTIONS if e != "none / unspecified"]


def weather_choices() -> list[str]:
    extra = ("thunder",)
    seen: list[str] = []
    for item in (*WEATHERS, *extra):
        if item not in seen:
            seen.append(item)
    return seen
