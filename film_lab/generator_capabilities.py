"""Truthful generator capability contracts and routing."""
from dataclasses import dataclass, asdict
from typing import Any, Iterable
CAPABILITIES=("text_prompt","start_image","end_image","reference_images","identity_conditioning","camera_control","blocking","objects","mask_regeneration","audio","voice","performance_timeline_control","structured_conditioning")
@dataclass(frozen=True)
class GeneratorCapabilities:
    text_prompt: bool=True; start_image: bool=False; end_image: bool=False; reference_images: bool=False; identity_conditioning: bool=False; camera_control: bool=False; blocking: bool=False; objects: bool=False; mask_regeneration: bool=False; audio: bool=False; voice: bool=False; performance_timeline_control: bool=False; structured_conditioning: bool=False
    def to_dict(self): return asdict(self)
    def supports(self,name):
        if name not in CAPABILITIES: raise ValueError(f"Unknown generator capability: {name}")
        return bool(getattr(self,name))
@dataclass(frozen=True)
class GeneratorRequirement: name: str; required: bool=True
@dataclass(frozen=True)
class RouteDecision:
    generator: Any|None; generator_id: str; missing_required: tuple[str,...]; unsupported_optional: tuple[str,...]; score: int; usable: bool
def capabilities_for(generator):
    raw=getattr(generator,"capabilities",None); raw=raw() if callable(raw) else raw
    if isinstance(raw,GeneratorCapabilities): return raw
    if isinstance(raw,dict): return GeneratorCapabilities(**{k:bool(v) for k,v in raw.items() if k in CAPABILITIES})
    return GeneratorCapabilities(text_prompt=True,start_image=True)
def requirements_from_conditioning(c):
    req=[GeneratorRequirement("text_prompt"),GeneratorRequirement("start_image")]
    if getattr(c,"end_image",""): req.append(GeneratorRequirement("end_image"))
    chars=getattr(c,"characters",()) or ()
    if any(getattr(x,"reference_images",()) for x in chars): req.append(GeneratorRequirement("reference_images",False))
    if any(getattr(x,"identity_adapter","") or getattr(x,"identity_reference","") for x in chars): req.append(GeneratorRequirement("identity_conditioning",False))
    for name,attr in (("camera_control","camera"),("blocking","blocking"),("objects","objects")):
        if getattr(c,attr,{} if attr=="camera" else ()): req.append(GeneratorRequirement(name,False))
    if (getattr(c,"metadata",{}) or {}).get("regional_actor_controls"): req.append(GeneratorRequirement("mask_regeneration",False))
    if (getattr(c,"metadata",{}) or {}).get("performance_timelines"): req.append(GeneratorRequirement("performance_timeline_control",False))
    req.append(GeneratorRequirement("structured_conditioning",False)); return tuple(req)
def evaluate(generator,requirements:Iterable[GeneratorRequirement]):
    caps=capabilities_for(generator); missing=[]; optional=[]; score=0
    for r in requirements:
        if caps.supports(r.name): score+=3 if r.required else 1
        elif r.required: missing.append(r.name)
        else: optional.append(r.name)
    gid=str(getattr(generator,"id",generator.__class__.__name__)); return RouteDecision(generator,gid,tuple(missing),tuple(optional),score,not missing)
def choose_generator(generators,requirements):
    ds=[evaluate(g,requirements) for g in generators]; usable=[d for d in ds if d.usable]
    if not usable: return None,tuple(ds)
    usable.sort(key=lambda d:(d.score,d.generator_id),reverse=True); return usable[0],tuple(ds)
