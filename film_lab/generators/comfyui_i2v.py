"""Local image-to-video via a ComfyUI sidecar on this PC.

Primary path: SVD-XT img2vid (``svd_xt.safetensors``) through ComfyUI's
own API — still + motion prompt → MP4. No hosted Grok / xAI / Higgsfield
video call. No Film Lab NSFW filter. Adults 18+ only (minors stay blocked).

Default hardware: AMD Radeon RX 5600 XT (~6GB). Liam's Comfy-Desktop
sidecar listens on ``http://127.0.0.1:8188`` with ``--cuda-device 1``.
First clips are short (2–4s) at 512×288 / 288×512.

If the sidecar is down, generate fails soft with start steps.
Primary Generate will not zoom-pan a still instead.
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PIL import Image, ImageOps

from film_lab.constants import ASPECT_SIZES
from film_lab.ffmpeg_support import ffmpeg_available, run_ffmpeg
from film_lab.generators.base import GenerateJob, GeneratorUnavailable, ProbeResult
from film_lab.generator_capabilities import requirements_from_conditioning
from film_lab.workflow_router import choose_workflow, discover_workflows
from film_lab.advanced_conditioning_bridge import inject_advanced_conditioning
from film_lab.conditioning_profiles import apply_best_conditioning_profiles
from film_lab.multi_character_conditioning import assign_character_profiles
from film_lab.performance_timeline_bridge import inject_performance_timelines, update_timeline_enforcement
from film_lab.lip_sync_bridge import inject_lip_sync, update_dialogue_enforcement
from film_lab.voice_acting_bridge import inject_voice_acting, update_voice_acting_enforcement

ID = "amd_i2v"
LABEL = "Local img2vid (ComfyUI · SVD-XT)"

DEFAULT_COMFY_URL = "http://127.0.0.1:8188"
DEFAULT_TIMEOUT_S = 1800
POLL_S = 2.0
INTERNAL_FPS = 8
SVD_FPS = 6

# 6GB-safe sizes (multiples of 32). SVD-XT official is 1024×576 — too big here.
I2V_SIZES: dict[str, tuple[int, int]] = {
    "16:9": (512, 288),
    "9:16": (288, 512),
    "1:1": (384, 384),
}

# Concrete open model ids (filenames inside ComfyUI/models/checkpoints).
DEFAULT_SVD_CKPT = "svd_xt.safetensors"
DEFAULT_SD15_CKPT = "v1-5-pruned-emaonly.safetensors"
DEFAULT_AD_MOTION = "v3_sd15_mm.ckpt"
DEFAULT_LTX_CKPT = "ltxv-2b-0.9.8-distilled.safetensors"

# Quality + age only. Not an NSFW / clothing / intimacy filter.
DEFAULT_NEGATIVE = "blurry, jitter, morphing face, extra limbs, child, minor, teen, underage"

ProgressFn = Callable[[int], None]
CancelFn = Callable[[], bool]

_HOOKS = threading.local()


def set_generation_hooks(
    *,
    progress: ProgressFn | None = None,
    cancel: CancelFn | None = None,
) -> None:
    _HOOKS.progress = progress
    _HOOKS.cancel = cancel


def clear_generation_hooks() -> None:
    _HOOKS.progress = None
    _HOOKS.cancel = None


def _emit_progress(percent: int) -> None:
    cb = getattr(_HOOKS, "progress", None)
    if cb:
        cb(max(0, min(99, int(percent))))


def _cancelled() -> bool:
    cb = getattr(_HOOKS, "cancel", None)
    return bool(cb and cb())


def interrupt_comfy() -> str:
    """Ask the sidecar to stop the current job."""
    try:
        _json("POST", f"{comfy_url()}/interrupt", {})
        return "Cancelled."
    except GeneratorUnavailable as exc:
        return f"Cancel sent. {exc}"


INSTALL_HINT = (
    "ComfyUI sidecar is not running — that is the motion engine. "
    "Start the local ComfyUI at http://127.0.0.1:8188 with --cuda-device 1 "
    "(RX 5600 XT). SVD-XT should be the checkpoint filename svd_xt.safetensors "
    "under ComfyUI/models/checkpoints "
    "(Comfy-Desktop: %LOCALAPPDATA%\\Comfy-Desktop\\ComfyUI-Installs\\ComfyUI\\ComfyUI\\models\\checkpoints\\svd_xt.safetensors). "
    "Or run .\\scripts\\run_comfyui_amd.ps1. "
    "Primary Generate will not zoom-pan a still instead. "
    "No Film Lab credits. No Film Lab NSFW filter. Adults 18+ only. "
    "See START_HERE.md and docs/AMD_IMG2VID.md."
)


def comfy_url() -> str:
    return os.environ.get("FILM_LAB_COMFY_URL", DEFAULT_COMFY_URL).rstrip("/")


def comfy_timeout() -> float:
    raw = os.environ.get("FILM_LAB_COMFY_TIMEOUT", str(DEFAULT_TIMEOUT_S))
    try:
        return max(30.0, float(raw))
    except ValueError:
        return float(DEFAULT_TIMEOUT_S)


def i2v_size(aspect: str) -> tuple[int, int]:
    override_w = os.environ.get("FILM_LAB_I2V_WIDTH")
    override_h = os.environ.get("FILM_LAB_I2V_HEIGHT")
    if override_w and override_h:
        return _align(int(override_w), 32), _align(int(override_h), 32)
    from film_lab.quality import internal_size

    return internal_size("720p", aspect)


def i2v_frames(duration: float, kind: str = "svd") -> int:
    """Frame count for the active backend. Cap for 6GB."""
    seconds = max(2.0, float(duration))
    if kind == "svd":
        raw = int(round(seconds * svd_fps()))
        return int(min(14, max(8, raw)))
    raw = int(round(seconds * INTERNAL_FPS))
    snapped = 8 * max(1, round((raw - 1) / 8)) + 1
    return int(min(25, max(9, snapped)))


def svd_fps() -> int:
    raw = os.environ.get("FILM_LAB_SVD_FPS", str(SVD_FPS))
    try:
        return max(4, min(8, int(raw)))
    except ValueError:
        return SVD_FPS


def motion_bucket_id(strength: float, prompt: str = "") -> int:
    """SVD motion_bucket_id (1–255). Prompt steers intensity; image holds likeness."""
    base = int(40 + 180 * max(0.0, min(1.0, float(strength))))
    text = (prompt or "").lower()
    if any(word in text for word in ("still", "frozen", "hold", "static", "locked")):
        base = min(base, 70)
    if any(
        word in text
        for word in ("kiss", "breath", "hips", "walk", "turn", "push", "weight", "sex")
    ):
        base = max(base, 127)
    if any(word in text for word in ("fast", "run", "whip", "rush", "slam")):
        base = max(base, 180)
    return max(1, min(255, base))


def augment_level(strength: float) -> float:
    return round(min(0.25, max(0.0, float(strength) * 0.18)), 3)


def _align(value: int, step: int) -> int:
    return max(step, int(value) // step * step)


def workflow_dir() -> Path:
    env = os.environ.get("FILM_LAB_COMFY_WORKFLOW")
    if env:
        path = Path(env)
        if path.is_file():
            return path.parent
    return Path(__file__).resolve().parents[2] / "workflows"


def default_workflow_path(kind: str = "animatediff") -> Path:
    env = os.environ.get("FILM_LAB_COMFY_WORKFLOW")
    if env:
        path = Path(env)
        if path.is_file():
            return path
    name = {
        "svd": "svd_xt_i2v_api.json",
        "ltx": "amd_ltx_i2v_api.json",
        "animatediff": "amd_animatediff_i2v_api.json",
    }.get(kind, "svd_xt_i2v_api.json")
    return workflow_dir() / name


class ComfyUII2VGenerator:
    id = ID
    label = LABEL

    def __init__(self) -> None:
        self.last_route_metadata: dict[str, Any] = {}

    def route_metadata(self) -> dict[str, Any]:
        return dict(self.last_route_metadata)

    def probe(self) -> ProbeResult:
        url = comfy_url()
        try:
            stats = _json("GET", f"{url}/system_stats")
        except GeneratorUnavailable as exc:
            return ProbeResult(False, f"{exc} {INSTALL_HINT}")
        devices = stats.get("devices") or []
        names = []
        for dev in devices:
            name = dev.get("name") or dev.get("index")
            if name:
                names.append(str(name))
        gpu = ", ".join(names) or "unknown device"
        kind = "unknown"
        try:
            info = _json("GET", f"{url}/object_info")
            kind = _pick_backend(info)
        except GeneratorUnavailable:
            info = {}
        resolved = kind if kind != "unknown" else "svd"
        wf = default_workflow_path(resolved)
        fps = svd_fps() if resolved == "svd" else INTERNAL_FPS
        return ProbeResult(
            True,
            f"ComfyUI ready at {url} ({gpu}). Backend: {resolved} · "
            f"{_ckpt_for(resolved)}. 6GB path: {i2v_size('16:9')[0]}x{i2v_size('16:9')[1]} · "
            f"{fps} fps · 2–4s first. Workflow: {wf.name}. "
            "Open weights only — no Film Lab credits. No Film Lab NSFW filter.",
        )

    def generate(self, job: GenerateJob) -> Path:
        probe = self.probe()
        if not probe.available:
            raise GeneratorUnavailable(probe.message)
        ok, ff_msg = ffmpeg_available()
        if not ok:
            raise GeneratorUnavailable(ff_msg)

        job.output_path.parent.mkdir(parents=True, exist_ok=True)
        info = _json("GET", f"{comfy_url()}/object_info")
        conditioning = getattr(job, "conditioning", None)
        requested = ["video_generation"]
        if conditioning is not None:
            requested.extend(r.name for r in requirements_from_conditioning(conditioning) if r.name not in {"text_prompt", "start_image", "structured_conditioning"})
        installed_models = _installed_models_from_object_info(info)
        profiles = discover_workflows(workflow_dir(), info, installed_models=installed_models)
        route = choose_workflow(profiles, requested)
        selected_path = None
        if route.workflow is None:
            forced = (os.environ.get("FILM_LAB_COMFY_BACKEND") or "").strip().lower()
            if forced not in {"svd", "ltx", "animatediff", "custom"}:
                details = "; ".join(f"{w.id}: missing nodes={list(w.missing_nodes)} missing models={list(w.missing_models)}" for w in profiles)
                raise GeneratorUnavailable(f"No validated local ComfyUI I2V workflow is runnable. {route.reason} {details}".strip())
            # Explicit developer override only. This keeps mock/custom sidecars possible while
            # marking the route unvalidated rather than pretending discovery succeeded.
            kind = forced
            self.last_route_metadata = {"workflow_id": f"forced:{forced}", "workflow_path": str(default_workflow_path(forced)), "workflow_capabilities": [], "requested_capabilities": requested, "unsupported_capabilities": requested, "model_requirements": [], "missing_models": [], "routing_reason": "Explicit FILM_LAB_COMFY_BACKEND override; workflow validation bypassed.", "validated": False}
        else:
            kind = _kind_for_workflow(route.workflow.id)
            selected_path = Path(route.workflow.path)
            self.last_route_metadata = {
                "workflow_id": route.workflow.id, "workflow_path": route.workflow.path,
                "workflow_capabilities": list(route.workflow.capabilities),
                "requested_capabilities": list(route.requested_capabilities),
                "unsupported_capabilities": list(route.unsupported_capabilities),
                "model_requirements": list(route.workflow.model_requirements),
                "missing_models": list(route.workflow.missing_models), "routing_reason": route.reason, "validated": True,
            }
        from film_lab.quality import internal_size, native_desk_size

        width, height = internal_size(
            getattr(job.shot, "resolution", None), job.shot.aspect_ratio
        )
        frames = i2v_frames(job.shot.duration, kind)
        prompt = _positive_prompt(job)
        negative = (job.shot.negative_prompt or "").strip() or DEFAULT_NEGATIVE
        seed = int(job.shot.seed) if job.shot.seed is not None else int(uuid.uuid4().int % (2**31))

        work = job.output_path.parent / f".{job.output_path.stem}_amd"
        work.mkdir(parents=True, exist_ok=True)
        try:
            if _cancelled():
                raise GeneratorUnavailable("Cancelled.")
            _emit_progress(6)
            still = work / "start.png"
            _prep_still(job.start_path, still, width, height)
            _emit_progress(12)
            uploaded = _upload_image(still)
            _emit_progress(18)
            graph = _load_selected_workflow(selected_path, kind, info) if selected_path else _load_or_build_workflow(kind, info)
            _inject_workflow(
                graph,
                image_name=uploaded,
                prompt=prompt,
                negative=negative,
                seed=seed,
                width=width,
                height=height,
                frames=frames,
                motion=job.shot.subject_motion_strength,
                ckpt=_ckpt_for(kind),
            )
            if conditioning is not None and len(tuple(getattr(conditioning, "characters", ()) or ())) > 1:
                multi_character_evidence = assign_character_profiles(graph, conditioning)
                profile_evidence = {"version": 1, "mode": "multi_character", "applied": [], "available_profiles": []}
            else:
                multi_character_evidence = {"version": 1, "status": "NOT_REQUIRED", "assignments": []}
                profile_evidence = apply_best_conditioning_profiles(graph) if conditioning is not None else {"version": 1, "applied": [], "available_profiles": []}
            bridge = inject_advanced_conditioning(graph, conditioning, _upload_image) if conditioning is not None else {"version": 1, "wired_capabilities": [], "slots": []}
            timeline_bridge = inject_performance_timelines(graph, conditioning) if conditioning is not None else {"version":1,"wired":False,"slots":[],"enforced_character_ids":[]}
            if conditioning is not None:
                update_timeline_enforcement(conditioning, timeline_bridge)
            if timeline_bridge.get("wired"):
                bridge.setdefault("wired_capabilities", []).append("performance_timeline_control")
            lip_sync_bridge = inject_lip_sync(graph, conditioning) if conditioning is not None else {"version":1,"wired":False,"slots":[],"lip_sync_enforced_character_ids":[]}
            if conditioning is not None:
                update_dialogue_enforcement(conditioning, lip_sync_bridge)
            if lip_sync_bridge.get("wired"):
                bridge.setdefault("wired_capabilities", []).append("lip_sync")
            voice_acting_bridge = inject_voice_acting(graph, conditioning) if conditioning is not None else {"version":1,"wired":False,"slots":[],"enforced_character_ids":[]}
            if conditioning is not None:
                update_voice_acting_enforcement(conditioning, voice_acting_bridge)
            if voice_acting_bridge.get("wired"):
                bridge.setdefault("wired_capabilities", []).append("expressive_voice_control")
            if multi_character_evidence.get("assignments"):
                wired_targets = {str(x.get("target") or "").lower() for x in bridge.get("slots", []) if x.get("wired")}
                for assignment in multi_character_evidence["assignments"]:
                    if assignment.get("status") == "BOUND":
                        assignment["status"] = "ENFORCED" if str(assignment.get("character_id") or "").lower() in wired_targets else "AVAILABLE_NOT_WIRED"
                states = [a.get("status") for a in multi_character_evidence["assignments"]]
                multi_character_evidence["status"] = "PASS" if states and all(x == "ENFORCED" for x in states) else ("PARTIAL" if any(x == "ENFORCED" for x in states) else "FAIL")
            self.last_route_metadata["conditioning_profiles"] = profile_evidence
            self.last_route_metadata["multi_character_conditioning"] = multi_character_evidence
            self.last_route_metadata["conditioning_bridge"] = bridge
            self.last_route_metadata["performance_timeline_bridge"] = timeline_bridge
            self.last_route_metadata["lip_sync_bridge"] = lip_sync_bridge
            self.last_route_metadata["voice_acting_bridge"] = voice_acting_bridge
            self.last_route_metadata["wired_capabilities"] = list(bridge.get("wired_capabilities") or [])
            prompt_id = _queue_prompt(graph)
            _emit_progress(24)
            history = _wait_history(prompt_id)
            _emit_progress(94)
            raw = _download_output(history, work / "raw.mp4")
            _emit_progress(97)
            desk_w, desk_h = native_desk_size(
                getattr(job.shot, "resolution", None), job.shot.aspect_ratio
            )
            _rewrap(raw, job.output_path, desk_w, desk_h, job.shot.duration)
            return job.output_path
        finally:
            _cleanup(work)


def _positive_prompt(job: GenerateJob) -> str:
    shot = job.shot
    # The composed production prompt is the real render prompt when present.
    # This is where Scene World + Character continuity crosses into ComfyUI,
    # rather than being metadata/router-only state.
    conditioning = getattr(job, "conditioning", None)
    production_prompt = getattr(conditioning, "prompt", "") if conditioning is not None else ""
    bits = [production_prompt or shot.local_prompt()]
    bits.append(f"camera move: {shot.camera_move}")
    bits.append(f"motion strength {shot.subject_motion_strength:.2f}")
    if shot.body_motion_notes.strip():
        bits.append(shot.body_motion_notes.strip())
    if shot.start_frame_hint.strip():
        bits.append(shot.start_frame_hint.strip())
    from film_lab.motion_scope import likeness_prompt_bits

    bits.extend(likeness_prompt_bits(shot))
    return ", ".join(bits)


def _ckpt_for(kind: str) -> str:
    if kind == "svd":
        return os.environ.get("FILM_LAB_SVD_CKPT", DEFAULT_SVD_CKPT)
    if kind == "ltx":
        return os.environ.get("FILM_LAB_LTX_CKPT", DEFAULT_LTX_CKPT)
    return os.environ.get("FILM_LAB_SD15_CKPT", DEFAULT_SD15_CKPT)


def _pick_backend(object_info: dict[str, Any]) -> str:
    forced = (os.environ.get("FILM_LAB_COMFY_BACKEND") or "").strip().lower()
    if forced in {"svd", "ltx", "animatediff", "custom"}:
        return forced
    keys = set(object_info)
    if "SVD_img2vid_Conditioning" in keys and "ImageOnlyCheckpointLoader" in keys:
        return "svd"
    if "LTXVImgToVideo" in keys:
        return "ltx"
    if "ADE_LoadAnimateDiffModel" in keys or "ADE_AnimateDiffLoaderGen1" in keys:
        return "animatediff"
    if "WanImageToVideo" in keys:
        return "animatediff"
    return "svd"



def _kind_for_workflow(workflow_id: str) -> str:
    name = workflow_id.lower()
    if "ltx" in name:
        return "ltx"
    if "animatediff" in name or "animate" in name:
        return "animatediff"
    if "svd" in name:
        return "svd"
    return _pick_backend({})


def _installed_models_from_object_info(object_info: dict[str, Any]) -> set[str] | None:
    """Extract model filenames advertised by ComfyUI node choice inputs.

    Returns None when ComfyUI exposes no model choices, preserving 'unknown' rather
    than falsely treating every required model as missing.
    """
    names: set[str] = set()
    model_keys = {"ckpt_name", "model_name", "motion_model", "motion_model_name", "vae_name", "clip_name"}
    for node in object_info.values():
        if not isinstance(node, dict):
            continue
        inputs = node.get("input") or {}
        for group in (inputs.get("required") or {}, inputs.get("optional") or {}):
            if not isinstance(group, dict):
                continue
            for key, spec in group.items():
                if key not in model_keys or not isinstance(spec, (list, tuple)) or not spec:
                    continue
                choices = spec[0]
                if isinstance(choices, (list, tuple)):
                    names.update(str(x) for x in choices if isinstance(x, str))
    return names or None


def _load_selected_workflow(path: Path, kind: str, object_info: dict[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        raise GeneratorUnavailable(f"Selected workflow disappeared: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("nodes") is not None:
        raise GeneratorUnavailable(f"Selected workflow is not ComfyUI API format: {path.name}")
    _adapt_save_nodes(payload, object_info)
    return payload

def _load_or_build_workflow(kind: str, object_info: dict[str, Any]) -> dict[str, Any]:
    path = default_workflow_path(kind)
    if path.is_file():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and payload.get("nodes"):
            raise GeneratorUnavailable(
                f"{path.name} is a UI workflow, not API format. "
                "In ComfyUI: File → Export Workflow (API) and set "
                f"FILM_LAB_COMFY_WORKFLOW to that file."
            )
        if not isinstance(payload, dict):
            raise GeneratorUnavailable(f"Workflow {path} is not a JSON object")
        _adapt_save_nodes(payload, object_info)
        return payload
    if kind == "svd":
        return build_svd_xt_workflow(object_info=object_info)
    if kind == "ltx" and "LTXVImgToVideo" in object_info:
        return build_ltx_workflow()
    return build_animatediff_workflow()


def build_svd_xt_workflow(
    *,
    ckpt: str | None = None,
    width: int = 512,
    height: int = 288,
    frames: int = 14,
    seed: int = 0,
    image: str = "{{IMAGE}}",
    motion_bucket: int = 127,
    fps: int | None = None,
    augment: float = 0.0,
    object_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Stock ComfyUI SVD-XT img2vid. Image holds likeness; prompt steers motion_bucket."""
    ckpt = ckpt or DEFAULT_SVD_CKPT
    fps = int(fps or svd_fps())
    graph: dict[str, Any] = {
        "15": {
            "class_type": "ImageOnlyCheckpointLoader",
            "inputs": {"ckpt_name": ckpt},
            "_meta": {"title": "film_lab_ckpt"},
        },
        "23": {
            "class_type": "LoadImage",
            "inputs": {"image": image},
            "_meta": {"title": "film_lab_image"},
        },
        "12": {
            "class_type": "SVD_img2vid_Conditioning",
            "inputs": {
                "clip_vision": ["15", 1],
                "init_image": ["23", 0],
                "vae": ["15", 2],
                "width": int(width),
                "height": int(height),
                "video_frames": int(frames),
                "motion_bucket_id": int(motion_bucket),
                "fps": int(fps),
                "augmentation_level": float(augment),
            },
            "_meta": {"title": "film_lab_svd"},
        },
        "14": {
            "class_type": "VideoLinearCFGGuidance",
            "inputs": {"model": ["15", 0], "min_cfg": 1.0},
        },
        "11": {
            "class_type": "KSampler",
            "inputs": {
                "seed": int(seed),
                "steps": int(os.environ.get("FILM_LAB_SVD_STEPS", "14")),
                "cfg": 2.5,
                "sampler_name": "euler",
                "scheduler": "karras",
                "denoise": 1.0,
                "model": ["14", 0],
                "positive": ["12", 0],
                "negative": ["12", 1],
                "latent_image": ["12", 2],
            },
            "_meta": {"title": "film_lab_seed"},
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["11", 0], "vae": ["15", 2]},
        },
    }
    graph.update(_video_save_nodes(object_info or {}, decode_ref=["8", 0], fps=fps))
    return graph


def _video_save_nodes(object_info: dict[str, Any], *, decode_ref: list, fps: int) -> dict[str, Any]:
    keys = set(object_info)
    if "VHS_VideoCombine" in keys and "CreateVideo" not in keys:
        return {
            "22": {
                "class_type": "VHS_VideoCombine",
                "inputs": {
                    "images": decode_ref,
                    "frame_rate": int(fps),
                    "loop_count": 0,
                    "filename_prefix": "film_lab",
                    "format": "video/h264-mp4",
                    "pingpong": False,
                    "save_output": True,
                },
                "_meta": {"title": "film_lab_save"},
            }
        }
    return {
        "21": {
            "class_type": "CreateVideo",
            "inputs": {"images": decode_ref, "fps": float(fps)},
        },
        "22": {
            "class_type": "SaveVideo",
            "inputs": {
                "video": ["21", 0],
                "filename_prefix": "film_lab",
                "format": "mp4",
                "codec": "h264",
            },
            "_meta": {"title": "film_lab_save"},
        },
    }


def _adapt_save_nodes(graph: dict[str, Any], object_info: dict[str, Any]) -> None:
    """If bundled SaveVideo is missing, swap in VHS on this sidecar."""
    keys = set(object_info)
    uses_save = any(
        isinstance(node, dict) and node.get("class_type") == "SaveVideo"
        for node in graph.values()
    )
    if not uses_save or "SaveVideo" in keys or "CreateVideo" in keys:
        return
    if "VHS_VideoCombine" not in keys:
        return
    decode_ref = ["8", 0]
    fps = svd_fps()
    for node in graph.values():
        if not isinstance(node, dict):
            continue
        if node.get("class_type") == "VAEDecode":
            decode_ref = [next((k for k, v in graph.items() if v is node), "8"), 0]
        if node.get("class_type") == "CreateVideo":
            fps = int(node.get("inputs", {}).get("fps") or fps)
    drop = [
        key
        for key, node in graph.items()
        if isinstance(node, dict) and node.get("class_type") in {"CreateVideo", "SaveVideo"}
    ]
    for key in drop:
        del graph[key]
    graph.update(_video_save_nodes({"VHS_VideoCombine": {}}, decode_ref=decode_ref, fps=fps))


def build_ltx_workflow(
    *,
    ckpt: str | None = None,
    width: int = 512,
    height: int = 288,
    frames: int = 17,
    seed: int = 0,
    prompt: str = "{{PROMPT}}",
    negative: str = "{{NEGATIVE}}",
    image: str = "{{IMAGE}}",
) -> dict[str, Any]:
    """API-format graph for stock ComfyUI LTX-Video img2vid (2B distilled)."""
    ckpt = ckpt or DEFAULT_LTX_CKPT
    return {
        "10": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": ckpt},
            "_meta": {"title": "film_lab_ckpt"},
        },
        "11": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["10", 1]},
            "_meta": {"title": "film_lab_positive"},
        },
        "12": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative, "clip": ["10", 1]},
            "_meta": {"title": "film_lab_negative"},
        },
        "13": {
            "class_type": "LTXVConditioning",
            "inputs": {"positive": ["11", 0], "negative": ["12", 0], "frame_rate": float(INTERNAL_FPS)},
        },
        "14": {
            "class_type": "LoadImage",
            "inputs": {"image": image},
            "_meta": {"title": "film_lab_image"},
        },
        "15": {
            "class_type": "LTXVImgToVideo",
            "inputs": {
                "positive": ["13", 0],
                "negative": ["13", 1],
                "vae": ["10", 2],
                "image": ["14", 0],
                "width": width,
                "height": height,
                "length": frames,
                "batch_size": 1,
                "strength": 1.0,
            },
        },
        "16": {
            "class_type": "LTXVScheduler",
            "inputs": {
                "steps": 8,
                "max_shift": 2.05,
                "base_shift": 0.95,
                "stretch": True,
                "terminal": 0.1,
                "latent": ["15", 2],
            },
        },
        "17": {
            "class_type": "KSamplerSelect",
            "inputs": {"sampler_name": "euler"},
        },
        "18": {
            "class_type": "RandomNoise",
            "inputs": {"noise_seed": seed},
            "_meta": {"title": "film_lab_seed"},
        },
        "19": {
            "class_type": "SamplerCustom",
            "inputs": {
                "add_noise": True,
                "cfg": 3.0,
                "model": ["10", 0],
                "positive": ["15", 0],
                "negative": ["15", 1],
                "sampler": ["17", 0],
                "sigmas": ["16", 0],
                "latent_image": ["15", 2],
                "noise": ["18", 0],
            },
        },
        "20": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["19", 0], "vae": ["10", 2]},
        },
        "21": {
            "class_type": "CreateVideo",
            "inputs": {"images": ["20", 0], "fps": float(INTERNAL_FPS)},
        },
        "22": {
            "class_type": "SaveVideo",
            "inputs": {
                "video": ["21", 0],
                "filename_prefix": "film_lab",
                "format": "mp4",
                "codec": "h264",
            },
            "_meta": {"title": "film_lab_save"},
        },
    }


def build_animatediff_workflow(
    *,
    ckpt: str | None = None,
    motion: str | None = None,
    width: int = 512,
    height: int = 288,
    frames: int = 17,
    seed: int = 0,
    prompt: str = "{{PROMPT}}",
    negative: str = "{{NEGATIVE}}",
    image: str = "{{IMAGE}}",
    motion_scale: float = 0.8,
) -> dict[str, Any]:
    """API-format graph: SD 1.5 + AnimateDiff v3 (fits ~6GB at 512×288)."""
    ckpt = ckpt or DEFAULT_SD15_CKPT
    motion = motion or os.environ.get("FILM_LAB_AD_MOTION", DEFAULT_AD_MOTION)
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": ckpt},
            "_meta": {"title": "film_lab_ckpt"},
        },
        "2": {
            "class_type": "ADE_LoadAnimateDiffModel",
            "inputs": {"model_name": motion},
            "_meta": {"title": "film_lab_motion"},
        },
        "3": {
            "class_type": "ADE_ApplyAnimateDiffModelSimple",
            "inputs": {
                "motion_model": ["2", 0],
                "model": ["1", 0],
                "motion_scale": float(motion_scale),
            },
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["1", 1]},
            "_meta": {"title": "film_lab_positive"},
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative, "clip": ["1", 1]},
            "_meta": {"title": "film_lab_negative"},
        },
        "6": {
            "class_type": "LoadImage",
            "inputs": {"image": image},
            "_meta": {"title": "film_lab_image"},
        },
        "7": {
            "class_type": "VAEEncode",
            "inputs": {"pixels": ["6", 0], "vae": ["1", 2]},
        },
        "8": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": width, "height": height, "batch_size": frames},
            "_meta": {"title": "film_lab_latent"},
        },
        "9": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": 12,
                "cfg": 7.0,
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "denoise": 0.72,
                "model": ["3", 0],
                "positive": ["4", 0],
                "negative": ["5", 0],
                "latent_image": ["8", 0],
            },
            "_meta": {"title": "film_lab_seed"},
        },
        "10": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["9", 0], "vae": ["1", 2]},
        },
        "11": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": ["10", 0],
                "frame_rate": INTERNAL_FPS,
                "loop_count": 0,
                "filename_prefix": "film_lab",
                "format": "video/h264-mp4",
                "pingpong": False,
                "save_output": True,
            },
            "_meta": {"title": "film_lab_save"},
        },
    }


def _inject_workflow(
    graph: dict[str, Any],
    *,
    image_name: str,
    prompt: str,
    negative: str,
    seed: int,
    width: int,
    height: int,
    frames: int,
    motion: float,
    ckpt: str,
) -> dict[str, Any]:
    """Fill placeholders, titled nodes, then class-type fallbacks."""
    blob = json.dumps(graph)
    blob = (
        blob.replace('"{{WIDTH}}"', str(int(width)))
        .replace('"{{HEIGHT}}"', str(int(height)))
        .replace('"{{FRAMES}}"', str(int(frames)))
        .replace('"{{SEED}}"', str(int(seed)))
        .replace('"{{FPS}}"', str(INTERNAL_FPS))
        .replace('"{{MOTION_SCALE}}"', f"{0.35 + 0.85 * float(motion):.3f}")
        .replace('"{{MOTION_BUCKET}}"', str(motion_bucket_id(motion, prompt)))
        .replace('"{{AUGMENT}}"', str(augment_level(motion)))
        .replace("{{IMAGE}}", image_name)
        .replace("{{PROMPT}}", _json_escape(prompt))
        .replace("{{NEGATIVE}}", _json_escape(negative))
        .replace("{{CKPT}}", ckpt)
        .replace("{{WIDTH}}", str(int(width)))
        .replace("{{HEIGHT}}", str(int(height)))
        .replace("{{FRAMES}}", str(int(frames)))
        .replace("{{SEED}}", str(int(seed)))
        .replace("{{FPS}}", str(INTERNAL_FPS))
        .replace("{{MOTION_SCALE}}", f"{0.35 + 0.85 * float(motion):.3f}")
        .replace("{{MOTION_BUCKET}}", str(motion_bucket_id(motion, prompt)))
        .replace("{{AUGMENT}}", str(augment_level(motion)))
    )
    graph.clear()
    graph.update(json.loads(blob))

    def title(node: dict[str, Any]) -> str:
        meta = node.get("_meta") or {}
        return str(meta.get("title") or "")

    for node in graph.values():
        if not isinstance(node, dict):
            continue
        inputs = node.setdefault("inputs", {})
        tag = title(node)
        ctype = node.get("class_type")
        if tag == "film_lab_image" or ctype == "LoadImage":
            inputs["image"] = image_name
        if tag == "film_lab_positive" and "text" in inputs:
            inputs["text"] = prompt
        if tag == "film_lab_negative" and "text" in inputs:
            inputs["text"] = negative
        if tag == "film_lab_seed":
            if "seed" in inputs:
                inputs["seed"] = int(seed)
            if "noise_seed" in inputs:
                inputs["noise_seed"] = int(seed)
        if tag == "film_lab_ckpt" and "ckpt_name" in inputs:
            inputs["ckpt_name"] = ckpt
        if ctype == "ImageOnlyCheckpointLoader" and "ckpt_name" in inputs:
            inputs["ckpt_name"] = ckpt
        if ctype == "SVD_img2vid_Conditioning":
            inputs["width"] = int(width)
            inputs["height"] = int(height)
            inputs["video_frames"] = int(frames)
            inputs["motion_bucket_id"] = motion_bucket_id(motion, prompt)
            inputs["fps"] = svd_fps()
            inputs["augmentation_level"] = augment_level(motion)
        if ctype == "LTXVImgToVideo":
            inputs["width"] = int(width)
            inputs["height"] = int(height)
            inputs["length"] = int(frames)
        if ctype == "EmptyLatentImage":
            inputs["width"] = int(width)
            inputs["height"] = int(height)
            inputs["batch_size"] = int(frames)
        if ctype == "ADE_ApplyAnimateDiffModelSimple" and "motion_scale" in inputs:
            inputs["motion_scale"] = 0.35 + 0.85 * float(motion)
        svd_graph = any(
            isinstance(other, dict) and other.get("class_type") == "SVD_img2vid_Conditioning"
            for other in graph.values()
        )
        out_fps = svd_fps() if svd_graph else INTERNAL_FPS
        if ctype in {"CreateVideo", "VHS_VideoCombine"}:
            if "fps" in inputs:
                inputs["fps"] = float(out_fps)
            if "frame_rate" in inputs:
                inputs["frame_rate"] = out_fps
    return graph


def _json_escape(text: str) -> str:
    return json.dumps(text)[1:-1]


def _prep_still(src: Path, dest: Path, width: int, height: int) -> None:
    image = Image.open(src)
    image = ImageOps.exif_transpose(image).convert("RGB")
    fitted = ImageOps.fit(image, (width, height), method=Image.Resampling.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fitted.save(dest, format="PNG")


def _json(method: str, url: str, payload: dict | None = None, timeout: float | None = None) -> Any:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout or 20) as resp:
            raw = resp.read()
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:800]
        raise GeneratorUnavailable(f"ComfyUI {method} {url} failed ({exc.code}): {body}") from exc
    except URLError as exc:
        raise GeneratorUnavailable(f"Cannot reach ComfyUI at {comfy_url()}: {exc.reason}") from exc
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise GeneratorUnavailable(f"ComfyUI returned non-JSON from {url}") from exc


def _upload_image(path: Path) -> str:
    """POST /upload/image as multipart. Returns the filename ComfyUI stored."""
    boundary = f"----FilmLab{uuid.uuid4().hex}"
    filename = path.name
    blob = path.read_bytes()
    chunks = [
        f"--{boundary}\r\n".encode(),
        (
            f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
            "Content-Type: image/png\r\n\r\n"
        ).encode(),
        blob,
        b"\r\n",
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="overwrite"\r\n\r\n',
        b"true\r\n",
        f"--{boundary}--\r\n".encode(),
    ]
    body = b"".join(chunks)
    url = f"{comfy_url()}/upload/image"
    req = Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, json.JSONDecodeError) as exc:
        raise GeneratorUnavailable(f"ComfyUI image upload failed: {exc}") from exc
    name = payload.get("name") or filename
    sub = payload.get("subfolder") or ""
    return f"{sub}/{name}" if sub else str(name)


def _queue_prompt(graph: dict[str, Any]) -> str:
    payload = {"prompt": graph, "client_id": "film-lab"}
    result = _json("POST", f"{comfy_url()}/prompt", payload, timeout=60)
    if result.get("error") or result.get("node_errors"):
        raise GeneratorUnavailable(
            "ComfyUI rejected the workflow. For SVD-XT you need stock nodes "
            "ImageOnlyCheckpointLoader + SVD_img2vid_Conditioning + VideoLinearCFGGuidance "
            "and svd_xt.safetensors in models/checkpoints. "
            f"Details: {json.dumps(result)[:900]}"
        )
    prompt_id = result.get("prompt_id")
    if not prompt_id:
        raise GeneratorUnavailable(f"ComfyUI /prompt did not return prompt_id: {result}")
    return str(prompt_id)


def _wait_history(prompt_id: str) -> dict[str, Any]:
    deadline = time.time() + comfy_timeout()
    started = time.time()
    url = f"{comfy_url()}/history/{prompt_id}"
    while time.time() < deadline:
        if _cancelled():
            interrupt_comfy()
            raise GeneratorUnavailable("Cancelled.")
        hist = _json("GET", url, timeout=20)
        entry = hist.get(prompt_id) if isinstance(hist, dict) else None
        if entry:
            status = entry.get("status") or {}
            if status.get("status_str") == "error" or status.get("completed") is False and status.get("messages"):
                msgs = status.get("messages") or entry.get("status")
                raise GeneratorUnavailable(f"ComfyUI job failed: {msgs}")
            if entry.get("outputs"):
                return entry
        elapsed = time.time() - started
        _emit_progress(min(92, 24 + int(elapsed / 90.0 * 68)))
        time.sleep(POLL_S)
    raise GeneratorUnavailable(
        f"ComfyUI job {prompt_id} timed out after {comfy_timeout():.0f}s. "
        "6GB first runs can take several minutes. Raise FILM_LAB_COMFY_TIMEOUT."
    )


def _download_output(history: dict[str, Any], dest: Path) -> Path:
    outputs = history.get("outputs") or {}
    files: list[dict[str, Any]] = []
    for node_out in outputs.values():
        if not isinstance(node_out, dict):
            continue
        for key in ("gifs", "videos", "images"):
            for item in node_out.get(key) or []:
                if isinstance(item, dict) and item.get("filename"):
                    files.append(item)
    if not files:
        raise GeneratorUnavailable(f"ComfyUI finished but produced no video: {list(outputs)}")

    def score(item: dict[str, Any]) -> int:
        name = str(item.get("filename") or "").lower()
        if name.endswith(".mp4"):
            return 3
        if name.endswith(".webm"):
            return 2
        return 1

    files.sort(key=score, reverse=True)
    item = files[0]
    query = urlencode(
        {
            "filename": item["filename"],
            "subfolder": item.get("subfolder") or "",
            "type": item.get("type") or "output",
        }
    )
    url = f"{comfy_url()}/view?{query}"
    req = Request(url, method="GET")
    try:
        with urlopen(req, timeout=120) as resp:
            dest.write_bytes(resp.read())
    except (HTTPError, URLError) as exc:
        raise GeneratorUnavailable(f"Could not download ComfyUI output: {exc}") from exc
    if dest.stat().st_size < 32:
        raise GeneratorUnavailable("ComfyUI output was empty")
    return dest


def _rewrap(src: Path, dest: Path, width: int, height: int, duration: float) -> None:
    run_ffmpeg(
        [
            "-y",
            "-i",
            str(src),
            "-vf",
            (
                f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
            ),
            "-t",
            f"{max(2.0, duration):.3f}",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(dest),
        ]
    )


def _cleanup(work: Path) -> None:
    if not work.exists():
        return
    for child in sorted(work.rglob("*"), reverse=True):
        try:
            if child.is_file():
                child.unlink()
            else:
                child.rmdir()
        except OSError:
            pass
    try:
        work.rmdir()
    except OSError:
        pass
