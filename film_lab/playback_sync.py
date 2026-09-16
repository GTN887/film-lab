"""Director Timeline playback/scrub state.

This module is deliberately UI-independent. It resolves the real selected Take for a
Scene/Shot, persists the Creator's playhead, and exposes timeline cursor metadata.
It never claims browser/native playback synchronization until the UI reports it.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Any

from film_lab.production import ProductionStore, Take

@dataclass(frozen=True)
class PlaybackState:
    scene_id: str
    shot_id: str
    take_id: str = ""
    media_path: str = ""
    duration_s: float = 0.0
    playhead_s: float = 0.0
    status: str = "NO_SELECTED_TAKE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

class PlaybackSyncStore:
    def __init__(self, project):
        self.project=project; project.ensure_dirs(); self.path=project.root/"director_playback.json"
    def _load(self):
        try: return json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}
        except (OSError,json.JSONDecodeError): return {}
    def _save(self,data):
        tmp=self.path.with_suffix(".json.tmp"); tmp.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8"); tmp.replace(self.path)
    @staticmethod
    def key(scene_id,shot_id): return f"{scene_id}::{shot_id}"
    def saved_playhead(self,scene_id,shot_id):
        raw=self._load().get(self.key(scene_id,shot_id),{})
        try: return max(0.0,float(raw.get("playhead_s",0)))
        except (TypeError,ValueError): return 0.0
    def save_playhead(self,scene_id,shot_id,seconds):
        state=resolve_playback(self.project,scene_id,shot_id,requested_s=seconds)
        data=self._load(); data[self.key(scene_id,shot_id)]={"playhead_s":state.playhead_s,"take_id":state.take_id}; self._save(data); return state

def selected_take(project,scene_id:str,shot_id:str)->Take|None:
    candidates=[t for t in ProductionStore(project).selected_takes(existing_media_only=True) if t.scene_id==scene_id and t.shot_id==shot_id]
    return candidates[0] if candidates else None

def _duration(take:Take|None)->float:
    if not take: return 0.0
    try:
        d=float(take.duration or 0)
        return d if d>0 else 0.0
    except (TypeError,ValueError): return 0.0

def resolve_playback(project,scene_id:str,shot_id:str,requested_s:float|None=None)->PlaybackState:
    scene=(scene_id or "scene-1").strip(); shot=(shot_id or "shot-1").strip(); take=selected_take(project,scene,shot)
    if not take: return PlaybackState(scene,shot)
    dur=_duration(take); saved=PlaybackSyncStore(project).saved_playhead(scene,shot) if requested_s is None else max(0.0,float(requested_s or 0))
    head=min(saved,dur) if dur>0 else saved
    return PlaybackState(scene,shot,take.id,take.media_path,dur,head,"READY")

def cursor_percent(state:PlaybackState)->float:
    if state.duration_s<=0: return 0.0
    return max(0.0,min(100.0,state.playhead_s/state.duration_s*100.0))

def playback_status(state:PlaybackState)->str:
    if state.status!="READY": return "No selected Take with real media for this Scene/Shot. Select a Take on Take Board first."
    dur=f" / {state.duration_s:.2f}s" if state.duration_s>0 else ""
    return f"Selected Take `{state.take_id}` · playhead {state.playhead_s:.2f}s{dur} · persistent scrub state ready."
