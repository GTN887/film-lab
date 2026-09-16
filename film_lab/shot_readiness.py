"""Director-facing Take ranking and Shot Readiness gate.

Ranks Takes from persisted QC evidence without changing selection. A recommendation is
advisory: only the Creator may select a Take. Readiness is conservative and never
claims semantic/identity quality from pixel or tracking evidence alone.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json
from film_lab.production import ProductionStore
from film_lab.autonomous_repair_planner import qc_penalty

@dataclass(frozen=True)
class TakeScore:
    take_id: str
    status: str
    score: float
    qc_penalty: float
    severe_events: int
    event_count: int
    media_exists: bool
    evidence_status: str
    reasons: tuple[str, ...]
    selected: bool = False
    def to_dict(self):
        d=asdict(self); d['reasons']=list(self.reasons); return d

@dataclass(frozen=True)
class ShotReadiness:
    scene_id: str
    shot_id: str
    status: str
    selected_take_id: str
    recommended_take_id: str
    recommendation_requires_creator_approval: bool
    selected_score: float | None
    recommended_score: float | None
    take_scores: tuple[TakeScore, ...]
    reasons: tuple[str, ...]
    truth: str
    def to_dict(self):
        d=asdict(self); d['take_scores']=[x.to_dict() for x in self.take_scores]; d['reasons']=list(self.reasons); return d

class ShotReadinessStore:
    def __init__(self, project):
        self.project=project; project.ensure_dirs(); self.path=project.root/'shot_readiness.json'
    def save(self, report:ShotReadiness):
        data={}
        if self.path.exists():
            try: data=json.loads(self.path.read_text(encoding='utf-8'))
            except (OSError,json.JSONDecodeError): data={}
        data[f'{report.scene_id}:{report.shot_id}']=report.to_dict()
        tmp=self.path.with_suffix('.json.tmp'); tmp.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf-8'); tmp.replace(self.path); return report

def _scan(take)->dict[str,Any]:
    m=take.metadata if isinstance(take.metadata,dict) else {}
    for key in ('full_take_continuity_scan','continuity_repair_scan'):
        if isinstance(m.get(key),dict): return m[key]
    return {}

def score_take(take)->TakeScore:
    report=_scan(take); events=list(report.get('events',[]) or []); penalty=qc_penalty(events)
    severe=sum(1 for e in events if str(e.get('severity','')).upper() in {'HIGH','CRITICAL'})
    exists=Path(take.media_path).is_file()
    evidence='TESTED' if report else 'NOT_TESTED'
    # 100 is only a deterministic QC score, never a semantic quality percentage.
    score=max(0.0,100.0-penalty-(25.0 if not exists else 0.0)-(8.0 if not report else 0.0))
    reasons=[]
    if not exists: reasons.append('Take media is missing.')
    if not report: reasons.append('No persisted full-take continuity scan is available.')
    if severe: reasons.append(f'{severe} HIGH/CRITICAL continuity event(s) remain.')
    elif events: reasons.append(f'{len(events)} continuity event(s) remain for review.')
    else: reasons.append('No persisted continuity events are present.' if report else 'Continuity evidence has not been run.')
    return TakeScore(take.id,take.status,round(score,2),penalty,severe,len(events),exists,evidence,tuple(reasons),take.status=='selected')

def evaluate_shot(project, scene_id:str, shot_id:str)->ShotReadiness:
    store=ProductionStore(project); takes=[t for t in store.list_takes(shot_id=shot_id,existing_media_only=False) if t.scene_id==scene_id]
    if not takes:
        r=ShotReadiness(scene_id,shot_id,'FAIL','','',True,None,None,(),('No Takes exist for this shot.',),'FAIL means production evidence is insufficient; Film Lab did not select anything.')
        return ShotReadinessStore(project).save(r)
    scores=tuple(sorted((score_take(t) for t in takes),key=lambda x:(x.media_exists,x.evidence_status=='TESTED',-x.severe_events,x.score),reverse=True))
    selected=next((s for s in scores if s.selected),None)
    eligible=[s for s in scores if s.media_exists and s.evidence_status=='TESTED']
    recommended=max(eligible,key=lambda x:x.score,default=None)
    reasons=[]
    if selected is None: status='FAIL'; reasons.append('No Take is selected for this shot.')
    elif not selected.media_exists: status='FAIL'; reasons.append('Selected Take media is missing.')
    elif selected.evidence_status!='TESTED': status='NOT TESTED'; reasons.append('Selected Take has no persisted full-take continuity scan.')
    elif selected.severe_events: status='REVIEW'; reasons.append(f'Selected Take has {selected.severe_events} HIGH/CRITICAL continuity event(s).')
    elif selected.event_count: status='REVIEW'; reasons.append(f'Selected Take has {selected.event_count} remaining continuity event(s).')
    else: status='PASS'; reasons.append('Selected Take has media and its persisted continuity scan contains no events.')
    if recommended and (selected is None or recommended.take_id!=selected.take_id) and (selected is None or recommended.score>selected.score):
        reasons.append(f'Film Lab recommends reviewing {recommended.take_id} because its deterministic QC score is higher; it was NOT selected automatically.')
    truth='QC score ranks persisted machine evidence only. It does not prove acting quality, story quality, semantic identity, anatomy, or Creator preference. Final Take selection is always manual.'
    r=ShotReadiness(scene_id,shot_id,status,selected.take_id if selected else '',recommended.take_id if recommended else '',True,selected.score if selected else None,recommended.score if recommended else None,scores,tuple(reasons),truth)
    return ShotReadinessStore(project).save(r)

def format_shot_readiness(report:ShotReadiness)->str:
    lines=[f'### Shot Readiness — {report.status}',f'**Scene / Shot:** `{report.scene_id}` / `{report.shot_id}`',f'**Selected Take:** `{report.selected_take_id or "NONE"}`',f'**Recommended for Director review:** `{report.recommended_take_id or "NONE"}`']
    for s in report.take_scores:
        mark=' · SELECTED' if s.selected else ''
        lines.append(f'- `{s.take_id}` — QC **{s.score:.2f}** · {s.evidence_status} · severe {s.severe_events} · events {s.event_count}{mark}')
    lines.extend([f'**Reason:** {" ".join(report.reasons)}',f'**Truth:** {report.truth}','**Automatic selection: NO.**'])
    return '\n'.join(lines)
