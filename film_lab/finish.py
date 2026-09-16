"""LUT + light VFX post on stills or gallery clips (ffmpeg, local)."""

from __future__ import annotations

from pathlib import Path

from film_lab.ffmpeg_support import FFmpegError, probe_duration_seconds, run_ffmpeg
from film_lab.luts import list_luts
from film_lab.project import Project
from film_lab.shot_card import slugify
from film_lab.util import new_id

VFX_OPS = ("fade", "grain", "bloom", "letterbox", "speed")


def lut_choices(project: Project) -> list[str]:
    return [p.name for p in list_luts(project.root)]


def resolve_lut(project: Project, name: str) -> Path:
    for path in list_luts(project.root):
        if path.name == name:
            return path
    raise FileNotFoundError(f"LUT {name!r} not found in data/luts or the project luts/ folder.")


def apply_lut(src: Path, lut: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    # lut3d wants a POSIX-ish path; quote via filter escaping.
    lut_esc = str(lut.resolve()).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    vf = f"lut3d='{lut_esc}'"
    _transcode(src, dest, vf)
    return dest


def apply_vfx(src: Path, dest: Path, op: str, *, strength: float = 0.5, speed: float = 1.0) -> Path:
    if op not in VFX_OPS:
        raise ValueError(f"Unknown VFX op {op!r}. Choose {VFX_OPS}.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    duration = probe_duration_seconds(src) or 4.0
    strength = max(0.0, min(1.0, strength))
    if op == "fade":
        fade_in = 0.15 + 0.55 * strength
        fade_out = 0.2 + 0.7 * strength
        start_out = max(0.1, duration - fade_out)
        vf = f"fade=t=in:st=0:d={fade_in:.3f},fade=t=out:st={start_out:.3f}:d={fade_out:.3f}"
    elif op == "grain":
        alls = 4 + int(20 * strength)
        vf = f"noise=alls={alls}:allf=t+u"
    elif op == "bloom":
        blur = 4 + int(18 * strength)
        opacity = 0.12 + 0.4 * strength
        vf = (
            f"split[a][b];[b]boxblur={blur}:{max(1, blur // 2)}[b];"
            f"[a][b]blend=all_mode=screen:all_opacity={opacity:.3f}"
        )
    elif op == "letterbox":
        bar = 0.08 + 0.14 * strength
        vf = (
            f"scale=iw:ih*(1-{bar * 2:.4f}),"
            f"pad=iw:ih/(1-{bar * 2:.4f}):0:(oh-ih)/2:black"
        )
    else:  # speed
        factor = max(0.25, min(2.5, speed))
        vf = f"setpts=PTS/{factor:.4f}"
    _transcode(src, dest, vf)
    return dest


def finish_output_path(project: Project, src: Path, tag: str) -> Path:
    project.ensure_dirs()
    return project.outputs_dir / f"{slugify(src.stem)}_{tag}_{new_id()}.mp4"


def _transcode(src: Path, dest: Path, vf: str) -> None:
    if not src.is_file():
        raise FileNotFoundError(src)
    extra: list[str] = []
    if src.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}:
        extra = ["-loop", "1", "-t", "4"]
    try:
        run_ffmpeg(
            [
                "-y",
                *extra,
                "-i",
                str(src),
                "-vf",
                vf,
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
    except FFmpegError:
        raise
