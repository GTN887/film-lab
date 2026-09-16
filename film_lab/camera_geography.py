"""Explicit camera geography and 180-degree line-of-action continuity.

This module evaluates persisted Scene World/Director intent. It does not infer a 3D
camera pose, actor identity, gaze, or the line of action from video pixels.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
import math

from film_lab.production import Take

@dataclass(frozen=True)
class CameraGeographyReport:
    status: str
    axis_status: str
    side_status: str
    from_side: str | None
    to_side: str | None
    axis_angle_delta_deg: float | None
    issues: tuple[dict[str, Any], ...]
    evidence: dict[str, Any]
    truth: str
    def to_dict(self):
        d=asdict(self); d['issues']=[dict(x) for x in self.issues]; return d

def _intent(t: Take) -> dict[str, Any]:
    m=t.metadata if isinstance(t.metadata,dict) else {}
    x=m.get('camera_geography_intent') or {}
    return x if isinstance(x,dict) else {}

def _point(v):
    if not isinstance(v,(list,tuple)) or len(v)!=2: return None
    try: return float(v[0]),float(v[1])
    except (TypeError,ValueError): return None

def _axis(i):
    a=_point(i.get('line_of_action_start')); b=_point(i.get('line_of_action_end'))
    if a is None or b is None or math.dist(a,b)<1e-6: return None
    return a,b

def _side(i):
    ax=_axis(i); c=_point(i.get('camera_position'))
    if ax is None or c is None: return None
    a,b=ax; cross=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    if abs(cross)<1e-6:return 'ON_AXIS'
    return 'LEFT' if cross>0 else 'RIGHT'

def _axis_angle(i):
    ax=_axis(i)
    if ax is None:return None
    a,b=ax; return math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))

def _angle_delta(a,b):
    if a is None or b is None:return None
    return abs((b-a+180.0)%360.0-180.0)

def evaluate_camera_geography(a:Take,b:Take, *, axis_tolerance_deg:float=20.0)->CameraGeographyReport:
    ai,bi=_intent(a),_intent(b); issues=[]
    aa,ba=_axis_angle(ai),_axis_angle(bi); delta=_angle_delta(aa,ba)
    aside,bside=_side(ai),_side(bi)
    if delta is None:
        axis_status='NOT_TESTED'; issues.append({'domain':'camera_axis','severity':'REVIEW','message':'A valid explicit line of action is not persisted for both Shots.'})
    elif delta<=axis_tolerance_deg or abs(delta-180.0)<=axis_tolerance_deg:
        axis_status='PASS'
    else:
        axis_status='REVIEW'; issues.append({'domain':'camera_axis','severity':'MEDIUM','message':f'Persisted line-of-action orientation changes by {delta:.1f}° across the cut; confirm Scene geography or intentional axis reset.'})
    allow=bool(ai.get('allow_axis_cross') or bi.get('allow_axis_cross'))
    if aside is None or bside is None:
        side_status='NOT_TESTED'; issues.append({'domain':'180_degree_rule','severity':'REVIEW','message':'Explicit camera position relative to the line of action is missing for one or both Shots.'})
    elif 'ON_AXIS' in {aside,bside}:
        side_status='REVIEW'; issues.append({'domain':'180_degree_rule','severity':'MEDIUM','message':'A camera is persisted on the line of action; screen-side continuity requires Director review.'})
    elif aside==bside:
        side_status='PASS'
    elif allow:
        side_status='REVIEW'; issues.append({'domain':'180_degree_rule','severity':'REVIEW','message':f'Camera crosses the action axis ({aside} → {bside}), but the Director explicitly allowed an axis cross.'})
    else:
        side_status='REVIEW'; issues.append({'domain':'180_degree_rule','severity':'HIGH','message':f'Camera crosses the persisted line of action ({aside} → {bside}); this may reverse screen geography unless intentionally motivated.'})
    status='REVIEW' if 'REVIEW' in {axis_status,side_status} else 'PASS' if axis_status==side_status=='PASS' else 'NOT_TESTED'
    truth='Camera geography uses explicit 2D Scene/Director intent for camera position and line of action. It does not infer camera pose or actor geography from pixels, prove the 180-degree rule semantically, or declare an intentional axis crossing wrong.'
    evidence={'from_intent':ai,'to_intent':bi,'axis_tolerance_deg':axis_tolerance_deg,'axis_cross_explicitly_allowed':allow}
    return CameraGeographyReport(status,axis_status,side_status,aside,bside,None if delta is None else round(delta,4),tuple(issues),evidence,truth)
