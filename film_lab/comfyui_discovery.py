"""Evidence-based local ComfyUI capability discovery."""
import json
from dataclasses import dataclass,asdict
from urllib.request import Request,urlopen
from urllib.error import URLError,HTTPError
from film_lab.generator_capabilities import GeneratorCapabilities
@dataclass(frozen=True)
class ComfyUIDiscovery:
    available:bool; endpoint:str; node_count:int=0; nodes:tuple[str,...]=(); capabilities:GeneratorCapabilities=GeneratorCapabilities(); evidence:dict[str,tuple[str,...]]|None=None; error:str=""
    def to_dict(self): d=asdict(self); d["capabilities"]=self.capabilities.to_dict(); return d
NODE_FAMILIES={"identity_conditioning":("InstantID","ApplyInstantID","IPAdapterFaceID","Pulid","PuLID","FaceID"),"reference_images":("IPAdapter","ReferenceOnly","InstantID"),"camera_control":("CameraCtrl","CameraControl","MotionCtrl"),"mask_regeneration":("InpaintModelConditioning","VAEEncodeForInpaint","SetLatentNoiseMask"),"audio":("VHS_VideoCombine","SaveAudio","AudioEncoder","LoadAudio"),"voice":("TTS","TextToSpeech","F5TTS","Kokoro","XTTS")}
def _matches(nodes,terms): return tuple(sorted({n for n in nodes for t in terms if t.lower() in n.lower()}))
def infer_capabilities(nodes):
    names=tuple(sorted(map(str,nodes))); e={k:_matches(names,v) for k,v in NODE_FAMILIES.items()}; c=GeneratorCapabilities(text_prompt=True,start_image=True,end_image=True,reference_images=bool(e["reference_images"]),identity_conditioning=bool(e["identity_conditioning"]),camera_control=bool(e["camera_control"]),mask_regeneration=bool(e["mask_regeneration"]),audio=bool(e["audio"]),voice=bool(e["voice"]),structured_conditioning=True); return c,e
def discover_comfyui(endpoint="http://127.0.0.1:8188",timeout=3.0):
    base=endpoint.rstrip("/")
    try:
        with urlopen(Request(base+"/object_info",headers={"Accept":"application/json"}),timeout=timeout) as r: raw=json.loads(r.read().decode())
        nodes=tuple(sorted(raw.keys())) if isinstance(raw,dict) else (); caps,e=infer_capabilities(nodes); return ComfyUIDiscovery(True,base,len(nodes),nodes,caps,e,"")
    except (URLError,HTTPError,TimeoutError,OSError,json.JSONDecodeError) as exc: return ComfyUIDiscovery(False,base,error=f"ComfyUI discovery unavailable: {exc}")
