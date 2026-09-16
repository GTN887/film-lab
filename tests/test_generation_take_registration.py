from pathlib import Path

from film_lab.generators.base import GenerateJob, ProbeResult
from film_lab.production import ProductionStore
from film_lab.project import Project
from film_lab.queue import GenerationQueue
from film_lab.shot_card import ShotCard


class FileGenerator:
    id = "unit-render"
    label = "Unit Render"
    model = "unit-model"

    def probe(self):
        return ProbeResult(True, "ready")

    def generate(self, job: GenerateJob) -> Path:
        job.output_path.parent.mkdir(parents=True, exist_ok=True)
        job.output_path.write_bytes(b"real-output-boundary")
        return job.output_path


class BrokenGenerator(FileGenerator):
    id = "broken-render"

    def generate(self, job: GenerateJob) -> Path:
        raise RuntimeError("renderer failed")


def _project_with_still(tmp_path):
    project = Project.create("movie", data_root=tmp_path / "projects")
    still = project.stills_dir / "start.png"
    still.write_bytes(b"still")
    return project, still.name


def test_successful_generation_automatically_becomes_persistent_take(tmp_path):
    project, still_name = _project_with_still(tmp_path)
    shot = ShotCard(name="Run and hide", start_frame=still_name, scene_id="scene_chase")
    queue = GenerationQueue(); queue.enqueue(shot); queue.run(project, FileGenerator())
    assert queue.items[0].status == "done"
    takes = ProductionStore(project).list_takes(shot_id=shot.id, existing_media_only=True)
    assert len(takes) == 1
    take = takes[0]
    assert take.scene_id == "scene_chase"
    assert take.generator == "unit-render"
    assert take.model == "unit-model"
    assert take.metadata["source"] == "generation_queue"
    assert Path(take.media_path).is_file()


def test_failed_generation_never_creates_fake_take(tmp_path):
    project, still_name = _project_with_still(tmp_path)
    shot = ShotCard(name="Failure", start_frame=still_name)
    queue = GenerationQueue(); queue.enqueue(shot); queue.run(project, BrokenGenerator())
    assert queue.items[0].status == "error"
    assert ProductionStore(project).list_takes(shot_id=shot.id) == []
