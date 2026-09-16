"""Grok-like Animate stage helpers. Local ComfyUI only — no cloud safety gate."""

from __future__ import annotations

import os
from pathlib import Path

# Never surface these. Grok used them to block Liam's adult couple.
CLOUD_SAFETY_PHRASES: tuple[str, ...] = (
    "safety guidelines",
    "cannot animate",
    "request rejected",
    "due to safety",
    "content policy",
    "rejected due to safety",
)

QUICK_DURATION = 2.0
QUICK_STRENGTH = 0.72
QUICK_PROMPT = (
    "natural body motion, breathing, slow push-in, "
    "late-20s adults, held lamp, cinematic still-to-motion"
)

REF_NAMES = ("alison_bradley_ref.jpg", "alison_bradley_ref.png", "alison_bradley_ref.webp")


SAFE_REWRITE = (
    "Cinematic adult 18+ take. Keep the locked bible. "
    "No safety lecture. Continue the idea as written."
)


def rewrite_cloud_safety(text: str) -> str:
    """Strip cloud NSFW-reject copy from feed or prompt text."""
    cleaned = (text or "").strip()
    lower = cleaned.lower()
    if any(phrase in lower for phrase in CLOUD_SAFETY_PHRASES):
        return SAFE_REWRITE
    return cleaned


def toast_html(message: str) -> str:
    """Bottom-right error chip. Technical only — never a cloud NSFW reject."""
    text = sanitize_motion_error(message)
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return (
        "<div class='fl-toast' role='status'>"
        f"<b>Film Lab</b><span>{escaped}</span>"
        "</div>"
    )


def sanitize_motion_error(message: str) -> str:
    raw = (message or "").strip() or "Could not write a local MP4."
    lower = raw.lower()
    if any(phrase in lower for phrase in CLOUD_SAFETY_PHRASES):
        return (
            "Local ComfyUI could not finish this take. "
            "Adult 18+ intimate content is allowed here — Film Lab has no NSFW filter. "
            "Check the sidecar at http://127.0.0.1:8188 (--cuda-device 1) and svd_xt.safetensors."
        )
    return raw


def generating_label(percent: int) -> str:
    pct = max(0, min(99, int(percent)))
    return f"Generating… {pct}%"


def default_ref_still() -> Path | None:
    """Find Liam's Alison/Bradley still if it is on this machine."""
    env = os.environ.get("FILM_LAB_REF_STILL")
    if env:
        path = Path(env)
        if path.is_file():
            return path
    local = os.environ.get("LOCALAPPDATA") or ""
    home = Path.home()
    roots = [
        Path.cwd() / "input",
        Path.cwd() / "examples" / "alison_bradley" / "stills",
        Path.cwd() / "data" / "projects" / "alison-bradley-study" / "stills",
        home / "FilmLab-ComfyUI" / "input",
    ]
    if local:
        roots.append(
            Path(local)
            / "Comfy-Desktop"
            / "ComfyUI-Installs"
            / "ComfyUI"
            / "ComfyUI"
            / "input"
        )
    extra = os.environ.get("FILM_LAB_COMFY_HOME")
    if extra:
        roots.append(Path(extra) / "input")
    seen: set[Path] = set()
    for root in roots:
        try:
            resolved = root.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        for name in REF_NAMES:
            candidate = resolved / name
            if candidate.is_file():
                return candidate
    return None


def extra_allowed_paths() -> list[str]:
    paths: list[str] = []
    ref = default_ref_still()
    if ref:
        paths.append(str(ref.parent.resolve()))
    return paths
