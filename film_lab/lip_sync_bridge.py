"""Character-bound dialogue audio / lip-sync bridge for ComfyUI workflows.

Film Lab only calls lip synchronization ENFORCED when an explicit per-character
Film Lab audio slot is present and the graph contains a lip/face-sync consumer.
Timed dialogue or a lip-sync-looking node alone is not proof of wiring.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any

LIP_SYNC_TERMS=("wav2lip","musetalk","lipsync","lip_sync","synctalk","audio2video","audio driven","audiodriven")
FACE_TERMS=("liveportrait","face","facial","expression")


def _title(node:dict[str,Any])->str:
    return str((node.get("_meta") or {}).get("title") or "").strip()

def _slot(title:str)->tuple[str,str]:
    if ":" in title:
        a,b=title.split(":",1); return a.strip().lower(),b.strip().lower()
    return title.strip().lower(),""

def _dialogue(conditioning):
    return (getattr(conditioning,"metadata",{}) or {}).get("dialogue_performance") or {}

def _beats_for(conditioning,target:str)->list[dict[str,Any]]:
    beats=list(_dialogue(conditioning).get("beats") or [])
    if not target:
        ids={str(x.get("character_id") or "").lower() for x in beats}
        return beats if len(ids)==1 else []
    return [x for x in beats if str(x.get("character_id") or "").lower()==target]

def inspect_lip_sync_controls(graph:dict[str,Any])->dict[str,bool]:
    names=[str(n.get("class_type","")).lower() for n in graph.values() if isinstance(n,dict)]
    return {
        "lip_sync": any(any(t in n for t in LIP_SYNC_TERMS) for n in names),
        "facial_performance": any(any(t in n for t in FACE_TERMS) for n in names),
    }

def _set_audio(inputs:dict[str,Any], path:str)->bool:
    for key in ("audio","audio_path","wav","wav_path","sound","file","filename"):
        if key in inputs and not isinstance(inputs[key],(list,dict)):
            inputs[key]=path; return True
    return False

def _set_text(inputs:dict[str,Any], value:str)->bool:
    for key in ("text","value","dialogue","instruction","prompt"):
        if key in inputs and not isinstance(inputs[key],(list,dict)):
            inputs[key]=value; return True
    return False

def inject_lip_sync(graph:dict[str,Any],conditioning)->dict[str,Any]:
    controls=inspect_lip_sync_controls(graph); slots=[]; audio_bound=set(); face_bound=set()
    for node_id,node in graph.items():
        if not isinstance(node,dict): continue
        base,target=_slot(_title(node)); inputs=node.setdefault("inputs",{})
        if base=="film_lab_dialogue_audio":
            beats=_beats_for(conditioning,target); paths=[]
            for beat in beats:
                p=Path(str(beat.get("audio_path") or "")).expanduser()
                if p.is_file(): paths.append(str(p.resolve()))
            ok=False
            # One slot represents one continuous Character audio source. Multiple files
            # require an upstream mix/sequence step and are therefore not falsely enforced.
            if len(paths)==1 and controls["lip_sync"]:
                ok=_set_audio(inputs,paths[0])
            if ok: audio_bound.add(str(beats[0].get("character_id") or target))
            slots.append({"node_id":str(node_id),"slot":base,"target":target,"wired":ok,"audio_files":len(paths)})
        elif base=="film_lab_facial_performance":
            beats=_beats_for(conditioning,target); value=" | ".join(
                f'{b.get("start_s",0)}s {b.get("emotion","")} {b.get("intention","")} {b.get("text","")}'.strip() for b in beats
            )
            ok=bool(value and controls["facial_performance"] and _set_text(inputs,value))
            if ok and beats: face_bound.add(str(beats[0].get("character_id") or target))
            slots.append({"node_id":str(node_id),"slot":base,"target":target,"wired":ok})
    enforced=sorted(audio_bound)
    return {"version":1,"controls":controls,"slots":slots,"audio_bound_character_ids":sorted(audio_bound),"facial_bound_character_ids":sorted(face_bound),"lip_sync_enforced_character_ids":enforced,"wired":bool(enforced)}

def update_dialogue_enforcement(conditioning,evidence:dict[str,Any])->dict[str,Any]:
    from film_lab.dialogue_performance import DialogueBeat, DialoguePerformance, dialogue_enforcement
    raw=_dialogue(conditioning)
    if not raw: return {}
    beats=tuple(DialogueBeat(**x) for x in raw.get("beats",[]) if isinstance(x,dict))
    perf=DialoguePerformance(str(raw.get("scene_id",conditioning.scene_id)),str(raw.get("shot_id",conditioning.shot_id)),beats,str(raw.get("status","TIMED_AUDIO")))
    required=set(perf.character_ids); enforced=set(evidence.get("lip_sync_enforced_character_ids") or [])
    result=dialogue_enforcement(perf,audio_timing_wired=True,lip_sync_wired=bool(required and required<=enforced),character_audio_wired=bool(required and required<=enforced))
    result["per_character"]=[{"character_id":cid,"status":"ENFORCED" if cid in enforced else "PARTIAL"} for cid in sorted(required)]
    conditioning.metadata["dialogue_performance_enforcement"]=result
    return result
