"""Generator protocol shared by Ken Burns and optional local I2V."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from film_lab.shot_card import ShotCard


@dataclass(frozen=True)
class ProbeResult:
    available: bool
    message: str


@dataclass
class GenerateJob:
    shot: ShotCard
    start_path: Path
    end_path: Path | None
    output_path: Path
    # Formal production conditioning. Legacy generators may ignore it; capable
    # adapters can consume Scene World / Character / camera state without
    # relying on ad-hoc attributes.
    conditioning: Any | None = None


class GeneratorUnavailable(RuntimeError):
    """Optional generator cannot run (missing CUDA, weights, or deps)."""


class Generator(Protocol):
    id: str
    label: str

    def probe(self) -> ProbeResult: ...

    def generate(self, job: GenerateJob) -> Path: ...
