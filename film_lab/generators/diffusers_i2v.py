"""Optional local image-to-video via diffusers when CUDA + weights exist.

This path is intentionally local-only. It never calls a hosted API.
If torch, CUDA, or the model weights are missing, `probe()` / `generate()`
fail soft with a clear message so the Ken Burns generator can stay in use.

Documented model IDs (download once, keep on disk):

- ``stabilityai/stable-video-diffusion-img2vid-xt`` (default)
- ``stabilityai/stable-video-diffusion-img2vid``
- override with env ``FILM_LAB_I2V_MODEL`` (Hugging Face id or local folder)

SVD does not take an end frame. When an end frame is set, Film Lab renders
the start still, then the end still, and crossfades them. For true start/end
actor motion (Wan, AnimateDiff), use the ComfyUI path in the README.
"""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageOps

from film_lab.constants import ASPECT_SIZES, DEFAULT_FPS
from film_lab.ffmpeg_support import ffmpeg_available, run_ffmpeg
from film_lab.generators.base import GenerateJob, GeneratorUnavailable, ProbeResult
from film_lab.stitch import crossfade_pair

DEFAULT_MODEL = "stabilityai/stable-video-diffusion-img2vid-xt"
ALT_MODELS = (
    "stabilityai/stable-video-diffusion-img2vid-xt",
    "stabilityai/stable-video-diffusion-img2vid",
)


class DiffusersI2VGenerator:
    id = "diffusers_i2v"
    label = "Diffusers I2V (local CUDA)"

    def probe(self) -> ProbeResult:
        try:
            import torch  # type: ignore[import-not-found]
        except ImportError:
            return ProbeResult(
                False,
                "torch is not installed. Ken Burns still works. "
                "For local I2V: pip install torch torchvision --index-url "
                "https://download.pytorch.org/whl/cu124 && "
                "pip install diffusers transformers accelerate",
            )
        if not torch.cuda.is_available():
            return ProbeResult(
                False,
                "CUDA GPU not visible to torch. Film Lab stays in demo/Ken Burns mode. "
                "Install a CUDA build of torch, or use ComfyUI for Wan/AnimateDiff.",
            )
        try:
            import diffusers  # noqa: F401  # type: ignore[import-not-found]
        except ImportError:
            return ProbeResult(
                False,
                "diffusers is not installed. pip install diffusers transformers accelerate",
            )
        model = os.environ.get("FILM_LAB_I2V_MODEL", DEFAULT_MODEL)
        gpu = torch.cuda.get_device_name(0)
        return ProbeResult(
            True,
            f"CUDA ready ({gpu}). Model id: {model}. "
            "First run downloads weights locally — nothing is uploaded.",
        )

    def generate(self, job: GenerateJob) -> Path:
        probe = self.probe()
        if not probe.available:
            raise GeneratorUnavailable(probe.message)
        ok, ff_msg = ffmpeg_available()
        if not ok:
            raise GeneratorUnavailable(ff_msg)

        import torch  # type: ignore[import-not-found]
        from diffusers import StableVideoDiffusionPipeline  # type: ignore[import-not-found]

        job.output_path.parent.mkdir(parents=True, exist_ok=True)
        model_id = os.environ.get("FILM_LAB_I2V_MODEL", DEFAULT_MODEL)
        width, height = ASPECT_SIZES[job.shot.aspect_ratio]
        # SVD XT is trained around 1024x576; we fit then letterbox back to desk AR.
        pipe_w, pipe_h = _svd_size(job.shot.aspect_ratio)

        try:
            dtype = torch.float16 if torch.cuda.is_available() else torch.float32
            pipe = StableVideoDiffusionPipeline.from_pretrained(
                model_id,
                torch_dtype=dtype,
                variant="fp16" if dtype == torch.float16 else None,
            )
            pipe.to("cuda")
        except Exception as exc:  # noqa: BLE001
            raise GeneratorUnavailable(
                f"Could not load local I2V model {model_id!r}: {exc}. "
                "Set FILM_LAB_I2V_MODEL to a downloaded folder, or stay on Ken Burns."
            ) from exc

        work = job.output_path.parent / f".{job.output_path.stem}_i2v"
        work.mkdir(parents=True, exist_ok=True)
        try:
            start_mp4 = work / "start.mp4"
            _run_svd(pipe, torch, job, job.start_path, start_mp4, pipe_w, pipe_h)
            if job.end_path is None:
                _rewrap(start_mp4, job.output_path, width, height, job.shot.duration)
                return job.output_path
            end_mp4 = work / "end.mp4"
            _run_svd(pipe, torch, job, job.end_path, end_mp4, pipe_w, pipe_h)
            a = work / "a.mp4"
            b = work / "b.mp4"
            _rewrap(start_mp4, a, width, height, job.shot.duration * 0.55)
            _rewrap(end_mp4, b, width, height, job.shot.duration * 0.55)
            crossfade_pair(a, b, job.output_path, overlap=0.5)
            return job.output_path
        finally:
            _cleanup(work)
            del pipe
            try:
                torch.cuda.empty_cache()
            except Exception:  # noqa: BLE001
                pass


def _svd_size(aspect: str) -> tuple[int, int]:
    from film_lab.constants import normalize_aspect

    key = normalize_aspect(aspect)
    if key in {"9:16", "4:5", "2:3"}:
        return 576, 1024
    if key == "1:1":
        return 768, 768
    if key == "21:9":
        return 1024, 440
    if key == "4:3":
        return 1024, 768
    if key == "3:4":
        return 768, 1024
    if "2.39" in key or key.endswith("scope"):
        return 1024, 432
    if key == "1.85:1":
        return 1024, 552
    return 1024, 576


def _run_svd(pipe, torch, job: GenerateJob, still: Path, dest: Path, w: int, h: int) -> None:
    image = Image.open(still)
    image = ImageOps.exif_transpose(image).convert("RGB")
    image = ImageOps.fit(image, (w, h), method=Image.Resampling.LANCZOS)
    strength = job.shot.subject_motion_strength
    motion_bucket = int(40 + 140 * strength)
    noise = 0.02 + 0.08 * strength
    generator = None
    if job.shot.seed is not None:
        generator = torch.Generator(device="cuda").manual_seed(int(job.shot.seed))
    result = pipe(
        image,
        decode_chunk_size=8,
        generator=generator,
        motion_bucket_id=motion_bucket,
        noise_aug_strength=noise,
    )
    frames = result.frames[0]
    dest.parent.mkdir(parents=True, exist_ok=True)
    frames_dir = dest.with_suffix("") 
    frames_dir.mkdir(parents=True, exist_ok=True)
    for i, frame in enumerate(frames):
        frame.save(frames_dir / f"f_{i:04d}.png")
    run_ffmpeg(
        [
            "-y",
            "-framerate",
            str(DEFAULT_FPS),
            "-i",
            str(frames_dir / "f_%04d.png"),
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(dest),
        ]
    )


def _rewrap(src: Path, dest: Path, width: int, height: int, duration: float) -> None:
    """Scale/pad to the shot aspect and stretch or trim to the requested duration."""
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
            "-t",
            f"{max(1.0, duration):.3f}",
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


def _cleanup(work: Path) -> None:
    if not work.exists():
        return
    for child in sorted(work.rglob("*"), reverse=True):
        try:
            if child.is_file():
                child.unlink()
            else:
                child.rmdir()
        except OSError:
            pass
    try:
        work.rmdir()
    except OSError:
        pass
