"""Intelligent seam blending for localized Film Lab repairs.

Uses short visual crossfades and audio acrossfades around a localized repair window,
then produces explicit boundary evidence. This is media-processing enforcement, not
a claim that the creative/identity continuity is visually perfect.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from film_lab.ffmpeg_support import run_ffmpeg, probe_duration_seconds, probe_has_audio, FFmpegError
from film_lab.production import ProductionStore
from film_lab.visual_continuity_certification import _sample_frame, _metrics
from film_lab.motion_aware_seam_matching import analyze_motion_seams

@dataclass(frozen=True)
class SeamBlendResult:
    source_take_id: str
    repair_take_id: str
    assembled_take_id: str
    window_start_s: float
    window_end_s: float
    blend_duration_s: float
    output_path: str
    visual_blend_status: str
    audio_blend_status: str
    boundary_certification_status: str
    boundary_evidence: dict[str, Any]
    truth: str
    def to_dict(self): return asdict(self)


def _certify_assembled_boundaries(project, source: Path, assembled: Path, start: float, end: float, blend: float):
    root=project.root/"seam_blend_certification"; root.mkdir(parents=True,exist_ok=True)
    checks={}
    # Compare preserved-side frames just outside the transition zones.
    for name,t in (("entry",max(0.0,start-blend)),("exit",end+blend)):
        a=root/f"{name}_source.png"; b=root/f"{name}_assembled.png"
        try:
            _sample_frame(source,a,t); _sample_frame(assembled,b,t)
            m=_metrics(a,b); d=m.to_dict()
            d["status"]="PASS" if m.perceptual_similarity>=.90 and m.histogram_similarity>=.90 else "REVIEW"
            checks[name]=d
        except (OSError,ValueError,RuntimeError,FFmpegError) as exc:
            checks[name]={"status":"NOT_TESTED","error":str(exc)}
    vals=[v.get("status") for v in checks.values()]
    status="REVIEW" if "REVIEW" in vals else "NOT_TESTED" if "NOT_TESTED" in vals else "PASS"
    return {"status":status,"checks":checks,"method":"source-vs-assembled preserved-side frame certification around blended boundaries"}


def reassemble_blended_audio_visual_segment(project, *, source_take_id: str, repair_take_id: str,
                                             window_start_s: float, window_end_s: float,
                                             blend_duration_s: float=.12):
    store=ProductionStore(project); source=store.get_take(source_take_id); repair=store.get_take(repair_take_id)
    src=Path(source.media_path); rep=Path(repair.media_path)
    if not src.is_file() or not rep.is_file(): raise FileNotFoundError("Source and repair Take media must exist.")
    if probe_has_audio(src) is not True or probe_has_audio(rep) is not True:
        raise ValueError("Intelligent A/V seam blending requires proven audio streams in both source and repair Takes.")
    duration=probe_duration_seconds(src) or source.duration
    if duration is None: raise ValueError("Source Take duration is required for seam blending.")
    start=max(0.0,float(window_start_s)); end=min(float(duration),float(window_end_s))
    if end<=start: raise ValueError("Repair window end must be after its start.")
    # Keep blend safely inside available media and avoid pathological windows.
    max_blend=max(0.0,min(start,float(duration)-end,(end-start)/4.0,.5))
    requested_blend=max(0.0,float(blend_duration_s))
    motion_plan=analyze_motion_seams(project,src,rep,window_start_s=start,window_end_s=end,requested_blend_s=requested_blend)
    blend=min(motion_plan.recommended_blend_s,max_blend)
    if blend < .01: raise ValueError("Repair window does not leave enough surrounding media for seam blending.")
    xdur=2.0*blend
    p_end=start+blend; r_start=start-blend; r_end=end+blend; s_start=end-blend
    first_offset=start-blend; second_offset=end-blend
    out_dir=project.takes_dir/source.scene_id/source.shot_id; out_dir.mkdir(parents=True,exist_ok=True)
    temp=out_dir/f"seam_blended_{repair.id}.mp4"
    fc=(
      f"[0:v]trim=start=0:end={p_end:.6f},setpts=PTS-STARTPTS[v0];"
      f"[1:v]trim=start={r_start:.6f}:end={r_end:.6f},setpts=PTS-STARTPTS[v1];"
      f"[0:v]trim=start={s_start:.6f}:end={float(duration):.6f},setpts=PTS-STARTPTS[v2];"
      f"[v0][v1]xfade=transition=fade:duration={xdur:.6f}:offset={first_offset:.6f}[vx];"
      f"[vx][v2]xfade=transition=fade:duration={xdur:.6f}:offset={second_offset:.6f}[v];"
      f"[0:a]atrim=start=0:end={p_end:.6f},asetpts=PTS-STARTPTS[a0];"
      f"[1:a]atrim=start={r_start:.6f}:end={r_end:.6f},asetpts=PTS-STARTPTS[a1];"
      f"[0:a]atrim=start={s_start:.6f}:end={float(duration):.6f},asetpts=PTS-STARTPTS[a2];"
      f"[a0][a1]acrossfade=d={xdur:.6f}:c1=tri:c2=tri[ax];"
      f"[ax][a2]acrossfade=d={xdur:.6f}:c1=tri:c2=tri[a]"
    )
    run_ffmpeg(["-y","-i",str(src),"-i",str(rep),"-filter_complex",fc,"-map","[v]","-map","[a]","-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac",str(temp)])
    if not temp.is_file(): raise RuntimeError("Seam blending produced no output video.")
    evidence=_certify_assembled_boundaries(project,src,temp,start,end,blend)
    truth="FFmpeg xfade/acrossfade blending was applied around both localized repair boundaries. Automated frame evidence does not prove semantic identity or audible perfection."
    meta={"intelligent_seam_blending":{"source_take_id":source.id,"repair_take_id":repair.id,"window_start_s":start,"window_end_s":end,"blend_duration_s":blend,"visual_blend_status":"ENFORCED","audio_blend_status":"ENFORCED","boundary_certification_status":evidence["status"],"boundary_evidence":evidence,"motion_seam_matching":motion_plan.to_dict(),"truth":truth}}
    assembled=store.add_take(temp,shot_id=source.shot_id,scene_id=source.scene_id,name=f"Seam-blended repair of {source.name or source.id}",generator="Film Lab Intelligent Seam Blending",duration=duration,metadata=meta)
    try: temp.unlink()
    except OSError: pass
    data=store._load(); data["takes"][assembled.id]["metadata"]["intelligent_seam_blending"]["assembled_take_id"]=assembled.id; store._save(data)
    result=SeamBlendResult(source.id,repair.id,assembled.id,start,end,blend,assembled.media_path,"ENFORCED","ENFORCED",evidence["status"],{**evidence,"motion_seam_matching":motion_plan.to_dict()},truth)
    return store.get_take(assembled.id),result


def reassemble_blended_from_repair_plan(project, repair_take_id: str, blend_duration_s: float=.12):
    from film_lab.continuity_problem_repair import RepairPlanStore
    plan=RepairPlanStore(project).load()
    if plan is None: raise ValueError("No localized continuity repair plan is ready.")
    return reassemble_blended_audio_visual_segment(project,source_take_id=plan.candidate_take_id,repair_take_id=repair_take_id,window_start_s=plan.window_start_s,window_end_s=plan.window_end_s,blend_duration_s=blend_duration_s)


def reassemble_motion_aligned_blended_audio_visual_segment(project, *, source_take_id: str, repair_take_id: str,
                                                            window_start_s: float, window_end_s: float,
                                                            blend_duration_s: float=.12):
    """Retiming-aware seam repair: align repair boundary states, retime, then blend.

    The output timeline remains the source Take duration. Extreme retimes are rejected
    instead of being silently applied.
    """
    from film_lab.motion_retiming_transition_alignment import analyze_motion_retiming
    store=ProductionStore(project); source=store.get_take(source_take_id); repair=store.get_take(repair_take_id)
    src=Path(source.media_path); rep=Path(repair.media_path)
    if not src.is_file() or not rep.is_file(): raise FileNotFoundError("Source and repair Take media must exist.")
    if probe_has_audio(src) is not True or probe_has_audio(rep) is not True:
        raise ValueError("Motion-aligned A/V repair requires proven audio streams in both source and repair Takes.")
    duration=probe_duration_seconds(src) or source.duration; rep_duration=probe_duration_seconds(rep) or repair.duration
    if duration is None or rep_duration is None: raise ValueError("Source and repair Take durations are required for motion retiming.")
    start=max(0.0,float(window_start_s)); end=min(float(duration),float(window_end_s))
    if end<=start: raise ValueError("Repair window end must be after its start.")
    retime=analyze_motion_retiming(project,src,rep,window_start_s=start,window_end_s=end,repair_duration_s=float(rep_duration))
    if retime.enforcement != "AVAILABLE":
        raise ValueError(f"Motion retiming is not safe to apply: {retime.status} / {retime.enforcement}.")
    motion_plan=analyze_motion_seams(project,src,rep,window_start_s=start,window_end_s=end,requested_blend_s=float(blend_duration_s))
    max_blend=max(0.0,min(start,float(duration)-end,retime.repair_input_start_s,float(rep_duration)-retime.repair_input_end_s,(end-start)/4.0,.5))
    blend=min(motion_plan.recommended_blend_s,max_blend)
    if blend < .01: raise ValueError("Repair window does not leave enough surrounding media for motion-aligned seam blending.")
    xdur=2.0*blend
    p_end=start+blend; s_start=end-blend
    r_start=retime.repair_input_start_s-blend; r_end=retime.repair_input_end_s+blend
    target_span=(end-start)+2*blend; input_span=r_end-r_start; speed=input_span/target_span
    if not (.5 <= speed <= 2.0): raise ValueError("Required audio/video retime exceeds safe FFmpeg alignment limits.")
    first_offset=start-blend; second_offset=end-blend
    out_dir=project.takes_dir/source.scene_id/source.shot_id; out_dir.mkdir(parents=True,exist_ok=True)
    temp=out_dir/f"motion_aligned_{repair.id}.mp4"
    fc=(
      f"[0:v]trim=start=0:end={p_end:.6f},setpts=PTS-STARTPTS[v0];"
      f"[1:v]trim=start={r_start:.6f}:end={r_end:.6f},setpts=(PTS-STARTPTS)/{speed:.9f}[v1];"
      f"[0:v]trim=start={s_start:.6f}:end={float(duration):.6f},setpts=PTS-STARTPTS[v2];"
      f"[v0][v1]xfade=transition=fade:duration={xdur:.6f}:offset={first_offset:.6f}[vx];"
      f"[vx][v2]xfade=transition=fade:duration={xdur:.6f}:offset={second_offset:.6f}[v];"
      f"[0:a]atrim=start=0:end={p_end:.6f},asetpts=PTS-STARTPTS[a0];"
      f"[1:a]atrim=start={r_start:.6f}:end={r_end:.6f},asetpts=PTS-STARTPTS,atempo={speed:.9f}[a1];"
      f"[0:a]atrim=start={s_start:.6f}:end={float(duration):.6f},asetpts=PTS-STARTPTS[a2];"
      f"[a0][a1]acrossfade=d={xdur:.6f}:c1=tri:c2=tri[ax];"
      f"[ax][a2]acrossfade=d={xdur:.6f}:c1=tri:c2=tri[a]"
    )
    run_ffmpeg(["-y","-i",str(src),"-i",str(rep),"-filter_complex",fc,"-map","[v]","-map","[a]","-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac",str(temp)])
    if not temp.is_file(): raise RuntimeError("Motion-aligned seam repair produced no output video.")
    evidence=_certify_assembled_boundaries(project,src,temp,start,end,blend)
    truth=("FFmpeg applied an evidence-derived affine time map to the localized repair, then xfade/acrossfade at both boundaries while preserving final Take duration. "
           "This is real temporal retiming/alignment, not optical-flow interpolation; semantic identity and perceived motion quality still require visual acceptance.")
    meta={"motion_retiming_transition_alignment":{"source_take_id":source.id,"repair_take_id":repair.id,"window_start_s":start,"window_end_s":end,"blend_duration_s":blend,"retiming_status":"ENFORCED","retiming_plan":retime.to_dict(),"applied_speed_factor":round(speed,6),"motion_seam_matching":motion_plan.to_dict(),"boundary_certification_status":evidence["status"],"boundary_evidence":evidence,"truth":truth}}
    assembled=store.add_take(temp,shot_id=source.shot_id,scene_id=source.scene_id,name=f"Motion-aligned repair of {source.name or source.id}",generator="Film Lab Motion Retiming & Transition Alignment",duration=duration,metadata=meta)
    try: temp.unlink()
    except OSError: pass
    data=store._load(); data["takes"][assembled.id]["metadata"]["motion_retiming_transition_alignment"]["assembled_take_id"]=assembled.id; store._save(data)
    return store.get_take(assembled.id), meta["motion_retiming_transition_alignment"]


def reassemble_motion_aligned_from_repair_plan(project, repair_take_id: str, blend_duration_s: float=.12):
    from film_lab.continuity_problem_repair import RepairPlanStore
    plan=RepairPlanStore(project).load()
    if plan is None: raise ValueError("No localized continuity repair plan is ready.")
    return reassemble_motion_aligned_blended_audio_visual_segment(project,source_take_id=plan.candidate_take_id,repair_take_id=repair_take_id,window_start_s=plan.window_start_s,window_end_s=plan.window_end_s,blend_duration_s=blend_duration_s)



def reassemble_optical_flow_aligned_audio_visual_segment(project, *, source_take_id: str, repair_take_id: str,
                                                           window_start_s: float, window_end_s: float,
                                                           blend_duration_s: float=.10, interpolation_fps: float=60.0):
    """Retiming + FFmpeg motion-compensated interpolation + seam blending.

    This is only ENFORCED after capability discovery and successful FFmpeg output.
    The original/source Take is never overwritten.
    """
    from film_lab.motion_retiming_transition_alignment import analyze_motion_retiming
    from film_lab.optical_flow_transition_alignment import inspect_optical_flow_capability, minterpolate_filter
    capability=inspect_optical_flow_capability()
    if capability.enforcement != "AVAILABLE":
        raise ValueError(f"Optical-flow interpolation is unavailable: {capability.evidence}")
    store=ProductionStore(project); source=store.get_take(source_take_id); repair=store.get_take(repair_take_id)
    src=Path(source.media_path); rep=Path(repair.media_path)
    if not src.is_file() or not rep.is_file(): raise FileNotFoundError("Source and repair Take media must exist.")
    if probe_has_audio(src) is not True or probe_has_audio(rep) is not True:
        raise ValueError("Optical-flow A/V repair requires proven audio streams in both source and repair Takes.")
    duration=probe_duration_seconds(src) or source.duration; rep_duration=probe_duration_seconds(rep) or repair.duration
    if duration is None or rep_duration is None: raise ValueError("Source and repair Take durations are required.")
    start=max(0.0,float(window_start_s)); end=min(float(duration),float(window_end_s))
    if end<=start: raise ValueError("Repair window end must be after its start.")
    retime=analyze_motion_retiming(project,src,rep,window_start_s=start,window_end_s=end,repair_duration_s=float(rep_duration))
    if retime.enforcement != "AVAILABLE": raise ValueError(f"Motion retiming is not safe to apply: {retime.status} / {retime.enforcement}.")
    motion_plan=analyze_motion_seams(project,src,rep,window_start_s=start,window_end_s=end,requested_blend_s=float(blend_duration_s))
    max_blend=max(0.0,min(start,float(duration)-end,retime.repair_input_start_s,float(rep_duration)-retime.repair_input_end_s,(end-start)/4.0,.4))
    blend=min(motion_plan.recommended_blend_s,max_blend)
    if blend < .01: raise ValueError("Repair window does not leave enough surrounding media for optical-flow seam blending.")
    xdur=2.0*blend; p_end=start+blend; s_start=end-blend
    r_start=retime.repair_input_start_s-blend; r_end=retime.repair_input_end_s+blend
    target_span=(end-start)+2*blend; input_span=r_end-r_start; speed=input_span/target_span
    if not (.5 <= speed <= 2.0): raise ValueError("Required retime exceeds safe FFmpeg alignment limits.")
    first_offset=start-blend; second_offset=end-blend
    flow=minterpolate_filter(interpolation_fps)
    out_dir=project.takes_dir/source.scene_id/source.shot_id; out_dir.mkdir(parents=True,exist_ok=True)
    temp=out_dir/f"optical_flow_aligned_{repair.id}.mp4"
    fc=(
      f"[0:v]trim=start=0:end={p_end:.6f},setpts=PTS-STARTPTS[v0];"
      f"[1:v]trim=start={r_start:.6f}:end={r_end:.6f},setpts=(PTS-STARTPTS)/{speed:.9f},{flow}[v1];"
      f"[0:v]trim=start={s_start:.6f}:end={float(duration):.6f},setpts=PTS-STARTPTS[v2];"
      f"[v0][v1]xfade=transition=fade:duration={xdur:.6f}:offset={first_offset:.6f}[vx];"
      f"[vx][v2]xfade=transition=fade:duration={xdur:.6f}:offset={second_offset:.6f}[v];"
      f"[0:a]atrim=start=0:end={p_end:.6f},asetpts=PTS-STARTPTS[a0];"
      f"[1:a]atrim=start={r_start:.6f}:end={r_end:.6f},asetpts=PTS-STARTPTS,atempo={speed:.9f}[a1];"
      f"[0:a]atrim=start={s_start:.6f}:end={float(duration):.6f},asetpts=PTS-STARTPTS[a2];"
      f"[a0][a1]acrossfade=d={xdur:.6f}:c1=tri:c2=tri[ax];"
      f"[ax][a2]acrossfade=d={xdur:.6f}:c1=tri:c2=tri[a]"
    )
    run_ffmpeg(["-y","-i",str(src),"-i",str(rep),"-filter_complex",fc,"-map","[v]","-map","[a]","-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac",str(temp)])
    if not temp.is_file(): raise RuntimeError("Optical-flow reconstruction produced no output video.")
    evidence=_certify_assembled_boundaries(project,src,temp,start,end,blend)
    truth=("FFmpeg minterpolate motion-compensated interpolation was actually executed on the retimed localized repair, followed by visual/audio seam blending. "
           "This is real optical-flow interpolation; it does not prove semantic identity, anatomical correctness, or perceived motion quality without visual acceptance.")
    meta={"optical_flow_transition_alignment":{"source_take_id":source.id,"repair_take_id":repair.id,"window_start_s":start,"window_end_s":end,"blend_duration_s":blend,"interpolation_fps":float(interpolation_fps),"optical_flow_status":"ENFORCED","capability":capability.to_dict(),"retiming_plan":retime.to_dict(),"applied_speed_factor":round(speed,6),"motion_seam_matching":motion_plan.to_dict(),"boundary_certification_status":evidence["status"],"boundary_evidence":evidence,"truth":truth}}
    assembled=store.add_take(temp,shot_id=source.shot_id,scene_id=source.scene_id,name=f"Optical-flow repair of {source.name or source.id}",generator="Film Lab Optical-Flow Transition Alignment",duration=duration,metadata=meta)
    try: temp.unlink()
    except OSError: pass
    data=store._load(); data["takes"][assembled.id]["metadata"]["optical_flow_transition_alignment"]["assembled_take_id"]=assembled.id; store._save(data)
    return store.get_take(assembled.id), meta["optical_flow_transition_alignment"]


def reassemble_optical_flow_from_repair_plan(project, repair_take_id: str, blend_duration_s: float=.10, interpolation_fps: float=60.0):
    from film_lab.continuity_problem_repair import RepairPlanStore
    plan=RepairPlanStore(project).load()
    if plan is None: raise ValueError("No localized continuity repair plan is ready.")
    return reassemble_optical_flow_aligned_audio_visual_segment(project,source_take_id=plan.candidate_take_id,repair_take_id=repair_take_id,window_start_s=plan.window_start_s,window_end_s=plan.window_end_s,blend_duration_s=blend_duration_s,interpolation_fps=interpolation_fps)
