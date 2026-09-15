"""Sequential in-process generation queue."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from film_lab.ffmpeg_support import probe_duration_seconds
from film_lab.generators.base import GenerateJob, Generator
from film_lab.project import Project
from film_lab.shot_card import ShotCard, slugify, utc_now

ProgressFn = Callable[[int, int, str], None]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class QueueItem:
    shot: ShotCard
    status: str = "queued"
    message: str = ""
    output_path: str | None = None
    enqueued_at: str = field(default_factory=_now)

    def row(self) -> list[str]:
        return [self.shot.id, self.shot.name, self.shot.camera_move, f"{self.shot.duration:.1f}s", self.shot.intimacy_mode, self.status, self.message]


class GenerationQueue:
    def __init__(self) -> None:
        self.items: list[QueueItem] = []

    def enqueue(self, shot: ShotCard) -> QueueItem:
        item = QueueItem(shot=shot); self.items.append(item); return item

    def clear_finished(self) -> None:
        self.items = [i for i in self.items if i.status in {"queued", "running"}]

    def clear_all(self) -> None:
        self.items.clear()

    def rows(self) -> list[list[str]]:
        return [item.row() for item in self.items]

    def run(self, project: Project, generator: Generator, *, progress: ProgressFn | None = None) -> list[QueueItem]:
        pending = [i for i in self.items if i.status == "queued"]
        total = len(pending)
        for index, item in enumerate(pending, start=1):
            if progress: progress(index, total, f"Generating {item.shot.name}")
            item.status = "running"; item.message = f"via {generator.label}"
            try:
                output = _output_path(project, item.shot, generator.id)
                start = project.resolve_still(item.shot.start_frame)
                if start is None: raise FileNotFoundError("Start frame is required. Ingest a still and assign it on the shot.")
                job = GenerateJob(shot=item.shot, start_path=start, end_path=project.resolve_still(item.shot.end_frame), output_path=output)
                result = generator.generate(job)
                item.output_path = str(result); item.status = "done"; item.message = result.name
                project.save_shot(item.shot)
                duration = probe_duration_seconds(result) or item.shot.duration
                project.register_output(result, shot=item.shot, generator=generator.id, duration=duration)
                # A successful render is not complete until it enters the same
                # persistent Scene -> Shot -> Take model used by Take Board and Cinema.
                # Never create a Take before the generator has written real video.
                from film_lab.production import ProductionStore
                ProductionStore(project).add_take(
                    result,
                    scene_id=item.shot.scene_id or "scene_001",
                    shot_id=item.shot.id,
                    name=item.shot.name,
                    generator=generator.id,
                    model=getattr(generator, "model", "") or getattr(generator, "label", ""),
                    prompt=item.shot.local_prompt(),
                    duration=duration,
                    metadata={"source": "generation_queue", "camera_move": item.shot.camera_move, "aspect_ratio": item.shot.aspect_ratio, "resolution": item.shot.resolution},
                )
            except Exception as exc:
                item.status = "error"; item.message = str(exc)
        return self.items


def generate_one(project: Project, shot: ShotCard, generator: Generator) -> Path:
    queue = GenerationQueue(); queue.enqueue(shot); queue.run(project, generator)
    item = queue.items[0]
    if item.status != "done" or not item.output_path: raise RuntimeError(item.message or "Generation failed")
    return Path(item.output_path)


def _output_path(project: Project, shot: ShotCard, generator_id: str) -> Path:
    project.ensure_dirs()
    stamp = utc_now().replace(":", "").replace("-", "")
    filename = f"{shot.id}_{slugify(shot.name)}_{generator_id}_{stamp}.mp4"
    return project.outputs_dir / filename
