"""Automated Take Quality Control and conservative repair decisions.

Diagnoses persisted continuity evidence and recommends a repair path. Recommendations
never select, overwrite, or reject a Take. Execution forks a new candidate and leaves
final A/B acceptance to the Creator.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
import json
from film_lab.production import ProductionStore

@dataclass(frozen=True)
class RepairDecision:
    candidate_take_id: str
    status: str
    strategy: str
    confidence: str
    event_index: int | None
    time_s: float | None
    target_id: str
    domain: str
    reason: str
    preserve: tuple[str, ...]
    automatic_action: str
    requires_creator_approval: bool = True
    def to_dict(self):
        d=asdict(self); d["preserve"]=list(self.preserve); return d

class TakeQualityControlStore:
    def __init__(self,project):
        self.project=project; project.ensure_dirs(); self.path=project.root/"take_quality_control.json"
    def save(self,decision:RepairDecision):
        tmp=self.path.with_suffix(".json.tmp"); tmp.write_text(json.dumps(decision.to_dict(),indent=2,sort_keys=True)+"\n",encoding="utf-8"); tmp.replace(self.path); return decision
    def load(self):
        if not self.path.exists(): return None
        try:
            d=json.loads(self.path.read_text(encoding="utf-8")); d["preserve"]=tuple(d.get("preserve",[])); return RepairDecision(**d)
        except (OSError,json.JSONDecodeError,TypeError,KeyError): return None

def _report(take):
    m=take.metadata if isinstance(take.metadata,dict) else {}
    for key in ("full_take_continuity_scan","continuity_repair_scan"):
        if isinstance(m.get(key),dict): return m[key]
    return {}

def diagnose_take(project,candidate_take_id:str)->RepairDecision:
    take=ProductionStore(project).get_take(candidate_take_id); report=_report(take); events=report.get("events",[]) or []
    timed=[e for e in events if e.get("time_s") is not None]
    high=[e for e in events if str(e.get("severity","")).upper()=="HIGH"]
    preserve=("character_identity","wardrobe_appearance","other_actors","set_location","props_unless_targeted","lighting","camera_unless_targeted","dialogue_timing","audio_unless_targeted")
    if not events:
        d=RepairDecision(take.id,"PASS","NONE","HIGH",None,None,"","none","No continuity repair event is present.",preserve,"NO_REPAIR")
        return TakeQualityControlStore(project).save(d)
    # Multiple independent severe failures are safer as a new Take than stacked patches.
    severe_domains={str(e.get("domain") or "continuity") for e in high}
    if len(high)>=3 and len(severe_domains)>=2:
        d=RepairDecision(take.id,"REVIEW","REGENERATE_TAKE","HIGH",None,None,"","multiple_severe_failures",f"{len(high)} severe events span multiple continuity domains; repeated local patches may compound artifacts.",preserve,"FORK_FULL_CANDIDATE")
        return TakeQualityControlStore(project).save(d)
    e=(high[0] if high else (timed[0] if timed else events[0])); domain=str(e.get("domain") or "continuity"); target=str(e.get("target_id") or "")
    mapping={
      "registered_visual_target":("REGIONAL_TARGET_REPAIR","HIGH","LOCALIZED_REPAIR"),
      "target_position_track":("MOTION_TEMPORAL_REPAIR","MEDIUM","LOCALIZED_REPAIR"),
      "global_frame_similarity":("LOCALIZED_VISUAL_REPAIR","MEDIUM","LOCALIZED_REPAIR"),
      "camera":("CAMERA_CONTINUITY_REPAIR","MEDIUM","LOCALIZED_REPAIR"),
      "dialogue":("DIALOGUE_AUDIO_REPAIR","MEDIUM","LOCALIZED_REPAIR"),
      "lip_sync":("LIP_SYNC_REPAIR","MEDIUM","LOCALIZED_REPAIR"),
      "audio":("LOCALIZED_AUDIO_REPAIR","MEDIUM","LOCALIZED_REPAIR"),
      "performance":("CHARACTER_PERFORMANCE_REPAIR","MEDIUM","LOCALIZED_REPAIR"),
      "seam":("SEAM_BLEND_REPAIR","HIGH","SEAM_BLEND"),
      "motion_seam":("MOTION_ALIGNMENT_REPAIR","HIGH","MOTION_ALIGN"),
    }
    strategy,confidence,action=mapping.get(domain,("CONTINUITY_LOCAL_REPAIR","MEDIUM","LOCALIZED_REPAIR"))
    t=float(e["time_s"]) if e.get("time_s") is not None else None
    # localizer indexes only timed events
    idx=timed.index(e) if e in timed else None
    if t is None and action=="LOCALIZED_REPAIR": action="MANUAL_REVIEW"
    reason=str(e.get("message") or f"Continuity event in {domain} requires review.")
    d=RepairDecision(take.id,"REVIEW",strategy,confidence,idx,t,target,domain,reason,preserve,action)
    return TakeQualityControlStore(project).save(d)

def execute_recommended_repair(project,*,generator,decision:RepairDecision|None=None):
    """Execute only a safe fork operation. Never changes Selected Take status."""
    from film_lab.continuity_problem_repair import localize_candidate_problem, execute_repair
    from film_lab.mark_direct_regenerate import regenerate_take
    decision=decision or TakeQualityControlStore(project).load()
    if decision is None: raise ValueError("Run Take Quality Control first.")
    if decision.automatic_action=="NO_REPAIR": raise ValueError("Quality Control found no repair to execute.")
    if decision.automatic_action=="FORK_FULL_CANDIDATE":
        new=regenerate_take(project,source_take_id=decision.candidate_take_id,generator=generator,director_instruction="Regenerate this Take while preserving locked continuity and correcting the diagnosed severe continuity failures.")
        data=ProductionStore(project)._load(); data["takes"][new.id].setdefault("metadata",{})["quality_control_decision"]=decision.to_dict(); ProductionStore(project)._save(data)
        return ProductionStore(project).get_take(new.id),{"status":"NOT_TESTED","truth":"A new candidate was forked; quality must be rescanned before acceptance."}
    if decision.automatic_action!="LOCALIZED_REPAIR" or decision.event_index is None:
        raise ValueError(f"Recommended strategy {decision.strategy} requires its specialized/manual repair control; it will not be silently substituted.")
    plan=localize_candidate_problem(project,decision.candidate_take_id,event_index=decision.event_index,instruction=f"Correct {decision.domain} while preserving all unspecified locked continuity. {decision.reason}")
    new,report=execute_repair(project,generator=generator,plan=plan)
    data=ProductionStore(project)._load(); data["takes"][new.id].setdefault("metadata",{})["quality_control_decision"]=decision.to_dict(); ProductionStore(project)._save(data)
    return ProductionStore(project).get_take(new.id),report
