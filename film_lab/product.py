"""UGC / Product desk — product ref + avatar + prompt → still / video.

Local composite (not a fake diffusion merge). Animate on SVD-XT.
Mark & Direct the finished take. Adults 18+ only. Zero credits.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from film_lab.characters import (
    CharacterError,
    load_character,
    parse_age_years,
    resolve_refs,
)
from film_lab.constants import STORY_INTIMACY, normalize_aspect
from film_lab.filming import role_is_minor
from film_lab.project import IMAGE_SUFFIXES, Project, _unique_dest
from film_lab.quality import native_desk_size, normalize_quality
from film_lab.shot_card import ShotCard, new_shot_id
from film_lab.ugc import UGC_ASPECT, UgcError, assert_ugc_adult
from film_lab.util import new_id, slugify

PLACEMENTS: tuple[str, ...] = (
    "in hands",
    "lower third",
    "beside face",
    "on table",
)
DEFAULT_PLACE = "in hands"
STROKE = (126, 232, 232)

PRODUCT_HELP = (
    "Upload a **product** still. Pick an **avatar** from the Character Bible "
    "or upload a picture. Write how the product and the person appear. "
    "**Generate still** is a local composite (honest overlay). "
    "**Enhance** then **Animate**. Edit the take with **Mark & Direct** → Regenerate. "
    "Adults 18+ only. Zero credits."
)


class ProductError(ValueError):
    """Missing product, avatar, or adult gate."""


def product_markdown() -> str:
    return (
        "### Product ad — still or video\n"
        f"{PRODUCT_HELP}\n\n"
        "This is not a hosted UGC marketplace. Local desk only."
    )


def product_prompt(
    *,
    product_name: str,
    notes: str,
    direction: str,
    avatar_name: str,
    placement: str,
) -> str:
    who = (avatar_name or "the adult").strip()
    item = (product_name or "the product").strip()
    place = (placement or DEFAULT_PLACE).strip()
    user = (direction or "").strip()
    extra = (notes or "").strip()
    line = (
        f"{who} on camera with {item} {place}. "
        "Product readable. Face holds. Handheld UGC. Don't cut."
    )
    if user:
        line = f"{user} {line}"
    if extra:
        line = f"{line} {extra}"
    return " ".join(line.split())


def _as_image(path: Path) -> Image.Image:
    image = Image.open(path)
    image = ImageOps.exif_transpose(image)
    return image.convert("RGBA")


def _paste_box(width: int, height: int, placement: str) -> tuple[int, int, int, int]:
    key = (placement or DEFAULT_PLACE).strip().lower()
    if key == "beside face":
        return (int(width * 0.60), int(height * 0.10), int(width * 0.32), int(height * 0.32))
    if key == "lower third":
        return (int(width * 0.58), int(height * 0.62), int(width * 0.34), int(height * 0.28))
    if key == "on table":
        return (int(width * 0.30), int(height * 0.66), int(width * 0.40), int(height * 0.26))
    return (int(width * 0.32), int(height * 0.50), int(width * 0.36), int(height * 0.36))


def compose_product_still(
    project: Project,
    avatar: Path | str,
    product: Path | str,
    *,
    aspect: str = UGC_ASPECT,
    quality: str = "720p",
    placement: str = DEFAULT_PLACE,
    name: str = "product",
) -> Path:
    """Fit the avatar, overlay the product. Local pixels only — not an inpaint rewrite."""
    person = Path(avatar)
    item = Path(product)
    if not person.is_file() or person.suffix.lower() not in IMAGE_SUFFIXES:
        raise ProductError("Avatar needs a still (png / jpg / webp).")
    if not item.is_file() or item.suffix.lower() not in IMAGE_SUFFIXES:
        raise ProductError("Upload a product still (png / jpg / webp).")
    ratio = normalize_aspect(aspect or UGC_ASPECT)
    q = normalize_quality(quality)
    width, height = native_desk_size(q, ratio)
    base = ImageOps.fit(_as_image(person).convert("RGB"), (width, height), method=Image.Resampling.LANCZOS)
    canvas = base.convert("RGBA")
    px, py, pw, ph = _paste_box(width, height, placement)
    prop = ImageOps.contain(_as_image(item), (max(16, pw), max(16, ph)), method=Image.Resampling.LANCZOS)
    ring = Image.new("RGBA", (prop.width + 4, prop.height + 4), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ring)
    draw.rectangle((0, 0, ring.width - 1, ring.height - 1), outline=STROKE + (220,), width=2)
    ring.paste(prop, (2, 2), prop)
    x = min(max(0, px), max(0, canvas.width - ring.width))
    y = min(max(0, py), max(0, canvas.height - ring.height))
    canvas.alpha_composite(ring, (x, y))
    dest = _unique_dest(project.stills_dir, f"ugc_{slugify(name, 'product')}_{new_id()[:6]}.png")
    canvas.convert("RGB").save(dest, format="PNG")
    return dest


def resolve_avatar_still(
    project: Project,
    *,
    character_id: str = "",
    upload: Path | str | None = None,
) -> tuple[Path, str]:
    """Uploaded picture wins if present; otherwise the bible's first pinned still."""
    if upload:
        path = Path(upload)
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
            return path, "upload"
    cid = (character_id or "").strip()
    if cid:
        try:
            profile = load_character(project, cid)
        except (OSError, CharacterError, TypeError, ValueError) as exc:
            raise ProductError(f"Could not load bible avatar `{cid}`.") from exc
        if role_is_minor(profile.role):
            raise ProductError(
                f"{profile.name} is a story-role minor. UGC / product ads are adult 18+ only."
            )
        years = parse_age_years(profile.age_years)
        if years is not None:
            assert_ugc_adult(years)
        refs = resolve_refs(project, profile)
        if not refs:
            raise ProductError(
                f"{profile.name} has no pinned still. Pin a bible ref or upload a picture."
            )
        return refs[0], profile.name
    raise ProductError("Pick a Character Bible avatar or upload a picture.")


def build_product_shot(
    project: Project,
    *,
    still_name: str,
    prompt: str,
    aspect: str = UGC_ASPECT,
    quality: str = "720p",
    character_ids: list[str] | None = None,
    product_name: str = "Product",
) -> ShotCard:
    shot = ShotCard(
        id=new_shot_id(),
        name=f"UGC · {product_name or 'Product'}",
        start_frame=still_name,
        duration=2.5,
        aspect_ratio=normalize_aspect(aspect or UGC_ASPECT),
        camera_move="OTS",
        subject_motion_strength=0.42,
        body_motion_notes="handheld, product readable, don't rush the face",
        director_intent=prompt,
        lighting="phone light / practical room",
        character_ids=list(character_ids or []),
        face_lock_strength=project.face_lock_strength,
        resolution=normalize_quality(quality),
        intimacy_mode=STORY_INTIMACY,
        content_intensity=0.0,
    )
    project.save_shot(shot)
    return shot
