"""Motion Desk scope: any still → Animate. Product ads on UGC. No marketplace.

Motion is the primary image→video path (people, products, cans, posters).
UGC Ads / Product desk is for product + person ads.
Multi-beat product motion: Mark & Direct, or two shots + Cinema stitch.
Zero credits.
"""

from __future__ import annotations

from dataclasses import dataclass

from film_lab.constants import STORY_INTIMACY, normalize_aspect
from film_lab.quality import normalize_quality
from film_lab.shot_card import ShotCard, new_shot_id
from film_lab.ugc import UGC_ASPECT

SUBJECT_PERSON = "Person"
SUBJECT_PRODUCT = "Product / object"
SUBJECT_POSTER = "Poster / ad still"
MOTION_SUBJECTS: tuple[str, ...] = (SUBJECT_PERSON, SUBJECT_PRODUCT, SUBJECT_POSTER)
DEFAULT_SUBJECT = SUBJECT_PERSON

MOTION_SCOPE_HELP = (
    "Any still → **Animate**: people, products, cans, posters. "
    "Motion Desk is the primary image→video path. "
    "Pose and face lock are for people — skip them on a can or poster. "
    "Product + person ads live on **UGC Ads Desk**. No marketplace."
)


@dataclass(frozen=True)
class ProductBeat:
    key: str
    label: str
    prompt: str
    camera: str
    duration: float = 2.5


DEFAULT_PRODUCT_BEATS: tuple[ProductBeat, ...] = (
    ProductBeat(
        key="open",
        label="Opens alone",
        prompt=(
            "The can sits alone on the table. The lid lifts. "
            "No hands yet. Product readable. Don't cut."
        ),
        camera="static",
    ),
    ProductBeat(
        key="pour",
        label="Pick up and pour",
        prompt=(
            "The adult picks up the can and pours. "
            "Keep the label readable. Handheld. Don't rush the face."
        ),
        camera="OTS",
    ),
)


class MotionScopeError(ValueError):
    """Missing stills or adult gate on a product beat."""


def is_object_still(subject: str | None) -> bool:
    return (subject or "").strip() in {SUBJECT_PRODUCT, SUBJECT_POSTER}


def motion_scope_help() -> str:
    return MOTION_SCOPE_HELP


def product_beats_help() -> str:
    return (
        "### Multi-beat product motion\n"
        "Example: **can opens alone** → then a person **picks up and pours**.\n"
        "Two local paths — **no marketplace**:\n"
        "1. **Mark & Direct** — Animate beat 1 on Motion Desk, Fix this frame, "
        "note the pour, **Regenerate**. Old take stays.\n"
        "2. **Multi-shot stitch** — push two shots, Animate each on Motion, "
        "Cinema Desk stitch.\n"
        "Motion Desk stays primary for plain image→video."
    )


def likeness_prompt_bits(shot: ShotCard) -> list[str]:
    """Face-lock language only when a person / bible cast is on the shot."""
    ids = [c for c in (getattr(shot, "character_ids", None) or []) if str(c).strip()]
    lock = float(getattr(shot, "face_lock_strength", 0) or 0)
    if ids or lock > 0.05:
        return [
            "natural body motion, consistent adult faces, cinematic still-to-motion",
            f"face lock {lock:.2f} — keep start-frame likeness",
        ]
    return [
        "cinematic still-to-motion, keep the start-frame object readable, no face lock"
    ]


def apply_motion_subject(shot: ShotCard, subject: str | None) -> ShotCard:
    """Object / poster stills drop bible face lock. Person path unchanged."""
    if not is_object_still(subject):
        return shot
    shot.character_ids = []
    shot.character_tags = []
    shot.face_lock_strength = 0.0
    shot.intimacy_mode = STORY_INTIMACY
    shot.content_intensity = 0.0
    return shot


def build_product_beats(
    project,
    *,
    stills: list[str] | None = None,
    prompts: list[str] | None = None,
    product_name: str = "Product",
    aspect: str = UGC_ASPECT,
    quality: str = "720p",
    character_ids: list[str] | None = None,
) -> list[ShotCard]:
    """Two short shots: object alone, then person + product. Animate on Motion."""
    item = (product_name or "Product").strip() or "Product"
    ratio = normalize_aspect(aspect or UGC_ASPECT)
    q = normalize_quality(quality)
    frames = list(stills or [])
    lines = list(prompts or [])
    created: list[ShotCard] = []
    for i, beat in enumerate(DEFAULT_PRODUCT_BEATS):
        still = frames[i] if i < len(frames) and frames[i] else (frames[0] if frames else None)
        prompt = (lines[i] if i < len(lines) and (lines[i] or "").strip() else beat.prompt)
        ids = list(character_ids or []) if i > 0 else []
        shot = ShotCard(
            id=new_shot_id(),
            name=f"{item} · {beat.label}",
            start_frame=still,
            duration=beat.duration,
            aspect_ratio=ratio,
            camera_move=beat.camera,
            subject_motion_strength=0.40,
            body_motion_notes="product readable, don't rush",
            director_intent=prompt,
            lighting="phone light / practical room",
            character_ids=ids,
            face_lock_strength=0.0 if i == 0 else project.face_lock_strength,
            resolution=q,
            intimacy_mode=STORY_INTIMACY,
            content_intensity=0.0,
        )
        if i == 0:
            shot.face_lock_strength = 0.0
        project.save_shot(shot)
        created.append(shot)
    return created
