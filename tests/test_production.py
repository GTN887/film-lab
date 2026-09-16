from pathlib import Path
from film_lab.project import Project
from film_lab.production import ProductionStore


def _video(tmp_path: Path, name: str = "clip.mp4") -> Path:
    p = tmp_path / name; p.write_bytes(b"fake-mp4-for-store-test"); return p


def test_take_is_copied_and_persists(tmp_path):
    p = Project.create("movie", data_root=tmp_path / "projects")
    store = ProductionStore(p)
    t = store.add_take(_video(tmp_path), shot_id="shot_001", generator="test", model="unit")
    assert Path(t.media_path).is_file()
    again = ProductionStore(Project.load("movie", data_root=tmp_path / "projects")).get_take(t.id)
    assert again.generator == "test" and again.model == "unit"


def test_only_one_selected_take_per_shot(tmp_path):
    p = Project.create("movie", data_root=tmp_path / "projects"); s = ProductionStore(p)
    a = s.add_take(_video(tmp_path, "a.mp4"), shot_id="shot_001")
    b = s.add_take(_video(tmp_path, "b.mp4"), shot_id="shot_001")
    s.set_status(a.id, "selected"); s.set_status(b.id, "selected")
    assert s.get_take(a.id).status == "review"
    assert s.get_take(b.id).status == "selected"


def test_notes_tags_survive_restart(tmp_path):
    p = Project.create("movie", data_root=tmp_path / "projects"); s = ProductionStore(p)
    t = s.add_take(_video(tmp_path), shot_id="shot_001")
    s.update_notes(t.id, director_notes="More fear in the eyes", tags=["close-up", "hero", "hero"])
    t2 = ProductionStore(Project.load("movie", data_root=tmp_path / "projects")).get_take(t.id)
    assert t2.director_notes == "More fear in the eyes" and t2.tags == ["close-up", "hero"]


def test_cinema_manifest_contains_selected_existing_media(tmp_path):
    p = Project.create("movie", data_root=tmp_path / "projects"); s = ProductionStore(p)
    a = s.add_take(_video(tmp_path, "a.mp4"), shot_id="shot_001")
    s.add_take(_video(tmp_path, "b.mp4"), shot_id="shot_002")
    s.set_status(a.id, "selected")
    manifest = s.cinema_manifest()
    assert len(manifest) == 1 and manifest[0]["take_id"] == a.id


def test_reject_take(tmp_path):
    p = Project.create("movie", data_root=tmp_path / "projects"); s = ProductionStore(p)
    t = s.add_take(_video(tmp_path), shot_id="shot_001")
    assert s.set_status(t.id, "rejected").status == "rejected"

def test_single_selected_take_exports_without_fake_render(tmp_path):
    from film_lab.cinema_export import export_selected
    p=Project.create("movie",data_root=tmp_path/"projects"); s=ProductionStore(p)
    t=s.add_take(_video(tmp_path,"only.mp4"),shot_id="shot_001"); s.set_status(t.id,"selected")
    out=export_selected(p,tmp_path/"final.mp4")
    assert out.read_bytes()==b"fake-mp4-for-store-test"

def test_cinema_export_requires_selection(tmp_path):
    import pytest
    from film_lab.cinema_export import export_selected
    p=Project.create("movie",data_root=tmp_path/"projects")
    with pytest.raises(ValueError,match="no Selected Takes"):
        export_selected(p,tmp_path/"final.mp4")

def test_selected_take_is_scoped_by_scene_and_shot(tmp_path):
    project = Project.create("scene-scope", data_root=tmp_path / "projects")
    store = ProductionStore(project)
    a = tmp_path / "a.mp4"; a.write_bytes(b"a")
    b = tmp_path / "b.mp4"; b.write_bytes(b"b")
    take_a = store.add_take(a, scene_id="scene-a", shot_id="shot-1")
    take_b = store.add_take(b, scene_id="scene-b", shot_id="shot-1")
    store.set_status(take_a.id, "selected")
    store.set_status(take_b.id, "selected")
    assert store.get_take(take_a.id).status == "selected"
    assert store.get_take(take_b.id).status == "selected"
