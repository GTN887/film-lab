"""Persistent Scene -> Shot -> Take production records for Film Lab."""
from __future__ import annotations
import json, shutil, uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

VIDEO_SUFFIXES={".mp4",".webm",".mov"}
TAKE_STATES={"review","selected","rejected"}
def utc_now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def _id(prefix): return f"{prefix}_{uuid.uuid4().hex[:12]}"

@dataclass
class Take:
    id:str; scene_id:str; shot_id:str; media_path:str; name:str=""; status:str="review"; director_notes:str=""; tags:list[str]=field(default_factory=list); generator:str=""; model:str=""; prompt:str=""; duration:float|None=None; created_at:str=field(default_factory=utc_now); metadata:dict[str,Any]=field(default_factory=dict)
    @classmethod
    def from_dict(cls, raw):
        data=dict(raw); data["tags"]=[str(x) for x in data.get("tags",[])]; data["metadata"]=data.get("metadata") if isinstance(data.get("metadata"),dict) else {}; status=str(data.get("status","review")).lower(); data["status"]=status if status in TAKE_STATES else "review"; return cls(**{k:data[k] for k in cls.__dataclass_fields__ if k in data})

class ProductionStore:
    def __init__(self, project):
        self.project=project; project.ensure_dirs(); self.path=project.root/"production.json"
    def _load(self):
        if not self.path.exists(): return {"version":1,"scenes":{},"shots":{},"takes":{}}
        try: raw=json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError): return {"version":1,"scenes":{},"shots":{},"takes":{}}
        raw.setdefault("version",1); raw.setdefault("scenes",{}); raw.setdefault("shots",{}); raw.setdefault("takes",{}); return raw
    def _save(self,data):
        tmp=self.path.with_suffix(".json.tmp"); tmp.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8"); tmp.replace(self.path)
    def ensure_scene(self,scene_id="scene_001",name="Scene 1"):
        data=self._load(); data["scenes"].setdefault(scene_id,{"id":scene_id,"name":name,"created_at":utc_now()}); self._save(data); return scene_id
    def ensure_shot(self,shot_id,scene_id="scene_001",name=""):
        self.ensure_scene(scene_id); data=self._load(); data["shots"].setdefault(shot_id,{"id":shot_id,"scene_id":scene_id,"name":name or shot_id,"created_at":utc_now()}); self._save(data); return shot_id
    def add_take(self,media,shot_id,scene_id="scene_001",name="",generator="",model="",prompt="",duration=None,metadata=None,copy_media=True):
        src=Path(media)
        if not src.is_file(): raise FileNotFoundError(src)
        if src.suffix.lower() not in VIDEO_SUFFIXES: raise ValueError(f"Unsupported Take media: {src.suffix}")
        self.ensure_shot(shot_id,scene_id); take_id=_id("take"); dest=src
        if copy_media:
            folder=self.project.takes_dir/scene_id/shot_id; folder.mkdir(parents=True,exist_ok=True); dest=folder/f"{take_id}{src.suffix.lower()}"; shutil.copy2(src,dest)
        take=Take(id=take_id,scene_id=scene_id,shot_id=shot_id,media_path=str(dest.resolve()),name=name or src.stem,generator=generator,model=model,prompt=prompt,duration=duration,metadata=metadata or {})
        data=self._load(); data["takes"][take.id]=asdict(take); self._save(data); return take
    def list_takes(self,shot_id=None,existing_media_only=False):
        takes=[Take.from_dict(x) for x in self._load()["takes"].values()]
        if shot_id is not None: takes=[t for t in takes if t.shot_id==shot_id]
        if existing_media_only: takes=[t for t in takes if Path(t.media_path).is_file()]
        return sorted(takes,key=lambda t:t.created_at,reverse=True)
    def get_take(self,take_id):
        raw=self._load()["takes"].get(take_id)
        if raw is None: raise KeyError(take_id)
        return Take.from_dict(raw)
    def set_status(self,take_id,status):
        status=status.strip().lower()
        if status not in TAKE_STATES: raise ValueError(f"status must be one of {sorted(TAKE_STATES)}")
        data=self._load(); raw=data["takes"].get(take_id)
        if raw is None: raise KeyError(take_id)
        if status=="selected":
            for other in data["takes"].values():
                if other.get("shot_id")==raw.get("shot_id") and other.get("id")!=take_id and other.get("status")=="selected": other["status"]="review"
        raw["status"]=status; self._save(data); return Take.from_dict(raw)
    def update_notes(self,take_id,director_notes=None,tags=None):
        data=self._load(); raw=data["takes"].get(take_id)
        if raw is None: raise KeyError(take_id)
        if director_notes is not None: raw["director_notes"]=str(director_notes)
        if tags is not None: raw["tags"]=list(dict.fromkeys(str(x).strip() for x in tags if str(x).strip()))
        self._save(data); return Take.from_dict(raw)
    def selected_takes(self,existing_media_only=True): return [t for t in self.list_takes(existing_media_only=existing_media_only) if t.status=="selected"]
    def cinema_manifest(self): return [{"take_id":t.id,"scene_id":t.scene_id,"shot_id":t.shot_id,"media_path":t.media_path,"duration":t.duration,"director_notes":t.director_notes,"tags":t.tags} for t in self.selected_takes(True)]
