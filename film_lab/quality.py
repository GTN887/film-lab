"""Quality lock — 480p / 720p / 1080p / 4K for stills and video.

RX 5600 XT (~6GB): prefer native 480p / 720p. 1080p when VRAM allows.
4K is never a native SVD pass — generate lower, upscale on export.
Resolution sticks on the shot card so Regenerate keeps the take.
Zero credits.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

from film_lab.constants import (
    ASPECT_FLAT,
    ASPECT_RATIOS,
    ASPECT_SCOPE,
    DEFAULT_ASPECT,
    normalize_aspect,
)
from film_lab.ffmpeg_support import FFmpegError, run_ffmpeg

QUALITY_480 = "480p"
QUALITY_720 = "720p"
QUALITY_1080 = "1080p"
QUALITY_1440 = "1440p"
QUALITY_4K = "4K"

QUALITY_PRESETS: tuple[str, ...] = (
    QUALITY_480,
    QUALITY_720,
    QUALITY_1080,
    QUALITY_1440,
    QUALITY_4K,
)
DEFAULT_QUALITY = QUALITY_720
NATIVE_PRESETS: tuple[str, ...] = (QUALITY_480, QUALITY_720, QUALITY_1080)
EXPORT_ONLY: tuple[str, ...] = (QUALITY_1440, QUALITY_4K)

_ALIASES: dict[str, str] = {
    "480": QUALITY_480,
    "480p": QUALITY_480,
    "720": QUALITY_720,
    "720p": QUALITY_720,
    "1080": QUALITY_1080,
    "1080p": QUALITY_1080,
    "1440": QUALITY_1440,
    "1440p": QUALITY_1440,
    "2160": QUALITY_4K,
    "2160p": QUALITY_4K,
    "4k": QUALITY_4K,
    "4K": QUALITY_4K,
}

# Named Quality edge is the shorter side (16:9 height / 9:16 width).
_QUALITY_SHORT: dict[str, int] = {
    QUALITY_480: 480,
    QUALITY_720: 720,
    QUALITY_1080: 1080,
    QUALITY_1440: 1440,
    QUALITY_4K: 2160,
}
_INTERNAL_SHORT: dict[str, int] = {
    QUALITY_480: 216,
    QUALITY_720: 288,
    QUALITY_1080: 360,
}
_ASPECT_PAIR: dict[str, tuple[int, int]] = {
    "9:16": (9, 16),
    "16:9": (16, 9),
    "1:1": (1, 1),
    "4:5": (4, 5),
    "3:2": (3, 2),
    "2:3": (2, 3),
    "4:3": (4, 3),
    "3:4": (3, 4),
    "21:9": (21, 9),
    ASPECT_SCOPE: (239, 100),
    ASPECT_FLAT: (37, 20),
}

# Locked triples — keep existing AMD pixels. Other ratios are computed.
_LOCKED_DESK: dict[str, dict[str, tuple[int, int]]] = {
    QUALITY_480: {"16:9": (854, 480), "9:16": (480, 854), "1:1": (480, 480)},
    QUALITY_720: {"16:9": (1280, 720), "9:16": (720, 1280), "1:1": (720, 720)},
    QUALITY_1080: {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080)},
    QUALITY_1440: {"16:9": (2560, 1440), "9:16": (1440, 2560), "1:1": (1440, 1440)},
    QUALITY_4K: {"16:9": (3840, 2160), "9:16": (2160, 3840), "1:1": (2160, 2160)},
}
_LOCKED_INTERNAL: dict[str, dict[str, tuple[int, int]]] = {
    QUALITY_480: {"16:9": (384, 216), "9:16": (216, 384), "1:1": (256, 256)},
    QUALITY_720: {"16:9": (512, 288), "9:16": (288, 512), "1:1": (384, 384)},
    QUALITY_1080: {"16:9": (640, 360), "9:16": (360, 640), "1:1": (512, 512)},
}


def _even(n: int) -> int:
    return max(2, int(n) // 2 * 2)


def _align32(n: int) -> int:
    return max(32, int(n) // 32 * 32)


def _frame(short: int, aspect: str, *, align: int = 2) -> tuple[int, int]:
    aw, ah = _ASPECT_PAIR[normalize_aspect(aspect)]
    if aw >= ah:
        height = short
        width = int(round(short * aw / ah))
    else:
        width = short
        height = int(round(short * ah / aw))
    snap = _align32 if align == 32 else _even
    return snap(width), snap(height)


def _fill_sizes(
    locked: dict[str, dict[str, tuple[int, int]]],
    shorts: dict[str, int],
    *,
    align: int,
) -> dict[str, dict[str, tuple[int, int]]]:
    out: dict[str, dict[str, tuple[int, int]]] = {}
    for quality, short in shorts.items():
        row = dict(locked.get(quality, {}))
        for aspect in ASPECT_RATIOS:
            if aspect not in row:
                row[aspect] = _frame(short, aspect, align=align)
        out[quality] = row
    return out


# Final desk / export pixels. 4K is export-only.
DESK_SIZES: dict[str, dict[str, tuple[int, int]]] = _fill_sizes(
    _LOCKED_DESK, _QUALITY_SHORT, align=2
)

# SVD-XT internal on ~6GB. Never 4K.
INTERNAL_SIZES: dict[str, dict[str, tuple[int, int]]] = _fill_sizes(
    _LOCKED_INTERNAL, _INTERNAL_SHORT, align=32
)

AMD_NOTE = (
    "RX 5600 XT (~6GB): prefer native **480p / 720p**. "
    "**1080p** only if VRAM allows. **1440p / 4K** are generate-lower then upscale on export — "
    "never a native SVD pass on this GPU."
)

QUALITY_PROGRAM = (
    "### Quality program (RX 5600 XT, not NVIDIA)\n"
    "1. Pick **Resolution** **480p / 720p / 1080p / 1440p / 4K** on Pipeline, Still, and Motion "
    "(Cinema export uses the same picker).\n"
    "2. Hardware defaults: native **480 / 720**; **1080** when VRAM allows; "
    "**1440p / 4K = generate lower then upscale on export**.\n"
    "3. The shot card stores Quality so **Regenerate** keeps the take.\n"
    "4. On fail / OOM / crash, run the debug checklist — do not force native 4K."
)

DEBUG_CHECKLIST = (
    "### DEBUG CHECKLIST (fail / OOM / crash — AMD, not NVIDIA)\n"
    "1. Drop one resolution step (**1080p → 720p → 480p**).\n"
    "2. Shorter duration / fewer frames (30s → 15s → 5s).\n"
    "3. Retry **Regenerate** (new seed, same still + prompt + Quality).\n"
    "4. Restart Comfy via the launcher if the sidecar is still dead (`8188`).\n"
    "5. **Never force native 4K** on this GPU. Same for **1440p**."
)


def normalize_quality(value: str | None) -> str:
    text = (value or "").strip()
    if text in QUALITY_PRESETS:
        return text
    return _ALIASES.get(text, _ALIASES.get(text.lower(), DEFAULT_QUALITY))


def is_4k(value: str | None) -> bool:
    return normalize_quality(value) == QUALITY_4K


def native_quality(value: str | None) -> str:
    """What SVD actually generates. 4K → 720p native."""
    q = normalize_quality(value)
    if q in EXPORT_ONLY:
        return QUALITY_720
    return q


def desk_size(quality: str | None, aspect: str = DEFAULT_ASPECT) -> tuple[int, int]:
    table = DESK_SIZES.get(normalize_quality(quality), DESK_SIZES[DEFAULT_QUALITY])
    key = normalize_aspect(aspect)
    return table.get(key, table[DEFAULT_ASPECT])


def native_desk_size(quality: str | None, aspect: str = DEFAULT_ASPECT) -> tuple[int, int]:
    return desk_size(native_quality(quality), aspect)


def export_size(quality: str | None, aspect: str = DEFAULT_ASPECT) -> tuple[int, int]:
    return desk_size(quality, aspect)


def internal_size(quality: str | None, aspect: str = DEFAULT_ASPECT) -> tuple[int, int]:
    q = native_quality(quality)
    table = INTERNAL_SIZES.get(q, INTERNAL_SIZES[DEFAULT_QUALITY])
    key = normalize_aspect(aspect)
    return table.get(key, table[DEFAULT_ASPECT])


def next_lower_quality(value: str | None) -> str | None:
    q = native_quality(value)
    order = [QUALITY_1080, QUALITY_720, QUALITY_480]
    if q not in order:
        return QUALITY_720
    idx = order.index(q)
    if idx + 1 >= len(order):
        return None
    return order[idx + 1]


def quality_program() -> str:
    return f"{AMD_NOTE}\n\n{QUALITY_PROGRAM}"


def quality_help() -> str:
    return (
        f"{AMD_NOTE} Quality sticks on the shot card — **Regenerate** keeps it. "
        "4K export upscales the native take."
    )


def quality_debug_md() -> str:
    return f"{quality_program()}\n\n{DEBUG_CHECKLIST}"


def oom_hint(quality: str | None = None) -> str:
    nxt = next_lower_quality(quality)
    drop = (
        f"Drop Quality {normalize_quality(quality)} → **{nxt}**. "
        if nxt
        else "Already at 480p. "
    )
    return (
        f"{drop}{DEBUG_CHECKLIST}"
    )


def resize_still(src: Path, dest: Path, quality: str | None, aspect: str = DEFAULT_ASPECT) -> Path:
    """Fit a still to native desk size (4K stills ingest at 720p)."""
    width, height = native_desk_size(quality, aspect)
    image = Image.open(src)
    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")
    fitted = ImageOps.fit(image, (width, height), method=Image.Resampling.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fitted.save(dest, format="PNG")
    return dest


def scale_media(src: Path, dest: Path, quality: str | None, aspect: str = DEFAULT_ASPECT) -> Path:
    """Rewrap / upscale an MP4 (or still) to the export size for this Quality."""
    width, height = export_size(quality, aspect)
    dest.parent.mkdir(parents=True, exist_ok=True)
    suffix = src.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        image = Image.open(src).convert("RGB")
        fitted = ImageOps.fit(image, (width, height), method=Image.Resampling.LANCZOS)
        fitted.save(dest, format="PNG")
        return dest
    try:
        run_ffmpeg(
            [
                "-y",
                "-i",
                str(src),
                "-vf",
                f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-an",
                str(dest),
            ]
        )
    except FFmpegError as exc:
        raise ValueError(str(exc)) from exc
    return dest
