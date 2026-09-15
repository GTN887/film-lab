"""Truthful generator capability contracts and routing for Film Lab."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Iterable

CAPABILITIES=("text_prompt","start_image","end_image","reference_images","identity_conditioning","camera_control","blocking","objects","mask_regeneration","audio","voice","structured_conditioning")

@dataclass(frozen=True)
class GeneratorCapabilities:
    text_prompt: bool=True
    start_image: bool=False
    end_image: bool=False
    reference_images: bool=False
    identity_conditioning: bool=False
    camera_control: bool=False
    blocking: bool=False
    objects: bool=False
    mask_regeneration: bool=False
    audio: bool=False
    voice: bool=False
    structured_conditioning: bool=False
    def to_dict(self): return asdict(self)
    def supports(self,name):
        if name not in CAPABILITIES: raise ValueError(f"Unknown generator capability: {name}")
        return bool(getattr(self,name))

@dataclass(frozen=True)
class GeneratorRequirement:
    name: str
    required: bool=True

@dataclass(frozen=True)
class RouteDecision:
    generator: Any|None
    generator_id: str
    missing_required: tuple[str,...]
    unsupported_optional: tuple[str,...]
    score: int
    usable: bool


def capabilities_for(generator)->GeneratorCapabilities:
    raw=getattr(generator,"capabilities",None)
    if callable(raw): raw=raw()
    if isinstance(raw,GeneratorCapabilities): return raw
    if isinstance(raw,dict): return GeneratorCapabilities(**{k:bool(v) for k,v in raw.items() if k in CAPABILITIES})
    # Legacy engines are deliberately conservative: do not claim controls merely because a prompt can mention them.
    return GeneratorCapabilities(text_prompt=True,start_image=True)


def requirements_from_conditioning(conditioning)->tuple[GeneratorRequirement,...]:
    req=[GeneratorRequirement("text_prompt"),GeneratorRequirement("start_image")]
    if getattr(conditioning,"end_image",""): req.append(GeneratorRequirement("end_image"))
    chars=getattr(conditioning,"characters",()) or ()
    if any(getattr(c,"reference_images",()) for c in chars): req.append(GeneratorRequirement("reference_images",False))
    if any(getattr(c,"identity_adapter","") or getattr(c,"identity_reference","") for c in chars): req.append(GeneratorRequirement("identity_conditioning",False))
    if getattr(conditioning,"camera",{}): req.append(GeneratorRequirement("camera_control",False))
    if getattr(conditioning,"blocking",()): req.append(GeneratorRequirement("blocking",False))
    if getattr(conditioning,"objects",()): req.append(GeneratorRequirement("objects",False))
    req.append(GeneratorRequirement("structured_conditioning",False))
    return tuple(req)


def evaluate(generator,requirements:Iterable[GeneratorRequirement])->RouteDecision:
    caps=capabilities_for(generator); missing=[]; optional=[]; score=0
    for r in requirements:
        if caps.supports(r.name): score+=3 if r.required else 1
        elif r.required: missing.append(r.name)
        else: optional.append(r.name)
    gid=str(getattr(generator,"id",generator.__class__.__name__))
    return RouteDecision(generator,gid,tuple(missing),tuple(optional),score,not missing)


def choose_generator(generators,requirements):
    decisions=[evaluate(g,requirements) for g in generators]
    usable=[d for d in decisions if d.usable]
    if not usable: return None,tuple(decisions)
    usable.sort(key=lambda d:(d.score,d.generator_id),reverse=True)
    return usable[0],tuple(decisions)


def require_generator(generator,requirements):
    decision=evaluate(generator,requirements)
    if not decision.usable: raise RuntimeError(f"Generator {decision.generator_id} lacks required capabilities: {', '.join(decision.missing_required)}")
    return decision
