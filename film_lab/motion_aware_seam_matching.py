"""Motion-aware seam matching for localized Film Lab repairs.

Estimates coarse frame motion around the source/repair entry and exit boundaries,
then adjusts the visual crossfade duration conservatively. This is motion evidence,
not optical-flow warping and not semantic/identity certification.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import math
import numpy as np
from PIL import Image

from film_lab.ffmpeg_support import FFmpegError
from film_lab.visual_continuity_certification import _sample_frame

@dataclass(frozen=True)
class MotionBoundaryEvidence:
    boundary: str
    time_s: float
    source_motion: tuple[float,float]
    repair_motion: tuple[float,float]
    velocity_delta: float
    direction_similarity: float | None
    status: str
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class MotionSeamPlan:
    requested_blend_s: float
    recommended_blend_s: float
    status: str
    entry: MotionBoundaryEvidence | None
    exit: MotionBoundaryEvidence | None
    truth: str
    def to_dict(self): return asdict(self)


def _gray(path: Path, size=(160,90)) -> np.ndarray:
    return np.asarray(Image.open(path).convert("L").resize(size, Image.Resampling.BILINEAR), dtype=np.float32)/255.0


def _estimate_translation(a: Path, b: Path, max_shift: int=8) -> tuple[float,float]:
    """Coarse deterministic translation estimate in normalized-frame units."""
    x=_gray(a); y=_gray(b); h,w=x.shape
    best=(0,0); best_err=float("inf")
    for dy in range(-max_shift,max_shift+1):
        for dx in range(-max_shift,max_shift+1):
            ax0=max(0,-dx); ax1=min(w,w-dx); ay0=max(0,-dy); ay1=min(h,h-dy)
            bx0=ax0+dx; bx1=ax1+dx; by0=ay0+dy; by1=ay1+dy
            if ax1-ax0<20 or ay1-ay0<20: continue
            err=float(np.mean(np.abs(x[ay0:ay1,ax0:ax1]-y[by0:by1,bx0:bx1])))
            if err<best_err: best_err=err; best=(dx,dy)
    return (best[0]/w,best[1]/h)


def _direction_similarity(a,b):
    na=math.hypot(*a); nb=math.hypot(*b)
    if na<1e-6 or nb<1e-6: return None
    return max(-1.0,min(1.0,(a[0]*b[0]+a[1]*b[1])/(na*nb)))


def _boundary(project, source: Path, repair: Path, name: str, t: float, sample_delta_s: float):
    root=project.root/"motion_seam_evidence"; root.mkdir(parents=True,exist_ok=True)
    s0=root/f"{name}_source_0.png"; s1=root/f"{name}_source_1.png"
    r0=root/f"{name}_repair_0.png"; r1=root/f"{name}_repair_1.png"
    t0=max(0.0,t-sample_delta_s); t1=max(t0+0.001,t+sample_delta_s)
    _sample_frame(source,s0,t0); _sample_frame(source,s1,t1)
    _sample_frame(repair,r0,t0); _sample_frame(repair,r1,t1)
    sm=_estimate_translation(s0,s1); rm=_estimate_translation(r0,r1)
    delta=math.dist(sm,rm); direction=_direction_similarity(sm,rm)
    status="PASS" if delta<=.025 and (direction is None or direction>=.5) else "REVIEW" if delta<=.07 else "FAIL"
    return MotionBoundaryEvidence(name,float(t),tuple(round(v,6) for v in sm),tuple(round(v,6) for v in rm),round(delta,6),None if direction is None else round(direction,6),status)


def analyze_motion_seams(project, source: Path, repair: Path, *, window_start_s: float, window_end_s: float,
                         requested_blend_s: float=.12, sample_delta_s: float=.08) -> MotionSeamPlan:
    try:
        entry=_boundary(project,source,repair,"entry",float(window_start_s),sample_delta_s)
        exit=_boundary(project,source,repair,"exit",float(window_end_s),sample_delta_s)
    except (OSError,ValueError,RuntimeError,FFmpegError) as exc:
        return MotionSeamPlan(float(requested_blend_s),float(requested_blend_s),"NOT_TESTED",None,None,
            f"Motion analysis could not be completed: {exc}")
    statuses={entry.status,exit.status}
    status="FAIL" if "FAIL" in statuses else "REVIEW" if "REVIEW" in statuses else "PASS"
    # More mismatch gets a longer dissolve, bounded so this remains a subtle seam treatment.
    worst=max(entry.velocity_delta,exit.velocity_delta)
    factor=1.0 if worst<=.025 else 1.35 if worst<=.07 else 1.75
    recommended=max(.05,min(.5,float(requested_blend_s)*factor))
    truth=("Coarse source/repair motion vectors were compared at both boundaries and used to choose a safer blend duration. "
           "This does not perform optical-flow retiming/warping and does not prove semantic or identity continuity.")
    return MotionSeamPlan(float(requested_blend_s),round(recommended,6),status,entry,exit,truth)
