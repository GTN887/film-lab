from pathlib import Path
from tempfile import TemporaryDirectory

from film_lab.project import Project
from film_lab.takes import TakeStore


def fake_video(path: Path, marker: bytes = b"film-lab-test") -> Path:
    path.write_bytes(marker)
    return path


def test_add_take_persists_and_copies_media():
    with TemporaryDirectory() as td:
        root = Path(td)
        project = Project.create("movie", data_root=root / "projects")
        source = fake_video(root / "source.mp4")
        take = TakeStore(project).add_video(source, scene_id="scene-1", shot_id="shot-1", generator="test-engine", model="test-model", notes="Run", tags=["wide"])
        reloaded = TakeStore(Project.load("movie", data_root=root / "projects")).get(take.id)
        assert reloaded.status == "Review"
        assert reloaded.generator == "test-engine"
        assert reloaded.model == "test-model"
        assert reloaded.notes == "Run"
        assert reloaded.tags == ["wide"]
        assert Path(reloaded.media_path).is_file()
        assert Path(reloaded.media_path) != source


def test_exactly_one_selected_take_per_shot():
    with TemporaryDirectory() as td:
        root = Path(td); project = Project.create("movie", data_root=root / "projects"); store = TakeStore(project)
        a = store.add_video(fake_video(root / "a.mp4", b"a"), scene_id="s1", shot_id="sh1")
        b = store.add_video(fake_video(root / "b.mp4", b"b"), scene_id="s1", shot_id="sh1")
        store.update(a.id, status="Selected")
        store.update(b.id, status="Selected")
        assert store.get(a.id).status == "Review"
        assert store.get(b.id).status == "Selected"
        assert store.selected(scene_id="s1", shot_id="sh1").id == b.id


def test_selection_is_scoped_to_scene_and_shot():
    with TemporaryDirectory() as td:
        root = Path(td); project = Project.create("movie", data_root=root / "projects"); store = TakeStore(project)
        a = store.add_video(fake_video(root / "a.mp4"), scene_id="s1", shot_id="sh1")
        b = store.add_video(fake_video(root / "b.mp4"), scene_id="s1", shot_id="sh2")
        store.update(a.id, status="Selected"); store.update(b.id, status="Selected")
        assert len([t for t in store.list(scene_id="s1") if t.status == "Selected"]) == 2


def test_notes_tags_rejection_and_cinema_manifest_survive_restart():
    with TemporaryDirectory() as td:
        root = Path(td); data_root = root / "projects"; project = Project.create("movie", data_root=data_root); store = TakeStore(project)
        a = store.add_video(fake_video(root / "a.mp4"), scene_id="s1", shot_id="sh1")
        b = store.add_video(fake_video(root / "b.mp4"), scene_id="s1", shot_id="sh2")
        store.update(a.id, status="Selected", notes="Keep performance", tags=["hero", "hero", "close"])
        store.update(b.id, status="Rejected")
        restarted = TakeStore(Project.load("movie", data_root=data_root))
        assert restarted.get(a.id).notes == "Keep performance"
        assert restarted.get(a.id).tags == ["hero", "close"]
        assert restarted.get(b.id).status == "Rejected"
        manifest = restarted.cinema_manifest(scene_id="s1")
        assert [x["take_id"] for x in manifest] == [a.id]


def test_requires_real_supported_video_file():
    with TemporaryDirectory() as td:
        root = Path(td); store = TakeStore(Project.create("movie", data_root=root / "projects"))
        try:
            store.add_video(root / "missing.mp4", scene_id="s1", shot_id="sh1")
        except ValueError as exc:
            assert "real supported video" in str(exc)
        else:
            raise AssertionError("missing media must not create a Take")
