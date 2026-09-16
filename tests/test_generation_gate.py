from types import SimpleNamespace
from film_lab.generation_gate import requested_capabilities_for_shot, preflight_generation


def test_shot_intent_maps_to_preflight_capabilities():
    shot=SimpleNamespace(end_frame="end.png", character_ids=["char_1"], camera_move="orbit")
    req=requested_capabilities_for_shot(shot)
    assert "start_image" in req and "end_image" in req
    assert "reference_images" in req and "camera_control" in req


def test_gate_blocks_not_ready(monkeypatch):
    import film_lab.generation_gate as module
    report=SimpleNamespace(ready=False, blockers=("ComfyUI unavailable",), missing_models=(), missing_nodes=(), selected_workflow="", gpu_devices=(), unsupported_capabilities=())
    monkeypatch.setattr(module,"run_preflight",lambda **kwargs: report)
    gate=preflight_generation(SimpleNamespace(end_frame="",character_ids=[],camera_move="static"))
    assert not gate.allowed
    assert "Generation blocked by Preflight" in gate.message


def test_gate_allows_ready_and_surfaces_optional_gap(monkeypatch):
    import film_lab.generation_gate as module
    report=SimpleNamespace(ready=True, blockers=(), missing_models=(), missing_nodes=(), selected_workflow="svd", gpu_devices=("AMD GPU",), unsupported_capabilities=("camera_control",))
    monkeypatch.setattr(module,"run_preflight",lambda **kwargs: report)
    gate=preflight_generation(SimpleNamespace(end_frame="",character_ids=[],camera_move="orbit"))
    assert gate.allowed
    assert "Ready to Generate" in gate.message and "AMD GPU" in gate.message
    assert "camera_control" in gate.message
