from pathlib import Path
import film_lab.ffmpeg_support as fs

def test_probe_has_audio_true(monkeypatch,tmp_path):
    class P: returncode=0; stdout="audio\n"
    monkeypatch.setattr(fs,"find_ffprobe",lambda:"ffprobe")
    monkeypatch.setattr(fs.subprocess,"run",lambda *a,**k:P())
    assert fs.probe_has_audio(tmp_path/"x.mp4") is True

def test_probe_has_audio_unknown_without_ffprobe(monkeypatch,tmp_path):
    monkeypatch.setattr(fs,"find_ffprobe",lambda:None)
    assert fs.probe_has_audio(tmp_path/"x.mp4") is None
