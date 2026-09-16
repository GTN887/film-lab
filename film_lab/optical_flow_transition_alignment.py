"""Optical-flow transition alignment for localized Film Lab repairs.

This module is deliberately capability-gated. Film Lab only reports optical-flow
interpolation as ENFORCED when the installed FFmpeg exposes `minterpolate` and the
actual reconstruction command succeeds. Otherwise the feature is UNAVAILABLE/NOT_ENFORCED.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path

from film_lab.ffmpeg_support import ffmpeg_filter_available

@dataclass(frozen=True)
class OpticalFlowCapability:
    status: str
    enforcement: str
    filter_name: str
    evidence: str
    truth: str
    def to_dict(self): return asdict(self)


def inspect_optical_flow_capability() -> OpticalFlowCapability:
    ok, evidence = ffmpeg_filter_available("minterpolate")
    if ok:
        return OpticalFlowCapability(
            "PASS", "AVAILABLE", "minterpolate", evidence,
            "The installed FFmpeg exposes minterpolate. Optical-flow interpolation is available but is not ENFORCED until a reconstruction command succeeds."
        )
    return OpticalFlowCapability(
        "NOT_TESTED", "NOT_ENFORCED", "minterpolate", evidence,
        "Film Lab will not claim optical-flow interpolation when the required FFmpeg filter is unavailable."
    )


def minterpolate_filter(fps: float = 60.0) -> str:
    fps=max(24.0,min(120.0,float(fps)))
    return f"minterpolate=fps={fps:.3f}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
