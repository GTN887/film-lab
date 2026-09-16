"""Dialogue/voice synchronization for persistent Film Lab Characters.

Dialogue timing is real production state. Lip synchronization is never called ENFORCED
unless a renderer explicitly proves a Character-bound audio/lip-control bridge.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DialogueBeat:
    start_s: float
    character_id: str
    text: str
    cue_id: str = ""
    audio_path: str = ""
    end_s: float | None = None
    emotion: str = ""
    intention: str = ""
    reaction_to: str = ""

    def __post_init__(self):
        if float(self.start_s) < 0:
            raise ValueError("Dialogue start time cannot be negative.")
        if self.end_s is not None and float(self.end_s) < float(self.start_s):
            raise ValueError("Dialogue end time cannot precede start time.")
        if not self.character_id.strip():
            raise ValueError("Dialogue requires a stable Character ID.")
        if not self.text.strip():
            raise ValueError("Dialogue text cannot be empty.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DialoguePerformance:
    scene_id: str
    shot_id: str
    beats: tuple[DialogueBeat, ...]
    status: str = "TIMED_AUDIO"

    def __post_init__(self):
        object.__setattr__(self, "beats", tuple(sorted(self.beats, key=lambda x: float(x.start_s))))

    @property
    def character_ids(self) -> tuple[str, ...]:
        return tuple(sorted({x.character_id for x in self.beats}))

    def to_dict(self) -> dict[str, Any]:
        return {"scene_id": self.scene_id, "shot_id": self.shot_id, "beats": [x.to_dict() for x in self.beats], "status": self.status, "character_ids": list(self.character_ids)}

    def prompt(self, names: dict[str, str] | None = None) -> str:
        names = names or {}; rows=[]
        for beat in self.beats:
            actor=names.get(beat.character_id, beat.character_id)
            timing=f"{beat.start_s:.2f}s" + (f"–{beat.end_s:.2f}s" if beat.end_s is not None else "")
            bits=[f'line: "{beat.text}"']
            if beat.emotion: bits.append(f"emotion: {beat.emotion}")
            if beat.intention: bits.append(f"delivery: {beat.intention}")
            if beat.reaction_to: bits.append(f"reaction to: {beat.reaction_to}")
            rows.append(f"{timing} {actor} [{beat.character_id}] — " + "; ".join(bits))
        return " | ".join(rows)


class DialoguePerformanceStore:
    def __init__(self, project): self.path=Path(project.root)/"dialogue_performance.json"
    @staticmethod
    def _key(scene_id:str,shot_id:str)->str: return f"{scene_id}::{shot_id}"
    def _load(self):
        if not self.path.exists(): return {"version":1,"shots":{}}
        try: data=json.loads(self.path.read_text(encoding="utf-8"))
        except Exception: return {"version":1,"shots":{}}
        return data if isinstance(data,dict) else {"version":1,"shots":{}}
    def save(self, performance:DialoguePerformance)->DialoguePerformance:
        data=self._load(); data.setdefault("shots",{})[self._key(performance.scene_id,performance.shot_id)]=performance.to_dict()
        self.path.parent.mkdir(parents=True,exist_ok=True); self.path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"); return performance
    def get(self,scene_id:str,shot_id:str)->DialoguePerformance|None:
        raw=self._load().get("shots",{}).get(self._key(scene_id,shot_id))
        if not isinstance(raw,dict): return None
        beats=tuple(DialogueBeat(**x) for x in raw.get("beats",[]) if isinstance(x,dict))
        return DialoguePerformance(str(raw.get("scene_id",scene_id)),str(raw.get("shot_id",shot_id)),beats,str(raw.get("status","TIMED_AUDIO")))


def build_from_voice_cues(project, scene_id:str, shot_id:str) -> DialoguePerformance | None:
    """Build stable Character-bound timing from real VoiceCue sidecars/files."""
    from film_lab.voice import list_cues
    beats=[]
    for cue in list_cues(project):
        if cue.shot_id != shot_id or (cue.scene_id and cue.scene_id != scene_id): continue
        path=Path(cue.path)
        if not path.is_file(): continue
        end=None
        try:
            from film_lab.wavutil import wav_duration_seconds
            end=float(cue.start_s)+float(wav_duration_seconds(path))
        except Exception: pass
        beats.append(DialogueBeat(float(cue.start_s),cue.character_id,cue.text,cue.id,str(path.resolve()),end,"",cue.intention,""))
    return DialoguePerformance(scene_id,shot_id,tuple(beats)) if beats else None


def dialogue_enforcement(performance:DialoguePerformance, *, audio_timing_wired:bool=True, lip_sync_wired:bool=False, character_audio_wired:bool=False)->dict[str,Any]:
    lip=bool(lip_sync_wired and character_audio_wired)
    if lip:
        status="ENFORCED"; reason="Character-bound audio is wired to a proven lip/face synchronization path."
    elif audio_timing_wired:
        status="PARTIAL"; reason="Dialogue/audio timing is real, but Character-bound lip synchronization is not proven."
    else:
        status="PROMPT_ONLY"; reason="Dialogue is production direction only; no proven timed audio/lip renderer bridge is wired."
    return {"status":status,"reason":reason,"lip_sync_enforced":lip,"characters":list(performance.character_ids),"beats":len(performance.beats)}
