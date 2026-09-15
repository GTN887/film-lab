"""Discover capabilities from the ComfyUI instance actually running on the Creator's machine."""
from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from film_lab.generator_capabilities import GeneratorCapabilities

@dataclass(frozen=True)
class ComfyUIDiscovery:
    available: bool
    endpoint: str
    node_count: int=0
    nodes: tuple[str,...]=()
    capabilities: GeneratorCapabilities=GeneratorCapabilities()
    evidence: dict[str,tuple[str,...]]|None=None
    error: str=""
    def to_dict(self):
        d=asdict(self); d["capabilities"]=self.capabilities.to_dict(); return d

# Evidence is intentionally node-based. A feature is not advertised just because Film Lab has a button for it.
NODE_FAMILIES={
 "identity_conditioning":("InstantID","ApplyInstantID","IPAdapterFaceID","Pulid","PuLID","FaceID"),
 "reference_images":("IPAdapter","IPAdapterAdvanced","ReferenceOnly","InstantID","ApplyInstantID"),
 "camera_control":("CameraCtrl","CameraControl","MotionCtrl","AnimateDiffCameraCtrl"),
 "mask_regeneration":("InpaintModelConditioning","VAEEncodeForInpaint","SetLatentNoiseMask","MaskToImage"),
 "audio":("VHS_VideoCombine","SaveAudio","AudioEncoder","LoadAudio"),
 "voice":("TTS","TextToSpeech","F5TTS","Kokoro","XTTS"),
}

def _matches(nodes,terms):
    low={n.lower():n for n in nodes}; found=[]
    for term in terms:
        t=term.lower()
        found.extend(original for key,original in low.items() if t in key)
    return tuple(sorted(set(found)))

def infer_capabilities(nodes):
    names=tuple(sorted(str(n) for n in nodes)); evidence={k:_matches(names,v) for k,v in NODE_FAMILIES.items()}
    caps=GeneratorCapabilities(text_prompt=True,start_image=True,end_image=True,
        reference_images=bool(evidence["reference_images"]),identity_conditioning=bool(evidence["identity_conditioning"]),
        camera_control=bool(evidence["camera_control"]),mask_regeneration=bool(evidence["mask_regeneration"]),
        audio=bool(evidence["audio"]),voice=bool(evidence["voice"]),structured_conditioning=True)
    return caps,evidence

def discover_comfyui(endpoint="http://127.0.0.1:8188",timeout=3.0):
    base=endpoint.rstrip("/")
    try:
        req=Request(base+"/object_info",headers={"Accept":"application/json"})
        with urlopen(req,timeout=timeout) as response: raw=json.loads(response.read().decode("utf-8"))
        nodes=tuple(sorted(raw.keys())) if isinstance(raw,dict) else ()
        caps,evidence=infer_capabilities(nodes)
        return ComfyUIDiscovery(True,base,len(nodes),nodes,caps,evidence,"")
    except (URLError,HTTPError,TimeoutError,OSError,json.JSONDecodeError) as exc:
        return ComfyUIDiscovery(False,base,error=f"ComfyUI discovery unavailable: {exc}")
