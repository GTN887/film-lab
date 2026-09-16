"""Original open sample .cube LUTs (not commercial packs) plus a user drop folder."""

from __future__ import annotations

from pathlib import Path

LUT_SIZE = 9


def lut_root() -> Path:
    return Path.cwd() / "data" / "luts"


def project_lut_dir(project_root: Path) -> Path:
    return project_root / "luts"


def ensure_stock_luts() -> Path:
    """Write three original 3D LUTs if they are missing."""
    root = lut_root()
    root.mkdir(parents=True, exist_ok=True)
    recipes = {
        "warm_lamp.cube": _warm_lamp,
        "soft_print.cube": _soft_print,
        "cool_shadow.cube": _cool_shadow,
    }
    for name, fn in recipes.items():
        path = root / name
        if not path.exists():
            _write_cube(path, name.replace(".cube", ""), fn)
    readme = root / "README.txt"
    if not readme.exists():
        readme.write_text(
            "Drop your own .cube LUTs here or in data/projects/<name>/luts/.\n"
            "The three stock files are original Film Lab samples — not commercial LUT packs.\n",
            encoding="utf-8",
        )
    return root


def list_luts(project_root: Path | None = None) -> list[Path]:
    ensure_stock_luts()
    found: list[Path] = []
    roots = [lut_root()]
    if project_root is not None:
        roots.append(project_lut_dir(project_root))
    for root in roots:
        if not root.exists():
            continue
        found.extend(sorted(root.glob("*.cube")))
    return found


def _write_cube(path: Path, title: str, mapper) -> None:
    lines = [
        f'TITLE "{title}"',
        f"LUT_3D_SIZE {LUT_SIZE}",
        "DOMAIN_MIN 0.0 0.0 0.0",
        "DOMAIN_MAX 1.0 1.0 1.0",
    ]
    last = LUT_SIZE - 1
    for bi in range(LUT_SIZE):
        for gi in range(LUT_SIZE):
            for ri in range(LUT_SIZE):
                r, g, b = mapper(ri / last, gi / last, bi / last)
                lines.append(f"{r:.6f} {g:.6f} {b:.6f}")
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def _warm_lamp(r: float, g: float, b: float) -> tuple[float, float, float]:
    return (
        _clamp(r * 1.07 + 0.025),
        _clamp(g * 1.01 + 0.01),
        _clamp(b * 0.88),
    )


def _soft_print(r: float, g: float, b: float) -> tuple[float, float, float]:
    def roll(x: float) -> float:
        # Gentle highlight roll-off, lift the floor a hair.
        x = 0.04 + x * 0.92
        return _clamp(x * (1.04 - 0.08 * x))

    return roll(r), roll(g), roll(b)


def _cool_shadow(r: float, g: float, b: float) -> tuple[float, float, float]:
    luma = 0.3 * r + 0.59 * g + 0.11 * b
    shadow = max(0.0, 1.0 - luma * 1.4)
    return (
        _clamp(r * 0.96),
        _clamp(g * 1.0 + 0.02 * shadow),
        _clamp(b * 1.08 + 0.04 * shadow),
    )
