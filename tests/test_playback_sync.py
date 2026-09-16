from pathlib import Path
from film_lab.project import Project
from film_lab.production import ProductionStore
from film_lab.playback_sync import PlaybackSyncStore, resolve_playback, cursor_percent

def mk(tmp_path): return Project.create("p",data_root=tmp_path)
def video(p): p.write_bytes(b"real-media-boundary"); return p

def test_resolves_exact_selected_scene_shot(tmp_path):
    p=mk(tmp_path); s=ProductionStore(p)
    a=s.add_take(video(tmp_path/"a.mp4"),scene_id="s1",shot_id="q1",copy_media=False,duration=10); s.set_status(a.id,"selected")
    b=s.add_take(video(tmp_path/"b.mp4"),scene_id="s2",shot_id="q1",copy_media=False,duration=8); s.set_status(b.id,"selected")
    st=resolve_playback(p,"s1","q1")
    assert st.take_id==a.id and st.media_path.endswith("a.mp4") and st.status=="READY"

def test_playhead_persists_and_clamps_to_known_duration(tmp_path):
    p=mk(tmp_path); s=ProductionStore(p); t=s.add_take(video(tmp_path/"a.mp4"),scene_id="s",shot_id="q",copy_media=False,duration=5); s.set_status(t.id,"selected")
    saved=PlaybackSyncStore(p).save_playhead("s","q",9)
    assert saved.playhead_s==5
    assert resolve_playback(p,"s","q").playhead_s==5

def test_cursor_percent_is_truthful(tmp_path):
    p=mk(tmp_path); s=ProductionStore(p); t=s.add_take(video(tmp_path/"a.mp4"),scene_id="s",shot_id="q",copy_media=False,duration=8); s.set_status(t.id,"selected")
    st=PlaybackSyncStore(p).save_playhead("s","q",2)
    assert cursor_percent(st)==25.0

def test_no_selected_take_is_explicit(tmp_path):
    st=resolve_playback(mk(tmp_path),"s","q")
    assert st.status=="NO_SELECTED_TAKE" and not st.media_path
