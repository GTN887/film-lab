"""Full-Take Continuity Scanning.

Samples an entire source/candidate Take, measures visual drift over time, and (when
Creator-registered targets exist) follows those targets across the sampled frames.
The scanner reports *where* continuity risk occurs. Tracking and visual similarity
are evidence only; neither is biometric identity certification.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
import json, math, shutil
from PIL import Image

from film_lab.ffmpeg_support import FFmpegError, probe_duration_seconds, run_ffmpeg
from film_lab.production import ProductionStore
from film_lab.visual_continuity_certification import _metrics, _global_status
from film_lab.visual_target_recognition import VisualTargetStore
from film_lab.visual_target_tracking import track_target_frames, compare_tracks

_IMAGE_EXTS={".png",".jpg",".jpeg",".webp",".bmp"}

def _times(duration: float, sample_count: int) -> list[float]:
    n=max(2,int(sample_count)); d=max(0.0,float(duration))
    if d<=0: return [0.0]
    # Avoid exact EOF, where some codecs return no frame.
    end=max(0.0,d-.001)
    return [round(end*i/(n-1),6) for i in range(n)]

def _extract_samples(media: Path, out_dir: Path, *, sample_count: int=9, duration: float|None=None) -> tuple[list[Path],list[float]]:
    media=Path(media); out_dir.mkdir(parents=True,exist_ok=True)
    if not media.is_file(): raise FileNotFoundError(f"Media does not exist: {media}")
    if media.suffix.lower() in _IMAGE_EXTS:
        p=out_dir/"000.png"; Image.open(media).convert("RGB").save(p,"PNG"); return [p],[0.0]
    d=float(duration) if duration is not None else probe_duration_seconds(media)
    if not d or d<=0: raise RuntimeError("Could not determine Take duration for full-Take continuity scan.")
    paths=[]; ts=_times(d,sample_count)
    for i,t in enumerate(ts):
        p=out_dir/f"{i:03d}.png"
        run_ffmpeg(["-y","-ss",f"{t:.3f}","-i",str(media),"-frames:v","1",str(p)])
        if not p.is_file(): raise RuntimeError(f"No frame extracted at {t:.3f}s")
        paths.append(p)
    return paths,ts

def scan_frame_sequences(project, *, source_frames:list[Path], candidate_frames:list[Path], times_s:list[float]|None=None, contract:dict[str,Any]|None=None) -> dict[str,Any]:
    n=min(len(source_frames),len(candidate_frames))
    if n==0: return {"version":1,"status":"NOT_TESTED","samples":[],"events":[],"truth":"No paired frames were available; no full-Take continuity claim is made."}
    times=list(times_s or [float(i) for i in range(n)])[:n]
    if len(times)<n: times += [float(i) for i in range(len(times),n)]
    samples=[]; events=[]
    for i,(a,b) in enumerate(zip(source_frames[:n],candidate_frames[:n])):
        m=_metrics(Path(a),Path(b)); st=_global_status(m)
        row={"sample_index":i,"time_s":float(times[i]),"status":st,"metrics":m.to_dict()}; samples.append(row)
        if st in {"REVIEW","FAIL"}:
            events.append({"time_s":float(times[i]),"domain":"global_frame_similarity","severity":"HIGH" if st=="FAIL" else "MEDIUM","status":st,"message":"Unexpected visual drift detected in sampled Take frame."})
    target_reports=[]
    for target in VisualTargetStore(project).list():
        src=track_target_frames(target,source_frames[:n],fps=1.0)
        cand=track_target_frames(target,candidate_frames[:n],fps=1.0)
        cmp=compare_tracks(src,cand)
        lost_src=[times[i] for i,p in enumerate(src.points[:n]) if p.status=="LOST"]
        lost_cand=[times[i] for i,p in enumerate(cand.points[:n]) if p.status=="LOST"]
        target_reports.append({"target":target.to_dict(),"source_track":src.to_dict(),"candidate_track":cand.to_dict(),"comparison":cmp,"candidate_lost_times_s":lost_cand})
        for t in lost_cand:
            events.append({"time_s":float(t),"domain":"registered_visual_target","target_id":target.id,"severity":"HIGH","status":"LOST","message":f"Registered target '{target.label}' was lost in candidate tracking."})
        if cmp["status"] in {"REVIEW","FAIL"}:
            events.append({"time_s":None,"domain":"target_position_track","target_id":target.id,"severity":"HIGH" if cmp["status"]=="FAIL" else "MEDIUM","status":cmp["status"],"message":f"Registered target '{target.label}' has unexpected source/candidate position-track drift."})
    fail=any(e["severity"]=="HIGH" for e in events)
    review=any(e["severity"]=="MEDIUM" for e in events)
    status="FAIL" if fail else "PARTIAL" if review else "PASS"
    return {"version":1,"status":status,"sample_count":n,"samples":samples,"events":sorted(events,key=lambda e:(e["time_s"] is None,e["time_s"] or 0)),"targets":target_reports,"contract":contract or {},"truth":"Full-Take scanning samples temporal visual continuity and Creator-bound target tracks. It does not prove biometric identity, semantic sameness, or inspect unsampled frames."}

def scan_take_continuity(project, *, source_take_id:str, candidate_take_id:str, contract:dict[str,Any]|None=None, sample_count:int=9) -> dict[str,Any]:
    store=ProductionStore(project); src=store.get_take(source_take_id); cand=store.get_take(candidate_take_id)
    root=project.root/"full_take_continuity"/candidate_take_id
    try:
        sd=probe_duration_seconds(Path(src.media_path)); cd=probe_duration_seconds(Path(cand.media_path))
        duration=min(x for x in (sd,cd) if x is not None) if any(x is not None for x in (sd,cd)) else None
        sframes,ts=_extract_samples(Path(src.media_path),root/"source",sample_count=sample_count,duration=duration)
        cframes,_=_extract_samples(Path(cand.media_path),root/"candidate",sample_count=len(ts),duration=duration)
        report=scan_frame_sequences(project,source_frames=sframes,candidate_frames=cframes,times_s=ts,contract=contract)
        report.update({"source_take_id":src.id,"candidate_take_id":cand.id,"duration_s":duration})
    except (OSError,ValueError,RuntimeError,FFmpegError) as exc:
        report={"version":1,"status":"NOT_TESTED","source_take_id":src.id,"candidate_take_id":cand.id,"error":str(exc),"events":[],"truth":"Full-Take media sampling could not run; no temporal continuity claim is made."}
    return report

def scan_candidate_take(project, candidate_take_id:str, *, sample_count:int=9) -> dict[str,Any]:
    store=ProductionStore(project); take=store.get_take(candidate_take_id); meta=take.metadata if isinstance(take.metadata,dict) else {}
    contract=meta.get("continuity_contract") if isinstance(meta.get("continuity_contract"),dict) else {}
    source_id=str(contract.get("source_take_id") or meta.get("ab_source_take_id") or "")
    if not source_id: raise ValueError("Candidate Take has no source Take continuity contract.")
    report=scan_take_continuity(project,source_take_id=source_id,candidate_take_id=candidate_take_id,contract=contract,sample_count=sample_count)
    data=store._load(); rm=data["takes"][candidate_take_id].setdefault("metadata",{}); rm["full_take_continuity_scan"]=report
    cr=rm.setdefault("continuity_report",{}); cr["full_take_scan"]=report["status"]; cr["full_take_events"]=report.get("events",[])
    store._save(data); return report
