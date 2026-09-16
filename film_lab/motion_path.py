"""Working Motion Desk path: prompt + start still → local img2vid MP4.

Primary: ComfyUI img2vid on the RX 5600 XT (6GB DirectML). That is the product.
Ken Burns is Advanced-only timing/zoom — never the hero path, never auto-fallback.
Honest block if the sidecar is Off. Open weights only. Zero Film Lab credits.
"""

from __future__ import annotations

from pathlib import Path

from film_lab.ffmpeg_support import ffmpeg_available
from film_lab.generators import (
    DEFAULT_GENERATOR_ID,
    FALLBACK_GENERATOR_ID,
    GENERATORS,
    get_generator,
)
from film_lab.generators.base import GeneratorUnavailable
from film_lab.generators.comfyui_i2v import INSTALL_HINT, ComfyUII2VGenerator
from film_lab.project import Project
from film_lab.prompt_still import render_prompt_still
from film_lab.queue import generate_one
from film_lab.shot_card import ShotCard

FFMPEG_HINT = (
    "ffmpeg is missing, so Film Lab cannot write an MP4. "
    "Windows: winget install Gyan.FFmpeg  (or re-run .\\scripts\\install_windows.ps1). "
    "Then restart the desk. Zero credits — this is a local binary, not a shop."
)


class MotionBlocked(RuntimeError):
    """Nothing on this machine can write an MP4 right now."""


def motion_engine_markdown() -> str:
    ff_ok, _ff_msg = ffmpeg_available()
    comfy = ComfyUII2VGenerator().probe()
    lines = [
        "### Motion engine (this PC)",
        "Any still + motion prompt → **local SVD-XT img2vid** on the RX 5600 XT "
        "(people, products, cans, posters). That is the product. "
        "Zero Film Lab credits. No Film Lab NSFW filter.",
        "",
    ]
    if comfy.available:
        lines.append(f"- **Local img2vid (SVD-XT):** Ready — {comfy.message}")
        lines.append(
            "- **Generate video** talks to ComfyUI at 127.0.0.1:8188 "
            "(`svd_xt.safetensors`, 512×288 / 288×512, **2–4s per pass** on 6GB)."
        )
        lines.append(
            "- A **1 min / 2 min** reel (60s / 120s) is **not** one SVD pass. "
            "Generate on that lock builds a last-frame chain, then Cinema Desk stitch. "
            "Regenerate rolls a new seed on the same still + prompt."
        )
    else:
        lines.append(f"- **Local img2vid (SVD-XT):** Off — {comfy.message}")
        lines.append(
            "- Primary Generate **will not** zoom-pan a still. "
            "Start ComfyUI with `--cuda-device 1`, then generate again."
        )
    if not ff_ok:
        lines.append("")
        lines.append(f"**Blocked.** {FFMPEG_HINT}")
    else:
        lines.append(
            "- Ken Burns (CPU zoom) lives under **Advanced** — timing only, "
            "not actor motion, not the product."
        )
    return "\n".join(lines)


def user_motion_text(shot: ShotCard) -> str:
    bits = [
        (shot.director_intent or "").strip(),
        (shot.body_motion_notes or "").strip(),
        (shot.start_frame_hint or "").strip(),
    ]
    return ", ".join(b for b in bits if b)


def motion_prompt_text(shot: ShotCard) -> str:
    return user_motion_text(shot) or (shot.local_prompt() or "").strip()


def ensure_motion_still(
    project: Project,
    shot: ShotCard,
    uploaded: list[Path] | None = None,
) -> Path:
    """Use the dropped image, the selected start frame, or a prompt card."""
    for src in uploaded or []:
        if src.is_file():
            written = project.ingest_files([src])
            if written:
                shot.start_frame = written[0].name
                return written[0]
    existing = project.resolve_still(shot.start_frame)
    if existing:
        return existing
    from film_lab.envlock import resolve_env_still

    locked = resolve_env_still(project)
    if locked:
        shot.start_frame = locked.name
        return locked
    if not user_motion_text(shot):
        raise MotionBlocked(
            "Type a motion prompt or drop a still. "
            "Generate writes a local MP4 either way. Adults 18+ only."
        )
    dest = render_prompt_still(project, shot, motion_prompt_text(shot))
    shot.start_frame = dest.name
    return dest


def generate_motion_mp4(
    project: Project,
    shot: ShotCard,
    *,
    generator_id: str = DEFAULT_GENERATOR_ID,
    uploaded: list[Path] | None = None,
    allow_fallback: bool = False,
) -> tuple[Path, str]:
    """Return (mp4, human status). Primary path never auto-falls back to Ken Burns."""
    ff_ok, _ = ffmpeg_available()
    if not ff_ok:
        raise MotionBlocked(FFMPEG_HINT)

    ensure_motion_still(project, shot, uploaded)
    project.save_shot(shot)

    wanted = generator_id if generator_id in GENERATORS else DEFAULT_GENERATOR_ID
    errors: list[str] = []

    for candidate, label in _engine_order(wanted, allow_fallback=allow_fallback):
        gen = get_generator(candidate)
        probe = gen.probe()
        if not probe.available:
            errors.append(f"{label}: {probe.message}")
            continue
        try:
            output = generate_one(project, shot, gen)
            if not output.is_file() or output.stat().st_size < 64:
                raise GeneratorUnavailable(f"{label} wrote an empty file.")
            note = f"Wrote `{output.name}` with **{label}**."
            return output, note
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{label}: {exc}")
            if not allow_fallback:
                break

    detail = " ".join(errors) if errors else "No local engine."
    raise MotionBlocked(
        f"Could not write an MP4. {detail} {INSTALL_HINT if wanted == DEFAULT_GENERATOR_ID else ''} "
        f"{FFMPEG_HINT if not ff_ok else ''}".strip()
    )


def _engine_order(wanted: str, *, allow_fallback: bool) -> list[tuple[str, str]]:
    order = [(wanted, GENERATORS[wanted].label)]
    if allow_fallback and wanted != FALLBACK_GENERATOR_ID:
        order.append((FALLBACK_GENERATOR_ID, GENERATORS[FALLBACK_GENERATOR_ID].label))
    return order
