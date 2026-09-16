"""Evidence-based bridge for Character-bound expressive voice/prosody controls."""
from __future__ import annotations
import json
from typing import Any
EXPRESSIVE_TERMS=("emotion","expressive","prosody","styletts","fishspeech","f5tts","xtts","cosyvoice","parler")
def _title(n): return str((n.get("_meta") or {}).get("title") or "").strip()
def _slot(t):
    if ":" in t: a,b=t.split(":",1); return a.strip().lower(),b.strip().lower()
    return t.lower(),""
def _set(inputs,value):
    for k in ("voice_performance","prosody","style","instruction","text","prompt","value"):
        if k in inputs and not isinstance(inputs[k],(list,dict)): inputs[k]=value; return True
    return False
def inject_voice_acting(graph:dict[str,Any],conditioning)->dict[str,Any]:
    raw=(getattr(conditioning,"metadata",{}) or {}).get("voice_acting") or {}; beats=raw.get("beats") or []
    names=[str(n.get("class_type","")).lower() for n in graph.values() if isinstance(n,dict)]
    expressive=any(any(t in n for t in EXPRESSIVE_TERMS) for n in names); slots=[]; enforced=[]
    for nid,node in graph.items():
        if not isinstance(node,dict): continue
        base,target=_slot(_title(node))
        if base!="film_lab_voice_performance": continue
        mine=[b for b in beats if not target or str(b.get("character_id","")).lower()==target]
        ids={str(b.get("character_id","")).lower() for b in mine}
        value=json.dumps(mine,ensure_ascii=False,separators=(",",":")) if mine else ""
        ok=bool(expressive and len(ids)==1 and value and _set(node.setdefault("inputs",{}),value))
        if ok: enforced.extend(ids)
        slots.append({"node_id":str(nid),"target":target,"wired":ok,"beats":len(mine)})
    return {"version":1,"expressive_renderer":expressive,"slots":slots,"enforced_character_ids":sorted(set(enforced)),"wired":bool(enforced)}
def update_voice_acting_enforcement(conditioning,evidence):
    from film_lab.voice_acting import VoiceActingBeat,VoiceActingPerformance,voice_acting_enforcement
    raw=(conditioning.metadata or {}).get("voice_acting") or {}
    if not raw:return {}
    p=VoiceActingPerformance(str(raw.get("scene_id",conditioning.scene_id)),str(raw.get("shot_id",conditioning.shot_id)),tuple(VoiceActingBeat(**x) for x in raw.get("beats",[]) if isinstance(x,dict)))
    req=set(p.character_ids); got=set(evidence.get("enforced_character_ids") or [])
    r=voice_acting_enforcement(p,expressive_voice_wired=bool(req and req<=got),character_voice_wired=bool(req and req<=got)); r["per_character"]=[{"character_id":x,"status":"ENFORCED" if x in got else "PROMPT_ONLY"} for x in sorted(req)]; conditioning.metadata["voice_acting_enforcement"]=r; return r
