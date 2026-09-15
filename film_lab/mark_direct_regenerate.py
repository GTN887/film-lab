"""Mark & Direct regeneration service.

A directing pass always forks a new Take. The source Take is preserved. Regional
marks are folded into the Shot prompt and the selected frame becomes the new
start reference for the configured generator.
"""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
from film_lab.generators.base import Generator
from film_lab.mark import fold_marks_into_seed, load_marks, still_from_source
from film_lab.production import ProductionStore, Take
from film_lab.project import Project
from film_lab.queue import GenerationQueue
from film_lab.shot_card import ShotCard

class MarkDirectRegenerationError(RuntimeError): pass

def regenerate_take(project: Project, *, source_take_id: str, generator: Generator, director_instruction: str = "") -> Take:
    store=ProductionStore(project); source=store.get_take(source_take_id); source_media=Path(source.media_path)
    if not source_media.is_file(): raise MarkDirectRegenerationError("Source Take media is missing.")
    try: shot=deepcopy(project.load_shot(source.shot_id))
    except (OSError,ValueError,TypeError): shot=ShotCard(id=source.shot_id,name=source.name or "Directed take")
    shot.scene_id=source.scene_id
    frame=project.stills_dir/f"mark_direct_{source.id}.png"; still_from_source(source_media,frame); shot.start_frame=frame.name
    instruction=(director_instruction or "").strip(); seed=shot.director_intent or source.prompt or ""
    if instruction: seed=f"{seed}\n{instruction}".strip()
    shot.director_intent=fold_marks_into_seed(seed,load_marks(project)); project.save_shot(shot)
    before={t.id for t in store.list_takes(shot_id=shot.id)}; queue=GenerationQueue(); queue.enqueue(shot); queue.run(project,generator); item=queue.items[0]
    if item.status!="done": raise MarkDirectRegenerationError(item.message or "Mark & Direct regeneration failed.")
    created=[t for t in store.list_takes(shot_id=shot.id) if t.id not in before]
    if not created: raise MarkDirectRegenerationError("Renderer completed but no persistent Take was created.")
    new_take=created[0]; data=store._load(); raw=data["takes"][new_take.id]; raw.setdefault("metadata",{})["source"]="mark_direct_regeneration"; raw["metadata"]["source_take_id"]=source.id; raw["metadata"]["director_instruction"]=instruction; store._save(data); return store.get_take(new_take.id)
