"""Effects Desk — descriptive motion presets on a character still.

UX jobs (upload, optional plates, preset grid, aspect, generate) are a
public effects-page *shape* only. Names are Film Lab descriptions.
No third-party brand, no credit meter, no free-gens counter.

Generate is local ComfyUI SVD-XT when the sidecar is up. A per-preset
API graph is optional under workflows/effects/<id>.json — if that file
is a stub or missing, Film Lab says so and uses the shared SVD graph.
Ken Burns is not this desk. Adults 18+. Zero credits.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from film_lab.constants import ASPECT_SIZES
from film_lab.ffmpeg_support import ffmpeg_available, run_ffmpeg
from film_lab.generators.comfyui_i2v import INSTALL_HINT, ComfyUII2VGenerator
from film_lab.hub import FORBIDDEN_BRANDS
from film_lab.motion_path import FFMPEG_HINT
from film_lab.shot_card import ShotCard, new_shot_id
from film_lab.util import new_id

WORKFLOWS = Path(__file__).resolve().parents[1] / "workflows" / "effects"

ASPECTS: tuple[str, ...] = ("9:16", "16:9")
RESOLUTIONS: tuple[str, ...] = ("720", "1080")

DESK_SIZES: dict[str, dict[str, tuple[int, int]]] = {
    "720": {"16:9": (1280, 720), "9:16": (720, 1280)},
    "1080": {"16:9": (1920, 1080), "9:16": (1080, 1920)},
}


@dataclass(frozen=True)
class EffectPreset:
    id: str
    label: str
    blurb: str
    motion: str
    camera: str
    tone: str = "#2a1848"
    strength: float = 0.72


EFFECT_PRESETS: tuple[EffectPreset, ...] = (
    EffectPreset(
        "floating_fall",
        "Floating fall",
        "Body eases off the ground, slow drop, hair and cloth lift.",
        "slow floating fall, subject leaves the floor, weightless drop, "
        "hair and cloth lift, hold the face, cinematic still-to-motion",
        "high",
        "#3a2468",
        0.78,
    ),
    EffectPreset(
        "high_flip",
        "High flip",
        "A committed flip; camera stays with the face.",
        "high flip, full-body rotation, committed athletic motion, "
        "same adult face locked, no morph, cinematic",
        "low",
        "#2a1858",
        0.88,
    ),
    EffectPreset(
        "studio_slide",
        "Studio slide",
        "Lateral slide across a clean studio floor.",
        "studio slide, lateral body travel, feet skim the floor, "
        "controlled fashion motion, locked likeness",
        "pan L",
        "#1c2848",
        0.7,
    ),
    EffectPreset(
        "melting_hold",
        "Melting hold",
        "Form softens and drips while the face stays adult.",
        "slow melting hold, fabric and flesh soften, drip, "
        "face remains the same late-20s adult, no child features",
        "static",
        "#321848",
        0.65,
    ),
    EffectPreset(
        "slow_orbit",
        "Slow orbit",
        "Camera arcs around a planted subject.",
        "slow orbit around the subject, planted stance, "
        "background slides, face lock, cinematic",
        "pan R",
        "#1c3850",
        0.58,
    ),
    EffectPreset(
        "weight_drop",
        "Weight drop",
        "Knees give; gravity wins in one beat.",
        "weight drop, knees soften, body yields to gravity, "
        "natural collapse, adult bodies, micro-motion into the fall",
        "high",
        "#2a2058",
        0.8,
    ),
    EffectPreset(
        "paper_lift",
        "Paper lift",
        "A light upward lift, as if the still were a sheet.",
        "paper lift, subject rises a few inches, cloth flutters, "
        "gentle upward drift, hold continuity with the still",
        "low",
        "#241848",
        0.6,
    ),
    EffectPreset(
        "lamp_bloom_drift",
        "Lamp bloom drift",
        "Warm bloom drifts across skin; almost no blocking change.",
        "lamp bloom drift, warm light crawls on skin, "
        "tiny breath, almost still, cinematic bedroom",
        "slow push-in",
        "#3a2080",
        0.45,
    ),
)


def preset_labels() -> list[str]:
    return [p.label for p in EFFECT_PRESETS]


def preset_detail_md(label: str) -> str:
    preset = preset_by_label(label)
    return (
        f"**{preset.label}.** {preset.blurb} "
        f"{workflow_stub_note(preset)} Zero credits."
    )


def preset_by_label(label: str) -> EffectPreset:
    for preset in EFFECT_PRESETS:
        if preset.label == label:
            return preset
    return EFFECT_PRESETS[0]


def workflow_path(preset: EffectPreset) -> Path:
    return WORKFLOWS / f"{preset.id}.json"


def workflow_is_live(preset: EffectPreset) -> bool:
    path = workflow_path(preset)
    if not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    return '"class_type"' in text and "stub" not in text.lower()


def workflow_stub_note(preset: EffectPreset) -> str:
    path = workflow_path(preset)
    if workflow_is_live(preset):
        return f"Custom Comfy graph ready: `{path.name}`."
    return (
        f"No custom Comfy graph for **{preset.label}** yet "
        f"(drop an API-format workflow at `workflows/effects/{preset.id}.json`). "
        "Until then Generate uses the shared local SVD-XT img2vid graph "
        "with this preset's motion prompt. "
        f"{INSTALL_HINT}"
    )


def engine_markdown() -> str:
    ff_ok, ff_msg = ffmpeg_available()
    comfy = ComfyUII2VGenerator().probe()
    lines = [
        "### Effects engine (this PC)",
        "Character still + preset motion → **local ComfyUI**. Zero Film Lab credits. "
        "No free-gens counter. No Film Lab NSFW filter.",
        "",
    ]
    if comfy.available:
        lines.append(f"- **Local SVD-XT:** Ready — {comfy.message}")
    else:
        lines.append(f"- **Local SVD-XT:** Off — {comfy.message}")
        lines.append(f"- {INSTALL_HINT}")
    live = sum(1 for p in EFFECT_PRESETS if workflow_is_live(p))
    lines.append(
        f"- Custom per-preset graphs: **{live}/{len(EFFECT_PRESETS)}** live under "
        "`workflows/effects/`. Missing graphs are stubs — Generate still uses SVD-XT."
    )
    if not ff_ok:
        lines.append(f"- ffmpeg: missing — {ff_msg} {FFMPEG_HINT}")
    lines.append(
        "- After export, finishing is often **DaVinci Resolve** or **Adobe After Effects** "
        "on this machine. Film Lab does not replace that grade."
    )
    lines.append("- Ken Burns is not this desk.")
    blob = "\n".join(lines)
    lower = blob.lower()
    for banned in FORBIDDEN_BRANDS:
        if banned in lower:
            raise RuntimeError(f"Forbidden brand leaked into Effects engine copy: {banned}")
    return blob


def compose_effect_prompt(
    preset: EffectPreset,
    *,
    extra: str = "",
    use_extra: bool = False,
    has_location: bool = False,
    has_product: bool = False,
    lighting: str = "",
) -> str:
    bits = [
        preset.motion,
        "same adult face as the character still",
        "adults 18+",
        "natural body motion, cinematic still-to-motion",
    ]
    if has_location:
        bits.append("environment continuity with the location plate")
    if has_product:
        bits.append("product readable in frame, held or worn")
    if use_extra and (extra or "").strip():
        bits.append(extra.strip())
    from film_lab.lighting import lighting_prompt_bit

    light = lighting_prompt_bit(lighting)
    if light:
        bits.append(light)
    return ", ".join(bits)


def desk_size(aspect: str, resolution: str) -> tuple[int, int]:
    table = DESK_SIZES.get(resolution) or DESK_SIZES["720"]
    return table.get(aspect, table["16:9"])


def scale_desk_mp4(src: Path, dest: Path, *, aspect: str, resolution: str) -> Path:
    width, height = desk_size(aspect, resolution)
    dest.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(
        [
            "-y",
            "-i",
            str(src),
            "-vf",
            (
                f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
            ),
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(dest),
        ]
    )
    return dest


def build_effect_shot(
    preset: EffectPreset,
    *,
    aspect: str,
    extra: str = "",
    use_extra: bool = False,
    has_location: bool = False,
    has_product: bool = False,
    start_frame: str | None = None,
    character_ids: list[str] | None = None,
    lighting: str = "",
) -> ShotCard:
    ratio = aspect if aspect in ASPECTS else "16:9"
    return ShotCard(
        id=new_shot_id(),
        name=f"FX · {preset.label}",
        start_frame=start_frame,
        duration=2.5,
        aspect_ratio=ratio if ratio in ASPECT_SIZES else "16:9",
        camera_move=preset.camera,
        subject_motion_strength=preset.strength,
        body_motion_notes=preset.blurb,
        director_intent=compose_effect_prompt(
            preset,
            extra=extra,
            use_extra=use_extra,
            has_location=has_location,
            has_product=has_product,
            lighting=lighting,
        ),
        character_ids=list(character_ids or ["alison", "bradley"]),
        lighting=lighting or "",
    )


def effects_shelf_html() -> str:
    tiles = []
    for preset in EFFECT_PRESETS:
        stub = "" if workflow_is_live(preset) else "<i>SVD-XT</i>"
        tiles.append(
            "<button type='button' class='fl-fx-tile' "
            f"style='--tone:{_esc(preset.tone)}'>"
            f"<span class='fl-fx-poster'></span>"
            f"<b>{_esc(preset.label)}</b>"
            f"<span>{_esc(preset.blurb)}</span>{stub}"
            "</button>"
        )
    return (
        "<div class='fl-fx-grid' role='list'>"
        + "".join(tiles)
        + "</div>"
    )


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def unique_output(project, stem: str) -> Path:
    project.ensure_dirs()
    return project.outputs_dir / f"{stem}_{new_id()}.mp4"
