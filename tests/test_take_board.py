from pathlib import Path
import pytest

from film_lab.production import ProductionStore
from film_lab.project import Project
from film_lab.take_board import TakeBoardError, export_selected_to_cinema, reject_take, review_take, save_take_direction, select_take, selected_take_for_shot, take_cards


def video(tmp_path: Path, name: str) -> Path:
    p = tmp_path / name; p.write_bytes(b"video-bytes"); return p


def setup(tmp_path):
    p = Project.create("movie", data_root=tmp_path / "projects")
    s = ProductionStore(p)
    a = s.add_take(video(tmp_path, "a.mp4"), shot_id="shot_001")
    b = s.add_take(video(tmp_path, "b.mp4"), shot_id="shot_001")
    return p, a, b


def test_take_board_controls_are_persistent(tmp_path):
    p, a, b = setup(tmp_path)
    select_take(p, a.id)
    save_take_direction(p, a.id, director_notes="Hold longer", tags=["hero", "close"])
    reject_take(p, b.id)
    p2 = Project.load("movie", data_root=tmp_path / "projects")
    cards = {x["id"]: x for x in take_cards(p2)}
    assert cards[a.id]["status"] == "selected" and cards[a.id]["director_notes"] == "Hold longer"
    assert cards[b.id]["status"] == "rejected"
    assert selected_take_for_shot(p2, "shot_001").id == a.id


def test_review_control_returns_take_to_review(tmp_path):
    p, a, _ = setup(tmp_path); select_take(p, a.id)
    assert review_take(p, a.id).status == "review"


def test_missing_media_cannot_be_selected(tmp_path):
    p, a, _ = setup(tmp_path); Path(a.media_path).unlink()
    with pytest.raises(TakeBoardError): select_take(p, a.id)


def test_single_selected_take_exports_real_file_without_ffmpeg(tmp_path):
    p, a, _ = setup(tmp_path); select_take(p, a.id)
    out = export_selected_to_cinema(p)
    assert out.is_file() and out.read_bytes() == Path(a.media_path).read_bytes()
    assert any(Path(x.path).resolve() == out.resolve() for x in p.load_gallery())


def test_cinema_refuses_empty_selection(tmp_path):
    p, _, _ = setup(tmp_path)
    with pytest.raises(TakeBoardError): export_selected_to_cinema(p)
