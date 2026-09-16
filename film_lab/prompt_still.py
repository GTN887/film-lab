"""Local prompt card still — so prompt-only Motion Desk still writes an MP4.

Typography on a dark studio field. Not a hosted image model. Adults 18+ copy only.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from film_lab.constants import ASPECT_SIZES
from film_lab.project import Project, _unique_dest
from film_lab.shot_card import ShotCard
from film_lab.util import slugify

BG = (10, 7, 18)
GOLD = (126, 232, 232)  # locked cyan accent (name kept)
INK = (242, 238, 248)
MUTE = (154, 147, 168)


def render_prompt_still(project: Project, shot: ShotCard, prompt: str) -> Path:
    """Write a cinematic title-card PNG into the project stills folder."""
    project.ensure_dirs()
    width, height = ASPECT_SIZES.get(shot.aspect_ratio, ASPECT_SIZES["16:9"])
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)
    # Purple wash left; soft cyan falloff right — matches the locked studio chrome.
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(10 + 36 * (1 - t) * 0.45)
        g = int(7 + 18 * (1 - t) * 0.2)
        b = int(18 + 42 * (1 - t) * 0.55)
        draw.line([(0, y), (int(width * 0.42), y)], fill=(r, g, b))
    draw.rectangle((48, 48, width - 48, height - 48), outline=GOLD, width=2)
    font_title = _font(max(28, width // 28))
    font_body = _font(max(20, width // 42))
    font_small = _font(max(16, width // 56))
    draw.text((72, 64), "FILM LAB", fill=GOLD, font=font_small)
    draw.text((72, 92), (shot.name or "Motion").upper()[:48], fill=INK, font=font_title)
    wrapped = textwrap.fill((prompt or "").strip() or "held lamp, two adults, no cut", width=36)
    draw.multiline_text((72, 160), wrapped[:600], fill=MUTE, font=font_body, spacing=8)
    draw.text((72, height - 88), f"{shot.aspect_ratio}  ·  local still  ·  adults 18+", fill=GOLD, font=font_small)
    dest = _unique_dest(project.stills_dir, f"prompt_{slugify(shot.name, 'shot')}.png")
    image.save(dest, format="PNG")
    return dest


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
