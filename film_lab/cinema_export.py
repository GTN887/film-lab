"""Cinema export built from the durable Selected Takes, never from UI state."""
from __future__ import annotations
import shutil
import json
import tempfile
from pathlib import Path
from film_lab.production import ProductionStore
from film_lab.stitch import stitch_clips
from film_lab.ffmpeg_support import probe_has_audio
from film_lab.audio_preserving_cinema import plan_audio_transition, stitch_clips_av
from film_lab.room_tone import RoomToneStore, mix_room_tone


def _assemble(selected, out: Path, overlap: float) -> Path:
    clips = [Path(t.media_path) for t in selected]
    if len(clips) == 1:
        shutil.copy2(clips[0], out); return out
    if all(probe_has_audio(c) is True for c in clips):
        transitions = [plan_audio_transition(a, b, video_overlap=overlap) for a, b in zip(selected, selected[1:])]
        blocked = [p for p in transitions if p.edit_style != "HARD_CUT" and not p.enforced]
        if blocked:
            from film_lab.ffmpeg_support import FFmpegError
            raise FFmpegError(blocked[0].truth)
        return stitch_clips_av(clips, out, video_overlap=overlap, audio_overlap=overlap, transitions=transitions)
    return stitch_clips(clips, out, overlap=overlap)


def export_selected(project, dest: Path | str, *, overlap: float = 0.6) -> Path:
    store = ProductionStore(project)
    selected = store.selected_takes(existing_media_only=True)
    if not selected:
        raise ValueError("Cinema has no Selected Takes to export.")
    selected = sorted(selected, key=lambda t: (str(getattr(t,"scene_id","")), str(getattr(t,"shot_id","")), str(getattr(t,"created_at","")), str(getattr(t,"id",""))))
    clips = [Path(t.media_path) for t in selected]
    out = Path(dest)
    if out.suffix.lower() != ".mp4":
        out = out.with_suffix(".mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    if not hasattr(project, "root"):
        return _assemble(selected, out, overlap)
    tones = RoomToneStore(project)
    active = {scene: tones.get(scene) for scene in {t.scene_id for t in selected}}
    active = {k: v for k, v in active.items() if v and v.enabled}
    if not active:
        return _assemble(selected, out, overlap)
    # Assemble and mix each Scene independently so one bed remains continuous
    # across its Shot cuts, then join the Scene masters into the final film.
    with tempfile.TemporaryDirectory(prefix="film_lab_room_tone_", dir=str(out.parent)) as temp:
        work = Path(temp); scene_outputs=[]; audit=[]
        scene_ids=[]
        for take in selected:
            if take.scene_id not in scene_ids: scene_ids.append(take.scene_id)
        for index, scene_id in enumerate(scene_ids):
            group=[t for t in selected if t.scene_id == scene_id]
            base=work/f"scene_{index:04d}_base.mp4"; _assemble(group, base, overlap)
            state=tones.get(scene_id); final=base
            if state and state.enabled:
                final=work/f"scene_{index:04d}_room_tone.mp4"; mix_room_tone(base, state, final)
            scene_outputs.append(final)
            audit.append({"scene_id":scene_id,"selected_take_ids":[t.id for t in group],"room_tone":state.to_dict() if state else None,"room_tone_enforced":bool(state and state.enabled)})
        staged=work/"film_master.mp4"
        if len(scene_outputs)==1: shutil.copy2(scene_outputs[0], staged)
        elif all(probe_has_audio(x) is True for x in scene_outputs): stitch_clips_av(scene_outputs, staged, video_overlap=overlap, audio_overlap=overlap)
        else: stitch_clips(scene_outputs, staged, overlap=overlap)
        shutil.copy2(staged, out)
        manifest=out.with_suffix(".audio_edit.json")
        manifest.write_text(json.dumps({"version":1,"output":str(out.resolve()),"scenes":audit,"truth":"Room-tone files are explicit Director assignments; Film Lab does not infer room identity or artistic correctness."},indent=2)+"\n",encoding="utf-8")
        return out
