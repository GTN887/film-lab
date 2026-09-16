from pathlib import Path
from types import SimpleNamespace

import pytest

import film_lab.audio_preserving_cinema as apc
from film_lab.ffmpeg_support import FFmpegError


def take(path, take_id, **intent):
    return SimpleNamespace(id=take_id, media_path=str(path), metadata={"audio_cut_intent": intent})


def plan(monkeypatch, tmp_path, incoming=None, outgoing=None, durations=(6.0, 5.0)):
    a, b = tmp_path / "a.mp4", tmp_path / "b.mp4"
    a.write_bytes(b"a"); b.write_bytes(b"b")
    monkeypatch.setattr(apc, "probe_has_audio", lambda p: True)
    monkeypatch.setattr(apc, "probe_duration_seconds", lambda p: durations[0] if p.name == "a.mp4" else durations[1])
    return apc.plan_audio_transition(take(a, "take-a", **(outgoing or {})), take(b, "take-b", **(incoming or {})))


def test_hard_cut_needs_no_split_handles(monkeypatch, tmp_path):
    p = plan(monkeypatch, tmp_path)
    assert p.status == "PASS" and p.enforced and p.edit_style == "HARD_CUT"


def test_j_cut_uses_proven_incoming_preroll(monkeypatch, tmp_path):
    p = plan(monkeypatch, tmp_path, {"j_cut": True, "j_cut_lead_s": .5, "picture_in_s": .75})
    assert p.status == "PASS" and p.j_handle_available_s == .75


def test_j_cut_rejects_missing_preroll(monkeypatch, tmp_path):
    p = plan(monkeypatch, tmp_path, {"j_cut": True, "j_cut_lead_s": .5, "picture_in_s": .2})
    assert p.status == "FAIL" and not p.enforced and "not fabricate" in p.truth


def test_l_cut_uses_proven_outgoing_postroll(monkeypatch, tmp_path):
    p = plan(monkeypatch, tmp_path, {"l_cut": True, "l_cut_tail_s": .6, "picture_out_s": 5.25})
    assert p.status == "PASS" and p.l_handle_available_s == .75


def test_l_cut_rejects_missing_postroll(monkeypatch, tmp_path):
    p = plan(monkeypatch, tmp_path, {"l_cut": True, "l_cut_tail_s": .6, "picture_out_s": 5.8})
    assert p.status == "FAIL" and not p.enforced


def test_combined_split_edit_validates_both_handles(monkeypatch, tmp_path):
    p = plan(monkeypatch, tmp_path, {"j_cut": True, "l_cut": True, "j_cut_lead_s": .4, "l_cut_tail_s": .5, "picture_in_s": .5, "picture_out_s": 5.4})
    assert p.status == "PASS" and p.edit_style == "J_L_CUT"


def test_split_edit_requires_proven_source_durations(monkeypatch, tmp_path):
    p = plan(monkeypatch, tmp_path, {"j_cut": True, "j_cut_lead_s": .2, "picture_in_s": .4}, durations=(0.0, 0.0))
    assert p.status == "FAIL" and not p.enforced


def test_picture_in_must_be_inside_incoming_source(monkeypatch, tmp_path):
    p = plan(monkeypatch, tmp_path, {"j_cut": True, "j_cut_lead_s": .2, "picture_in_s": 5.0})
    assert p.status == "FAIL"


def test_picture_out_must_be_inside_outgoing_source(monkeypatch, tmp_path):
    p = plan(monkeypatch, tmp_path, {"l_cut": True, "l_cut_tail_s": .2, "picture_out_s": 6.1})
    assert p.status == "FAIL"


def test_plan_records_take_provenance(monkeypatch, tmp_path):
    p = plan(monkeypatch, tmp_path)
    assert p.provenance == "take-a->take-b"


def test_director_handle_request_is_safety_bounded(monkeypatch, tmp_path):
    p = plan(monkeypatch, tmp_path, {"j_cut": True, "j_cut_lead_s": 9, "picture_in_s": 3})
    assert p.j_cut_lead_s == 2.0 and p.enforced


def test_split_graph_trims_picture_at_explicit_points(monkeypatch, tmp_path):
    a,b,o=tmp_path/'a.mp4',tmp_path/'b.mp4',tmp_path/'out.mp4'; a.write_bytes(b'a'); b.write_bytes(b'b')
    monkeypatch.setattr(apc,'probe_has_audio',lambda p: True); monkeypatch.setattr(apc,'probe_duration_seconds',lambda p: 6.0 if p.name=='a.mp4' else 5.0)
    seen={}; monkeypatch.setattr(apc,'run_ffmpeg',lambda args: seen.setdefault('args',args))
    p=apc.CinemaAudioPlan('PASS',True,.6,.6,'J_L_CUT','',.4,.5,.75,5.25,5,6,.75,.75,True,'a->b')
    apc.crossfade_pair_av(a,b,o,transition=p)
    graph=seen['args'][seen['args'].index('-filter_complex')+1]
    assert 'trim=start=0:end=5.250' in graph and 'trim=start=0.750:end=5.000' in graph


def test_split_graph_reads_incoming_audio_preroll(monkeypatch, tmp_path):
    a,b,o=tmp_path/'a.mp4',tmp_path/'b.mp4',tmp_path/'out.mp4'; a.write_bytes(b'a'); b.write_bytes(b'b')
    monkeypatch.setattr(apc,'probe_has_audio',lambda p: True); monkeypatch.setattr(apc,'probe_duration_seconds',lambda p: 6.0 if p.name=='a.mp4' else 5.0)
    seen={}; monkeypatch.setattr(apc,'run_ffmpeg',lambda args: seen.setdefault('args',args))
    p=apc.CinemaAudioPlan('PASS',True,.6,.6,'J_CUT','',.4,0,.75,6,5,6,.75,0,True,'a->b')
    apc.crossfade_pair_av(a,b,o,transition=p)
    assert 'atrim=start=0.350:end=5.000' in seen['args'][seen['args'].index('-filter_complex')+1]


def test_unenforced_split_edit_never_runs_ffmpeg(monkeypatch, tmp_path):
    a,b,o=tmp_path/'a.mp4',tmp_path/'b.mp4',tmp_path/'out.mp4'; a.write_bytes(b'a'); b.write_bytes(b'b')
    monkeypatch.setattr(apc,'probe_has_audio',lambda p: True); monkeypatch.setattr(apc,'probe_duration_seconds',lambda p: 5.0)
    monkeypatch.setattr(apc,'run_ffmpeg',lambda args: (_ for _ in ()).throw(AssertionError('must not run')))
    p=apc.CinemaAudioPlan('FAIL',True,.6,.6,'J_CUT','',.5,0,.1,5,5,5,.1,0,False,'a->b')
    with pytest.raises(FFmpegError, match='not enforceable'): apc.crossfade_pair_av(a,b,o,transition=p)


def test_missing_audio_is_not_split_edit_proof(monkeypatch, tmp_path):
    a,b=tmp_path/'a.mp4',tmp_path/'b.mp4'; a.write_bytes(b'a'); b.write_bytes(b'b')
    monkeypatch.setattr(apc,'probe_has_audio',lambda p: p.name=='a.mp4')
    p=apc.plan_audio_transition(take(a,'a'),take(b,'b',j_cut=True,picture_in_s=.5,j_cut_lead_s=.2))
    assert p.status=='NOT_TESTED' and not p.audio_preserved
