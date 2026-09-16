"""Character-specific regional controls for truthful masked generation.

A regional control is only a request until a validated workflow explicitly wires
its mask into an inpaint/masked-regeneration path. Stable Character IDs prevent
regions from drifting to another performer when cast ordering changes.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from film_lab.mark import load_marks

@dataclass(frozen=True)
class RegionalActorControl:
    character_id: str
    region_id: str
    target: str
    instruction: str
    mask_path: str = ""
    shape: str = ""
    status: str = "REQUESTED"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_regional_actor_controls(project, conditioning) -> tuple[RegionalActorControl, ...]:
    """Resolve saved marks to stable characters without guessing by list position."""
    known = {str(getattr(c, "character_id", "") or "") for c in (getattr(conditioning, "characters", ()) or ())}
    out: list[RegionalActorControl] = []
    for region in load_marks(project).regions:
        cid = str(getattr(region, "character_id", "") or "").strip()
        if not cid:
            continue  # legacy/global marks remain prompt guidance, never actor-isolated
        mask = ""
        if region.mask_name:
            p = project.stills_dir / "mark_masks" / region.mask_name
            if p.is_file():
                mask = str(p.resolve())
        status = "REQUESTED" if cid in known else "UNRESOLVED_CHARACTER"
        out.append(RegionalActorControl(cid, region.id, region.target, region.note, mask, region.shape, status))
    return tuple(out)
