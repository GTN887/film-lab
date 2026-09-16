"""Automated visual continuity checks for Director A/B candidates.

This module deliberately separates measurable frame drift from semantic claims.
Pixel/perceptual comparison can certify that two sampled frames are globally close;
it cannot by itself prove that a person's identity, wardrobe, or a named prop is the
same. Those semantic domains remain REVIEW_REQUIRED until a specialized visual
model or Creator review supplies evidence.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import math

from PIL import Image, ImageChops, ImageStat, ImageFilter

from film_lab.ffmpeg_support import FFmpegError, run_ffmpeg
from film_lab.production import ProductionStore

_IMAGE_EXTS={".png",".jpg",".jpeg",".webp",".bmp"}

@dataclass(frozen=True)
class FrameMetrics:
    mean_absolute_error: float
    rms_error: float
    edge_error: float
    histogram_similarity: float
    perceptual_similarity: float
    def to_dict(self): return asdict(self)


def _sample_frame(media: Path, dest: Path, seconds: float) -> Path:
    media=Path(media)
    if not media.is_file(): raise FileNotFoundError(f"Media does not exist: {media}")
    dest.parent.mkdir(parents=True,exist_ok=True)
    if media.suffix.lower() in _IMAGE_EXTS:
        Image.open(media).convert("RGB").save(dest,"PNG"); return dest
    run_ffmpeg(["-y","-ss",f"{max(0.0,float(seconds)):.3f}","-i",str(media),"-frames:v","1",str(dest)])
    if not dest.is_file(): raise RuntimeError("Frame extraction produced no image.")
    return dest


def _average_hash(image: Image.Image, size: int=16) -> tuple[int,...]:
    g=image.convert("L").resize((size,size),Image.Resampling.LANCZOS)
    vals=list(g.get_flattened_data() if hasattr(g, "get_flattened_data") else g.getdata()); avg=sum(vals)/len(vals)
    return tuple(1 if v>=avg else 0 for v in vals)


def _metrics(a_path: Path,b_path: Path) -> FrameMetrics:
    a=Image.open(a_path).convert("RGB").resize((256,256),Image.Resampling.LANCZOS)
    b=Image.open(b_path).convert("RGB").resize((256,256),Image.Resampling.LANCZOS)
    diff=ImageChops.difference(a,b)
    stat=ImageStat.Stat(diff)
    mae=sum(stat.mean)/(3*255.0)
    rms=math.sqrt(sum(v*v for v in stat.rms)/3.0)/255.0
    ea=a.convert("L").filter(ImageFilter.FIND_EDGES); eb=b.convert("L").filter(ImageFilter.FIND_EDGES)
    edge=sum(ImageStat.Stat(ImageChops.difference(ea,eb)).mean)/255.0
    ha=a.histogram(); hb=b.histogram(); denom=math.sqrt(sum(x*x for x in ha)*sum(y*y for y in hb))
    hist=(sum(x*y for x,y in zip(ha,hb))/denom) if denom else 1.0
    ah=_average_hash(a); bh=_average_hash(b); ph=1.0-(sum(x!=y for x,y in zip(ah,bh))/len(ah))
    return FrameMetrics(round(mae,6),round(rms,6),round(edge,6),round(hist,6),round(ph,6))


def _global_status(m: FrameMetrics) -> str:
    # Conservative drift gate. A candidate can differ intentionally, so FAIL means
    # "large unreviewed visual drift", not "bad generation".
    if m.perceptual_similarity >= .90 and m.histogram_similarity >= .92 and m.mean_absolute_error <= .12: return "PASS"
    if m.perceptual_similarity >= .72 and m.histogram_similarity >= .78 and m.mean_absolute_error <= .28: return "REVIEW"
    return "FAIL"


def certify_visual_continuity(project, *, source_take_id: str, candidate_take_id: str, contract: dict[str,Any], playhead_s: float=0.0) -> dict[str,Any]:
    store=ProductionStore(project); source=store.get_take(source_take_id); candidate=store.get_take(candidate_take_id)
    root=project.root/"visual_certification"/candidate.id
    src_frame=root/"source.png"; cand_frame=root/"candidate.png"
    try:
        _sample_frame(Path(source.media_path),src_frame,playhead_s)
        _sample_frame(Path(candidate.media_path),cand_frame,playhead_s)
        m=_metrics(src_frame,cand_frame); global_status=_global_status(m)
    except (OSError,ValueError,RuntimeError,FFmpegError) as exc:
        return {"version":1,"status":"NOT_TESTED","source_take_id":source.id,"candidate_take_id":candidate.id,"playhead_s":float(playhead_s),"error":str(exc),"domains":{},"visual_drift":[],"truth":"Visual certification could not sample both media files; no visual continuity claim is made."}

    preserve=contract.get("preserve",{}) if isinstance(contract,dict) else {}
    semantic=[]
    if preserve.get("characters") is not None: semantic += ["character_identity","wardrobe_hair_makeup"]
    if preserve.get("set_id") or preserve.get("location"): semantic.append("set_background")
    if preserve.get("objects") is not None: semantic.append("props_objects")
    if preserve.get("lighting") is not None: semantic.append("lighting")
    domains={
        "global_frame_similarity":{"status":global_status,"method":"pixel + histogram + perceptual-hash comparison"},
        "composition":{"status":global_status,"method":"whole-frame perceptual/edge comparison"},
    }
    for name in dict.fromkeys(semantic):
        domains[name]={"status":"REVIEW_REQUIRED","method":"global frame evidence only","reason":"Semantic sameness is not proven by pixel similarity alone."}
    drift=[]
    if global_status=="FAIL": drift.append({"domain":"global_frame_similarity","severity":"HIGH","message":"Large visual drift detected at the sampled playhead; review locked elements before accepting this Take."})
    elif global_status=="REVIEW": drift.append({"domain":"global_frame_similarity","severity":"MEDIUM","message":"Meaningful visual change detected; Creator or specialized semantic review is required."})
    from film_lab.visual_target_recognition import certify_visual_targets
    target_report=certify_visual_targets(project,source_frame=src_frame,candidate_frame=cand_frame,contract=contract)
    if target_report["status"] != "NOT_TESTED":
        domains["registered_visual_targets"]={"status":target_report["status"],"method":"project-bound target region comparison"}
        for tid in target_report.get("failed_target_ids",[]): drift.append({"domain":"registered_visual_target","target_id":tid,"severity":"HIGH","message":"Registered target region drifted substantially; review before accepting this Take."})
    status="FAIL" if global_status=="FAIL" or target_report["status"]=="FAIL" else "PARTIAL" if semantic or global_status=="REVIEW" or target_report["status"] in {"PARTIAL","NOT_TESTED"} else "PASS"
    return {"version":1,"status":status,"source_take_id":source.id,"candidate_take_id":candidate.id,"playhead_s":float(playhead_s),"source_frame":str(src_frame),"candidate_frame":str(cand_frame),"metrics":m.to_dict(),"domains":domains,"visual_targets":target_report,"visual_drift":drift,"semantic_review_required":list(dict.fromkeys(semantic)),"truth":"PASS/PARTIAL/FAIL here describes automated sampled-frame continuity. Registered project targets add region-specific visual evidence, but biometric identity and semantic sameness remain unclaimed unless separately certified."}


def certify_candidate_take(project, candidate_take_id: str) -> dict[str,Any]:
    store=ProductionStore(project); take=store.get_take(candidate_take_id); meta=take.metadata if isinstance(take.metadata,dict) else {}
    contract=meta.get("continuity_contract") if isinstance(meta.get("continuity_contract"),dict) else {}
    source_id=str(contract.get("source_take_id") or meta.get("ab_source_take_id") or "")
    if not source_id: raise ValueError("Candidate Take has no source Take continuity contract.")
    report=certify_visual_continuity(project,source_take_id=source_id,candidate_take_id=candidate_take_id,contract=contract,playhead_s=float(meta.get("preview_playhead_s") or 0))
    data=store._load(); raw=data["takes"][candidate_take_id]; rm=raw.setdefault("metadata",{})
    rm["visual_continuity_certification"]=report
    continuity=rm.setdefault("continuity_report",{})
    continuity["visual_certification"]=report["status"]
    continuity["visual_drift"]=report.get("visual_drift",[])
    continuity["visual_domains"]=report.get("domains",{})
    store._save(data)
    return report
