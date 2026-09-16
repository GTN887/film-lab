"""Temporal segment repair and seamless reassembly.

Replaces only a localized visual time window in a Take with frames from a repair
candidate. Source video before/after the window is preserved. Source audio is
preserved unchanged until an audio-aware segment renderer is explicitly wired.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json

from film_lab.ffmpeg_support import run_ffmpeg, probe_duration_seconds, probe_has_audio, FFmpegError
from film_lab.production import ProductionStore
from film_lab.visual_continuity_certification import _sample_frame, _metrics

@dataclass(frozen=True)
class SegmentRepairResult:
    source_take_id: str
    repair_take_id: str
    assembled_take_id: str
    window_start_s: float
    window_end_s: float
    output_path: str
    boundary_status: str
    boundary_evidence: dict[str, Any]
    video_patch_status: str = "ENFORCED"
    audio_patch_status: str = "SOURCE_AUDIO_PRESERVED"
    truth: str = "Only the localized visual window is replaced. Source video outside it and source audio are preserved."
    def to_dict(self): return asdict(self)


def _boundary_evidence(project, source: Path, repair: Path, start: float, end: float) -> dict[str, Any]:
    root=project.root/"segment_repair_boundary"
    root.mkdir(parents=True,exist_ok=True)
    checks={}
    for name,t in (("entry",start),("exit",end)):
        a=root/f"{name}_source.png"; b=root/f"{name}_repair.png"
        try:
            _sample_frame(source,a,max(0.0,t)); _sample_frame(repair,b,max(0.0,t))
            m=_metrics(a,b); d=m.to_dict()
            # A seam can still be intentional; this is a conservative risk signal.
            d["status"]="PASS" if m.perceptual_similarity>=.82 and m.histogram_similarity>=.82 else "REVIEW"
            checks[name]=d
        except (OSError,ValueError,RuntimeError,FFmpegError) as exc:
            checks[name]={"status":"NOT_TESTED","error":str(exc)}
    vals=[x.get("status") for x in checks.values()]
    status="REVIEW" if "REVIEW" in vals else "NOT_TESTED" if "NOT_TESTED" in vals else "PASS"
    return {"status":status,"checks":checks,"method":"source-vs-repair frame comparison at segment boundaries"}


def reassemble_visual_segment(project, *, source_take_id: str, repair_take_id: str,
                              window_start_s: float, window_end_s: float) -> tuple[Any, SegmentRepairResult]:
    store=ProductionStore(project); source=store.get_take(source_take_id); repair=store.get_take(repair_take_id)
    src=Path(source.media_path); rep=Path(repair.media_path)
    if not src.is_file() or not rep.is_file(): raise FileNotFoundError("Source and repair Take media must exist.")
    start=max(0.0,float(window_start_s)); end=float(window_end_s)
    duration=probe_duration_seconds(src) or source.duration
    if duration is not None: end=min(float(duration),end)
    if end <= start: raise ValueError("Repair window end must be after its start.")
    out_dir=project.takes_dir/source.scene_id/source.shot_id; out_dir.mkdir(parents=True,exist_ok=True)
    temp=out_dir/f"segment_reassembled_{repair.id}.mp4"
    # Three visual sections: untouched source prefix, repair window, untouched source suffix.
    # Audio deliberately remains the original source track; no false audio-repair claim.
    fc=(f"[0:v]trim=start=0:end={start:.6f},setpts=PTS-STARTPTS[v0];"
        f"[1:v]trim=start={start:.6f}:end={end:.6f},setpts=PTS-STARTPTS[v1];"
        f"[0:v]trim=start={end:.6f},setpts=PTS-STARTPTS[v2];"
        f"[v0][v1][v2]concat=n=3:v=1:a=0[v]")
    run_ffmpeg(["-y","-i",str(src),"-i",str(rep),"-filter_complex",fc,"-map","[v]","-map","0:a?","-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac","-shortest",str(temp)])
    if not temp.is_file(): raise RuntimeError("Temporal segment reassembly produced no output video.")
    boundary=_boundary_evidence(project,src,rep,start,end)
    meta={"temporal_segment_repair":{"source_take_id":source.id,"repair_take_id":repair.id,"window_start_s":start,"window_end_s":end,"boundary_status":boundary["status"],"boundary_evidence":boundary,"video_patch_status":"ENFORCED","audio_patch_status":"SOURCE_AUDIO_PRESERVED","truth":"FFmpeg replaced only the localized visual segment. Audio remains from the source Take."}}
    assembled=store.add_take(temp,shot_id=source.shot_id,scene_id=source.scene_id,name=f"Segment repair of {source.name or source.id}",generator="Film Lab Temporal Reassembly",duration=duration,metadata=meta)
    try: temp.unlink()
    except OSError: pass
    result=SegmentRepairResult(source.id,repair.id,assembled.id,start,end,assembled.media_path,boundary["status"],boundary)
    data=store._load(); data["takes"][assembled.id]["metadata"]["temporal_segment_repair"]["assembled_take_id"]=assembled.id; store._save(data)
    return store.get_take(assembled.id),result



def reassemble_audio_visual_segment(project, *, source_take_id: str, repair_take_id: str,
                                    window_start_s: float, window_end_s: float) -> tuple[Any, SegmentRepairResult]:
    """Replace the localized video *and* audio window when repair audio is proven present.

    This is intentionally separate from reassemble_visual_segment: absence or unknown
    repair audio never silently falls back to an ENFORCED audio-repair claim.
    """
    store=ProductionStore(project); source=store.get_take(source_take_id); repair=store.get_take(repair_take_id)
    src=Path(source.media_path); rep=Path(repair.media_path)
    if not src.is_file() or not rep.is_file(): raise FileNotFoundError("Source and repair Take media must exist.")
    src_audio=probe_has_audio(src); rep_audio=probe_has_audio(rep)
    if src_audio is not True or rep_audio is not True:
        raise ValueError("Localized audio repair requires proven audio streams in both source and repair Takes.")
    start=max(0.0,float(window_start_s)); end=float(window_end_s)
    duration=probe_duration_seconds(src) or source.duration
    if duration is not None: end=min(float(duration),end)
    if end <= start: raise ValueError("Repair window end must be after its start.")
    out_dir=project.takes_dir/source.scene_id/source.shot_id; out_dir.mkdir(parents=True,exist_ok=True)
    temp=out_dir/f"segment_av_reassembled_{repair.id}.mp4"
    fc=(f"[0:v]trim=start=0:end={start:.6f},setpts=PTS-STARTPTS[v0];"
        f"[1:v]trim=start={start:.6f}:end={end:.6f},setpts=PTS-STARTPTS[v1];"
        f"[0:v]trim=start={end:.6f},setpts=PTS-STARTPTS[v2];"
        f"[v0][v1][v2]concat=n=3:v=1:a=0[v];"
        f"[0:a]atrim=start=0:end={start:.6f},asetpts=PTS-STARTPTS[a0];"
        f"[1:a]atrim=start={start:.6f}:end={end:.6f},asetpts=PTS-STARTPTS[a1];"
        f"[0:a]atrim=start={end:.6f},asetpts=PTS-STARTPTS[a2];"
        f"[a0][a1][a2]concat=n=3:v=0:a=1[a]")
    run_ffmpeg(["-y","-i",str(src),"-i",str(rep),"-filter_complex",fc,"-map","[v]","-map","[a]","-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac",str(temp)])
    if not temp.is_file(): raise RuntimeError("Temporal audio/video segment reassembly produced no output video.")
    boundary=_boundary_evidence(project,src,rep,start,end)
    meta={"temporal_segment_repair":{"source_take_id":source.id,"repair_take_id":repair.id,"window_start_s":start,"window_end_s":end,"boundary_status":boundary["status"],"boundary_evidence":boundary,"video_patch_status":"ENFORCED","audio_patch_status":"ENFORCED","audio_evidence":{"source_audio":True,"repair_audio":True,"method":"ffprobe audio stream presence + FFmpeg atrim/concat"},"truth":"FFmpeg replaced only the localized video and audio segment using proven source and repair audio streams."}}
    assembled=store.add_take(temp,shot_id=source.shot_id,scene_id=source.scene_id,name=f"A/V segment repair of {source.name or source.id}",generator="Film Lab Temporal A/V Reassembly",duration=duration,metadata=meta)
    try: temp.unlink()
    except OSError: pass
    result=SegmentRepairResult(source.id,repair.id,assembled.id,start,end,assembled.media_path,boundary["status"],boundary,audio_patch_status="ENFORCED",truth="Only the localized video/audio window is replaced; source media outside it is preserved.")
    data=store._load(); data["takes"][assembled.id]["metadata"]["temporal_segment_repair"]["assembled_take_id"]=assembled.id; store._save(data)
    return store.get_take(assembled.id),result


def reassemble_audio_visual_from_repair_plan(project, repair_take_id: str):
    from film_lab.continuity_problem_repair import RepairPlanStore
    plan=RepairPlanStore(project).load()
    if plan is None: raise ValueError("No localized continuity repair plan is ready.")
    return reassemble_audio_visual_segment(project,source_take_id=plan.candidate_take_id,repair_take_id=repair_take_id,window_start_s=plan.window_start_s,window_end_s=plan.window_end_s)

def reassemble_from_repair_plan(project, repair_take_id: str):
    from film_lab.continuity_problem_repair import RepairPlanStore
    plan=RepairPlanStore(project).load()
    if plan is None: raise ValueError("No localized continuity repair plan is ready.")
    return reassemble_visual_segment(project,source_take_id=plan.candidate_take_id,repair_take_id=repair_take_id,window_start_s=plan.window_start_s,window_end_s=plan.window_end_s)
