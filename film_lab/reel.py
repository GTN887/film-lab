"""Director board: ordered scenes → shots → clips → audio, then assemble."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from film_lab.ffmpeg_support import probe_duration_seconds, run_ffmpeg
from film_lab.project import Project
from film_lab.script import REEL_STATUSES, list_scenes
from film_lab.stitch import stitch_clips
from film_lab.util import new_id, read_json, utc_now, write_json

REEL_NAME = "reel.json"


@dataclass
class ReelEntry:
    id: str
    order: int
    scene_id: str | None = None
    shot_id: str | None = None
    clip_path: str | None = None
    dialogue_wav: str | None = None
    music_path: str | None = None
    status: str = "idea"
    notes: str = ""
    updated_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if self.status not in REEL_STATUSES:
            self.status = "idea"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def row(self) -> list[str]:
        clip = Path(self.clip_path).name if self.clip_path else ""
        return [
            str(self.order),
            self.status,
            self.scene_id or "",
            self.shot_id or "",
            clip,
            Path(self.dialogue_wav).name if self.dialogue_wav else "",
            Path(self.music_path).name if self.music_path else "",
            self.notes,
            self.id,
        ]


def reel_path(project: Project) -> Path:
    return project.root / REEL_NAME


def load_reel(project: Project) -> list[ReelEntry]:
    path = reel_path(project)
    if not path.exists():
        return []
    raw = read_json(path)
    entries: list[ReelEntry] = []
    if not isinstance(raw, list):
        return entries
    for item in raw:
        if isinstance(item, dict) and "id" in item:
            entries.append(
                ReelEntry(**{k: item[k] for k in ReelEntry.__dataclass_fields__ if k in item})
            )
    entries.sort(key=lambda e: e.order)
    return entries


def save_reel(project: Project, entries: list[ReelEntry]) -> None:
    for index, entry in enumerate(entries):
        entry.order = index
        entry.updated_at = utc_now()
    write_json(reel_path(project), [e.to_dict() for e in entries])


def add_entry(project: Project, entry: ReelEntry) -> list[ReelEntry]:
    entries = load_reel(project)
    entry.order = len(entries)
    entries.append(entry)
    save_reel(project, entries)
    return entries


def rebuild_from_scenes(project: Project) -> list[ReelEntry]:
    """One reel row per linked shot, in scene file order then shot-id order."""
    existing = {((e.scene_id or ""), (e.shot_id or "")): e for e in load_reel(project)}
    rebuilt: list[ReelEntry] = []
    order = 0
    for scene in list_scenes(project):
        for shot_id in scene.shot_ids:
            key = (scene.id, shot_id)
            if key in existing:
                entry = existing[key]
                entry.order = order
                rebuilt.append(entry)
            else:
                clip = _latest_clip_for_shot(project, shot_id)
                dialogue = None
                try:
                    shot = project.load_shot(shot_id)
                    dialogue = shot.dialogue_wav
                except FileNotFoundError:
                    pass
                rebuilt.append(
                    ReelEntry(
                        id=new_id(),
                        order=order,
                        scene_id=scene.id,
                        shot_id=shot_id,
                        clip_path=str(clip) if clip else None,
                        dialogue_wav=dialogue,
                        status="generated" if clip else scene.status,
                    )
                )
            order += 1
    save_reel(project, rebuilt)
    return rebuilt


def _latest_clip_for_shot(project: Project, shot_id: str) -> Path | None:
    matches = [c for c in project.load_gallery() if c.shot_id == shot_id and Path(c.path).is_file()]
    if not matches:
        return None
    return Path(matches[0].path)


def attach_clip(project: Project, entry_id: str, clip: Path) -> list[ReelEntry]:
    entries = load_reel(project)
    for entry in entries:
        if entry.id == entry_id:
            entry.clip_path = str(clip.resolve())
            if entry.status in {"idea", "blocked"}:
                entry.status = "generated"
    save_reel(project, entries)
    return entries


def set_status(project: Project, entry_id: str, status: str) -> list[ReelEntry]:
    if status not in REEL_STATUSES:
        raise ValueError(f"Status must be one of {REEL_STATUSES}")
    entries = load_reel(project)
    for entry in entries:
        if entry.id == entry_id:
            entry.status = status
    save_reel(project, entries)
    return entries


def reel_rows(entries: list[ReelEntry]) -> list[list[str]]:
    return [e.row() for e in entries]


def assemble_reel(
    project: Project,
    *,
    music_path: Path | None = None,
    include_dialogue: bool = True,
) -> Path:
    """Stitch picture in reel order, then optionally mux a music bed + dialogue."""
    entries = [e for e in load_reel(project) if e.status != "blocked"]
    clips: list[Path] = []
    dialogue: list[tuple[Path, float]] = []
    cursor = 0.0
    for entry in entries:
        path = Path(entry.clip_path) if entry.clip_path else None
        if path is None and entry.shot_id:
            latest = _latest_clip_for_shot(project, entry.shot_id)
            path = latest
            if latest:
                entry.clip_path = str(latest)
        if path is None or not path.is_file():
            continue
        clips.append(path)
        dur = probe_duration_seconds(path) or 0.0
        if include_dialogue:
            from film_lab.voice import cues_for_entry

            for cue in cues_for_entry(project, entry):
                wav = Path(cue.path)
                if wav.is_file():
                    dialogue.append((wav, cursor + float(cue.start_s or 0)))
        cursor += dur
    if not clips:
        raise ValueError("Reel has no generated clips to assemble.")
    save_reel(project, load_reel(project))
    dest = project.outputs_dir / f"reel_{new_id()}.mp4"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if len(clips) == 1:
        picture = dest.with_name(dest.stem + "_pic.mp4")
        run_ffmpeg(["-y", "-i", str(clips[0]), "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(picture)])
    else:
        picture = dest.with_name(dest.stem + "_pic.mp4")
        stitch_clips(clips, picture)

    audio_inputs: list[Path] = []
    if music_path and music_path.is_file():
        audio_inputs.append(music_path)
    elif entries:
        for entry in entries:
            if entry.music_path and Path(entry.music_path).is_file():
                audio_inputs.append(Path(entry.music_path))
                break

    if not audio_inputs and not dialogue:
        picture.replace(dest)
        project.register_output(dest, generator="reel")
        return dest

    mux_audio_mix(picture, dest, music=audio_inputs[0] if audio_inputs else None, dialogue=dialogue)
    try:
        picture.unlink()
    except OSError:
        pass
    project.register_output(dest, generator="reel")
    return dest


def mux_audio_mix(
    picture: Path,
    dest: Path,
    *,
    music: Path | None,
    dialogue: list[tuple[Path, float]],
) -> Path:
    """Underlay music (loop/pad) and delay dialogue cues onto the picture."""
    args: list[str] = ["-y", "-i", str(picture)]
    filter_parts: list[str] = []
    mix_labels: list[str] = []
    index = 1
    if music is not None:
        args.extend(["-stream_loop", "-1", "-i", str(music)])
        filter_parts.append(f"[{index}:a]volume=0.22,apad[a{index}]")
        mix_labels.append(f"[a{index}]")
        index += 1
    for wav, start in dialogue:
        args.extend(["-i", str(wav)])
        delay_ms = max(0, int(start * 1000))
        filter_parts.append(f"[{index}:a]adelay={delay_ms}|{delay_ms},volume=0.85[a{index}]")
        mix_labels.append(f"[a{index}]")
        index += 1
    if not mix_labels:
        raise ValueError("No audio to mux.")
    n = len(mix_labels)
    filter_parts.append(f"{''.join(mix_labels)}amix=inputs={n}:dropout_transition=0:normalize=0[aout]")
    args.extend(
        [
            "-filter_complex",
            ";".join(filter_parts),
            "-map",
            "0:v",
            "-map",
            "[aout]",
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
    run_ffmpeg(args)
    return dest
