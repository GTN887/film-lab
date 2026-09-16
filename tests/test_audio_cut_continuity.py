from types import SimpleNamespace
from film_lab.audio_cut_continuity import analyze_pcm_samples, evaluate_audio_cut, AudioBoundaryMetrics
import film_lab.audio_cut_continuity as ac

def take(path,meta=None): return SimpleNamespace(media_path=str(path),metadata=meta or {})

def test_pcm_metrics_distinguish_silence_and_level():
    quiet=analyze_pcm_samples([0]*1000); loud=analyze_pcm_samples([12000,-12000]*500)
    assert quiet.silence_ratio==1.0 and loud.silence_ratio==0.0 and loud.rms_db>quiet.rms_db

def test_level_jump_and_silence_drop_are_review(monkeypatch,tmp_path):
    a=tmp_path/'a.mp4'; b=tmp_path/'b.mp4'; a.write_bytes(b'x'); b.write_bytes(b'x')
    monkeypatch.setattr(ac,'probe_has_audio',lambda p:True); monkeypatch.setattr(ac,'probe_duration_seconds',lambda p:5.0)
    vals=iter([AudioBoundaryMetrics(-12,-3,.1,100),AudioBoundaryMetrics(-30,-20,.98,100)])
    monkeypatch.setattr(ac,'_decode_window',lambda *args,**kw:next(vals))
    r=evaluate_audio_cut(take(a),take(b)); assert r.status=='REVIEW' and r.level_jump_db==18 and r.silence_gap_risk

def test_explicit_j_cut_is_preserved_not_inferred(monkeypatch,tmp_path):
    a=tmp_path/'a.mp4'; b=tmp_path/'b.mp4'; a.write_bytes(b'x'); b.write_bytes(b'x')
    monkeypatch.setattr(ac,'probe_has_audio',lambda p:True); monkeypatch.setattr(ac,'probe_duration_seconds',lambda p:5.0)
    monkeypatch.setattr(ac,'_decode_window',lambda *args,**kw:AudioBoundaryMetrics(-18,-8,.2,100))
    r=evaluate_audio_cut(take(a),take(b,{'audio_cut_intent':{'j_cut':True}})); assert r.edit_style=='J_CUT' and r.dialogue_handoff_status=='REVIEW'

def test_missing_audio_is_not_tested(monkeypatch,tmp_path):
    a=tmp_path/'a.mp4'; b=tmp_path/'b.mp4'; a.write_bytes(b'x'); b.write_bytes(b'x')
    monkeypatch.setattr(ac,'probe_has_audio',lambda p:False)
    r=evaluate_audio_cut(take(a),take(b)); assert r.status=='NOT_TESTED' and r.level_jump_db is None
