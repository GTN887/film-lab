#!/usr/bin/env python3
"""Write the locked purple + cyan FL icon used by the Windows zip / shortcuts."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
PURPLE = (10, 7, 18, 255)
VIOLET = (139, 108, 255, 255)
CYAN = (126, 232, 232, 255)
def _font(size: int) -> ImageFont.ImageFont:
    for name in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "DejaVuSans-Bold.ttf",
        "C:\\Windows\\Fonts\\segoeuib.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
    ):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_mark(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = max(1, size // 16)
    draw.rounded_rectangle(
        [pad, pad, size - pad - 1, size - pad - 1],
        radius=max(4, size // 6),
        fill=PURPLE,
        outline=VIOLET,
        width=max(1, size // 28),
    )
    glow = max(2, size // 10)
    draw.ellipse(
        [size // 2 - glow * 2, size // 5, size // 2 + glow * 2, size // 5 + glow * 3],
        fill=(139, 108, 255, 70),
    )
    font = _font(max(10, int(size * 0.42)))
    text = "FL"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) // 2 - bbox[0]
    y = (size - th) // 2 - bbox[1] - size // 32
    draw.text((x, y), text, font=font, fill=CYAN)
    return img


def write_icons(dest_dir: Path | None = None) -> tuple[Path, Path]:
    folder = dest_dir or ASSETS
    folder.mkdir(parents=True, exist_ok=True)
    png = folder / "film_lab.png"
    ico = folder / "film_lab.ico"
    hero = render_mark(256)
    hero.save(png, format="PNG")
    hero.save(
        ico,
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    return ico, png


def main() -> int:
    ico, png = write_icons()
    print(f"Wrote {ico} ({ico.stat().st_size} bytes)")
    print(f"Wrote {png} ({png.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
