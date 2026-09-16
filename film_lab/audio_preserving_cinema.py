"""Audio-preserving Cinema assembly for Selected Takes.

This module closes a production gap in the legacy visual-only stitcher. When every
input clip has a proven audio stream, it crossfades picture and sound together.
If audio cannot be proven for every clip, callers can deliberately fall back to
the established visual-only stitcher rather than claiming an audio-preserving
export.

J/L-cut semantics are never inferred. Explicit persisted Director timing can
move incoming audio before incoming picture and/or retain outgoing audio under
incoming picture, within the source handles and a bounded two-second window.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from film_lab.ffmpeg_support import FFmpegError, probe_duration_seconds, probe_has_audio, run_ffmpeg


@dataclass(frozen=True)
class CinemaAudioPlan:
    status: str
    audio_preserved: bool
    video_overlap_s: float
    audio_overlap_s: float
    edit_style: str
    truth: str
    j_cut_lead_s: float = 0.0
    l_cut_tail_s: float = 0.0
    picture_in_s: float = 0.0
    picture_out_s: float = 0.0
    incoming_source_duration_s: float = 0.0
    outgoing_source_duration_s: float = 0.0
    j_handle_available_s: float = 0.0
    l_handle_available_s: float = 0.0
    enforced: bool = False
    provenance: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def plan_audio_transition(first_take, second_take, *, video_overlap: float = 0.6) -> CinemaAudioPlan:
    """Build an auditable transition plan from proven streams + Director intent."""
    a = first_take.metadata.get("audio_cut_intent", {}) if isinstance(first_take.metadata, dict) else {}
    b = second_take.metadata.get("audio_cut_intent", {}) if isinstance(second_take.metadata, dict) else {}
    a = a if isinstance(a, dict) else {}
    b = b if isinstance(b, dict) else {}
    style = "HARD_CUT"
    if a.get("l_cut") or b.get("l_cut"):
        style = "L_CUT"
    if a.get("j_cut") or b.get("j_cut"):
        style = "J_CUT" if style == "HARD_CUT" else "J_L_CUT"
    has_a = probe_has_audio(Path(first_take.media_path)) is True
    has_b = probe_has_audio(Path(second_take.media_path)) is True
    if not (has_a and has_b):
        return CinemaAudioPlan(
            "NOT_TESTED", False, float(video_overlap), 0.0, style,
            "Audio-preserving Cinema assembly is not claimed unless both boundary Takes have proven audio streams.",
        )
    # Boundary intent belongs primarily to the incoming Take; accepting the
    # outgoing record preserves compatibility with the earlier continuity gate.
    requested = b.get("audio_overlap_s", a.get("audio_overlap_s", video_overlap))
    try:
        audio_overlap = float(requested)
    except (TypeError, ValueError):
        audio_overlap = float(video_overlap)
    audio_overlap = max(0.05, min(2.0, audio_overlap))
    def bounded(value: Any, enabled: bool) -> float:
        if not enabled:
            return 0.0
        try: seconds = float(value)
        except (TypeError, ValueError): seconds = audio_overlap
        return max(0.05, min(2.0, seconds))
    j_enabled = style in {"J_CUT", "J_L_CUT"}
    l_enabled = style in {"L_CUT", "J_L_CUT"}
    j_lead = bounded(b.get("j_cut_lead_s", a.get("j_cut_lead_s", audio_overlap)), j_enabled)
    l_tail = bounded(b.get("l_cut_tail_s", a.get("l_cut_tail_s", audio_overlap)), l_enabled)
    d1 = probe_duration_seconds(Path(first_take.media_path)) or 0.0
    d2 = probe_duration_seconds(Path(second_take.media_path)) or 0.0
    try: picture_in = float(b.get("picture_in_s", 0.0) or 0.0)
    except (TypeError, ValueError): picture_in = -1.0
    picture_out_raw = b.get("picture_out_s", a.get("picture_out_s", d1))
    try: picture_out = float(picture_out_raw if picture_out_raw is not None else d1)
    except (TypeError, ValueError): picture_out = -1.0
    j_available = max(0.0, picture_in)
    l_available = max(0.0, d1 - picture_out)
    valid_picture = d1 > 0 and d2 > 0 and 0 <= picture_in < d2 and 0 < picture_out <= d1
    handles_valid = (not j_enabled or j_lead <= j_available + 1e-6) and (not l_enabled or l_tail <= l_available + 1e-6)
    enforced = style == "HARD_CUT" or (valid_picture and handles_valid)
    status = "PASS" if enforced else "FAIL"
    truth = (
        "REAL source-handle split-edit plan: picture timing is separate from audio timing, requested handles are bounded and proven from the same source Takes; no dialogue semantics are inferred."
        if enforced else
        "Split edit cannot be enforced because requested picture timing or same-source audio handles are missing or too short; Film Lab will not fabricate handles."
    )
    return CinemaAudioPlan(
        status, True, float(video_overlap), audio_overlap, style, truth,
        j_lead, l_tail, picture_in, picture_out, d2, d1, j_available, l_available,
        enforced, f"{getattr(first_take, 'id', '')}->{getattr(second_take, 'id', '')}",
    )


def crossfade_pair_av(first: Path, second: Path, dest: Path, *, video_overlap: float = 0.6, audio_overlap: float | None = None, transition: CinemaAudioPlan | None = None) -> Path:
    """Crossfade picture and proven audio streams into one MP4."""
    first, second, dest = Path(first), Path(second), Path(dest)
    for clip in (first, second):
        if not clip.is_file():
            raise FileNotFoundError(f"Missing clip: {clip}")
        if probe_has_audio(clip) is not True:
            raise FFmpegError(f"Audio-preserving stitch requires a proven audio stream: {clip.name}")
    d1 = probe_duration_seconds(first)
    d2 = probe_duration_seconds(second)
    if d1 is None or d2 is None or d1 <= 0 or d2 <= 0:
        raise FFmpegError("Could not prove clip duration for audio-preserving Cinema assembly.")
    vf = min(float(video_overlap), max(0.05, d1 * 0.25), max(0.05, d2 * 0.25))
    af_req = vf if audio_overlap is None else float(audio_overlap)
    af = min(max(0.05, af_req), max(0.05, d1 * 0.25), max(0.05, d2 * 0.25))
    offset = max(0.0, d1 - vf)
    dest.parent.mkdir(parents=True, exist_ok=True)
    video_duration = d1 + d2 - vf
    if transition and transition.edit_style != "HARD_CUT":
        if not transition.enforced:
            raise FFmpegError("Split edit is not enforceable; requested same-source audio handles are unavailable.")
        picture_in = transition.picture_in_s
        picture_out = transition.picture_out_s
        j = transition.j_cut_lead_s
        l = transition.l_cut_tail_s
        picture_duration = picture_out + (d2 - picture_in)
        incoming_at = max(0.0, picture_out - j)
        outgoing_until = min(d1, picture_out + l)
        delay_ms = int(round(incoming_at * 1000.0))
        fade = min(0.08, max(0.02, af * 0.25))
        graph = (
            f"[0:v]trim=start=0:end={picture_out:.3f},setpts=PTS-STARTPTS[v0];"
            f"[1:v]trim=start={picture_in:.3f}:end={d2:.3f},setpts=PTS-STARTPTS[v1];"
            f"[v0][v1]concat=n=2:v=1:a=0[v];"
            f"[0:a]atrim=0:{outgoing_until:.3f},asetpts=PTS-STARTPTS,"
            f"afade=t=out:st={max(0.0, outgoing_until-fade):.3f}:d={fade:.3f}[a0];"
            f"[1:a]atrim=start={max(0.0, picture_in-j):.3f}:end={d2:.3f},asetpts=PTS-STARTPTS,"
            f"afade=t=in:st=0:d={fade:.3f},adelay={delay_ms}|{delay_ms}[a1];"
            f"[a0][a1]amix=inputs=2:duration=longest:normalize=0,atrim=0:{picture_duration:.3f}[a]"
        )
    else:
        graph = (
            f"[0:v][1:v]xfade=transition=fade:duration={vf:.3f}:offset={offset:.3f}[v];"
            f"[0:a][1:a]acrossfade=d={af:.3f}:c1=tri:c2=tri[a]"
        )
    run_ffmpeg([
        "-y", "-i", str(first), "-i", str(second),
        "-filter_complex", graph,
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
        "-movflags", "+faststart", str(dest),
    ])
    return dest


def stitch_clips_av(clips: list[Path], dest: Path, *, video_overlap: float = 0.6, audio_overlap: float | None = None, transitions: list[CinemaAudioPlan] | None = None) -> Path:
    """Sequentially assemble clips while preserving/crossfading their audio."""
    if len(clips) < 2:
        raise ValueError("Select at least two clips for audio-preserving Cinema assembly.")
    clips = [Path(x) for x in clips]
    dest = Path(dest)
    work = dest.parent / f".{dest.stem}_av_stitch"
    work.mkdir(parents=True, exist_ok=True)
    current = clips[0]
    try:
        for index, nxt in enumerate(clips[1:], start=1):
            out = dest if index == len(clips) - 1 else work / f"acc_{index}.mp4"
            transition = transitions[index - 1] if transitions and index - 1 < len(transitions) else None
            crossfade_pair_av(current, nxt, out, video_overlap=video_overlap, audio_overlap=audio_overlap, transition=transition)
            current = out
        return dest
    finally:
        for child in work.glob("*"):
            try: child.unlink()
            except OSError: pass
        try: work.rmdir()
        except OSError: pass
