"""Family Genetics — Regular / story kids from two adult bible faces.

Pick Actor A + Actress B (face-locked refs). Blend a local still.
Save as a Character Bible card that belongs to both parents.

Never routes through 18+ intimacy. Teen / Child / Infant stay
Regular-story roles. Not a hosted face model. Zero credits.
"""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

from film_lab.characters import (
    CharacterError,
    CharacterProfile,
    list_characters,
    load_character,
    parse_age_years,
    pin_reference,
    resolve_refs,
    save_character,
)
from film_lab.filming import (
    ROLE_CHILD,
    ROLE_INFANT,
    ROLE_TEEN,
    default_band_for_role,
    default_years_for_role,
    profile_is_adult,
    role_is_minor,
)
from film_lab.living import merge_living
from film_lab.project import Project, _unique_dest
from film_lab.util import slugify

KID_AGES = ("infant", "child", "teen")
AGE_TO_ROLE = {
    "infant": ROLE_INFANT,
    "child": ROLE_CHILD,
    "teen": ROLE_TEEN,
}
STORY_WARDROBE = {
    "infant": "Onesie or swaddle. Everyday Regular / story. Non-sexual.",
    "child": "Everyday kid clothes. Regular / story. Non-sexual.",
    "teen": "Everyday teen clothes. Regular / story. Non-sexual. Not a sexualized look.",
}
BLEND_SIZE = (720, 900)
_INTIMATE = re.compile(
    r"\b(nude|naked|bare skin|fallen sheet|sex|intimate|porn|explicit|"
    r"undress|penetration|bedroom:)\b",
    re.I,
)

GENETICS_HELP = (
    "Pick **Actor A** and **Actress B** — two adult (18+) bible faces with "
    "face-locked refs. Age: infant / child / teen. "
    "**What would their kids look like?** blends the refs locally "
    "(honest composite, not InstantID) and saves a Character Bible card "
    "that **belongs to both parents**. Regular / story only. "
    "Teen / Child / Infant never unlock 18+ intimacy. Zero credits."
)


class GeneticsError(ValueError):
    """Parent pick, missing refs, or Regular/story gate failed."""


def normalize_kid_age(raw: str | None) -> str:
    text = (raw or "child").strip().lower()
    if text not in KID_AGES:
        raise GeneticsError("Age picker is infant / child / teen (Regular / story only).")
    return text


def adult_parent_choices(project: Project) -> list[str]:
    return [p.label() for p in list_characters(project) if _is_adult_parent(p)]


def belongs_line(profile: CharacterProfile, project: Project | None = None) -> str:
    ids = list(getattr(profile, "parent_ids", None) or [])
    if not ids:
        return ""
    names: list[str] = []
    for cid in ids:
        label = cid
        if project is not None:
            try:
                label = load_character(project, cid).name
            except (CharacterError, OSError, ValueError, FileNotFoundError):
                label = cid
        names.append(label)
    return "Belongs to " + " + ".join(names) + ". Regular / story. Non-sexual."


def generate_kids(
    project: Project,
    actor_a,
    actress_b,
    age: str,
    *,
    name: str = "",
) -> tuple[CharacterProfile, list[Path]]:
    """Blend parent refs → stills + bible card. Regular / story only."""
    kid_age = normalize_kid_age(age)
    parent_a = _load_parent(project, actor_a, slot="Actor A")
    parent_b = _load_parent(project, actress_b, slot="Actress B")
    if parent_a.id == parent_b.id:
        raise GeneticsError("Pick two different adult parents (Actor A + Actress B).")
    refs_a = resolve_refs(project, parent_a)
    refs_b = resolve_refs(project, parent_b)
    if not refs_a:
        raise GeneticsError(
            f"{parent_a.name} needs a face-locked ref still first. Pin one on the bible."
        )
    if not refs_b:
        raise GeneticsError(
            f"{parent_b.name} needs a face-locked ref still first. Pin one on the bible."
        )

    role = AGE_TO_ROLE[kid_age]
    years = default_years_for_role(role)
    band = default_band_for_role(role)
    kid_id = slugify(f"{parent_a.id}_{parent_b.id}_{kid_age}", "kid")
    kid_name = (name or "").strip() or f"{parent_a.name} & {parent_b.name} — {kid_age}"
    look = _story_look(parent_a, parent_b, kid_age)
    lock = (
        f"{kid_name}, {role} story role, age {years}, child of "
        f"{parent_a.name} and {parent_b.name}, Regular / story, non-sexual"
    )
    nest = merge_living([parent_a.living_brief(), parent_b.living_brief()])
    existing = None
    refs: list[str] = []
    path = project.root / "characters" / kid_id / "profile.json"
    if path.is_file():
        existing = load_character(project, kid_id)
        refs = list(existing.reference_stills)

    child = CharacterProfile(
        id=kid_id,
        name=kid_name,
        role=role,
        age_band=band,
        age_years=years,
        look_notes=look,
        wardrobe=STORY_WARDROBE[kid_age],
        rings_props="None. Regular / story child. Not a sexualized prop.",
        personality=_story_personality(parent_a, parent_b),
        emotion_baseline="Curious, held, everyday.",
        lighting_notes="soft daylight or practical lamp. Regular / story.",
        voice_notes="Age-appropriate. Not an adult intimate voice.",
        locked_descriptor=lock,
        reference_stills=refs,
        living=nest.to_dict() if nest.has_content() else {},
        parent_ids=[parent_a.id, parent_b.id],
    )
    save_character(project, child)

    written: list[Path] = []
    for index, bias in enumerate((0.38, 0.62)):
        image = blend_parent_refs(refs_a[0], refs_b[0], kid_age, bias=bias)
        still = _unique_dest(
            project.stills_dir,
            f"genetics_{kid_id}_{index + 1}.png",
        )
        project.stills_dir.mkdir(parents=True, exist_ok=True)
        image.save(still, format="PNG")
        pin_reference(project, child.id, still)
        written.append(still)

    child = load_character(project, child.id)
    return child, written


def blend_parent_refs(
    path_a: Path | str,
    path_b: Path | str,
    age: str,
    *,
    bias: float = 0.5,
) -> Image.Image:
    """Local face-region blend. Honest composite — not InstantID / FaceID."""
    kid_age = normalize_kid_age(age)
    left = _face_plate(Path(path_a), kid_age)
    right = _face_plate(Path(path_b), kid_age)
    alpha = min(0.85, max(0.15, float(bias)))
    merged = Image.blend(left, right, alpha)
    merged = _age_wash(merged, kid_age)
    return _caption(merged, kid_age)


def _load_parent(project: Project, choice, *, slot: str) -> CharacterProfile:
    cid = _id_from_choice(choice)
    if not cid:
        raise GeneticsError(f"Pick {slot} from the Character Bible (adult 18+).")
    try:
        profile = load_character(project, cid)
    except (CharacterError, OSError, ValueError, FileNotFoundError) as exc:
        raise GeneticsError(f"{slot} `{cid}` is not on this bible.") from exc
    if not _is_adult_parent(profile):
        raise GeneticsError(
            f"{profile.name} cannot be a genetics parent. "
            f"Actor A and Actress B must be Adult / Mom / Dad, Age (years) 18+. "
            f"Teen / Child / Infant never make kids and never unlock 18+ intimacy."
        )
    return profile


def _is_adult_parent(profile: CharacterProfile) -> bool:
    if role_is_minor(profile.role):
        return False
    years = parse_age_years(profile.age_years)
    if years is not None and years < 18:
        return False
    return profile_is_adult(profile)


def _id_from_choice(choice) -> str:
    text = str(choice or "").strip()
    if " — " in text:
        text = text.split(" — ", 1)[0].strip()
    return text


def _story_look(a: CharacterProfile, b: CharacterProfile, age: str) -> str:
    bits = [
        _clean_adult_copy(a.look_notes) or f"{a.name} features",
        _clean_adult_copy(b.look_notes) or f"{b.name} features",
        f"{age} story role, Regular / story filming, non-sexual.",
        f"Child of {a.name} and {b.name}.",
    ]
    return " ".join(b for b in bits if b)


def _story_personality(a: CharacterProfile, b: CharacterProfile) -> str:
    left = _clean_adult_copy(a.personality)
    right = _clean_adult_copy(b.personality)
    if left and right:
        return f"Takes after both: {left} / {right}"
    return left or right or "Everyday. Curious. Regular / story."


def _clean_adult_copy(text: str) -> str:
    cleaned = _INTIMATE.sub("", text or "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.")
    return cleaned


def _face_plate(path: Path, age: str) -> Image.Image:
    image = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    width, height = image.size
    top = int(height * (0.04 if age != "infant" else 0.02))
    bottom = int(height * (0.78 if age == "teen" else 0.72 if age == "child" else 0.68))
    side = int(width * 0.12)
    box = (side, top, width - side, max(top + 8, bottom))
    crop = image.crop(box)
    return ImageOps.fit(crop, BLEND_SIZE, method=Image.Resampling.LANCZOS)


def _age_wash(image: Image.Image, age: str) -> Image.Image:
    out = image
    if age == "infant":
        out = out.filter(ImageFilter.GaussianBlur(radius=1.15))
        out = ImageEnhance.Color(out).enhance(0.92)
        out = Image.blend(out, Image.new("RGB", out.size, (255, 236, 220)), 0.12)
    elif age == "child":
        out = Image.blend(out, Image.new("RGB", out.size, (255, 244, 230)), 0.06)
        out = ImageEnhance.Contrast(out).enhance(1.04)
    else:
        out = ImageEnhance.Contrast(out).enhance(1.08)
        out = ImageEnhance.Sharpness(out).enhance(1.12)
    return out.convert("RGB")


def _caption(image: Image.Image, age: str) -> Image.Image:
    draw = ImageDraw.Draw(image)
    width, height = image.size
    bar = 36
    draw.rectangle((0, height - bar, width, height), fill=(12, 13, 16))
    font = _font(14)
    label = f"Family Genetics  ·  {age}  ·  Regular / story  ·  non-sexual"
    draw.text((14, height - 26), label, fill=(126, 232, 232), font=font)
    return image


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in (
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
    ):
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()
