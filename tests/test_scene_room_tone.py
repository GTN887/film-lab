import json
from pathlib import Path

import pytest

import film_lab.room_tone as rt
from film_lab.project import Project
from film_lab.production import ProductionStore
from film_lab.room_tone import RoomToneStore, SceneRoomTone


def project(tmp_path): return Project.create("room-tone", data_root=tmp_path / "projects")


def audio(tmp_path, name="room.wav"):
    p=tmp_path/name; p.write_bytes(b"real-audio-fixture"); return p


def test_assignment_copies_media_and_persists_provenance(tmp_path):
    p=project(tmp_path); state=RoomToneStore(p).assign("scene-1",audio(tmp_path),director_note="Bedroom night")
    again=RoomToneStore(Project.load(p.name,data_root=tmp_path/"projects")).get("scene-1")
    assert Path(state.media_path).is_file() and again==state and len(state.source_sha256)==64


def test_assignment_is_scene_scoped(tmp_path):
    p=project(tmp_path); store=RoomToneStore(p)
    a=store.assign("scene-a",audio(tmp_path,"a.wav")); b=store.assign("scene-b",audio(tmp_path,"b.wav"))
    assert store.get("scene-a")==a and store.get("scene-b")==b


def test_assignment_rejects_non_audio(tmp_path):
    p=project(tmp_path); bad=tmp_path/"note.txt"; bad.write_text("no")
    with pytest.raises(ValueError,match="audio file"): RoomToneStore(p).assign("scene",bad)


def test_assignment_validates_gain_and_fades(tmp_path):
    p=project(tmp_path); src=audio(tmp_path)
    with pytest.raises(ValueError,match="gain"): RoomToneStore(p).assign("scene",src,gain_db=20)
    with pytest.raises(ValueError,match="fades"): RoomToneStore(p).assign("scene",src,fade_in_s=11)


def test_enabled_state_survives_reload(tmp_path):
    p=project(tmp_path); store=RoomToneStore(p); store.assign("scene",audio(tmp_path))
    assert store.set_enabled("scene",False).enabled is False and RoomToneStore(p).get("scene").enabled is False


def test_project_creates_room_tone_media_directory(tmp_path):
    p=project(tmp_path); assert (p.audio_dir/"room_tone").is_dir()


def test_mix_combines_existing_program_audio(monkeypatch,tmp_path):
    pic=tmp_path/"p.mp4"; bed=audio(tmp_path); pic.write_bytes(b"video"); seen={}
    monkeypatch.setattr(rt,"probe_duration_seconds",lambda p:4.0); monkeypatch.setattr(rt,"probe_has_audio",lambda p:True)
    monkeypatch.setattr(rt,"run_ffmpeg",lambda args:seen.setdefault("args",args))
    rt.mix_room_tone(pic,SceneRoomTone("s",str(bed),gain_db=-20),tmp_path/"out.mp4")
    graph=seen["args"][seen["args"].index("-filter_complex")+1]
    assert "amix=inputs=2" in graph and seen["args"][seen["args"].index("-map",seen["args"].index("-map")+1)+1]=="[a]"


def test_mix_adds_bed_when_picture_is_silent(monkeypatch,tmp_path):
    pic=tmp_path/"p.mp4"; bed=audio(tmp_path); pic.write_bytes(b"video"); seen={}
    monkeypatch.setattr(rt,"probe_duration_seconds",lambda p:3.0); monkeypatch.setattr(rt,"probe_has_audio",lambda p:False)
    monkeypatch.setattr(rt,"run_ffmpeg",lambda args:seen.setdefault("args",args))
    rt.mix_room_tone(pic,SceneRoomTone("s",str(bed)),tmp_path/"out.mp4")
    assert "[bed]" in seen["args"] and "amix=inputs=2" not in seen["args"][seen["args"].index("-filter_complex")+1]


def test_disabled_mix_copies_picture_without_ffmpeg(monkeypatch,tmp_path):
    pic=tmp_path/"p.mp4"; bed=audio(tmp_path); pic.write_bytes(b"video")
    monkeypatch.setattr(rt,"run_ffmpeg",lambda args:(_ for _ in ()).throw(AssertionError("must not run")))
    out=rt.mix_room_tone(pic,SceneRoomTone("s",str(bed),enabled=False),tmp_path/"out.mp4")
    assert out.read_bytes()==b"video"


def test_scene_assembly_reports_persistent_room_tone(monkeypatch,tmp_path):
    import film_lab.scene_assembly_intelligence as sai
    p=project(tmp_path); src=tmp_path/"take.mp4"; src.write_bytes(b"video")
    s=ProductionStore(p); t=s.add_take(src,scene_id="scene",shot_id="shot",copy_media=False); s.set_status(t.id,"selected")
    RoomToneStore(p).assign("scene",audio(tmp_path))
    report=sai.evaluate_scene(p,"scene")
    assert report.room_tone_status=="PASS" and report.room_tone_path


def test_scene_assembly_does_not_guess_unassigned_room_tone(tmp_path):
    import film_lab.scene_assembly_intelligence as sai
    p=project(tmp_path); src=tmp_path/"take.mp4"; src.write_bytes(b"video")
    s=ProductionStore(p); t=s.add_take(src,scene_id="scene",shot_id="shot",copy_media=False); s.set_status(t.id,"selected")
    assert sai.evaluate_scene(p,"scene").room_tone_status=="NOT TESTED"


def test_missing_assigned_room_tone_blocks_scene_readiness(tmp_path):
    import film_lab.scene_assembly_intelligence as sai
    p=project(tmp_path); src=tmp_path/"take.mp4"; src.write_bytes(b"video")
    s=ProductionStore(p); t=s.add_take(src,scene_id="scene",shot_id="shot",copy_media=False); s.set_status(t.id,"selected")
    state=RoomToneStore(p).assign("scene",audio(tmp_path)); Path(state.media_path).unlink()
    report=sai.evaluate_scene(p,"scene")
    assert report.room_tone_status=="FAIL" and report.status=="FAIL" and not report.cinema_ready


def test_cinema_room_tone_writes_auditable_manifest(monkeypatch,tmp_path):
    import film_lab.cinema_export as ce
    p=project(tmp_path); src=tmp_path/"take.mp4"; src.write_bytes(b"video")
    s=ProductionStore(p); t=s.add_take(src,scene_id="scene",shot_id="shot",copy_media=False); s.set_status(t.id,"selected")
    RoomToneStore(p).assign("scene",audio(tmp_path))
    monkeypatch.setattr(ce,"_assemble",lambda selected,out,overlap:(out.write_bytes(b"base") or out))
    monkeypatch.setattr(ce,"mix_room_tone",lambda base,state,out:(out.write_bytes(b"mixed") or out))
    out=ce.export_selected(p,tmp_path/"film.mp4")
    audit=json.loads(out.with_suffix(".audio_edit.json").read_text())
    assert out.read_bytes()==b"mixed" and audit["scenes"][0]["room_tone_enforced"] is True and audit["scenes"][0]["selected_take_ids"]==[t.id]
