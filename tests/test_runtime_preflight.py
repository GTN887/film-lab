import json
from types import SimpleNamespace
import film_lab.runtime_preflight as pf


def _workflow(tmp_path, model="model.safetensors"):
    d=tmp_path/"workflows"; d.mkdir()
    (d/"i2v.json").write_text(json.dumps({"1":{"class_type":"LoadImage","inputs":{}},"2":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":model}}}),encoding="utf-8")
    return d


def test_preflight_ready_when_comfy_workflow_model_and_ffmpeg_are_ready(tmp_path, monkeypatch):
    wd=_workflow(tmp_path)
    obj={"LoadImage":{},"CheckpointLoaderSimple":{"input":{"required":{"ckpt_name":[["model.safetensors"],{}]}}}}
    discovery=SimpleNamespace(available=True,endpoint="http://local",node_count=2,error="",to_dict=lambda:{"available":True})
    monkeypatch.setattr(pf,"discover_comfyui",lambda endpoint,timeout=3.0:discovery)
    monkeypatch.setattr(pf,"ffmpeg_available",lambda:(True,"ffmpeg ok"))
    monkeypatch.setattr(pf,"_get_json",lambda endpoint,path,timeout=3.0: obj if path=="/object_info" else {"devices":[{"name":"AMD Radeon Test GPU"}]})
    report=pf.run_preflight(endpoint="http://local",workflow_dir=wd)
    assert report.ready
    assert report.gpu_devices==("AMD Radeon Test GPU",)
    assert report.selected_workflow=="i2v"
    assert report.required_models==("model.safetensors",)


def test_preflight_blocks_when_required_model_is_missing(tmp_path, monkeypatch):
    wd=_workflow(tmp_path,"missing.safetensors")
    obj={"LoadImage":{},"CheckpointLoaderSimple":{"input":{"required":{"ckpt_name":[["other.safetensors"],{}]}}}}
    discovery=SimpleNamespace(available=True,endpoint="http://local",node_count=2,error="",to_dict=lambda:{"available":True})
    monkeypatch.setattr(pf,"discover_comfyui",lambda endpoint,timeout=3.0:discovery)
    monkeypatch.setattr(pf,"ffmpeg_available",lambda:(True,"ok"))
    monkeypatch.setattr(pf,"_get_json",lambda endpoint,path,timeout=3.0: obj if path=="/object_info" else {"devices":[{"name":"AMD"}]})
    report=pf.run_preflight(endpoint="http://local",workflow_dir=wd)
    assert not report.ready
    assert report.selected_workflow==""
    assert any("No locally runnable workflow" in x for x in report.blockers)


def test_preflight_blocks_disconnected_comfyui_without_claiming_gpu(tmp_path, monkeypatch):
    discovery=SimpleNamespace(available=False,endpoint="http://local",node_count=0,error="ComfyUI offline",to_dict=lambda:{"available":False})
    monkeypatch.setattr(pf,"discover_comfyui",lambda endpoint,timeout=3.0:discovery)
    monkeypatch.setattr(pf,"ffmpeg_available",lambda:(True,"ok"))
    report=pf.run_preflight(endpoint="http://local",workflow_dir=tmp_path)
    assert not report.ready and not report.comfyui_connected
    assert report.gpu_devices==()
    assert "ComfyUI offline" in report.blockers


def test_preflight_blocks_missing_ffmpeg(tmp_path, monkeypatch):
    wd=_workflow(tmp_path)
    obj={"LoadImage":{},"CheckpointLoaderSimple":{"input":{"required":{"ckpt_name":[["model.safetensors"],{}]}}}}
    discovery=SimpleNamespace(available=True,endpoint="http://local",node_count=2,error="",to_dict=lambda:{"available":True})
    monkeypatch.setattr(pf,"discover_comfyui",lambda endpoint,timeout=3.0:discovery)
    monkeypatch.setattr(pf,"ffmpeg_available",lambda:(False,"missing"))
    monkeypatch.setattr(pf,"_get_json",lambda endpoint,path,timeout=3.0: obj if path=="/object_info" else {"devices":[{"name":"AMD"}]})
    report=pf.run_preflight(endpoint="http://local",workflow_dir=wd)
    assert not report.ready
    assert any("ffmpeg" in x for x in report.blockers)
