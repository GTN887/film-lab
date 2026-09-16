"""Target-aware visual continuity evidence for Film Lab.

This module never performs biometric identification.  It evaluates creator/project-bound
visual targets (characters, props, set elements) by comparing explicitly supplied frame
regions.  A label such as ``Sarah`` means "the region Film Lab was told represents
Sarah", not an independent claim that a real person was identified.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json, math
from PIL import Image, ImageChops, ImageStat, ImageFilter

@dataclass(frozen=True)
class VisualTarget:
    id: str
    kind: str
    label: str
    bbox: tuple[float,float,float,float]  # normalized x1,y1,x2,y2
    character_id: str = ""
    object_id: str = ""
    notes: str = ""
    def to_dict(self):
        d=asdict(self); d["bbox"]=list(self.bbox); return d

class VisualTargetStore:
    def __init__(self, project):
        self.project=project; project.ensure_dirs(); self.path=project.root/"visual_targets.json"
    def _load(self):
        if not self.path.exists(): return {"version":1,"targets":{}}
        try: d=json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError): return {"version":1,"targets":{}}
        d.setdefault("version",1); d.setdefault("targets",{}); return d
    def _save(self,d):
        t=self.path.with_suffix(".json.tmp"); t.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n",encoding="utf-8"); t.replace(self.path)
    def save(self,target:VisualTarget):
        _validate_bbox(target.bbox)
        if target.kind not in {"character","object","set_element"}: raise ValueError("Unsupported visual target kind")
        d=self._load(); d["targets"][target.id]=target.to_dict(); self._save(d); return target
    def list(self):
        return [VisualTarget(id=r["id"],kind=r["kind"],label=r.get("label",r["id"]),bbox=tuple(r["bbox"]),character_id=r.get("character_id",""),object_id=r.get("object_id",""),notes=r.get("notes","")) for r in self._load()["targets"].values()]

def _validate_bbox(b):
    if len(b)!=4: raise ValueError("bbox must contain four normalized values")
    x1,y1,x2,y2=map(float,b)
    if not (0<=x1<x2<=1 and 0<=y1<y2<=1): raise ValueError("bbox must be normalized and ordered")

def _crop(im:Image.Image,b):
    _validate_bbox(b); w,h=im.size; x1,y1,x2,y2=b
    return im.crop((round(x1*w),round(y1*h),round(x2*w),round(y2*h))).convert("RGB").resize((192,192),Image.Resampling.LANCZOS)

def _hash(im,size=16):
    g=im.convert("L").resize((size,size),Image.Resampling.LANCZOS); vals=list(g.get_flattened_data() if hasattr(g, "get_flattened_data") else g.getdata()); avg=sum(vals)/len(vals)
    return tuple(v>=avg for v in vals)

def compare_target_regions(source_frame:Path,candidate_frame:Path,target:VisualTarget)->dict[str,Any]:
    a=_crop(Image.open(source_frame),target.bbox); b=_crop(Image.open(candidate_frame),target.bbox)
    diff=ImageChops.difference(a,b); mae=sum(ImageStat.Stat(diff).mean)/(3*255.0)
    ea=a.convert("L").filter(ImageFilter.FIND_EDGES); eb=b.convert("L").filter(ImageFilter.FIND_EDGES)
    edge=sum(ImageStat.Stat(ImageChops.difference(ea,eb)).mean)/255.0
    ha,hb=_hash(a),_hash(b); percept=1-sum(x!=y for x,y in zip(ha,hb))/len(ha)
    if percept>=.90 and mae<=.14: status="PASS"
    elif percept>=.70 and mae<=.32: status="REVIEW"
    else: status="FAIL"
    return {"target":target.to_dict(),"status":status,"metrics":{"mean_absolute_error":round(mae,6),"edge_error":round(edge,6),"perceptual_similarity":round(percept,6)},"method":"project-bound normalized ROI visual comparison","truth":"This certifies visual consistency of the creator-bound target region, not biometric identity or semantic object recognition."}

def certify_visual_targets(project, *, source_frame:Path, candidate_frame:Path, contract:dict[str,Any]|None=None)->dict[str,Any]:
    targets=VisualTargetStore(project).list(); results=[]
    for t in targets: results.append(compare_target_regions(source_frame,candidate_frame,t))
    failed=[r for r in results if r["status"]=="FAIL"]; review=[r for r in results if r["status"]=="REVIEW"]
    status="FAIL" if failed else "PARTIAL" if review or not results else "PASS"
    return {"version":1,"status":status if results else "NOT_TESTED","targets":results,"failed_target_ids":[r["target"]["id"] for r in failed],"review_target_ids":[r["target"]["id"] for r in review],"truth":"Target-aware continuity uses explicitly registered project regions. Character labels are stable Film Lab project identities; no real-person identification or biometric verification is performed."}
