#!/usr/bin/env python3
"""AMD / ComfyUI img2vid generator: sizes, inject, mock sidecar, fail-soft."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.ffmpeg_support import ffmpeg_available, run_ffmpeg
from film_lab.generators import (
    DEFAULT_GENERATOR_ID,
    FALLBACK_GENERATOR_ID,
    GENERATORS,
    generator_dropdown_choices,
)
from film_lab.generators.comfyui_i2v import (
    DEFAULT_NEGATIVE,
    ComfyUII2VGenerator,
    _inject_workflow,
    _pick_backend,
    build_animatediff_workflow,
    build_svd_xt_workflow,
    i2v_frames,
    i2v_size,
    motion_bucket_id,
)
from film_lab.generators.ken_burns import KenBurnsGenerator
from film_lab.shot_card import ShotCard


class SizeTests(unittest.TestCase):
    def test_six_gb_sizes_and_frames(self) -> None:
        self.assertEqual(i2v_size("16:9"), (512, 288))
        self.assertEqual(i2v_size("9:16"), (288, 512))
        self.assertEqual(i2v_size("1:1"), (384, 384))
        self.assertEqual(i2v_frames(2.0, "animatediff"), 17)
        self.assertEqual(i2v_frames(3.0, "animatediff"), 25)
        self.assertEqual(i2v_frames(2.0, "svd"), 12)
        self.assertEqual(i2v_frames(3.0, "svd"), 14)
        self.assertLessEqual(i2v_frames(10.0, "svd"), 14)
        self.assertNotIn("nsfw", DEFAULT_NEGATIVE.lower())
        self.assertNotIn("nude", DEFAULT_NEGATIVE.lower())
        self.assertNotIn("explicit", DEFAULT_NEGATIVE.lower())

    def test_default_engine_is_amd(self) -> None:
        self.assertEqual(DEFAULT_GENERATOR_ID, "amd_i2v")
        self.assertEqual(FALLBACK_GENERATOR_ID, "ken_burns")
        self.assertIn("amd_i2v", GENERATORS)
        self.assertIn("svd-xt", GENERATORS["amd_i2v"].label.lower())
        self.assertIn("fallback", GENERATORS["ken_burns"].label.lower())
        ids = [item[1] for item in generator_dropdown_choices()]
        self.assertIn("amd_i2v", ids)
        self.assertNotIn("ken_burns", ids)


class InjectTests(unittest.TestCase):
    def test_placeholder_and_titles(self) -> None:
        graph = build_animatediff_workflow()
        _inject_workflow(
            graph,
            image_name="lamp.png",
            prompt='adults, "quoted", camera: slow push-in',
            negative="child",
            seed=42,
            width=512,
            height=288,
            frames=17,
            motion=0.4,
            ckpt="v1-5-pruned-emaonly.safetensors",
        )
        self.assertEqual(graph["6"]["inputs"]["image"], "lamp.png")
        self.assertIn("quoted", graph["4"]["inputs"]["text"])
        self.assertEqual(graph["5"]["inputs"]["text"], "child")
        self.assertEqual(graph["9"]["inputs"]["seed"], 42)
        self.assertEqual(graph["8"]["inputs"]["width"], 512)
        self.assertEqual(graph["8"]["inputs"]["batch_size"], 17)
        self.assertIsInstance(graph["3"]["inputs"]["motion_scale"], float)

    def test_svd_xt_graph_and_backend(self) -> None:
        self.assertEqual(_pick_backend({}), "svd")
        self.assertEqual(
            _pick_backend({"SVD_img2vid_Conditioning": {}, "ImageOnlyCheckpointLoader": {}}),
            "svd",
        )
        self.assertGreaterEqual(motion_bucket_id(0.55, "slow kiss, held breath"), 127)
        graph = build_svd_xt_workflow()
        _inject_workflow(
            graph,
            image_name="lamp.png",
            prompt="slow push-in, kiss, late-20s adults",
            negative=DEFAULT_NEGATIVE,
            seed=7,
            width=512,
            height=288,
            frames=14,
            motion=0.55,
            ckpt="svd_xt.safetensors",
        )
        self.assertEqual(graph["23"]["inputs"]["image"], "lamp.png")
        self.assertEqual(graph["15"]["inputs"]["ckpt_name"], "svd_xt.safetensors")
        self.assertEqual(graph["12"]["inputs"]["video_frames"], 14)
        self.assertGreaterEqual(graph["12"]["inputs"]["motion_bucket_id"], 127)
        self.assertEqual(graph["11"]["inputs"]["seed"], 7)

    def test_bundled_workflows_inject(self) -> None:
        folder = ROOT / "workflows"
        for name in ("amd_animatediff_i2v_api.json", "amd_ltx_i2v_api.json", "svd_xt_i2v_api.json"):
            graph = json.loads((folder / name).read_text(encoding="utf-8"))
            _inject_workflow(
                graph,
                image_name="still.png",
                prompt="breathing",
                negative="blur",
                seed=1,
                width=512,
                height=288,
                frames=17,
                motion=0.5,
                ckpt="v1-5-pruned-emaonly.safetensors",
            )
            images = [
                n["inputs"].get("image")
                for n in graph.values()
                if n.get("class_type") == "LoadImage"
            ]
            self.assertEqual(images, ["still.png"])


class ProbeTests(unittest.TestCase):
    def test_probe_fail_soft(self) -> None:
        os.environ["FILM_LAB_COMFY_URL"] = "http://127.0.0.1:1"
        try:
            probe = ComfyUII2VGenerator().probe()
        finally:
            os.environ.pop("FILM_LAB_COMFY_URL", None)
        self.assertFalse(probe.available)
        self.assertIn("run_comfyui_amd.ps1", probe.message)
        self.assertIn("svd_xt.safetensors", probe.message)
        self.assertNotIn("Use Ken Burns", probe.message)


class _MockComfy(BaseHTTPRequestHandler):
    mp4_bytes = b""

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        return

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/system_stats":
            self._json(200, {"devices": [{"name": "AMD Radeon RX 5600 XT"}]})
        elif path == "/object_info":
            self._json(200, {"ADE_LoadAnimateDiffModel": {}, "VHS_VideoCombine": {}})
        elif path.startswith("/history/"):
            pid = path.rsplit("/", 1)[-1]
            self._json(
                200,
                {
                    pid: {
                        "outputs": {
                            "11": {
                                "gifs": [
                                    {
                                        "filename": "film_lab.mp4",
                                        "subfolder": "",
                                        "type": "output",
                                    }
                                ]
                            }
                        },
                        "status": {"completed": True, "status_str": "success"},
                    }
                },
            )
        elif path == "/view":
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.end_headers()
            self.wfile.write(self.mp4_bytes)
        else:
            self._json(404, {"error": path})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(length)
        if path == "/upload/image":
            self._json(200, {"name": "start.png", "subfolder": "", "type": "input"})
        elif path == "/prompt":
            self._json(200, {"prompt_id": "job-1"})
        else:
            self._json(404, {"error": path})

    def _json(self, code: int, payload: dict) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


@unittest.skipUnless(ffmpeg_available()[0], "ffmpeg required")
class MockSidecarTests(unittest.TestCase):
    def test_generate_through_mock_comfy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tiny = Path(tmp) / "tiny.mp4"
            still = Path(tmp) / "still.png"
            Image.new("RGB", (640, 360), (80, 40, 30)).save(still)
            run_ffmpeg(
                [
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "color=c=0x502818:s=320x180:d=1",
                    "-an",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    str(tiny),
                ]
            )
            _MockComfy.mp4_bytes = tiny.read_bytes()
            server = ThreadingHTTPServer(("127.0.0.1", 0), _MockComfy)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            host, port = server.server_address[:2]
            os.environ["FILM_LAB_COMFY_URL"] = f"http://{host}:{port}"
            os.environ["FILM_LAB_COMFY_BACKEND"] = "animatediff"
            try:
                probe = ComfyUII2VGenerator().probe()
                self.assertTrue(probe.available)
                self.assertIn("RX 5600", probe.message)
                out = Path(tmp) / "out.mp4"
                job_shot = ShotCard(
                    name="AMD mock",
                    duration=2.0,
                    camera_move="slow push-in",
                    subject_motion_strength=0.4,
                    body_motion_notes="breathing",
                )
                from film_lab.generators.base import GenerateJob

                result = ComfyUII2VGenerator().generate(
                    GenerateJob(
                        shot=job_shot,
                        start_path=still,
                        end_path=None,
                        output_path=out,
                    )
                )
                self.assertTrue(result.is_file())
                self.assertGreater(result.stat().st_size, 200)
            finally:
                os.environ.pop("FILM_LAB_COMFY_URL", None)
                os.environ.pop("FILM_LAB_COMFY_BACKEND", None)
                server.shutdown()
                server.server_close()


class KenBurnsStillWorks(unittest.TestCase):
    @unittest.skipUnless(ffmpeg_available()[0], "ffmpeg required")
    def test_fallback_label_and_probe(self) -> None:
        gen = KenBurnsGenerator()
        self.assertIn("fallback", gen.label.lower())
        self.assertTrue(gen.probe().available)


if __name__ == "__main__":
    unittest.main()
