"""Local character-consistency stack. User-owned box only. No Film Lab credits.

Priority on a Radeon RX 5600 XT (~6GB): lock the person in the *start still*,
then img2vid. Heavier FaceID graphs are documented stubs until ComfyUI has
the nodes and VRAM. Not a hosted face API.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from film_lab.generators.comfyui_i2v import ComfyUII2VGenerator, comfy_url

DEFAULT_FACE_LOCK = 0.55


@dataclass(frozen=True)
class ConsistencyMethod:
    key: str
    title: str
    vram: str
    status: str  # primary | stub | advanced | optional
    notes: str


CONSISTENCY_STACK: tuple[ConsistencyMethod, ...] = (
    ConsistencyMethod(
        key="start_still_i2v",
        title="Reference still → img2vid",
        vram="~4–6GB DirectML",
        status="primary",
        notes=(
            "Primary on this AMD box. Pin 3–10 adult refs, pick one locked still, "
            "then Motion Desk. Same face because the video starts from that frame."
        ),
    ),
    ConsistencyMethod(
        key="ipadapter_faceid_plus_v2",
        title="IP-Adapter FaceID Plus V2",
        vram="tight on 6GB",
        status="stub",
        notes=(
            "Mature ComfyUI path. Wire a local FaceID Plus V2 graph at "
            "characters/<id>/refs/ when the sidecar lists those nodes. "
            "Use strength 0.4–0.65 first."
        ),
    ),
    ConsistencyMethod(
        key="instantid",
        title="InstantID (SDXL)",
        vram="heavy for 6GB",
        status="stub",
        notes="Higher likeness, SDXL-sized. Optional later; expect OOM on 6GB unless tiny.",
    ),
    ConsistencyMethod(
        key="pulid",
        title="PuLID (Flux path)",
        vram="not for 6GB first",
        status="advanced",
        notes="Flux-era identity. Documented only. Do not require it on RX 5600 XT.",
    ),
    ConsistencyMethod(
        key="openpose",
        title="ControlNet OpenPose (Pose Desk)",
        vram="still-first, light",
        status="wired",
        notes=(
            "Body / hands / face guide on the still via Pose Desk. "
            "Face pixels stay. Not video puppeting. Then Animate."
        ),
    ),
    ConsistencyMethod(
        key="face_lora",
        title="Character LoRA (train later)",
        vram="train off-box or overnight",
        status="advanced",
        notes="Optional later. 20–40 cropped adult stills. Not the daily path.",
    ),
    ConsistencyMethod(
        key="reactor",
        title="ReActor face-fix",
        vram="post only",
        status="optional",
        notes="Optional post face-swap after a take. Not the primary identity lock.",
    ),
)

FACE_METHODS: tuple[str, ...] = (
    "start_still_i2v",
    "ipadapter_faceid_plus_v2",
    "instantid",
    "pulid",
    "reactor",
)
DEFAULT_FACE_METHOD = "start_still_i2v"

CONSISTENCY_PROGRAM = (
    "### Character + Environment program (RX 5600 XT, not NVIDIA)\n"
    "**Actors (Character Bible)** — Face lock: InstantID (SDXL) and/or IP-Adapter FaceID "
    "when Comfy lists those nodes; PuLID only if a Flux path exists later. "
    "Body/style: ControlNet OpenPose via Pose Desk now; character LoRA later. "
    "Multi-ref character sheet in this bible (Alison, Bradley, family roles). "
    "ReActor is optional post fallback only.\n"
    "**Environments (World / Set Bible)** — Lock the set with a reference still + "
    "optional IP-Adapter style/scene ref. ControlNet depth / canny / softedge for "
    "room/street geometry. World Note + 3D Set reuse the same locked background. "
    "Img2vid seeds from the locked still; **Regenerate** keeps the World lock."
)

CONSISTENCY_DEBUG = (
    "### DEBUG CHECKLIST (identity / env drift — AMD, not NVIDIA)\n"
    "1. Strengthen adapter / face lock one step (0.55 → 0.65). Do not jump to 1.0.\n"
    "2. Re-apply Character sheet refs and **Environment lock** still.\n"
    "3. Drop Quality one step on OOM (1080p → 720p → 480p). Never native 4K.\n"
    "4. **Regenerate** (keeps World lock + face lock + Quality).\n"
    "5. InstantID / FaceID stay stubs until Comfy lists those nodes — "
    "Film Lab will not fake a rewrite. Start lightweight on 6GB."
)


def normalize_face_method(value: str | None) -> str:
    text = (value or "").strip()
    return text if text in FACE_METHODS else DEFAULT_FACE_METHOD


def stack_markdown() -> str:
    lines = [
        "### Local consistency stack (this PC)",
        "Zero Film Lab credits. No hosted face API. Adults 18+ only.",
        "",
    ]
    for method in CONSISTENCY_STACK:
        lines.append(
            f"- **{method.title}** — `{method.status}` · {method.vram}. {method.notes}"
        )
    lines.append(
        "- Video-native identity models are optional advanced docs. "
        "They want more VRAM than this 6GB card."
    )
    return "\n".join(lines)


def consistency_program_md() -> str:
    return f"{CONSISTENCY_PROGRAM}\n\n{CONSISTENCY_DEBUG}"


def detect_face_nodes(object_info: dict[str, Any] | None) -> list[str]:
    keys = set(object_info or {})
    found: list[str] = []
    for name in (
        "IPAdapterFaceID",
        "IPAdapterApply",
        "IPAdapterUnifiedLoader",
        "InstantIDFaceAnalysis",
        "ApplyInstantID",
        "PulidFluxApply",
        "ReActorFaceSwap",
    ):
        if name in keys:
            found.append(name)
    return found


def detect_env_nodes(object_info: dict[str, Any] | None) -> list[str]:
    keys = set(object_info or {})
    found: list[str] = []
    for name in (
        "ControlNetLoader",
        "ControlNetApply",
        "ControlNetApplyAdvanced",
        "CannyEdgePreprocessor",
        "CannyPreprocessor",
        "DepthAnythingPreprocessor",
        "MiDaS-DepthMapPreprocessor",
        "HEDPreprocessor",
        "SoftEdgePreprocessor",
        "IPAdapterApply",
        "IPAdapterUnifiedLoader",
    ):
        if name in keys:
            found.append(name)
    return found


def probe_face_lock() -> tuple[str, str]:
    """(Off|Stub|Ready, message). Never echoes paths that look like secrets."""
    comfy = ComfyUII2VGenerator().probe()
    if not comfy.available:
        return (
            "Off",
            "ComfyUI sidecar Off. Face lock still works as start-still img2vid "
            f"once you start `{comfy_url()}`. {comfy.message}",
        )
    try:
        from film_lab.generators.comfyui_i2v import _json

        info = _json("GET", f"{comfy_url()}/object_info")
        nodes = detect_face_nodes(info if isinstance(info, dict) else {})
    except Exception:  # noqa: BLE001
        nodes = []
    if nodes:
        return "Ready", f"Face nodes on sidecar: {', '.join(nodes)}. Strength slider applies."
    return (
        "Stub",
        "Sidecar is up. No FaceID/InstantID nodes yet — primary lock is the start still. "
        "Slider is stored for when you load those graphs.",
    )


def probe_env_lock() -> tuple[str, str]:
    """(Off|Stub|Ready, message). Environment ControlNet / IP-Adapter scene."""
    comfy = ComfyUII2VGenerator().probe()
    if not comfy.available:
        return (
            "Off",
            "ComfyUI sidecar Off. Environment lock still works as a locked start still "
            f"once you start `{comfy_url()}`. {comfy.message}",
        )
    try:
        from film_lab.generators.comfyui_i2v import _json

        info = _json("GET", f"{comfy_url()}/object_info")
        nodes = detect_env_nodes(info if isinstance(info, dict) else {})
    except Exception:  # noqa: BLE001
        nodes = []
    if nodes:
        return "Ready", f"Env nodes on sidecar: {', '.join(nodes)}. Strength slider applies."
    return (
        "Stub",
        "Sidecar is up. No ControlNet / IP-Adapter scene nodes yet — "
        "primary env lock is the locked set still → img2vid. "
        "Geometry chips are stored for when you load those graphs.",
    )


def face_lock_plan(*, strength: float, ref_count: int, method: str = "start_still_i2v") -> dict[str, Any]:
    strength = max(0.0, min(1.0, float(strength)))
    method = normalize_face_method(method)
    return {
        "method": method,
        "strength": strength,
        "ref_count": ref_count,
        "status": "wired" if method == DEFAULT_FACE_METHOD else "stub",
        "notes": (
            "Start-frame likeness is the 6GB program. "
            "Heavier graphs stay stubs until ComfyUI lists them."
        ),
    }
