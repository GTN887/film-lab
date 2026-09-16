"""Local video generators. AMD ComfyUI img2vid is the product; Ken Burns is Advanced only."""

from __future__ import annotations

from film_lab.generators.base import Generator, GeneratorUnavailable, ProbeResult
from film_lab.generators.comfyui_i2v import ComfyUII2VGenerator
from film_lab.generators.diffusers_i2v import DiffusersI2VGenerator
from film_lab.generators.ken_burns import KenBurnsGenerator

DEFAULT_GENERATOR_ID = ComfyUII2VGenerator.id
FALLBACK_GENERATOR_ID = KenBurnsGenerator.id

GENERATORS: dict[str, Generator] = {
    ComfyUII2VGenerator.id: ComfyUII2VGenerator(),
    KenBurnsGenerator.id: KenBurnsGenerator(),
    DiffusersI2VGenerator.id: DiffusersI2VGenerator(),
}


def get_generator(generator_id: str) -> Generator:
    try:
        return GENERATORS[generator_id]
    except KeyError as exc:
        raise KeyError(f"Unknown generator {generator_id!r}") from exc


def list_generator_ids() -> list[str]:
    return list(GENERATORS.keys())


def generator_dropdown_choices() -> list[tuple[str, str]]:
    """Main engine picker — Ken Burns is Advanced-only, not a desk choice."""
    return [
        (gen.label, gen.id)
        for gen in GENERATORS.values()
        if gen.id != FALLBACK_GENERATOR_ID
    ]


__all__ = [
    "DEFAULT_GENERATOR_ID",
    "FALLBACK_GENERATOR_ID",
    "GENERATORS",
    "ComfyUII2VGenerator",
    "DiffusersI2VGenerator",
    "Generator",
    "GeneratorUnavailable",
    "KenBurnsGenerator",
    "ProbeResult",
    "generator_dropdown_choices",
    "get_generator",
    "list_generator_ids",
]
