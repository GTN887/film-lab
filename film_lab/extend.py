"""Extended reel: chain short SVD-XT clips, then stitch.

One local SVD-XT pass is seconds (2–4s on 6GB). A 1 min / 2 min reel
(60s / 120s) is N continue-from-last-frame clips plus Cinema Desk crossfades.
Ken Burns is not this path. Zero Film Lab credits. Adults 18+.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from film_lab.animate_ux import rewrite_cloud_safety
from film_lab.constants import CAMERA_MOVES, DEFAULT_DURATION, DEFAULT_LIGHTING
from film_lab.duration import parse_duration_preset
from film_lab.ffmpeg_support import FFmpegError, run_ffmpeg
from film_lab.project import Project
from film_lab.shot_card import ShotCard, new_shot_id
from film_lab.stitch import DEFAULT_OVERLAP, stitch_clips
from film_lab.util import read_json, utc_now, write_json

SEQUENCE_NAME = "extend_sequence.json"
REEL_TARGETS: tuple[int, ...] = (60, 120)
TARGET_LABELS: tuple[str, ...] = ("60s reel", "120s reel")
CLIP_SECONDS = 2.5
OVERLAP = DEFAULT_OVERLAP
BEAT_HEADERS: tuple[str, ...] = ("#", "beat", "s", "camera", "prompt", "clip")

PHASES: tuple[str, ...] = (
    "establish the still — breath, hold, no cut",
    "weight shifts closer; fingers tighten on cloth or skin",
    "mouths meet; keep the locked faces",
    "slow push of bodies; micro-motion only",
    "lighting reads on skin — warmth, a small sweat sheen",
    "a swallow, a hip, the held want",
    "camera eases; same wardrobe, same bands",
    "they do not stop; continuity with the last frame",
    "hands travel; breath on a neck",
    "hold the frame; no fade to black",
    "after the peak, still touching",
    "linger — aftercare, quiet, adults 18+",
)


@dataclass
class Beat:
    index: int
    label: str
    prompt: str
    duration: float
    camera: str
    shot_id: str = ""
    clip_path: str = ""
    still: str = ""

    def row(self) -> list[str]:
        clip = Path(self.clip_path).name if self.clip_path else "—"
        return [
            str(self.index + 1),
            self.label,
            f"{self.duration:.1f}s",
            self.camera,
            self.prompt[:96],
            clip,
        ]


@dataclass
class ExtendSequence:
    target_seconds: int = 60
    clip_seconds: float = CLIP_SECONDS
    overlap: float = OVERLAP
    paragraph: str = ""
    aspect: str = "16:9"
    intimacy: str = "covered sheets"
    lighting: str = DEFAULT_LIGHTING
    beats: list[Beat] = field(default_factory=list)
    stitched_path: str = ""
    updated_at: str = field(default_factory=utc_now)

    def clip_paths(self) -> list[Path]:
        out: list[Path] = []
        for beat in self.beats:
            path = Path(beat.clip_path) if beat.clip_path else None
            if path and path.is_file():
                out.append(path)
        return out

    def next_index(self) -> int | None:
        for beat in self.beats:
            if not beat.clip_path or not Path(beat.clip_path).is_file():
                return beat.index
        return None

    def done_count(self) -> int:
        return len(self.clip_paths())

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["updated_at"] = utc_now()
        return payload

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ExtendSequence:
        beats = []
        for item in raw.get("beats") or []:
            if isinstance(item, dict):
                known = {k: item[k] for k in Beat.__dataclass_fields__ if k in item}
                beats.append(Beat(**known))
        return cls(
            target_seconds=int(raw.get("target_seconds") or 60),
            clip_seconds=float(raw.get("clip_seconds") or CLIP_SECONDS),
            overlap=float(raw.get("overlap") or OVERLAP),
            paragraph=str(raw.get("paragraph") or ""),
            aspect=str(raw.get("aspect") or "16:9"),
            intimacy=str(raw.get("intimacy") or "covered sheets"),
            lighting=str(raw.get("lighting") or DEFAULT_LIGHTING),
            beats=beats,
            stitched_path=str(raw.get("stitched_path") or ""),
            updated_at=str(raw.get("updated_at") or ""),
        )


class ExtendError(RuntimeError):
    """Could not plan, continue, or stitch the extended reel."""


def parse_target(label: str | int | None) -> int:
    pick = parse_duration_preset(label)
    return pick.seconds


def clips_needed(
    target_seconds: float,
    *,
    clip_seconds: float = CLIP_SECONDS,
    overlap: float = OVERLAP,
) -> int:
    """How many short SVD passes to reach the reel after crossfades."""
    clip = max(2.0, float(clip_seconds))
    fade = min(float(overlap), clip * 0.4)
    span = clip - fade
    if span <= 0:
        raise ExtendError("Clip length must be longer than the crossfade.")
    n = math.ceil((float(target_seconds) - fade) / span)
    return max(2, int(n))


def stitched_length(
    n: int,
    *,
    clip_seconds: float = CLIP_SECONDS,
    overlap: float = OVERLAP,
) -> float:
    if n <= 0:
        return 0.0
    if n == 1:
        return float(clip_seconds)
    fade = min(float(overlap), float(clip_seconds) * 0.4)
    return n * float(clip_seconds) - (n - 1) * fade


def sequence_status_md(seq: ExtendSequence | None, target: int = 60) -> str:
    if seq is None:
        return plan_note(target)
    extra = f" Progress **{seq.done_count()}/{len(seq.beats)}** clips."
    if seq.stitched_path:
        extra += f" Stitched `{Path(seq.stitched_path).name}`."
    return plan_note(seq.target_seconds, seq.clip_seconds, seq.overlap) + extra


def plan_note(target: int, clip_seconds: float = CLIP_SECONDS, overlap: float = OVERLAP) -> str:
    n = clips_needed(target, clip_seconds=clip_seconds, overlap=overlap)
    total = stitched_length(n, clip_seconds=clip_seconds, overlap=overlap)
    return (
        f"One SVD-XT pass is **seconds** ({clip_seconds:.1f}s on 6GB — not a one-shot minute). "
        f"A **{target:.0f}s** reel is **{n} chained clips** + Cinema Desk crossfades "
        f"({overlap:.1f}s each). Estimated stitch **~{total:.0f}s**. "
        "Continue from the last frame so faces stay locked. "
        "Adults 18+. Zero credits. Ken Burns is Advanced only."
    )


def plan_beats(
    paragraph: str,
    *,
    target_seconds: int = 60,
    clip_seconds: float = CLIP_SECONDS,
    overlap: float = OVERLAP,
    camera: str = "slow push-in",
) -> list[Beat]:
    text = rewrite_cloud_safety((paragraph or "").strip())
    if not text:
        raise ExtendError("Enhance a short command first, then build the shot list.")
    n = clips_needed(target_seconds, clip_seconds=clip_seconds, overlap=overlap)
    sentences = [s.strip() for s in _split_sentences(text) if s.strip()]
    beats: list[Beat] = []
    cam_cycle = list(CAMERA_MOVES)
    start = cam_cycle.index(camera) if camera in cam_cycle else 1
    for i in range(n):
        phase = PHASES[i % len(PHASES)]
        spine = sentences[i % len(sentences)] if sentences else text
        prompt = (
            f"{text} Beat {i + 1}/{n}: {phase}. {spine} "
            "Continue from the previous frame. Same faces, same bands, same wardrobe. "
            "Adults 18+. No fade to black."
        )
        beats.append(
            Beat(
                index=i,
                label=f"{target_seconds}s · {i + 1:02d}/{n:02d} · {phase.split('—')[0].strip()[:28]}",
                prompt=rewrite_cloud_safety(prompt),
                duration=float(clip_seconds),
                camera=cam_cycle[(start + i) % len(cam_cycle)],
            )
        )
    return beats


def _split_sentences(text: str) -> list[str]:
    chunk = text.replace("!", ".").replace("?", ".")
    return [p.strip() for p in chunk.split(".") if p.strip()]


def sequence_path(project: Project) -> Path:
    return project.root / SEQUENCE_NAME


def save_sequence(project: Project, seq: ExtendSequence) -> Path:
    dest = sequence_path(project)
    write_json(dest, seq.to_dict())
    return dest


def load_sequence(project: Project) -> ExtendSequence | None:
    path = sequence_path(project)
    if not path.is_file():
        return None
    raw = read_json(path)
    if not isinstance(raw, dict):
        return None
    return ExtendSequence.from_dict(raw)


def build_sequence(
    project: Project,
    paragraph: str,
    *,
    target_seconds: int = 60,
    clip_seconds: float = CLIP_SECONDS,
    aspect: str = "16:9",
    intimacy: str = "covered sheets",
    lighting: str = DEFAULT_LIGHTING,
    camera: str = "slow push-in",
    character_ids: list[str] | None = None,
    start_still: str | None = None,
) -> ExtendSequence:
    beats = plan_beats(
        paragraph,
        target_seconds=target_seconds,
        clip_seconds=clip_seconds,
        camera=camera,
    )
    ids = [str(x).split(" — ", 1)[0].strip() for x in (character_ids or []) if str(x).strip()]
    if not ids:
        ids = list(project.active_cast or ["alison", "bradley"])
    for beat in beats:
        shot = ShotCard(
            id=new_shot_id(),
            name=beat.label,
            start_frame=start_still if beat.index == 0 else None,
            duration=beat.duration,
            aspect_ratio=aspect or "16:9",
            camera_move=beat.camera if beat.camera in CAMERA_MOVES else "slow push-in",
            subject_motion_strength=0.62,
            body_motion_notes=beat.prompt[:180],
            director_intent=beat.prompt,
            intimacy_mode=intimacy or "covered sheets",
            lighting=lighting or DEFAULT_LIGHTING,
            character_ids=ids,
            face_lock_strength=project.face_lock_strength,
            resolution=getattr(project, "quality", None) or "720p",
        )
        project.save_shot(shot)
        beat.shot_id = shot.id
        if start_still and beat.index == 0:
            beat.still = start_still
    seq = ExtendSequence(
        target_seconds=int(target_seconds),
        clip_seconds=float(clip_seconds),
        overlap=OVERLAP,
        paragraph=rewrite_cloud_safety(paragraph),
        aspect=aspect or "16:9",
        intimacy=intimacy or "covered sheets",
        lighting=lighting or DEFAULT_LIGHTING,
        beats=beats,
    )
    save_sequence(project, seq)
    return seq


def beat_table(seq: ExtendSequence | None) -> list[list[str]]:
    if not seq:
        return []
    return [b.row() for b in seq.beats]


def extract_last_frame(clip: Path, dest: Path) -> Path:
    """Last video frame → still, used as the next SVD start."""
    if not clip.is_file():
        raise ExtendError(f"Missing clip: {clip}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        run_ffmpeg(
            [
                "-y",
                "-sseof",
                "-0.08",
                "-i",
                str(clip),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(dest),
            ]
        )
    except FFmpegError as exc:
        raise ExtendError(str(exc)) from exc
    if not dest.is_file() or dest.stat().st_size < 32:
        raise ExtendError(f"Could not pull the last frame from {clip.name}.")
    return dest


def last_frame_still(project: Project, clip: Path) -> Path:
    dest = project.stills_dir / f"continue_{clip.stem}.jpg"
    project.ensure_dirs()
    extract_last_frame(clip, dest)
    written = project.ingest_files([dest])
    return written[0] if written else dest


def prepare_next_shot(
    project: Project,
    seq: ExtendSequence,
    *,
    uploaded: list[Path] | None = None,
) -> tuple[ShotCard, Beat, Path | None]:
    """Next unfinished beat, start still = last frame of the previous clip."""
    idx = seq.next_index()
    if idx is None:
        raise ExtendError("Shot list is already complete. Auto-stitch on Cinema Desk.")
    beat = seq.beats[idx]
    shot = project.load_shot(beat.shot_id)
    start: Path | None = None
    if idx == 0:
        for src in uploaded or []:
            if src.is_file():
                start = src
                break
        if start is None:
            start = project.resolve_still(shot.start_frame or beat.still)
        if start is None:
            raise ExtendError("Add Prompt / drop a still for clip 1, then continue.")
        shot.start_frame = start.name if start.parent == project.stills_dir else None
        uploaded_out = start
    else:
        prev = seq.beats[idx - 1]
        prev_clip = Path(prev.clip_path) if prev.clip_path else None
        if prev_clip is None or not prev_clip.is_file():
            raise ExtendError(f"Clip {idx} needs the previous take. Generate beat {idx} first.")
        still = last_frame_still(project, prev_clip)
        shot.start_frame = still.name
        beat.still = still.name
        uploaded_out = still
    project.save_shot(shot)
    save_sequence(project, seq)
    return shot, beat, uploaded_out


def mark_clip(project: Project, seq: ExtendSequence, beat: Beat, clip: Path) -> ExtendSequence:
    beat.clip_path = str(clip.resolve())
    save_sequence(project, seq)
    return seq


def stitch_sequence(project: Project, seq: ExtendSequence | None = None) -> Path:
    current = seq or load_sequence(project)
    if current is None:
        raise ExtendError("No shot list yet. Build one on Motion Desk.")
    clips = current.clip_paths()
    if len(clips) < 2:
        raise ExtendError("Need at least two generated clips to stitch the reel.")
    dest = project.outputs_dir / f"reel_{current.target_seconds}s_{utc_now().replace(':', '')}.mp4"
    stitch_clips(clips, dest, overlap=current.overlap)
    current.stitched_path = str(dest.resolve())
    save_sequence(project, current)
    project.register_output(dest, generator="extend-stitch")
    return dest


def last_gallery_clip(project: Project) -> Path | None:
    for item in project.load_gallery():
        path = Path(item.path)
        if path.is_file() and path.suffix.lower() in {".mp4", ".webm", ".mov"}:
            if item.generator in {"stitch", "extend-stitch", "reel"}:
                continue
            return path
    return None


def duration_for_form(value: float | None) -> float:
    try:
        seconds = float(value if value is not None else DEFAULT_DURATION)
    except (TypeError, ValueError):
        seconds = CLIP_SECONDS
    return max(2.0, min(4.0, seconds))
