"""Autonomous repair planning with bounded multi-pass Quality Control.

The planner may fork technical repair candidates, but it never changes the selected
Take. Every pass must improve a deterministic QC score without introducing severe
regressions; otherwise that pass is rejected from the repair chain.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Any, Callable
import json
from film_lab.production import ProductionStore
from film_lab.take_quality_control import diagnose_take, execute_recommended_repair

SEVERITY_WEIGHT={"LOW":1.0,"MEDIUM":3.0,"HIGH":7.0,"CRITICAL":10.0}

@dataclass
class RepairPass:
    pass_number:int
    source_take_id:str
    candidate_take_id:str
    strategy:str
    qc_before:float
    qc_after:float
    outcome:str
    reason:str
    remaining_events:int
    severe_regressions:int=0

@dataclass
class MultiPassRepairPlan:
    original_take_id:str
    best_take_id:str
    status:str
    max_passes:int
    min_improvement:float
    passes:list[RepairPass]=field(default_factory=list)
    stop_reason:str=""
    requires_creator_approval:bool=True
    selected_take_changed:bool=False
    def to_dict(self): return asdict(self)

class MultiPassRepairStore:
    def __init__(self,project):
        self.project=project; project.ensure_dirs(); self.path=project.root/"multi_pass_repair.json"
    def save(self,plan):
        tmp=self.path.with_suffix('.json.tmp'); tmp.write_text(json.dumps(plan.to_dict(),indent=2,sort_keys=True)+"\n",encoding='utf-8'); tmp.replace(self.path); return plan
    def load(self):
        if not self.path.exists(): return None
        try:
            d=json.loads(self.path.read_text(encoding='utf-8')); d['passes']=[RepairPass(**x) for x in d.get('passes',[])]; return MultiPassRepairPlan(**d)
        except (OSError,json.JSONDecodeError,TypeError,KeyError): return None

def _events(take):
    m=take.metadata if isinstance(take.metadata,dict) else {}
    for key in ('full_take_continuity_scan','continuity_repair_scan'):
        r=m.get(key)
        if isinstance(r,dict): return list(r.get('events',[]) or [])
    return []

def qc_penalty(events:list[dict[str,Any]])->float:
    """Lower is better. Unknown events still carry a small penalty."""
    return round(sum(SEVERITY_WEIGHT.get(str(e.get('severity','MEDIUM')).upper(),3.0) for e in events),3)

def _event_signature(e):
    return (str(e.get('domain','continuity')),str(e.get('target_id','')),round(float(e.get('time_s') or -1),2))

def _severe_regressions(before,after):
    old={_event_signature(e) for e in before}
    return sum(1 for e in after if str(e.get('severity','')).upper() in {'HIGH','CRITICAL'} and _event_signature(e) not in old)

def run_multi_pass_repair(project,*,generator,max_passes:int=3,min_improvement:float=0.5,
                          repair_executor:Callable|None=None, rescan:Callable|None=None)->MultiPassRepairPlan:
    """Run a bounded technical repair loop; never select a Take.

    repair_executor(project, generator, decision) may be injected for deterministic QA.
    rescan(project, take) may update/return a continuity report after each repair.
    """
    from film_lab.director_preview_regeneration import DirectorPreviewStore
    review=DirectorPreviewStore(project).load()
    if review is None: raise ValueError('No Director A/B candidate is ready for multi-pass QC.')
    max_passes=max(1,min(int(max_passes),5)); min_improvement=max(0.0,float(min_improvement))
    store=ProductionStore(project); original=store.get_take(review.candidate_take_id); current=original; best=original
    original_selected={t.id for t in store.selected_takes(existing_media_only=False)}
    plan=MultiPassRepairPlan(original.id,original.id,'REVIEW',max_passes,min_improvement)
    executor=repair_executor or (lambda p,g,d: execute_recommended_repair(p,generator=g,decision=d))
    for n in range(1,max_passes+1):
        before_events=_events(current); before_score=qc_penalty(before_events); decision=diagnose_take(project,current.id)
        if decision.automatic_action in {'NO_REPAIR','MANUAL_REVIEW','SEAM_BLEND','MOTION_ALIGN'}:
            plan.stop_reason=f'{decision.strategy} requires no repair or a specialized/manual control.'; break
        try: new,report=executor(project,generator,decision)
        except Exception as exc:
            plan.stop_reason=f'Repair pass {n} stopped safely: {exc}'; break
        if rescan is not None:
            report=rescan(project,new) or report
        # executor/rescan is responsible for persisting scan evidence on the Take.
        new=store.get_take(new.id); after_events=_events(new); after_score=qc_penalty(after_events)
        regressions=_severe_regressions(before_events,after_events); improvement=before_score-after_score
        accepted=improvement>=min_improvement and regressions==0
        outcome='IMPROVED' if accepted else 'REJECTED_REGRESSION' if regressions else 'REJECTED_NO_IMPROVEMENT'
        reason=(f'QC penalty improved {before_score:.2f} → {after_score:.2f}.' if accepted else
                f'Pass not promoted: QC penalty {before_score:.2f} → {after_score:.2f}; severe regressions={regressions}.')
        plan.passes.append(RepairPass(n,current.id,new.id,decision.strategy,before_score,after_score,outcome,reason,len(after_events),regressions))
        if not accepted:
            plan.stop_reason='A repair must prove improvement without a new severe regression.'; break
        best=current=new; plan.best_take_id=new.id
        if not after_events:
            plan.status='PASS'; plan.stop_reason='No remaining continuity events after accepted repair.'; break
    else: plan.stop_reason=f'Repair budget reached ({max_passes} passes).'
    if plan.status!='PASS': plan.status='REVIEW'
    final_selected={t.id for t in store.selected_takes(existing_media_only=False)}
    plan.selected_take_changed=final_selected!=original_selected
    if plan.selected_take_changed:
        raise RuntimeError('Safety violation: multi-pass QC changed the selected Take.')
    return MultiPassRepairStore(project).save(plan)

def format_multi_pass_report(plan:MultiPassRepairPlan)->str:
    lines=[f'### Autonomous Repair Planning — {plan.status}',f'**Best candidate:** `{plan.best_take_id}`',f'**Repair budget:** {len(plan.passes)}/{plan.max_passes} used']
    for p in plan.passes:
        lines.append(f'- Pass {p.pass_number}: **{p.strategy} — {p.outcome}** · QC {p.qc_before:.2f} → {p.qc_after:.2f} · {p.remaining_events} event(s) remain')
    lines += [f'**Stop reason:** {plan.stop_reason or "Awaiting Director review."}','**Automatic selection: NO.** Creator approval is required to select any candidate.']
    return '\n'.join(lines)
