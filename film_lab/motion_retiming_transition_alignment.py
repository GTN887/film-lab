"""Motion retiming and transition alignment for localized repair Takes.

Finds source/repair temporal offsets around both repair boundaries using deterministic
frame evidence. The resulting affine time map can be applied by FFmpeg so the repair
arrives at the boundary motion state earlier/later without changing the final Take length.
This is temporal alignment, not optical-flow interpolation.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from film_lab.ffmpeg_support import FFmpegError
from film_lab.visual_continuity_certification import _sample_frame, _metrics

@dataclass(frozen=True)
class BoundaryAlignment:
    boundary: str
    source_time_s: float
    repair_time_s: float
    offset_s: float
    similarity: float
    status: str
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class MotionRetimingPlan:
    window_start_s: float
    window_end_s: float
    repair_input_start_s: float
    repair_input_end_s: float
    speed_factor: float
    entry: BoundaryAlignment | None
    exit: BoundaryAlignment | None
    status: str
    enforcement: str
    truth: str
    def to_dict(self): return asdict(self)


def _score(a: Path, b: Path) -> float:
    m=_metrics(a,b)
    return float((m.perceptual_similarity*0.7)+(m.histogram_similarity*0.3))


def _align_boundary(project, source: Path, repair: Path, name: str, source_t: float,
                    *, search_radius_s: float=.30, step_s: float=.05, repair_duration_s: float|None=None) -> BoundaryAlignment:
    root=project.root/"motion_retiming_evidence"; root.mkdir(parents=True,exist_ok=True)
    sf=root/f"{name}_source.png"; _sample_frame(source,sf,max(0.0,source_t))
    best_t=max(0.0,source_t); best=-1.0
    steps=max(1,int(round(search_radius_s/step_s)))
    for i in range(-steps,steps+1):
        t=max(0.0,source_t+i*step_s)
        if repair_duration_s is not None: t=min(max(0.0,repair_duration_s-.001),t)
        rf=root/f"{name}_repair_{i+steps:02d}.png"
        _sample_frame(repair,rf,t)
        score=_score(sf,rf)
        if score>best: best=score; best_t=t
    offset=best_t-source_t
    status="PASS" if best>=.88 else "REVIEW" if best>=.72 else "FAIL"
    return BoundaryAlignment(name,round(source_t,6),round(best_t,6),round(offset,6),round(best,6),status)


def analyze_motion_retiming(project, source: Path, repair: Path, *, window_start_s: float, window_end_s: float,
                            repair_duration_s: float|None=None, search_radius_s: float=.30, step_s: float=.05) -> MotionRetimingPlan:
    start=float(window_start_s); end=float(window_end_s)
    try:
        entry=_align_boundary(project,source,repair,"entry",start,search_radius_s=search_radius_s,step_s=step_s,repair_duration_s=repair_duration_s)
        exit=_align_boundary(project,source,repair,"exit",end,search_radius_s=search_radius_s,step_s=step_s,repair_duration_s=repair_duration_s)
    except (OSError,ValueError,RuntimeError,FFmpegError) as exc:
        return MotionRetimingPlan(start,end,start,end,1.0,None,None,"NOT_TESTED","NOT_ENFORCED",f"Temporal alignment evidence unavailable: {exc}")
    rin=max(0.0,entry.repair_time_s); rout=max(rin+.001,exit.repair_time_s)
    if repair_duration_s is not None: rout=min(float(repair_duration_s),rout)
    out_span=max(.001,end-start); in_span=max(.001,rout-rin)
    speed=in_span/out_span
    # Conservative guardrail: extreme retimes are review-only and not auto-applied.
    statuses={entry.status,exit.status}
    status="FAIL" if "FAIL" in statuses or not (.75<=speed<=1.33) else "REVIEW" if "REVIEW" in statuses else "PASS"
    enforcement="AVAILABLE" if .75<=speed<=1.33 else "UNSAFE_RETIME"
    truth=("Source/repair boundary frames were searched over time and converted into an affine repair-time map. "
           "When applied, FFmpeg changes repair timing while preserving final shot duration. This does not perform optical-flow interpolation or prove semantic continuity.")
    return MotionRetimingPlan(start,end,round(rin,6),round(rout,6),round(speed,6),entry,exit,status,enforcement,truth)
