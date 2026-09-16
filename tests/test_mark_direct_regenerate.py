from pathlib import Path

import pytest

from film_lab.mark_direct_regenerate import MarkDirectRegenerationError, regenerate_take
from film_lab.production import ProductionStore
from film_lab.project import Project
from film_lab.shot_card import ShotCard


class FakeGenerator:
    id = "fake-directed"
    label = "Fake Directed Generator"
    model = "fake-v1"
    def generate(self, job):
        job.output_path.parent.mkdir(parents=True, exist_ok=True)
        job.output_path.write_bytes(b"directed-video")
        return job.output_path


class FailingGenerator(FakeGenerator):
    def generate(self, job):
        raise RuntimeError("renderer unavailable")


def make_project(tmp_path):
    project = Project.create("mark-direct", data_root=tmp_path / "projects")
    shot = ShotCard(id="shot-a", name="Run and hide", scene_id="scene-a")
    project.save_shot(shot)
    src = tmp_path / "source.mp4"
    src.write_bytes(b"source-video")
    take = ProductionStore(project).add_take(src, scene_id="scene-a", shot_id="shot-a", name="Take 1")
    return project, take


def test_mark_direct_forks_new_take_and_preserves_source(tmp_path, monkeypatch):
    project, source = make_project(tmp_path)
    # Avoid depending on ffmpeg in this unit test; the service contract is the target.
    def fake_still(source_path, dest):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"png")
        return dest
    monkeypatch.setattr("film_lab.mark_direct_regenerate.still_from_source", fake_still)
    new_take = regenerate_take(project, source_take_id=source.id, generator=FakeGenerator(), director_instruction="Run faster and duck behind the wall")
    store = ProductionStore(project)
    assert store.get_take(source.id).id == source.id
    assert new_take.id != source.id
    assert new_take.scene_id == source.scene_id
    assert new_take.shot_id == source.shot_id
    assert Path(new_take.media_path).is_file()
    assert new_take.metadata["source"] == "mark_direct_regeneration"
    assert new_take.metadata["source_take_id"] == source.id
    assert "Run faster" in new_take.prompt


def test_mark_direct_failure_creates_no_fake_take(tmp_path, monkeypatch):
    project, source = make_project(tmp_path)
    monkeypatch.setattr("film_lab.mark_direct_regenerate.still_from_source", lambda source_path, dest: dest.parent.mkdir(parents=True, exist_ok=True) or dest.write_bytes(b"png") or dest)
    before = len(ProductionStore(project).list_takes())
    with pytest.raises(MarkDirectRegenerationError):
        regenerate_take(project, source_take_id=source.id, generator=FailingGenerator(), director_instruction="Change expression")
    assert len(ProductionStore(project).list_takes()) == before
