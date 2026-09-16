"""Project-bound visual target tracking across a sequence of frames.

Tracking follows a creator-registered visual region. It is not biometric identity
recognition and a successful track must not be reported as proof of identity.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable
import json, math
import numpy as np
from PIL import Image
from film_lab.visual_target_recognition import VisualTarget, _validate_bbox

@dataclass(frozen=True)
class TrackPoint:
    frame_index: int
    time_s: float
    bbox: tuple[float,float,float,float]
    confidence: float
    status: str
    def to_dict(self):
        d=asdict(self); d["bbox"]=list(self.bbox); return d

@dataclass(frozen=True)
class VisualTrack:
    target_id: str
    points: tuple[TrackPoint,...]
    status: str
    method: str="local appearance template tracking"
    def to_dict(self): return {"target_id":self.target_id,"points":[p.to_dict() for p in self.points],"status":self.status,"method":self.method,"truth":"Tracking follows the creator-bound target region; it does not certify biometric identity or semantic sameness."}

class VisualTrackStore:
    def __init__(self,project):
        self.project=project; project.ensure_dirs(); self.path=project.root/"visual_tracks.json"
    def _load(self):
        if not self.path.exists(): return {"version":1,"tracks":{}}
        try: d=json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError): return {"version":1,"tracks":{}}
        d.setdefault("version",1); d.setdefault("tracks",{}); return d
    def save(self,track:VisualTrack):
        d=self._load(); d["tracks"][track.target_id]=track.to_dict(); t=self.path.with_suffix(".json.tmp"); t.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n",encoding="utf-8"); t.replace(self.path); return track
    def get(self,target_id:str)->dict[str,Any]|None: return self._load()["tracks"].get(target_id)

def _gray(path:Path)->np.ndarray:
    return np.asarray(Image.open(path).convert("L"),dtype=np.float32)/255.0

def _px_bbox(b,w,h):
    _validate_bbox(b); x1,y1,x2,y2=b
    return int(round(x1*w)),int(round(y1*h)),int(round(x2*w)),int(round(y2*h))

def _resize_array(a:np.ndarray,size=(48,48))->np.ndarray:
    im=Image.fromarray(np.uint8(np.clip(a,0,1)*255),mode="L").resize(size,Image.Resampling.BILINEAR)
    return np.asarray(im,dtype=np.float32)/255.0

def _score(template:np.ndarray,crop:np.ndarray)->float:
    if crop.size==0: return 0.0
    a=_resize_array(template); b=_resize_array(crop)
    # Appearance error plus centered-contrast error makes flat brightness shifts less destructive.
    mae=float(np.mean(np.abs(a-b)))
    ac=a-a.mean(); bc=b-b.mean(); contrast=float(np.mean(np.abs(ac-bc)))
    return max(0.0,1.0-(0.65*mae+0.35*contrast)*2.0)

def track_target_frames(target:VisualTarget, frames:Iterable[Path], *, fps:float=1.0, search_radius:float=.20, steps:int=9, lost_threshold:float=.42)->VisualTrack:
    paths=[Path(p) for p in frames]
    if not paths: return VisualTrack(target.id,tuple(),"NOT_TESTED")
    first=_gray(paths[0]); h,w=first.shape; x1,y1,x2,y2=_px_bbox(target.bbox,w,h); template=first[y1:y2,x1:x2].copy()
    if template.size==0: raise ValueError("Registered target region is empty")
    current=target.bbox; points=[]
    for i,path in enumerate(paths):
        arr=_gray(path); hh,ww=arr.shape
        if i==0:
            conf=1.0; best=current
        else:
            cx=(current[0]+current[2])/2; cy=(current[1]+current[3])/2; bw=current[2]-current[0]; bh=current[3]-current[1]
            best=current; conf=-1.0
            for oy in np.linspace(-search_radius,search_radius,steps):
                for ox in np.linspace(-search_radius,search_radius,steps):
                    ncx=min(1-bw/2,max(bw/2,cx+float(ox))); ncy=min(1-bh/2,max(bh/2,cy+float(oy)))
                    b=(ncx-bw/2,ncy-bh/2,ncx+bw/2,ncy+bh/2); px=_px_bbox(b,ww,hh); crop=arr[px[1]:px[3],px[0]:px[2]]; s=_score(template,crop)
                    if s>conf: conf=s; best=b
            if conf>=lost_threshold: current=best
        status="TRACKED" if conf>=lost_threshold else "LOST"
        points.append(TrackPoint(i,i/max(float(fps),1e-9),tuple(round(float(v),6) for v in best),round(float(conf),6),status))
    tracked=sum(p.status=="TRACKED" for p in points); ratio=tracked/len(points)
    status="PASS" if ratio>=.90 else "PARTIAL" if ratio>=.50 else "FAIL"
    return VisualTrack(target.id,tuple(points),status)

def compare_tracks(source:VisualTrack,candidate:VisualTrack, *, center_tolerance:float=.12)->dict[str,Any]:
    n=min(len(source.points),len(candidate.points)); deviations=[]
    for a,b in zip(source.points[:n],candidate.points[:n]):
        if a.status!="TRACKED" or b.status!="TRACKED": continue
        ac=((a.bbox[0]+a.bbox[2])/2,(a.bbox[1]+a.bbox[3])/2); bc=((b.bbox[0]+b.bbox[2])/2,(b.bbox[1]+b.bbox[3])/2)
        deviations.append(math.dist(ac,bc))
    if not deviations: status="NOT_TESTED"; mean=None
    else:
        mean=sum(deviations)/len(deviations); status="PASS" if mean<=center_tolerance else "REVIEW" if mean<=center_tolerance*2 else "FAIL"
    return {"status":status,"mean_center_deviation":None if mean is None else round(mean,6),"samples_compared":len(deviations),"truth":"Position-track similarity is not identity certification."}
