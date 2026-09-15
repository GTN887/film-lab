from pathlib import Path
from film_lab.project import Project
from film_lab.scene_context import SceneContextStore
from film_lab.render_service import generate_take
from film_lab.shot_card import ShotCard


class CapturingGenerator:
    id = "capture"
    label = "Capture Generator"
    def __init__(self): self.prompt = ""
    def generate(self, job):
        self.prompt = job.shot.prompt
        job.output_path.write_bytes(b"real-video-output")
        return job.output_path


def test_generation_receives_scene_world_and_take_preserves_provenance(tmp_path):
    project = Project.create("scene-render", base_dir=tmp_path)
    still = project.stills_dir / "start.png"; still.write_bytes(b"image")
    SceneContextStore(project).update("scene_002", location="rooftop", weather="rain", lighting="neon", camera={"lens":"35mm"}, continuity_notes="Maya's coat stays wet")
    shot = ShotCard(id="shot_010", name="Escape", prompt="Maya runs to the stairwell", scene_id="scene_002")
    gen = CapturingGenerator()
    result = generate_take(project, shot, still, gen, model="test-model")
    assert "rooftop" in gen.prompt and "rain" in gen.prompt and "35mm" in gen.prompt
    assert "Maya runs to the stairwell" in gen.prompt
    assert result.take.metadata["scene_world"]["location"] == "rooftop"
    assert result.take.metadata["shot_prompt"] == "Maya runs to the stairwell"
    assert result.take.metadata["generation_prompt"] == gen.prompt
    assert result.take.prompt == gen.prompt


def test_generation_does_not_permanently_mutate_shot_prompt(tmp_path):
    project = Project.create("scene-render-clean", base_dir=tmp_path)
    still = project.stills_dir / "start.png"; still.write_bytes(b"image")
    SceneContextStore(project).update("scene_001", location="forest")
    shot = ShotCard(id="shot_001", name="Walk", prompt="walk forward", scene_id="scene_001")
    gen = CapturingGenerator()
    generate_take(project, shot, still, gen)
    assert shot.prompt == "walk forward"
    assert "forest" in gen.prompt
