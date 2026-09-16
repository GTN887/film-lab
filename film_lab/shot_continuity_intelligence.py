"""Continuity-aware intelligence for Director preview regeneration.

Builds an explicit change/preserve contract around a source Take and audits the
candidate against renderer enforcement evidence.  Visual sameness is never
claimed without a future visual certification pass.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

from film_lab.character_state import CharacterStore
from film_lab.production import ProductionStore
from film_lab.scene_context import SceneContextStore

_CHANGE_TERMS = {
    "performance": ("emotion", "expression", "afraid", "fear", "angry", "sad", "happy", "suspicious", "reaction", "react", "acting", "performance", "gaze", "look"),
    "blocking": ("move ", "walk", "approach", "retreat", "back away", "position", "blocking", "turn "),
    "camera": ("camera", "push in", "pull out", "pan ", "tilt ", "orbit", "dolly", "zoom", "close-up", "wide shot"),
    "dialogue_voice": ("say ", "dialogue", "voice", "whisper", "shout", "speak", "line "),
    "lighting": ("light", "lighting", "brighter", "darker", "shadow"),
    "environment": ("weather", "rain", "snow", "location", "room", "set ", "time of day", "night", "daylight"),
    "wardrobe_appearance": ("wardrobe", "clothes", "shirt", "dress", "hair", "makeup", "appearance"),
}


def infer_change_scope(instruction: str) -> list[str]:
    text=f" {str(instruction or '').lower()} "
    return [scope for scope, terms in _CHANGE_TERMS.items() if any(term in text for term in terms)] or ["performance"]


def build_regeneration_contract(project, *, scene_id: str, shot_id: str, source_take_id: str, instruction: str, character_id: str="") -> dict[str, Any]:
    source=ProductionStore(project).get_take(source_take_id)
    if source.scene_id != scene_id or source.shot_id != shot_id:
        raise ValueError("Source Take does not belong to the requested Scene/Shot.")
    world=SceneContextStore(project).get(scene_id)
    chars=CharacterStore(project).resolve_scene_characters(world.characters)
    scopes=infer_change_scope(instruction)
    target=(character_id or "").strip()
    if target and target not in {c.id for c in chars}:
        raise ValueError("Requested Character ID is not bound to this Scene World.")
    locks=[]
    for c in chars:
        locks.append({"character_id":c.id,"name":c.name,"identity":True,"appearance":c.appearance,"wardrobe":c.wardrobe,"hair":c.hair,"makeup":c.makeup,"reference_images":list(c.reference_images),"targeted_for_change":c.id==target})
    preserve={
        "set_id":world.set_id,"location":world.location,"time_of_day":world.time_of_day,"weather":world.weather,
        "lighting":world.lighting,"camera":world.camera,"blocking":world.blocking,"objects":world.objects,
        "characters":locks,"source_take_id":source.id,
    }
    # Remove a domain from the preserve contract only when the Director explicitly changes it.
    for scope, fields in {"camera":["camera"],"blocking":["blocking"],"lighting":["lighting"],"environment":["set_id","location","time_of_day","weather"],"wardrobe_appearance":["characters"]}.items():
        if scope in scopes:
            for f in fields: preserve.pop(f,None)
    return {"version":1,"scene_id":scene_id,"shot_id":shot_id,"source_take_id":source.id,"director_instruction":str(instruction or "").strip(),"target_character_id":target,"requested_change_scopes":scopes,"preserve":preserve,"truth":"Preserve entries are requested locks. Visual preservation is not certified until candidate media is visually checked."}


def audit_candidate(project, *, candidate_take_id: str, contract: dict[str, Any]) -> dict[str, Any]:
    take=ProductionStore(project).get_take(candidate_take_id)
    meta=take.metadata if isinstance(take.metadata,dict) else {}
    enforcement=meta.get("continuity_enforcement") if isinstance(meta.get("continuity_enforcement"),dict) else {}
    channels=enforcement.get("channels") if isinstance(enforcement.get("channels"),list) else []
    channel_status={str(x.get("name")):str(x.get("status","NOT_TESTED")) for x in channels if isinstance(x,dict)}
    regional=meta.get("regional_actor_control") if isinstance(meta.get("regional_actor_control"),dict) else {}
    requested=list(contract.get("requested_change_scopes") or [])
    evidence={
        "start_frame":channel_status.get("start_frame","NOT_TESTED"),
        "identity":channel_status.get("identity_conditioning","NOT_TESTED"),
        "references":channel_status.get("reference_images","NOT_TESTED"),
        "camera":channel_status.get("camera_control","NOT_TESTED"),
        "blocking":channel_status.get("blocking","NOT_TESTED"),
        "objects":channel_status.get("objects","NOT_TESTED"),
        "regional_actor_isolation":regional.get("status","NOT_REQUESTED"),
    }
    nonvisual=[v for v in evidence.values() if v not in {"ENFORCED","NOT_REQUESTED"}]
    return {"version":1,"candidate_take_id":take.id,"source_take_id":contract.get("source_take_id",""),"requested_changes":requested,"preserve_contract":contract.get("preserve",{}),"renderer_evidence":evidence,"renderer_status":"PARTIAL" if nonvisual else "ENFORCED_AT_INPUT_BOUNDARY","visual_certification":"NOT_TESTED","visual_drift":[],"truth":"Renderer evidence describes wired inputs only. It does not prove visual identity, wardrobe, set, prop, lighting, blocking, camera, or performance continuity."}
