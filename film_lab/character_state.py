"""Persistent Character IDs and continuity state for Film Lab productions."""
from __future__ import annotations
import json, uuid
from dataclasses import asdict, dataclass, field
from typing import Any


def _id(): return f"char_{uuid.uuid4().hex[:12]}"

@dataclass
class CharacterState:
    id: str
    name: str
    appearance: str = ""
    wardrobe: str = ""
    hair: str = ""
    makeup: str = ""
    voice_id: str = ""
    performance: str = ""
    emotional_state: str = ""
    continuity_notes: str = ""
    reference_images: list[str] = field(default_factory=list)
    identity_adapter: str = ""
    identity_reference: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw):
        data=dict(raw or {})
        return cls(**{k:data[k] for k in cls.__dataclass_fields__ if k in data})

    def prompt_context(self):
        parts=[f"Character {self.name} [{self.id}]"]
        for label,value in (("Appearance",self.appearance),("Wardrobe",self.wardrobe),("Hair",self.hair),("Makeup",self.makeup),("Performance",self.performance),("Emotion",self.emotional_state),("Character continuity",self.continuity_notes)):
            if value: parts.append(f"{label}: {value}")
        return ". ".join(parts)

class CharacterStore:
    def __init__(self, project):
        self.project=project; project.ensure_dirs(); self.path=project.root/"character_state.json"
    def _load(self):
        if not self.path.exists(): return {"version":1,"characters":{}}
        try: raw=json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError): return {"version":1,"characters":{}}
        raw.setdefault("version",1); raw.setdefault("characters",{}); return raw
    def _save(self,data):
        tmp=self.path.with_suffix(".json.tmp"); tmp.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8"); tmp.replace(self.path)
    def create(self,name,**fields):
        char=CharacterState(id=_id(),name=str(name).strip() or "Character")
        for key,value in fields.items():
            if key not in CharacterState.__dataclass_fields__ or key in {"id","name"}: raise ValueError(f"Unknown Character field: {key}")
            setattr(char,key,value)
        data=self._load(); data["characters"][char.id]=asdict(char); self._save(data); return char
    def get(self,character_id):
        raw=self._load()["characters"].get(character_id)
        if raw is None: raise KeyError(character_id)
        return CharacterState.from_dict(raw)
    def update(self,character_id,**changes):
        char=self.get(character_id)
        for key,value in changes.items():
            if key not in CharacterState.__dataclass_fields__ or key=="id": raise ValueError(f"Unknown Character field: {key}")
            setattr(char,key,value)
        data=self._load(); data["characters"][char.id]=asdict(char); self._save(data); return char
    def list(self): return [CharacterState.from_dict(x) for x in self._load()["characters"].values()]
    def resolve_scene_characters(self, scene_characters):
        """Resolve Scene World character refs by stable ID; preserve non-ID refs for compatibility."""
        resolved=[]
        for ref in scene_characters or []:
            cid=str(ref.get("id","")).strip() if isinstance(ref,dict) else str(ref).strip()
            if cid:
                try: resolved.append(self.get(cid)); continue
                except KeyError: pass
            if isinstance(ref,dict) and ref.get("name"):
                resolved.append(CharacterState(id=cid or "unbound",name=str(ref["name"])))
        return resolved
