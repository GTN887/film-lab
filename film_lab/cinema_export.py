"""Cinema export built from durable Selected Takes, never UI-only state."""
from __future__ import annotations
import shutil
from pathlib import Path
from film_lab.production import ProductionStore
from film_lab.stitch import stitch_clips

def export_selected(project,dest,overlap=0.6):
    selected=ProductionStore(project).selected_takes(existing_media_only=True)
    if not selected: raise ValueError("Cinema has no Selected Takes to export.")
    clips=[Path(t.media_path) for t in selected]; out=Path(dest)
    if out.suffix.lower()!=".mp4": out=out.with_suffix(".mp4")
    out.parent.mkdir(parents=True,exist_ok=True)
    if len(clips)==1:
        shutil.copy2(clips[0],out); return out
    return stitch_clips(clips,out,overlap=overlap)
