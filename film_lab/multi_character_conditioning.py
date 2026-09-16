"""Stable multi-character identity/reference assignment for generation workflows."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any
from film_lab.conditioning_profiles import discover_conditioning_profiles

@dataclass(frozen=True)
class CharacterAssignment:
    character_id: str
    name: str
    capability: str
    image_node: str = ""
    consumer_node: str = ""
    slot: str = ""
    status: str = "UNSUPPORTED"
    reason: str = ""
    region: str = ""

    def to_dict(self): return asdict(self)

def _explicit_targets(graph: dict[str, Any]) -> set[str]:
    out=set()
    for node in graph.values():
        if not isinstance(node,dict): continue
        title=str((node.get("_meta") or {}).get("title") or "").strip().lower()
        if title.startswith("film_lab_") and ":" in title:
            out.add(title.split(":",1)[1].strip())
    return out

def assign_character_profiles(graph: dict[str, Any], conditioning) -> dict[str, Any]:
    """Assign proven graph profiles to stable character IDs, never list aliases/names alone.

    Existing targeted Film Lab slots are preserved. Remaining proven identity/reference
    profiles are assigned deterministically to unassigned characters. If there are fewer
    proven slots than characters, the remainder is explicitly UNSUPPORTED.
    """
    chars=tuple(getattr(conditioning,"characters",()) or ())
    profiles=list(discover_conditioning_profiles(graph))
    explicit=_explicit_targets(graph)
    assignments=[]; used_images=set()
    for char in chars:
        cid=str(getattr(char,"character_id","") or "").strip()
        name=str(getattr(char,"name","") or "").strip()
        if not cid:
            assignments.append(CharacterAssignment("",name,"identity_conditioning",status="UNSUPPORTED",reason="Character has no stable ID."))
            continue
        if cid.lower() in explicit:
            assignments.append(CharacterAssignment(cid,name,"identity_conditioning",slot=f"film_lab_identity_image:{cid}",status="BOUND",reason="Workflow already contains an explicit targeted Film Lab slot; injection is verified separately."))
            continue
        profile=next((p for p in profiles if p.image_node not in used_images and p.capability=="identity_conditioning"),None)
        if profile is None:
            profile=next((p for p in profiles if p.image_node not in used_images and p.capability=="reference_images"),None)
        if profile is None:
            assignments.append(CharacterAssignment(cid,name,"identity_conditioning",status="UNSUPPORTED",reason="No remaining proven character-conditioning slot in this workflow."))
            continue
        node=graph.get(profile.image_node)
        if not isinstance(node,dict):
            assignments.append(CharacterAssignment(cid,name,profile.capability,status="UNSUPPORTED",reason="Conditioning image node disappeared.")); continue
        meta=node.setdefault("_meta",{})
        existing=str(meta.get("title") or "").strip()
        if existing.lower().startswith("film_lab_"):
            assignments.append(CharacterAssignment(cid,name,profile.capability,status="UNSUPPORTED",reason="Proven slot is already reserved by a Film Lab binding.")); used_images.add(profile.image_node); continue
        base="film_lab_identity_image" if profile.capability=="identity_conditioning" else "film_lab_reference_image"
        slot=f"{base}:{cid}"
        meta["title"]=slot; used_images.add(profile.image_node)
        assignments.append(CharacterAssignment(cid,name,profile.capability,profile.image_node,profile.consumer_node,slot,"BOUND","Stable Character ID bound to a proven connected workflow profile; injection is verified separately."))
    status="PASS" if assignments and all(a.status=="BOUND" for a in assignments) else ("PARTIAL" if any(a.status=="BOUND" for a in assignments) else "FAIL")
    if not assignments: status="NOT_REQUIRED"
    return {"version":1,"status":status,"assignments":[a.to_dict() for a in assignments]}
