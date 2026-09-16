"""Continuity problem localization and repair orchestration.

Turns Full-Take continuity events into auditable repair windows. A repair forks a
new candidate from the problematic candidate Take at the localized time and can
bind a Creator-registered target region/Character. It never overwrites either
source. Temporal *splicing* is not claimed unless a renderer later proves it.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
import json

from film_lab.production import ProductionStore
from film_lab.visual_target_recognition import VisualTargetStore
from film_lab.full_take_continuity_scanning import scan_take_continuity

@dataclass(frozen=True)
class RepairPlan:
    candidate_take_id: str
    original_source_take_id: str
    event_index: int
    time_s: float
    window_start_s: float
    window_end_s: float
    domain: str
    target_id: str
    target_label: str
    character_id: str
    bbox: tuple[float,float,float,float] | None
    instruction: str
    severity: str
    temporal_status: str = "LOCALIZED_NOT_SPLICED"
    def to_dict(self):
        d=asdict(self); d["bbox"]=list(self.bbox) if self.bbox else None; return d

class RepairPlanStore:
    def __init__(self,project):
        self.project=project; project.ensure_dirs(); self.path=project.root/"continuity_repair_plan.json"
    def save(self,plan:RepairPlan):
        t=self.path.with_suffix(".json.tmp"); t.write_text(json.dumps(plan.to_dict(),indent=2,sort_keys=True)+"\n",encoding="utf-8"); t.replace(self.path); return plan
    def load(self):
        if not self.path.exists(): return None
        try: d=json.loads(self.path.read_text(encoding="utf-8")); d["bbox"]=tuple(d["bbox"]) if d.get("bbox") else None; return RepairPlan(**d)
        except (OSError,json.JSONDecodeError,TypeError,KeyError): return None

def _bbox_at(report:dict[str,Any], target_id:str, time_s:float):
    if not target_id: return None
    for tr in report.get("targets",[]) or []:
        if (tr.get("target") or {}).get("id") != target_id: continue
        pts=(tr.get("candidate_track") or {}).get("points",[]) or []
        tracked=[p for p in pts if p.get("status")=="TRACKED" and p.get("bbox")]
        if tracked:
            p=min(tracked,key=lambda x:abs(float(x.get("time_s",0))-time_s)); return tuple(float(v) for v in p["bbox"])
    return None

def localize_candidate_problem(project, candidate_take_id:str, *, event_index:int=0, padding_s:float=.5, instruction:str="") -> RepairPlan:
    take=ProductionStore(project).get_take(candidate_take_id); meta=take.metadata if isinstance(take.metadata,dict) else {}
    report=meta.get("full_take_continuity_scan") if isinstance(meta.get("full_take_continuity_scan"),dict) else {}
    events=report.get("events",[]) or []
    timed=[(i,e) for i,e in enumerate(events) if e.get("time_s") is not None]
    if not timed: raise ValueError("Candidate has no time-localized continuity event to repair.")
    # event_index refers to the visible timed-event list, avoiding non-timed aggregate track warnings.
    idx=max(0,min(int(event_index),len(timed)-1)); original_index,event=timed[idx]
    t=max(0.0,float(event["time_s"])); pad=max(0.05,float(padding_s)); target_id=str(event.get("target_id") or "")
    target=next((x for x in VisualTargetStore(project).list() if x.id==target_id),None)
    bbox=_bbox_at(report,target_id,t) or (tuple(target.bbox) if target else None)
    label=target.label if target else target_id
    char_id=target.character_id if target else ""
    note=(instruction or "").strip() or (f"Repair continuity drift for {label or event.get('domain','this region')} at {t:.3f}s while preserving all unspecified locked continuity." )
    plan=RepairPlan(candidate_take_id,str(meta.get("ab_source_take_id") or (meta.get("continuity_contract") or {}).get("source_take_id") or ""),original_index,t,max(0.0,t-pad),t+pad,str(event.get("domain") or "continuity"),target_id,label,char_id,bbox,note,str(event.get("severity") or "MEDIUM"))
    return RepairPlanStore(project).save(plan)

def execute_repair(project, *, generator, plan:RepairPlan|None=None):
    """Fork a repair candidate and rescan it. This is localized regeneration prep,
    not a claim of temporal video inpainting/splicing."""
    from film_lab.mark_direct_regenerate import regenerate_take
    plan=plan or RepairPlanStore(project).load()
    if plan is None: raise ValueError("No localized continuity repair plan is ready.")
    new=regenerate_take(project,source_take_id=plan.candidate_take_id,generator=generator,director_instruction=plan.instruction,character_id=plan.character_id,source_time_s=plan.time_s,repair_bbox=plan.bbox)
    store=ProductionStore(project); data=store._load(); meta=data["takes"][new.id].setdefault("metadata",{})
    meta["continuity_repair"]={**plan.to_dict(),"repair_candidate_id":new.id,"source_candidate_preserved":True,"temporal_enforcement":"NOT_ENFORCED","truth":"Film Lab regenerated from the localized source moment. It did not splice only this time window into the video; temporal patch enforcement requires a proven renderer path."}
    store._save(data)
    # Compare repaired result to the candidate being repaired and persist evidence.
    report=scan_take_continuity(project,source_take_id=plan.candidate_take_id,candidate_take_id=new.id,contract={"repair_plan":plan.to_dict()})
    data=store._load(); data["takes"][new.id].setdefault("metadata",{})["continuity_repair_scan"]=report; store._save(data)
    return store.get_take(new.id),report
