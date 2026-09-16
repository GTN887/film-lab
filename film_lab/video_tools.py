"""Local AI video paths for Motion Desk. User-owned box only.

Lighter first on a Radeon RX 5600 XT (~6GB). No hosted video API. Zero Film Lab credits.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VideoPath:
    key: str
    title: str
    vram: str
    status: str
    notes: str


VIDEO_PATHS: tuple[VideoPath, ...] = (
    VideoPath(
        key="amd_i2v",
        title="ComfyUI img2vid (AMD DirectML)",
        vram="~4–6GB",
        status="primary",
        notes=(
            "Daily engine. Still + prompt → SVD-XT MP4 on Motion Desk. "
            "svd_xt.safetensors via ComfyUI at 127.0.0.1:8188 (--cuda-device 1). "
            "512×288, 2–4s first on 6GB."
        ),
    ),
    VideoPath(
        key="svd_class",
        title="SVD-XT (ComfyUI API)",
        vram="~6GB at 512×288 / 14 frames",
        status="primary",
        notes=(
            "Stock ComfyUI SVD_img2vid_Conditioning. Image holds likeness. "
            "Prompt steers motion bucket. Not a hosted Grok / xAI video API."
        ),
    ),
    VideoPath(
        key="wan_class",
        title="WAN-class / start–end motion (ComfyUI later)",
        vram="heavy",
        status="advanced",
        notes=(
            "True start-frame to end-frame actor motion when a later graph fits. "
            "Not required on 6GB. Documented so the picker can grow."
        ),
    ),
    VideoPath(
        key="ken_burns",
        title="Ken Burns (CPU zoompan)",
        vram="none",
        status="advanced",
        notes=(
            "Not the product. Timing / coverage only — no invented actor motion. "
            "Primary Generate never uses this. Open Advanced on Motion Desk if you need a zoom."
        ),
    ),
)


def video_tools_markdown() -> str:
    lines = [
        "### Local video tools (this PC)",
        "Zero Film Lab credits. No hosted video subscription. Adults 18+ only.",
        "",
    ]
    for path in VIDEO_PATHS:
        lines.append(
            f"- **{path.title}** — `{path.status}` · {path.vram}. {path.notes}"
        )
    lines.append(
        "- Primary CTA is **Generate video (SVD-XT · AMD)**. "
        "Ken Burns is collapsed under Advanced. See `docs/AMD_IMG2VID.md`."
    )
    return "\n".join(lines)
