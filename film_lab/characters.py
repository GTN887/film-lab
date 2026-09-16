"""Character bible, consistency packs, and local prompt injection."""

from __future__ import annotations

import re
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from film_lab.filming import (
    ROLE_ADULT,
    default_band_for_role,
    default_years_for_role,
    normalize_role,
    role_is_minor,
    validate_role_age,
)
from film_lab.intensity import intensity_requires_numeric_age
from film_lab.living import LivingBrief, living_preset_brief, living_shot_line
from film_lab.project import IMAGE_SUFFIXES, Project, _unique_dest
from film_lab.shot_card import ShotCard
from film_lab.util import new_id, read_json, slugify, utc_now, write_json

MIN_REFS = 3
MAX_REFS = 10

_NOT_ADULT = re.compile(
    r"\b(child|children|kid|kids|teen(?:ager)?s?|minor|underage|preteen|"
    r"infant|toddler|high[\s-]?school|middle[\s-]?school|under\s*18|"
    r"seventeen|sixteen|fifteen|fourteen|thirteen)\b",
    re.IGNORECASE,
)

# Age-band phrases → conservative years when age_years is blank.
_BAND_YEARS: tuple[tuple[re.Pattern[str], int], ...] = (
    (re.compile(r"\b1[0-7]\b"), 17),
    (re.compile(r"\b1[89]\s*[-–to]+\s*1[89]\b", re.I), 18),
    (re.compile(r"\b18\b"), 18),
    (re.compile(r"\b19\b"), 19),
    (re.compile(r"\bcollege senior\b", re.I), 21),
    (re.compile(r"\bnewly adult\b", re.I), 18),
    (re.compile(r"\bearly 20", re.I), 22),
    (re.compile(r"\bmid[-\s]?20", re.I), 25),
    (re.compile(r"\blate 20", re.I), 28),
    (re.compile(r"\bearly 30", re.I), 32),
    (re.compile(r"\bmid[-\s]?30", re.I), 35),
    (re.compile(r"\blate 30", re.I), 38),
    (re.compile(r"\b40", re.I), 42),
)


def parse_age_years(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def years_from_age_band(age_band: str) -> int | None:
    text = (age_band or "").strip()
    if not text:
        return None
    for pattern, years in _BAND_YEARS:
        if pattern.search(text):
            return years
    return None


class CharacterError(ValueError):
    """Invalid character bible entry."""


@dataclass
class CharacterProfile:
    id: str
    name: str
    role: str = ROLE_ADULT
    age_band: str = "late 20s (adult)"
    age_years: int | None = 28
    look_notes: str = ""
    wardrobe: str = ""
    rings_props: str = ""
    personality: str = ""
    emotion_baseline: str = ""
    micro_expression: str = ""
    behavior: str = ""
    lighting_notes: str = ""
    voice_notes: str = ""
    locked_descriptor: str = ""
    reference_stills: list[str] = field(default_factory=list)
    voice_backend: str = "auto"
    voice_id: str = ""
    voice_sample: str = ""
    living: dict[str, Any] = field(default_factory=dict)
    parent_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        from film_lab.filming import FilmingError

        self.role = normalize_role(self.role)
        years = parse_age_years(self.age_years)
        if years is None and role_is_minor(self.role):
            years = default_years_for_role(self.role)
        self.age_years = years
        try:
            validate_role_age(self.role, years, name=self.name)
        except FilmingError as exc:
            raise CharacterError(str(exc)) from exc
        if not role_is_minor(self.role):
            if years is not None and years < 18:
                raise CharacterError(
                    f"{self.name}: Age (years) is {years}. "
                    f"Adult / Mom / Dad roles are 18+. "
                    f"Teen / Child / Infant are Regular-story roles only."
                )
            band_years = years_from_age_band(self.age_band)
            if band_years is not None and band_years < 18:
                raise CharacterError(
                    f"{self.name}: age band reads under 18. "
                    f"Adult roles are 18+. Use Teen / Child / Infant for Regular story."
                )
            if _NOT_ADULT.search(self.age_band) or _NOT_ADULT.search(self.look_notes):
                raise CharacterError(
                    f"{self.name}: Adult / Mom / Dad look notes must describe adults. "
                    f"Teen / Child / Infant roles are for Regular / story filming only."
                )
        elif not (self.age_band or "").strip():
            self.age_band = default_band_for_role(self.role)
        self.reference_stills = list(dict.fromkeys(self.reference_stills))[:MAX_REFS]
        if not isinstance(self.living, dict):
            self.living = {}
        parents: list[str] = []
        for cid in self.parent_ids or []:
            text = str(cid).strip()
            if text and text != self.id and text not in parents:
                parents.append(text)
        self.parent_ids = parents

    def living_brief(self) -> LivingBrief:
        return LivingBrief.from_dict(self.living)

    def set_living(self, brief: LivingBrief) -> None:
        self.living = brief.to_dict()

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def label(self) -> str:
        return f"{self.id} — {self.name}"

    def consistency_ready(self) -> bool:
        return MIN_REFS <= len(self.reference_stills) <= MAX_REFS

    def injection_line(self) -> str:
        """One local prompt line. Never uploaded."""
        bits: list[str] = []
        lock = (self.locked_descriptor or "").strip()
        if lock:
            bits.append(lock)
        else:
            if role_is_minor(self.role):
                years = self.age_years if self.age_years is not None else default_years_for_role(self.role)
                bits.append(
                    f"{self.name}, {self.role} story role, age {years}, "
                    f"NON-SEXUAL Regular filming only"
                )
            else:
                bits.append(f"{self.name}, adult {self.role.lower()}, {self.age_band}")
            if self.look_notes.strip():
                bits.append(self.look_notes.strip())
        if self.wardrobe.strip() and self.wardrobe.strip().lower() not in lock.lower():
            bits.append(self.wardrobe.strip())
        if self.rings_props.strip():
            bits.append(self.rings_props.strip())
        if self.personality.strip():
            bits.append(f"personality: {self.personality.strip()}")
        if self.emotion_baseline.strip():
            bits.append(f"emotion: {self.emotion_baseline.strip()}")
        if (self.micro_expression or "").strip() and self.micro_expression.strip().lower() != "none":
            bits.append(f"micro-expression: {self.micro_expression.strip()}")
        if (self.behavior or "").strip() and self.behavior.strip().lower() != "none":
            bits.append(f"behavior: {self.behavior.strip()}")
        if self.lighting_notes.strip():
            bits.append(f"lighting: {self.lighting_notes.strip()}")
        if role_is_minor(self.role):
            bits.append("not for intimacy or explicit intensity")
            if self.parent_ids:
                bits.append("belongs to " + " + ".join(self.parent_ids))
        else:
            bits.append("adult 18+")
        return ", ".join(bits)


def studio_characters_root() -> Path:
    return Path.cwd() / "data" / "characters"


def characters_dir(project: Project) -> Path:
    return project.root / "characters"


def profile_path(project: Project, character_id: str) -> Path:
    return characters_dir(project) / character_id / "profile.json"


def refs_dir(project: Project, character_id: str) -> Path:
    return characters_dir(project) / character_id / "refs"


def hook_path(project: Project, character_id: str) -> Path:
    return characters_dir(project) / character_id / "consistency_hook.json"


def save_character(project: Project, profile: CharacterProfile) -> Path:
    project.ensure_dirs()
    profile.touch()
    path = profile_path(project, profile.id)
    refs_dir(project, profile.id).mkdir(parents=True, exist_ok=True)
    write_json(path, profile.to_dict())
    write_consistency_hook(project, profile)
    return path


def load_character(project: Project, character_id: str) -> CharacterProfile:
    data = read_json(profile_path(project, character_id))
    if not isinstance(data, dict):
        raise CharacterError(f"Bad character profile: {character_id}")
    return CharacterProfile(**{k: data[k] for k in CharacterProfile.__dataclass_fields__ if k in data})


def list_characters(project: Project) -> list[CharacterProfile]:
    root = characters_dir(project)
    if not root.exists():
        return []
    found: list[CharacterProfile] = []
    for child in sorted(root.iterdir()):
        if child.is_dir() and (child / "profile.json").exists():
            try:
                found.append(load_character(project, child.name))
            except (OSError, TypeError, ValueError):
                continue
    return found


def character_choices(project: Project) -> list[str]:
    return [c.label() for c in list_characters(project)]


def pin_reference(project: Project, character_id: str, source: Path) -> CharacterProfile:
    profile = load_character(project, character_id)
    if source.suffix.lower() not in IMAGE_SUFFIXES:
        raise CharacterError("Reference stills must be images (png / jpg / webp / tiff).")
    dest_dir = refs_dir(project, character_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = _unique_dest(dest_dir, source.name)
    shutil.copy2(source, dest)
    if dest.name not in profile.reference_stills:
        if len(profile.reference_stills) >= MAX_REFS:
            raise CharacterError(f"Consistency pack is full ({MAX_REFS} stills). Unpin one first.")
        profile.reference_stills.append(dest.name)
    save_character(project, profile)
    return profile


def unpin_reference(project: Project, character_id: str, filename: str) -> CharacterProfile:
    profile = load_character(project, character_id)
    profile.reference_stills = [n for n in profile.reference_stills if n != filename]
    save_character(project, profile)
    return profile


def resolve_refs(project: Project, profile: CharacterProfile) -> list[Path]:
    folder = refs_dir(project, profile.id)
    paths: list[Path] = []
    for name in profile.reference_stills:
        path = folder / name
        if path.is_file():
            paths.append(path)
    return paths


def refs_for_shot(project: Project, shot: ShotCard) -> list[Path]:
    paths: list[Path] = []
    for profile in matching_characters(project, shot):
        paths.extend(resolve_refs(project, profile))
    return paths


def matching_characters(project: Project, shot: ShotCard) -> list[CharacterProfile]:
    wanted_ids = set(shot.character_ids)
    wanted_names = {t.lower() for t in shot.character_tags}
    matched: list[CharacterProfile] = []
    for profile in list_characters(project):
        if profile.id in wanted_ids:
            matched.append(profile)
            continue
        if profile.name.lower() in wanted_names:
            matched.append(profile)
            continue
        if any(profile.name.lower() in tag or tag in profile.name.lower() for tag in wanted_names):
            matched.append(profile)
    return matched


def resolve_age_years(profile: CharacterProfile) -> int | None:
    direct = parse_age_years(profile.age_years)
    if direct is not None:
        return direct
    return years_from_age_band(profile.age_band)


def load_selected_characters(project: Project, character_ids: list[str] | None) -> list[CharacterProfile]:
    wanted = [str(c).strip() for c in (character_ids or []) if str(c).strip()]
    if not wanted:
        return []
    wanted_l = {c.lower() for c in wanted}
    found: list[CharacterProfile] = []
    seen: set[str] = set()
    for profile in list_characters(project):
        if profile.id in seen:
            continue
        if profile.id in wanted_l or profile.name.lower() in wanted_l:
            found.append(profile)
            seen.add(profile.id)
    return found


def assert_adult_cast(
    profiles: list[CharacterProfile],
    *,
    intimacy_mode: str = "",
    content_intensity: float = 0.0,
    require_age: bool = False,
    context: str = "this beat",
) -> None:
    """Hard-block minors. Intimate / frank+ / youth-shelf requires numeric 18+."""
    from film_lab.intimacy import is_intimate

    need_age = (
        require_age
        or is_intimate(intimacy_mode)
        or intensity_requires_numeric_age(content_intensity)
    )
    if need_age and not profiles:
        raise CharacterError(
            f"Select adult characters with Age (years) 18+ on the bible before {context}."
        )
    for profile in profiles:
        years = parse_age_years(profile.age_years)
        band_years = years_from_age_band(profile.age_band)
        if role_is_minor(getattr(profile, "role", ROLE_ADULT)):
            raise CharacterError(
                f"{profile.name} is a {normalize_role(profile.role)} story role. "
                f"Sexual or intimate generation is blocked. "
                f"Under-18 roles never unlock explicit tools."
            )
        if years is not None and years < 18:
            raise CharacterError(
                f"{profile.name} is {years} (under 18). Sexual or intimate "
                f"generation is blocked. Recast as an adult 18+."
            )
        if band_years is not None and band_years < 18:
            raise CharacterError(
                f"{profile.name}: age band implies under 18. "
                f"No sexual content involving minors under any framing."
            )
        blob = f"{profile.age_band} {profile.look_notes}"
        if _NOT_ADULT.search(blob):
            raise CharacterError(
                f"{profile.name}: age/look implies a minor. No sexual content "
                f"involving minors under any framing."
            )
        if need_age and years is None:
            raise CharacterError(
                f"{profile.name}: set Age (years) to 18+ on the character bible "
                f"before {context}. Intimate / frank / explicit modes and teen-film "
                f"/ YA tags require a numeric adult age — not just a vibe band."
            )


def compose_local_prompt(shot: ShotCard, project: Project | None = None) -> str:
    """Shot desk prompt plus locked character descriptors. Never uploaded."""
    parts = [shot.local_prompt()]
    if project is not None:
        from film_lab.director_notes import load_notes, notes_shot_bits
        from film_lab.envlock import env_shot_bits, load_env_lock
        from film_lab.mark import load_marks, mark_shot_bits
        from film_lab.setdesk import load_set_note, set_shot_bits

        parts.extend(notes_shot_bits(load_notes(project)))
        parts.extend(set_shot_bits(load_set_note(project)))
        parts.extend(env_shot_bits(load_env_lock(project)))
        parts.extend(mark_shot_bits(load_marks(project)))
        matched = matching_characters(project, shot)
        if not matched and shot.character_ids:
            matched = load_selected_characters(project, shot.character_ids)
        if not matched:
            matched = load_selected_characters(project, list(project.active_cast))
        for profile in matched:
            parts.append(profile.injection_line())
        nest = resolved_living(project, [p.id for p in matched])
        shot_line = living_shot_line(nest)
        if shot_line:
            parts.append(shot_line)
        strength = getattr(shot, "face_lock_strength", None)
        if strength is None:
            strength = project.face_lock_strength
        parts.append(f"face lock {float(strength):.2f} (start-still likeness, local)")
    return ", ".join(parts)


def cast_prompt_block(project: Project, character_ids: list[str] | None = None) -> str:
    ids = list(character_ids or project.active_cast or ["alison", "bradley"])
    profiles = load_selected_characters(project, ids)
    if not profiles:
        profiles = list_characters(project)
    lines = [p.injection_line() for p in profiles]
    from film_lab.lighting import lighting_bible_line

    lock = lighting_bible_line(project.active_lighting)
    if lock:
        lines.append(lock)
    return "\n".join(lines)


def resolved_living(
    project: Project,
    character_ids: list[str] | None = None,
    *,
    scene_living: LivingBrief | None = None,
    draft_living: LivingBrief | None = None,
) -> LivingBrief:
    """Draft override → scene → selected characters → project nest defaults."""
    if draft_living and draft_living.override:
        return draft_living
    if scene_living and scene_living.has_content():
        return scene_living
    wanted = {c.lower() for c in (character_ids or [])}
    briefs: list[LivingBrief] = []
    for profile in list_characters(project):
        if wanted and profile.id not in wanted and profile.name.lower() not in wanted:
            continue
        brief = profile.living_brief()
        if brief.has_content():
            briefs.append(brief)
    merged = merge_character_living(briefs)
    if merged.has_content():
        return merged
    if draft_living and draft_living.has_content():
        return draft_living
    return project.living_brief()


def merge_character_living(briefs: list[LivingBrief]) -> LivingBrief:
    from film_lab.living import merge_living

    return merge_living(briefs)


def write_consistency_hook(
    project: Project,
    profile: CharacterProfile,
    *,
    method: str | None = None,
) -> Path:
    """Document the local stack. Primary = start still → img2vid. No cloud call."""
    from film_lab.consistency import CONSISTENCY_STACK, DEFAULT_FACE_METHOD, face_lock_plan

    payload = {
        "hook": "local_face_ref",
        "status": "start_still_primary",
        "character_id": profile.id,
        "refs": profile.reference_stills,
        "face_lock": face_lock_plan(
            strength=project.face_lock_strength,
            ref_count=len(profile.reference_stills),
            method=method or DEFAULT_FACE_METHOD,
        ),
        "stack": [
            {"key": m.key, "title": m.title, "status": m.status, "vram": m.vram}
            for m in CONSISTENCY_STACK
        ],
        "notes": (
            "Primary on RX 5600 XT 6GB: lock the person in the start still, then img2vid. "
            f"Point a later FaceID / InstantID graph at characters/{profile.id}/refs/. "
            "Film Lab does not compute embeddings and does not call a hosted face API."
        ),
    }
    path = hook_path(project, profile.id)
    write_json(path, payload)
    return path


def seed_alison_bradley(project: Project) -> list[CharacterProfile]:
    """Ensure the two locked adult leads exist."""
    nest = living_preset_brief("Newlywed warm apartment")
    seeds = [
        CharacterProfile(
            id="alison",
            name="Alison",
            role=ROLE_ADULT,
            age_band="late 20s (adult)",
            age_years=28,
            look_notes="Blonde, late-20s adult woman. Soft jaw, warm skin, readable eyes.",
            wardrobe="Bedroom: bare skin or a fallen sheet, never costume-y.",
            rings_props="Wedding band on the left hand. Story prop.",
            personality="Direct, tender, a little sharp when she is tired.",
            emotion_baseline="Tenderness with a flicker of want.",
            lighting_notes="warm lamp bedroom, tungsten practical, amber falloff",
            voice_notes="Low-mid, unhurried, close-mic. Intimate, not theatrical.",
            voice_backend="auto",
            voice_id="en+f3",
            locked_descriptor=(
                "Alison, adult woman late 20s, blonde hair, warm skin, "
                "wedding band on left hand, naturalistic"
            ),
            living=nest.to_dict(),
        ),
        CharacterProfile(
            id="bradley",
            name="Bradley",
            role=ROLE_ADULT,
            age_band="late 20s (adult)",
            age_years=28,
            look_notes="Dark hair, athletic late-20s adult man. Broad shoulders, quiet face.",
            wardrobe="Bedroom: skin, watch off, no gym sheen.",
            rings_props="Wedding band on the left hand. Story prop.",
            personality="Steady, watchful, funny in a quiet way.",
            emotion_baseline="Held warmth, slightly behind her pace.",
            lighting_notes="warm lamp bedroom, motivated practical, rim from the hallway",
            voice_notes="Warm baritone, little projection. Speaks as if the lamp is the only audience.",
            voice_backend="auto",
            voice_id="en+m3",
            locked_descriptor=(
                "Bradley, adult man late 20s, dark hair, athletic build, "
                "wedding band on left hand, naturalistic"
            ),
            living=nest.to_dict(),
        ),
    ]
    written: list[CharacterProfile] = []
    for profile in seeds:
        path = profile_path(project, profile.id)
        if path.exists():
            existing = load_character(project, profile.id)
            dirty = False
            if not existing.living_brief().has_content():
                existing.set_living(nest)
                dirty = True
            if existing.age_years is None:
                existing.age_years = 28
                dirty = True
            if not existing.rings_props:
                existing.rings_props = profile.rings_props
                dirty = True
            if not existing.personality:
                existing.personality = profile.personality
                dirty = True
            if not existing.emotion_baseline:
                existing.emotion_baseline = profile.emotion_baseline
                dirty = True
            if not existing.lighting_notes:
                existing.lighting_notes = profile.lighting_notes
                dirty = True
            if not existing.voice_notes:
                existing.voice_notes = profile.voice_notes
                dirty = True
            from film_lab.voice import apply_voice_defaults

            if apply_voice_defaults(existing):
                dirty = True
            if dirty:
                save_character(project, existing)
            continue
        save_character(project, profile)
        written.append(profile)
    if not project.living_brief().has_content():
        project.set_living(nest)
    return written


def new_character(name: str) -> CharacterProfile:
    slug = slugify(name, "character")
    return CharacterProfile(id=slug or new_id(), name=name.strip() or "Unnamed")


def export_to_studio_library(profile: CharacterProfile) -> Path:
    """Write a key-free JSON copy under data/characters/."""
    root = studio_characters_root()
    root.mkdir(parents=True, exist_ok=True)
    payload = {
        k: getattr(profile, k)
        for k in (
            "id",
            "name",
            "role",
            "age_band",
            "age_years",
            "look_notes",
            "wardrobe",
            "rings_props",
            "personality",
            "emotion_baseline",
            "micro_expression",
            "behavior",
            "lighting_notes",
            "voice_notes",
            "locked_descriptor",
            "reference_stills",
            "voice_backend",
            "voice_id",
            "voice_sample",
            "parent_ids",
        )
    }
    path = root / f"{profile.id}.json"
    write_json(path, payload)
    return path


def load_studio_library() -> list[CharacterProfile]:
    root = studio_characters_root()
    if not root.is_dir():
        return []
    found: list[CharacterProfile] = []
    for path in sorted(root.glob("*.json")):
        data = read_json(path)
        if not isinstance(data, dict):
            continue
        try:
            found.append(
                CharacterProfile(
                    **{k: data[k] for k in CharacterProfile.__dataclass_fields__ if k in data}
                )
            )
        except (TypeError, ValueError, CharacterError):
            continue
    return found


def import_studio_library(project: Project) -> list[CharacterProfile]:
    """Copy studio JSON into this project's bible. Refs stay empty until pinned."""
    written: list[CharacterProfile] = []
    for profile in load_studio_library():
        path = profile_path(project, profile.id)
        if path.exists():
            continue
        from film_lab.voice import apply_voice_defaults

        apply_voice_defaults(profile)
        save_character(project, profile)
        written.append(profile)
    return written


def ensure_studio_library() -> None:
    """Guarantee Alison / Bradley JSON exist under data/characters/."""
    root = studio_characters_root()
    root.mkdir(parents=True, exist_ok=True)
    if not (root / "alison.json").is_file() or not (root / "bradley.json").is_file():
        from film_lab.living import living_preset_brief

        nest = living_preset_brief("Newlywed warm apartment")
        for profile in (
            CharacterProfile(
                id="alison",
                name="Alison",
                age_band="late 20s (adult)",
                age_years=28,
                look_notes="Blonde, late-20s adult woman. Soft jaw, warm skin, readable eyes.",
                wardrobe="Bedroom: bare skin or a fallen sheet, never costume-y.",
                rings_props="Wedding band on the left hand. Story prop.",
                personality="Direct, tender, a little sharp when she is tired.",
                emotion_baseline="Tenderness with a flicker of want.",
                lighting_notes="warm lamp bedroom, tungsten practical, amber falloff",
                voice_notes="Low-mid, unhurried, close-mic. Intimate, not theatrical.",
                voice_backend="auto",
                voice_id="en+f3",
                locked_descriptor=(
                    "Alison, adult woman late 20s, blonde hair, warm skin, "
                    "wedding band on left hand, naturalistic"
                ),
                living=nest.to_dict(),
            ),
            CharacterProfile(
                id="bradley",
                name="Bradley",
                age_band="late 20s (adult)",
                age_years=28,
                look_notes="Dark hair, athletic late-20s adult man. Broad shoulders, quiet face.",
                wardrobe="Bedroom: skin, watch off, no gym sheen.",
                rings_props="Wedding band on the left hand. Story prop.",
                personality="Steady, watchful, funny in a quiet way.",
                emotion_baseline="Held warmth, slightly behind her pace.",
                lighting_notes="warm lamp bedroom, motivated practical, rim from the hallway",
                voice_notes="Warm baritone, little projection. Speaks as if the lamp is the only audience.",
                voice_backend="auto",
                voice_id="en+m3",
                locked_descriptor=(
                    "Bradley, adult man late 20s, dark hair, athletic build, "
                    "wedding band on left hand, naturalistic"
                ),
                living=nest.to_dict(),
            ),
        ):
            if not (root / f"{profile.id}.json").is_file():
                export_to_studio_library(profile)
