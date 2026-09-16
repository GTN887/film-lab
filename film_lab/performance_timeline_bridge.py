"""Evidence-based bridge from Film Lab actor timelines to ComfyUI workflows.

A timeline is ENFORCED only when a workflow exposes an explicit per-character
Film Lab timeline slot *and* contains a time-aware consumer. Merely mentioning
seconds in a prompt remains PROMPT_ONLY.
"""
from __future__ import annotations
import json
from typing import Any

TEMPORAL_TERMS=("keyframe","timeline","promptschedule","promptschedule","animatediff","temporal","schedule")
POSE_TERMS=("openpose","dwpose","dwpreprocessor","pose","controlnet")
EXPRESSION_TERMS=("expression","liveportrait","faceexpression","facial")


def _title(node:dict[str,Any])->str:
    return str((node.get("_meta") or {}).get("title") or "").strip()

def _slot(title:str)->tuple[str,str]:
    if ":" in title:
        a,b=title.split(":",1); return a.strip().lower(),b.strip().lower()
    return title.strip().lower(),""

def _set_scalar(inputs:dict[str,Any], value:str)->bool:
    for key in ("timeline","schedule","keyframes","text","value","json"):
        if key in inputs and not isinstance(inputs[key],(list,dict)):
            inputs[key]=value; return True
    return False

def _timeline_for(conditioning,target:str):
    rows=list((getattr(conditioning,"metadata",{}) or {}).get("performance_timelines") or [])
    if not target: return rows[0] if len(rows)==1 else None
    for row in rows:
        if target in {str(row.get("character_id") or "").lower(),str(row.get("character_name") or "").lower()}:
            return row
    return None

def inspect_performance_controls(graph:dict[str,Any])->dict[str,Any]:
    names=[str(n.get("class_type","")).lower() for n in graph.values() if isinstance(n,dict)]
    return {
        "time_aware":any(any(t in n for t in TEMPORAL_TERMS) for n in names),
        "pose_control":any(any(t in n for t in POSE_TERMS) for n in names),
        "expression_control":any(any(t in n for t in EXPRESSION_TERMS) for n in names),
    }

def inject_performance_timelines(graph:dict[str,Any],conditioning)->dict[str,Any]:
    controls=inspect_performance_controls(graph); slots=[]; enforced=[]
    for node_id,node in graph.items():
        if not isinstance(node,dict): continue
        base,target=_slot(_title(node))
        if base!="film_lab_performance_timeline": continue
        row=_timeline_for(conditioning,target); ok=False
        if row and controls["time_aware"]:
            ok=_set_scalar(node.setdefault("inputs",{}),json.dumps(row,sort_keys=True))
        if ok: enforced.append(str(row.get("character_id") or target))
        slots.append({"node_id":str(node_id),"target":target,"wired":ok,"character_id":str((row or {}).get("character_id") or "")})
    return {"version":1,"controls":controls,"slots":slots,"enforced_character_ids":sorted(set(enforced)),"wired":bool(enforced)}

def update_timeline_enforcement(conditioning,evidence:dict[str,Any])->list[dict[str,Any]]:
    enforced=set(evidence.get("enforced_character_ids") or []); out=[]
    for row in list((getattr(conditioning,"metadata",{}) or {}).get("performance_timelines") or []):
        cid=str(row.get("character_id") or "")
        ok=cid in enforced
        out.append({"character_id":cid,"status":"ENFORCED" if ok else "PROMPT_ONLY","reason":"Time-aware performance timeline was injected into the selected workflow." if ok else "No proven time-aware workflow bridge was wired for this character.","keyframes":len(row.get("keyframes") or [])})
    conditioning.metadata["performance_timeline_enforcement"]=out
    return out
