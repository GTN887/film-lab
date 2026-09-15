from pathlib import Path
import pytest
from film_lab.project import Project
from film_lab.production import ProductionStore
from film_lab.render_service import generate_take, import_take
from film_lab.shot_card import ShotCard

class FakeGenerator:
    id = "fake-real-engine"; label = "Fake Real Engine"
    def generate(self, job):
        job.output_path.parent.mkdir(parents=True, exist_ok=True); job.output_path.write_bytes(b"not-empty-video-for-contract-test"); return job.output_path
class BrokenGenerator:
    id = "broken"; label = "Broken"
    def generate(self, job): return job.output_path

def _project(tmp_path): return Project.create("movie", data_root=tmp_path / "projects")
def _still(tmp_path):
    p = tmp_path / "start.png"; p.write_bytes(b"image"); return p

def test_generation_automatically_creates_persistent_take(tmp_path):
    project = _project(tmp_path); shot = ShotCard(id="shot_101", name="Run and hide", scene_id="scene_007")
    result = generate_take(project, shot, _still(tmp_path), FakeGenerator(), model="unit-model")
    assert result.take.shot_id == "shot_101" and result.take.scene_id == "scene_007" and result.take.generator == "fake-real-engine" and result.take.model == "unit-model" and Path(result.take.media_path).is_file()
    reopened = ProductionStore(Project.load("movie", data_root=tmp_path / "projects")).get_take(result.take.id); assert reopened.id == result.take.id

def test_failed_generation_never_creates_fake_take(tmp_path):
    project = _project(tmp_path); shot = ShotCard(id="shot_101")
    with pytest.raises(RuntimeError): generate_take(project, shot, _still(tmp_path), BrokenGenerator())
    assert ProductionStore(project).list_takes() == []

def test_import_uses_same_take_store(tmp_path):
    project = _project(tmp_path); video = tmp_path / "import.mp4"; video.write_bytes(b"video")
    take = import_take(project, video, shot_id="shot_002", scene_id="scene_003", director_notes="Hold longer", tags=["wide"])
    assert take.generator == "import" and take.director_notes == "Hold longer" and take.tags == ["wide"]
