from pathlib import Path
from types import SimpleNamespace
import film_lab.audio_preserving_cinema as apc


def take(path, **intent):
    return SimpleNamespace(media_path=str(path), metadata={"audio_cut_intent": intent})


def test_transition_plan_requires_proven_audio(monkeypatch, tmp_path):
    a,b=tmp_path/'a.mp4',tmp_path/'b.mp4'; a.write_bytes(b'x'); b.write_bytes(b'x')
    monkeypatch.setattr(apc,'probe_has_audio',lambda p: p.name=='a.mp4')
    plan=apc.plan_audio_transition(take(a),take(b))
    assert plan.status=='NOT_TESTED' and plan.audio_preserved is False


def test_transition_plan_honors_explicit_overlap_and_jcut(monkeypatch, tmp_path):
    a,b=tmp_path/'a.mp4',tmp_path/'b.mp4'; a.write_bytes(b'x'); b.write_bytes(b'x')
    monkeypatch.setattr(apc,'probe_has_audio',lambda p: True)
    monkeypatch.setattr(apc,'probe_duration_seconds',lambda p: 4.0)
    plan=apc.plan_audio_transition(take(a),take(b,j_cut=True,audio_overlap_s=.9,picture_in_s=1.0),video_overlap=.5)
    assert plan.status=='PASS' and plan.edit_style=='J_CUT'
    assert plan.audio_overlap_s==.9 and plan.video_overlap_s==.5
    assert plan.j_cut_lead_s==.9 and 'source-handle split-edit' in plan.truth


def test_incoming_take_controls_asymmetric_j_l_timing(monkeypatch, tmp_path):
    a,b=tmp_path/'a.mp4',tmp_path/'b.mp4'; a.write_bytes(b'x'); b.write_bytes(b'x')
    monkeypatch.setattr(apc,'probe_has_audio',lambda p: True)
    monkeypatch.setattr(apc,'probe_duration_seconds',lambda p: 4.0)
    plan=apc.plan_audio_transition(take(a),take(b,j_cut=True,l_cut=True,j_cut_lead_s=.35,l_cut_tail_s=.45,picture_in_s=.5,picture_out_s=3.5))
    assert plan.edit_style=='J_L_CUT' and plan.j_cut_lead_s==.35 and plan.l_cut_tail_s==.45


def test_asymmetric_pair_uses_timed_audio_mix(monkeypatch, tmp_path):
    a,b,o=tmp_path/'a.mp4',tmp_path/'b.mp4',tmp_path/'out.mp4'; a.write_bytes(b'x'); b.write_bytes(b'x')
    monkeypatch.setattr(apc,'probe_has_audio',lambda p: True)
    monkeypatch.setattr(apc,'probe_duration_seconds',lambda p: 4.0)
    seen={}; monkeypatch.setattr(apc,'run_ffmpeg',lambda args: seen.setdefault('args',args))
    plan=apc.CinemaAudioPlan('PASS',True,.6,.6,'J_L_CUT','explicit',.3,.4,.5,3.5,4,4,.5,.5,True,'a->b')
    apc.crossfade_pair_av(a,b,o,video_overlap=.6,transition=plan)
    graph=seen['args'][seen['args'].index('-filter_complex')+1]
    assert 'adelay=3200|3200' in graph and 'atrim=0:3.900' in graph and 'amix=' in graph


def test_crossfade_pair_av_maps_audio_and_video(monkeypatch, tmp_path):
    a,b,o=tmp_path/'a.mp4',tmp_path/'b.mp4',tmp_path/'out.mp4'; a.write_bytes(b'x'); b.write_bytes(b'x')
    monkeypatch.setattr(apc,'probe_has_audio',lambda p: True)
    monkeypatch.setattr(apc,'probe_duration_seconds',lambda p: 4.0)
    seen={}
    monkeypatch.setattr(apc,'run_ffmpeg',lambda args: seen.setdefault('args',args))
    apc.crossfade_pair_av(a,b,o,video_overlap=.4,audio_overlap=.3)
    args=seen['args']; graph=args[args.index('-filter_complex')+1]
    assert 'xfade=' in graph and 'acrossfade=' in graph
    assert '[v]' in args and '[a]' in args and '-an' not in args


def test_cinema_export_prefers_av_stitch_when_all_audio(monkeypatch, tmp_path):
    import film_lab.cinema_export as ce
    a,b=tmp_path/'a.mp4',tmp_path/'b.mp4'; a.write_bytes(b'x'); b.write_bytes(b'x')
    takes=[take(a),take(b,j_cut=True,j_cut_lead_s=.25)]
    class Store:
        def __init__(self,p): pass
        def selected_takes(self,existing_media_only=True): return takes
    monkeypatch.setattr(ce,'ProductionStore',Store)
    monkeypatch.setattr(ce,'probe_has_audio',lambda p: True)
    monkeypatch.setattr(ce,'plan_audio_transition',lambda a,b,video_overlap: apc.CinemaAudioPlan('PASS',True,.6,.6,'J_CUT','',.25,0,.5,4,4,4,.5,0,True,'a->b'))
    called={}
    def av(clips,out,**kw): called['av']=kw; return out
    monkeypatch.setattr(ce,'stitch_clips_av',av)
    monkeypatch.setattr(ce,'stitch_clips',lambda *a,**k: (_ for _ in ()).throw(AssertionError('visual fallback used')))
    out=ce.export_selected(object(),tmp_path/'final.mp4')
    assert called['av']['transitions'][0].edit_style=='J_CUT' and out.name=='final.mp4'


def test_stitch_passes_each_boundary_plan(monkeypatch, tmp_path):
    clips=[tmp_path/f'{x}.mp4' for x in 'abc']
    for clip in clips: clip.write_bytes(b'x')
    seen=[]
    monkeypatch.setattr(apc,'crossfade_pair_av',lambda *a,**kw: (seen.append(kw.get('transition')), a[2].write_bytes(b'x'))[1] or a[2])
    plans=[apc.CinemaAudioPlan('PASS',True,.6,.6,'J_CUT','',.2,0),apc.CinemaAudioPlan('PASS',True,.6,.6,'L_CUT','',0,.3)]
    apc.stitch_clips_av(clips,tmp_path/'out.mp4',transitions=plans)
    assert [p.edit_style for p in seen]==['J_CUT','L_CUT']
