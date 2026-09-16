from pathlib import Path
from types import SimpleNamespace

from film_lab.generators.base import GenerateJob
from film_lab.generators.comfyui_i2v import _positive_prompt
from film_lab.shot_card import ShotCard


def test_generate_job_has_formal_conditioning_field(tmp_path):
    shot=ShotCard(name="Bridge")
    marker=SimpleNamespace(prompt="Scene World production prompt")
    job=GenerateJob(shot=shot,start_path=tmp_path/"a.png",end_path=None,output_path=tmp_path/"out.mp4",conditioning=marker)
    assert job.conditioning is marker


def test_comfy_positive_prompt_uses_production_conditioning(tmp_path):
    shot=ShotCard(name="Bridge",director_intent="raw shot prompt",camera_move="slow push-in",subject_motion_strength=0.4)
    conditioning=SimpleNamespace(prompt="warehouse at night. Maya in wet black coat. Shot direction: Maya runs")
    job=GenerateJob(shot=shot,start_path=tmp_path/"a.png",end_path=None,output_path=tmp_path/"out.mp4",conditioning=conditioning)
    prompt=_positive_prompt(job)
    assert "warehouse at night" in prompt
    assert "Maya in wet black coat" in prompt
    assert "camera move: slow push-in" in prompt


def test_comfy_positive_prompt_keeps_legacy_fallback(tmp_path):
    shot=ShotCard(name="Legacy",director_intent="legacy shot direction")
    job=GenerateJob(shot=shot,start_path=tmp_path/"a.png",end_path=None,output_path=tmp_path/"out.mp4")
    assert "legacy shot direction" in _positive_prompt(job)
