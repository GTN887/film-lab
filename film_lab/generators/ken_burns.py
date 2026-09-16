"""Always-available ffmpeg Ken Burns / zoompan fallback from a still."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

from film_lab.constants import ASPECT_SIZES, DEFAULT_FPS
from film_lab.ffmpeg_support import FFmpegError, ffmpeg_available, run_ffmpeg
from film_lab.generators.base import GenerateJob, GeneratorUnavailable, ProbeResult
from film_lab.stitch import crossfade_pair

COVER_SCALE = 2.0


class KenBurnsGenerator:
    id = "ken_burns"
    label = "Ken Burns CPU fallback (Advanced · timing only)"

    def probe(self) -> ProbeResult:
        ok, message = ffmpeg_available()
        if not ok:
            return ProbeResult(False, message)
        return ProbeResult(True, f"Ready — {message}")

    def generate(self, job: GenerateJob) -> Path:
        probe = self.probe()
        if not probe.available:
            raise GeneratorUnavailable(probe.message)

        job.output_path.parent.mkdir(parents=True, exist_ok=True)
        width, height = ASPECT_SIZES[job.shot.aspect_ratio]
        frames = max(2, int(round(job.shot.duration * DEFAULT_FPS)))
        work = job.output_path.parent / f".{job.output_path.stem}_work"
        work.mkdir(parents=True, exist_ok=True)

        start_png = work / "start.png"
        _prep_still(job.start_path, start_png, width, height)

        if job.end_path is None:
            _zoompan(
                start_png,
                job.output_path,
                job.shot.camera_move,
                job.shot.subject_motion_strength,
                frames,
                width,
                height,
            )
            _cleanup(work)
            return job.output_path

        end_png = work / "end.png"
        _prep_still(job.end_path, end_png, width, height)
        first_frames = max(2, int(frames * 0.58))
        second_frames = max(2, frames - first_frames + int(0.5 * DEFAULT_FPS))
        a = work / "a.mp4"
        b = work / "b.mp4"
        _zoompan(
            start_png,
            a,
            job.shot.camera_move,
            job.shot.subject_motion_strength,
            first_frames,
            width,
            height,
        )
        # End frame holds the landing composition; milder complementary move.
        _zoompan(
            end_png,
            b,
            _complementary_move(job.shot.camera_move),
            max(0.15, job.shot.subject_motion_strength * 0.6),
            second_frames,
            width,
            height,
        )
        overlap = min(0.7, job.shot.duration * 0.12)
        crossfade_pair(a, b, job.output_path, overlap=overlap)
        _cleanup(work)
        return job.output_path


def render_camera_move(
    src: Path,
    dest: Path,
    camera: str,
    *,
    duration: float = 4.0,
    strength: float = 0.4,
    aspect: str = "16:9",
) -> Path:
    """Local ffmpeg look-around / zoom / aerial from one still. Not SVD."""
    ok, message = ffmpeg_available()
    if not ok:
        raise GeneratorUnavailable(message)
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    width, height = ASPECT_SIZES.get(aspect, ASPECT_SIZES["16:9"])
    frames = max(8, int(round(max(1.0, float(duration)) * DEFAULT_FPS)))
    work = dest.parent / f".{dest.stem}_env_work"
    work.mkdir(parents=True, exist_ok=True)
    start_png = work / "start.png"
    _prep_still(Path(src), start_png, width, height)
    move = {
        "look-around": "orbit",
        "look around": "orbit",
        "zoom": "slow push-in",
    }.get((camera or "").strip(), (camera or "").strip() or "orbit")
    _zoompan(start_png, dest, move, strength, frames, width, height)
    _cleanup(work)
    return dest


def _complementary_move(camera: str) -> str:
    return {
        "slow push-in": "static",
        "pull-out": "static",
        "pan L": "pan R",
        "pan R": "pan L",
        "low": "static",
        "high": "static",
        "OTS": "static",
        "orbit": "slow push-in",
        "aerial": "high",
        "drone": "high",
        "wide outdoor": "static",
    }.get(camera, "static")


def _prep_still(src: Path, dest: Path, out_w: int, out_h: int) -> None:
    image = Image.open(src)
    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")
    target = (int(out_w * COVER_SCALE), int(out_h * COVER_SCALE))
    fitted = ImageOps.fit(image, target, method=Image.Resampling.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fitted.save(dest, format="PNG")


def _zoompan(
    src: Path,
    dest: Path,
    camera: str,
    strength: float,
    frames: int,
    width: int,
    height: int,
) -> None:
    z_extra = 0.08 + 0.28 * strength
    last = max(1, frames - 1)
    # zoompan window is 1/zoom of the input. Keep zoom >= 1.12 so pans have travel.
    if camera == "static":
        # Tiny breathing zoom — readable as hold, not a crash-zoom.
        amp = 0.012 + 0.03 * strength
        z = f"1.14+{amp:.4f}*sin(2*PI*on/{frames})"
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)"
    elif camera == "slow push-in":
        z = f"1.12+{z_extra:.4f}*on/{last}"
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)"
    elif camera == "pull-out":
        z = f"{1.12 + z_extra:.4f}-{z_extra:.4f}*on/{last}"
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)"
    elif camera == "pan L":
        z = f"{1.22 + 0.06 * strength:.4f}"
        x = f"(iw-iw/zoom)*(1-on/{last})"
        y = "ih/2-(ih/zoom/2)"
    elif camera == "pan R":
        z = f"{1.22 + 0.06 * strength:.4f}"
        x = f"(iw-iw/zoom)*on/{last}"
        y = "ih/2-(ih/zoom/2)"
    elif camera == "low":
        # Low camera looks up — bias the crop toward the top of the still.
        z = f"1.16+{z_extra * 0.45:.4f}*on/{last}"
        x = "iw/2-(iw/zoom/2)"
        y = f"(ih-ih/zoom)*0.18"
    elif camera == "high":
        z = f"1.16+{z_extra * 0.45:.4f}*on/{last}"
        x = "iw/2-(iw/zoom/2)"
        y = f"(ih-ih/zoom)*0.82"
    elif camera == "OTS":
        # Over-the-shoulder: sit off-center, ease in.
        z = f"1.18+{z_extra * 0.55:.4f}*on/{last}"
        x = f"(iw-iw/zoom)*0.28"
        y = "ih/2-(ih/zoom/2)"
    elif camera in {"orbit", "look-around", "look around"}:
        z = f"1.16+{z_extra * 0.4:.4f}*on/{last}"
        x = f"(iw-iw/zoom)*(0.2+0.6*on/{last})"
        y = "ih/2-(ih/zoom/2)"
    elif camera in {"aerial", "drone"}:
        z = f"1.14+{z_extra * 0.35:.4f}*on/{last}"
        x = "iw/2-(iw/zoom/2)"
        y = f"(ih-ih/zoom)*0.12"
    elif camera == "wide outdoor":
        amp = 0.01 + 0.02 * strength
        z = f"1.12+{amp:.4f}*sin(2*PI*on/{frames})"
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)"
    else:
        raise ValueError(f"Unknown camera move: {camera}")

    vf = (
        f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:"
        f"s={width}x{height}:fps={DEFAULT_FPS}"
    )
    try:
        run_ffmpeg(
            [
                "-y",
                "-loop",
                "1",
                "-i",
                str(src),
                "-vf",
                vf,
                "-frames:v",
                str(frames),
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
    except FFmpegError as exc:
        raise GeneratorUnavailable(str(exc)) from exc


def _cleanup(work: Path) -> None:
    if not work.exists():
        return
    for child in work.iterdir():
        try:
            child.unlink()
        except OSError:
            pass
    try:
        work.rmdir()
    except OSError:
        pass
