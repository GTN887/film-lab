"""ffmpeg crossfade stitch of selected gallery clips."""

from __future__ import annotations

from pathlib import Path

from film_lab.ffmpeg_support import FFmpegError, probe_duration_seconds, run_ffmpeg

DEFAULT_OVERLAP = 0.6


def stitch_clips(
    clips: list[Path],
    dest: Path,
    *,
    overlap: float = DEFAULT_OVERLAP,
) -> Path:
    """Crossfade ``clips`` in order into one MP4."""
    if len(clips) < 2:
        raise ValueError("Select at least two gallery clips to stitch.")
    for clip in clips:
        if not clip.is_file():
            raise FileNotFoundError(f"Missing clip: {clip}")

    dest.parent.mkdir(parents=True, exist_ok=True)
    if len(clips) == 2:
        return crossfade_pair(clips[0], clips[1], dest, overlap=overlap)

    work = dest.parent / f".{dest.stem}_stitch"
    work.mkdir(parents=True, exist_ok=True)
    current = clips[0]
    try:
        for index, nxt in enumerate(clips[1:], start=1):
            step = work / f"acc_{index}.mp4"
            is_last = index == len(clips) - 1
            out = dest if is_last else step
            crossfade_pair(current, nxt, out, overlap=overlap)
            current = out
        return dest
    finally:
        _cleanup_dir(work)


def crossfade_pair(
    first: Path,
    second: Path,
    dest: Path,
    *,
    overlap: float = DEFAULT_OVERLAP,
) -> Path:
    d1 = probe_duration_seconds(first)
    if d1 is None or d1 <= 0:
        raise FFmpegError(f"Could not read duration for {first.name}")
    fade = min(overlap, max(0.2, d1 * 0.25))
    offset = max(0.0, d1 - fade)
    dest.parent.mkdir(parents=True, exist_ok=True)
    # xfade needs a time offset into the first clip; duration is the dissolve.
    filtergraph = (
        f"[0:v][1:v]xfade=transition=fade:duration={fade:.3f}:offset={offset:.3f}[v]"
    )
    run_ffmpeg(
        [
            "-y",
            "-i",
            str(first),
            "-i",
            str(second),
            "-filter_complex",
            filtergraph,
            "-map",
            "[v]",
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
    return dest


def mux_audio_under(picture: Path, audio: Path, dest: Path, *, volume: float = 0.35) -> Path:
    """Lay one audio file under a silent picture (pad or trim to picture length)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(
        [
            "-y",
            "-i",
            str(picture),
            "-stream_loop",
            "-1",
            "-i",
            str(audio),
            "-filter_complex",
            f"[1:a]volume={volume:.3f},apad[a]",
            "-map",
            "0:v",
            "-map",
            "[a]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            "-movflags",
            "+faststart",
            str(dest),
        ]
    )
    return dest


def _cleanup_dir(work: Path) -> None:
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
