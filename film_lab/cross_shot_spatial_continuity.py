"""Cross-shot action, screen-direction, position and eyeline continuity evidence.

Uses persisted Creator-bound target tracks and explicit shot metadata only. It does not
infer semantic identity, gaze, or the 180-degree rule from pixels alone.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
import math

from film_lab.production import Take

@dataclass(frozen=True)
class SpatialContinuityReport:
    status: str
    action_match_status: str
    screen_direction_status: str
    position_status: str
    eyeline_status: str
    issues: tuple[dict[str, Any], ...]
    target_reports: tuple[dict[str, Any], ...]
    truth: str
    def to_dict(self):
        d=asdict(self); d['issues']=[dict(x) for x in self.issues]; d['target_reports']=[dict(x) for x in self.target_reports]; return d

def _scan(t:Take)->dict[str,Any]:
    m=t.metadata if isinstance(t.metadata,dict) else {}
    s=m.get('full_take_continuity_scan') or m.get('continuity_repair_scan') or {}
    return s if isinstance(s,dict) else {}

def _candidate_points(target:dict[str,Any])->list[dict[str,Any]]:
    tr=target.get('candidate_track') or {}
    return [p for p in (tr.get('points',[]) or []) if isinstance(p,dict) and str(p.get('status','')).upper()=='TRACKED']

def _center(p:dict[str,Any])->tuple[float,float]|None:
    b=p.get('bbox') or []
    if not isinstance(b,(list,tuple)) or len(b)!=4: return None
    try: return ((float(b[0])+float(b[2]))/2,(float(b[1])+float(b[3]))/2)
    except (TypeError,ValueError): return None

def _motion(points:list[dict[str,Any]], *, end:bool)->tuple[float,float]|None:
    if len(points)<2: return None
    a,b=(points[-2],points[-1]) if end else (points[0],points[1])
    ca,cb=_center(a),_center(b)
    if ca is None or cb is None: return None
    v=(cb[0]-ca[0],cb[1]-ca[1])
    return None if math.hypot(*v)<.015 else v

def _dir(v):
    if v is None:return None
    if abs(v[0])>=abs(v[1]): return 'RIGHT' if v[0]>0 else 'LEFT'
    return 'DOWN' if v[1]>0 else 'UP'

def _targets(t:Take)->dict[str,dict[str,Any]]:
    out={}
    for row in _scan(t).get('targets',[]) or []:
        if not isinstance(row,dict): continue
        target=row.get('target') or {}; tid=str(target.get('id') or row.get('target_id') or '')
        if tid: out[tid]=row
    return out

def _eyeline(a:Take,b:Take)->tuple[str,list[dict[str,Any]]]:
    def intent(t):
        m=t.metadata if isinstance(t.metadata,dict) else {}
        x=m.get('cross_shot_spatial_intent') or {}
        return x if isinstance(x,dict) else {}
    ai,bi=intent(a),intent(b); ao=str(ai.get('eyeline_out','')).upper(); ii=str(bi.get('eyeline_in','')).upper()
    if not ao or not ii:
        return 'NOT_TESTED',[{'domain':'eyeline','severity':'REVIEW','message':'No explicit outgoing/incoming eyeline intent is persisted for both Shots.'}]
    # Matching screen-side gaze should normally reverse across a conversational cut.
    opposite={('LEFT','RIGHT'),('RIGHT','LEFT'),('UP','DOWN'),('DOWN','UP')}
    if (ao,ii) in opposite: return 'PASS',[]
    return 'REVIEW',[{'domain':'eyeline','severity':'MEDIUM','message':f'Explicit eyeline intent does not oppose across cut ({ao} → {ii}); Director review required.'}]

def evaluate_cross_shot_spatial(a:Take,b:Take, *, position_jump_tolerance:float=.38)->SpatialContinuityReport:
    issues=[]; reports=[]; at,bt=_targets(a),_targets(b); common=sorted(set(at)&set(bt))
    direction_states=[]; position_states=[]
    if not common:
        issues.append({'domain':'spatial_tracking','severity':'REVIEW','message':'No common Creator-registered target track exists across both Takes.'})
    for tid in common:
        ap,bp=_candidate_points(at[tid]),_candidate_points(bt[tid]); ac=_center(ap[-1]) if ap else None; bc=_center(bp[0]) if bp else None
        jump=math.dist(ac,bc) if ac is not None and bc is not None else None
        od,id_=_dir(_motion(ap,end=True)),_dir(_motion(bp,end=False))
        if od and id_:
            ds='PASS' if od==id_ else 'REVIEW'; direction_states.append(ds)
            if ds=='REVIEW': issues.append({'domain':'screen_direction','severity':'HIGH','target_id':tid,'message':f'Target motion reverses across cut ({od} → {id_}). This can be intentional but may create a screen-direction/action jump.'})
        else: direction_states.append('NOT_TESTED')
        if jump is None: ps='NOT_TESTED'
        elif jump<=position_jump_tolerance: ps='PASS'
        else:
            ps='REVIEW'; issues.append({'domain':'position','severity':'MEDIUM','target_id':tid,'message':f'Target boundary position changes by {jump:.3f} normalized-frame units.'})
        position_states.append(ps); reports.append({'target_id':tid,'outgoing_direction':od,'incoming_direction':id_,'boundary_position_delta':None if jump is None else round(jump,6),'screen_direction_status':direction_states[-1],'position_status':ps})
    def aggregate(states):
        if 'REVIEW' in states:return 'REVIEW'
        if states and all(x=='PASS' for x in states):return 'PASS'
        return 'NOT_TESTED'
    screen=aggregate(direction_states); position=aggregate(position_states)
    action='REVIEW' if screen=='REVIEW' or position=='REVIEW' else 'PASS' if screen=='PASS' and position=='PASS' else 'NOT_TESTED'
    eye,eyeissues=_eyeline(a,b); issues.extend(eyeissues)
    status='REVIEW' if 'REVIEW' in {action,screen,position,eye} else 'PASS' if {action,screen,position,eye}=={'PASS'} else 'NOT_TESTED'
    truth='Cross-shot spatial evidence uses Creator-bound target positions/motion plus explicit eyeline intent. It does not prove identity, semantic action matching, gaze from pixels, camera-axis compliance, or that an intentional jump cut is wrong.'
    return SpatialContinuityReport(status,action,screen,position,eye,tuple(issues),tuple(reports),truth)
