"""Still-first pose / hand–face adjust. OpenPose/ControlNet-style guide.

Edit the still, keep the face (Character Bible / FaceID lock), then Animate
on Motion Desk (ComfyUI SVD path). Not frame-by-frame video puppeting.

Local overlay always works. Comfy OpenPose/ControlNet nodes are optional;
Film Lab never fakes a ControlNet rewrite. Zero credits.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from film_lab.generators.comfyui_i2v import ComfyUII2VGenerator, comfy_url
from film_lab.project import Project
from film_lab.util import new_id, slugify, write_json

WORKFLOWS = Path(__file__).resolve().parents[1] / "workflows" / "pose"

# OpenPose BODY_18 names. Face joints are stored, never painted over the face.
KEYPOINT_NAMES: tuple[str, ...] = (
    "nose",
    "neck",
    "r_sho",
    "r_elb",
    "r_wri",
    "l_sho",
    "l_elb",
    "l_wri",
    "r_hip",
    "r_kne",
    "r_ank",
    "l_hip",
    "l_kne",
    "l_ank",
    "r_eye",
    "l_eye",
    "r_ear",
    "l_ear",
)

FACE_KEYS: frozenset[str] = frozenset(
    {"nose", "r_eye", "l_eye", "r_ear", "l_ear"}
)

LIMBS: tuple[tuple[str, str], ...] = (
    ("neck", "r_sho"),
    ("neck", "l_sho"),
    ("r_sho", "r_elb"),
    ("r_elb", "r_wri"),
    ("l_sho", "l_elb"),
    ("l_elb", "l_wri"),
    ("neck", "r_hip"),
    ("neck", "l_hip"),
    ("r_hip", "l_hip"),
    ("r_hip", "r_kne"),
    ("r_kne", "r_ank"),
    ("l_hip", "l_kne"),
    ("l_kne", "l_ank"),
)

# Film Lab purple + soft cyan — not a hosted-product lime.
LIMB_COLOR = (139, 108, 255, 210)
JOINT_COLOR = (126, 232, 232, 230)
TICK_COLOR = (126, 232, 232, 220)

POSE_NODE_NAMES: tuple[str, ...] = (
    "OpenposePreprocessor",
    "DWPreprocessor",
    "ControlNetLoader",
    "ControlNetApply",
    "ControlNetApplyAdvanced",
    "AIO_Preprocessor",
)

DEFAULT_BODY = "Stand"
DEFAULT_HANDS = "Rest"
DEFAULT_FACE = "Front"


@dataclass(frozen=True)
class PosePreset:
    label: str
    blurb: str
    notes: str = ""


BODY_PRESETS: tuple[PosePreset, ...] = (
    PosePreset("Stand", "Upright, weight even.", "Lead body facing the lens."),
    PosePreset("Sit", "Hips drop, knees bent."),
    PosePreset("Lean in", "Torso tips toward the other adult."),
    PosePreset("Walk", "One leg travels; other stays planted."),
    PosePreset("Look back", "Shoulders twist; glance over."),
    PosePreset("Kiss lean", "Heads close; still-first, not a puppeted kiss."),
    PosePreset("Embrace", "Arms wrap. One-figure guide plus blocking note."),
    PosePreset("Recline", "Body long on the bed or sofa."),
    PosePreset("Kneel", "Knees down, torso up."),
    PosePreset("Arms crossed", "Wrists meet the opposite ribs."),
    PosePreset("Reach", "One arm extends."),
    PosePreset("Turn 3/4", "Body yaws off the lens."),
)

HAND_PRESETS: tuple[PosePreset, ...] = (
    PosePreset("Rest", "Hands hang or rest at the sides."),
    PosePreset("On chest", "Palms on the sternum / partner chest."),
    PosePreset("In hair", "Wrists lift toward the crown — not over the face."),
    PosePreset("Near face", "Hands hover at the jaw line, outside the face lock."),
    PosePreset("Hold", "Fingers meet in front of the waist."),
    PosePreset("Gesture", "One hand talks."),
    PosePreset("Clasp", "Hands together at the midline."),
)

FACE_PRESETS: tuple[PosePreset, ...] = (
    PosePreset("Front", "Lens-on. Face pixels stay the original still."),
    PosePreset("3/4", "Yaw hint outside the face oval."),
    PosePreset("Profile", "Stronger yaw tick — still does not redraw features."),
    PosePreset("Tilt", "Ear-down tick."),
    PosePreset("Look up", "Chin-up tick."),
    PosePreset("Look down", "Chin-down tick."),
    PosePreset("Close", "Intimate distance note; no feature paint."),
)


class PoseError(ValueError):
    """Bad still or unknown pose preset."""


# Fractional BODY_18 templates (x, y) in 0–1 image space.
_BODY: dict[str, dict[str, tuple[float, float]]] = {
    "Stand": {
        "nose": (0.50, 0.18),
        "neck": (0.50, 0.26),
        "r_sho": (0.38, 0.30),
        "r_elb": (0.32, 0.46),
        "r_wri": (0.30, 0.60),
        "l_sho": (0.62, 0.30),
        "l_elb": (0.68, 0.46),
        "l_wri": (0.70, 0.60),
        "r_hip": (0.44, 0.56),
        "r_kne": (0.43, 0.74),
        "r_ank": (0.42, 0.90),
        "l_hip": (0.56, 0.56),
        "l_kne": (0.57, 0.74),
        "l_ank": (0.58, 0.90),
        "r_eye": (0.47, 0.16),
        "l_eye": (0.53, 0.16),
        "r_ear": (0.43, 0.18),
        "l_ear": (0.57, 0.18),
    },
    "Sit": {
        "nose": (0.50, 0.22),
        "neck": (0.50, 0.30),
        "r_sho": (0.38, 0.34),
        "r_elb": (0.30, 0.48),
        "r_wri": (0.34, 0.58),
        "l_sho": (0.62, 0.34),
        "l_elb": (0.70, 0.48),
        "l_wri": (0.66, 0.58),
        "r_hip": (0.44, 0.62),
        "r_kne": (0.36, 0.72),
        "r_ank": (0.30, 0.86),
        "l_hip": (0.56, 0.62),
        "l_kne": (0.64, 0.72),
        "l_ank": (0.70, 0.86),
        "r_eye": (0.47, 0.20),
        "l_eye": (0.53, 0.20),
        "r_ear": (0.43, 0.22),
        "l_ear": (0.57, 0.22),
    },
    "Lean in": {
        "nose": (0.56, 0.22),
        "neck": (0.54, 0.30),
        "r_sho": (0.40, 0.32),
        "r_elb": (0.36, 0.48),
        "r_wri": (0.40, 0.60),
        "l_sho": (0.66, 0.36),
        "l_elb": (0.72, 0.50),
        "l_wri": (0.70, 0.62),
        "r_hip": (0.42, 0.58),
        "r_kne": (0.40, 0.76),
        "r_ank": (0.38, 0.90),
        "l_hip": (0.54, 0.60),
        "l_kne": (0.56, 0.76),
        "l_ank": (0.58, 0.90),
        "r_eye": (0.53, 0.20),
        "l_eye": (0.59, 0.20),
        "r_ear": (0.48, 0.22),
        "l_ear": (0.62, 0.22),
    },
    "Walk": {
        "nose": (0.50, 0.18),
        "neck": (0.50, 0.26),
        "r_sho": (0.40, 0.30),
        "r_elb": (0.30, 0.42),
        "r_wri": (0.24, 0.52),
        "l_sho": (0.60, 0.30),
        "l_elb": (0.70, 0.44),
        "l_wri": (0.78, 0.54),
        "r_hip": (0.46, 0.56),
        "r_kne": (0.52, 0.72),
        "r_ank": (0.58, 0.88),
        "l_hip": (0.54, 0.56),
        "l_kne": (0.46, 0.74),
        "l_ank": (0.40, 0.90),
        "r_eye": (0.47, 0.16),
        "l_eye": (0.53, 0.16),
        "r_ear": (0.43, 0.18),
        "l_ear": (0.57, 0.18),
    },
    "Look back": {
        "nose": (0.42, 0.18),
        "neck": (0.48, 0.26),
        "r_sho": (0.58, 0.30),
        "r_elb": (0.64, 0.46),
        "r_wri": (0.62, 0.60),
        "l_sho": (0.36, 0.32),
        "l_elb": (0.28, 0.46),
        "l_wri": (0.26, 0.60),
        "r_hip": (0.52, 0.56),
        "r_kne": (0.54, 0.74),
        "r_ank": (0.56, 0.90),
        "l_hip": (0.42, 0.56),
        "l_kne": (0.40, 0.74),
        "l_ank": (0.38, 0.90),
        "r_eye": (0.40, 0.16),
        "l_eye": (0.44, 0.16),
        "r_ear": (0.48, 0.18),
        "l_ear": (0.36, 0.18),
    },
    "Kiss lean": {
        "nose": (0.58, 0.24),
        "neck": (0.54, 0.32),
        "r_sho": (0.40, 0.34),
        "r_elb": (0.38, 0.50),
        "r_wri": (0.48, 0.58),
        "l_sho": (0.66, 0.36),
        "l_elb": (0.70, 0.50),
        "l_wri": (0.64, 0.58),
        "r_hip": (0.44, 0.58),
        "r_kne": (0.42, 0.76),
        "r_ank": (0.40, 0.90),
        "l_hip": (0.56, 0.60),
        "l_kne": (0.58, 0.76),
        "l_ank": (0.60, 0.90),
        "r_eye": (0.55, 0.22),
        "l_eye": (0.61, 0.22),
        "r_ear": (0.50, 0.24),
        "l_ear": (0.64, 0.24),
    },
    "Embrace": {
        "nose": (0.50, 0.20),
        "neck": (0.50, 0.28),
        "r_sho": (0.36, 0.32),
        "r_elb": (0.48, 0.44),
        "r_wri": (0.62, 0.42),
        "l_sho": (0.64, 0.32),
        "l_elb": (0.52, 0.44),
        "l_wri": (0.38, 0.42),
        "r_hip": (0.44, 0.56),
        "r_kne": (0.43, 0.74),
        "r_ank": (0.42, 0.90),
        "l_hip": (0.56, 0.56),
        "l_kne": (0.57, 0.74),
        "l_ank": (0.58, 0.90),
        "r_eye": (0.47, 0.18),
        "l_eye": (0.53, 0.18),
        "r_ear": (0.43, 0.20),
        "l_ear": (0.57, 0.20),
    },
    "Recline": {
        "nose": (0.28, 0.38),
        "neck": (0.34, 0.40),
        "r_sho": (0.36, 0.50),
        "r_elb": (0.30, 0.60),
        "r_wri": (0.26, 0.68),
        "l_sho": (0.40, 0.32),
        "l_elb": (0.48, 0.28),
        "l_wri": (0.56, 0.26),
        "r_hip": (0.58, 0.52),
        "r_kne": (0.72, 0.56),
        "r_ank": (0.86, 0.58),
        "l_hip": (0.60, 0.44),
        "l_kne": (0.74, 0.42),
        "l_ank": (0.88, 0.40),
        "r_eye": (0.26, 0.36),
        "l_eye": (0.30, 0.34),
        "r_ear": (0.24, 0.40),
        "l_ear": (0.32, 0.32),
    },
    "Kneel": {
        "nose": (0.50, 0.26),
        "neck": (0.50, 0.34),
        "r_sho": (0.38, 0.38),
        "r_elb": (0.32, 0.50),
        "r_wri": (0.34, 0.60),
        "l_sho": (0.62, 0.38),
        "l_elb": (0.68, 0.50),
        "l_wri": (0.66, 0.60),
        "r_hip": (0.44, 0.62),
        "r_kne": (0.40, 0.78),
        "r_ank": (0.36, 0.88),
        "l_hip": (0.56, 0.62),
        "l_kne": (0.60, 0.78),
        "l_ank": (0.64, 0.88),
        "r_eye": (0.47, 0.24),
        "l_eye": (0.53, 0.24),
        "r_ear": (0.43, 0.26),
        "l_ear": (0.57, 0.26),
    },
    "Arms crossed": {
        "nose": (0.50, 0.18),
        "neck": (0.50, 0.26),
        "r_sho": (0.38, 0.30),
        "r_elb": (0.48, 0.42),
        "r_wri": (0.60, 0.46),
        "l_sho": (0.62, 0.30),
        "l_elb": (0.52, 0.42),
        "l_wri": (0.40, 0.46),
        "r_hip": (0.44, 0.56),
        "r_kne": (0.43, 0.74),
        "r_ank": (0.42, 0.90),
        "l_hip": (0.56, 0.56),
        "l_kne": (0.57, 0.74),
        "l_ank": (0.58, 0.90),
        "r_eye": (0.47, 0.16),
        "l_eye": (0.53, 0.16),
        "r_ear": (0.43, 0.18),
        "l_ear": (0.57, 0.18),
    },
    "Reach": {
        "nose": (0.50, 0.20),
        "neck": (0.50, 0.28),
        "r_sho": (0.40, 0.30),
        "r_elb": (0.36, 0.46),
        "r_wri": (0.34, 0.58),
        "l_sho": (0.62, 0.26),
        "l_elb": (0.70, 0.16),
        "l_wri": (0.76, 0.08),
        "r_hip": (0.44, 0.56),
        "r_kne": (0.43, 0.74),
        "r_ank": (0.42, 0.90),
        "l_hip": (0.56, 0.56),
        "l_kne": (0.57, 0.74),
        "l_ank": (0.58, 0.90),
        "r_eye": (0.47, 0.18),
        "l_eye": (0.53, 0.18),
        "r_ear": (0.43, 0.20),
        "l_ear": (0.57, 0.20),
    },
    "Turn 3/4": {
        "nose": (0.56, 0.18),
        "neck": (0.52, 0.26),
        "r_sho": (0.42, 0.32),
        "r_elb": (0.36, 0.46),
        "r_wri": (0.34, 0.60),
        "l_sho": (0.60, 0.28),
        "l_elb": (0.68, 0.42),
        "l_wri": (0.72, 0.54),
        "r_hip": (0.46, 0.56),
        "r_kne": (0.44, 0.74),
        "r_ank": (0.42, 0.90),
        "l_hip": (0.56, 0.54),
        "l_kne": (0.60, 0.72),
        "l_ank": (0.64, 0.88),
        "r_eye": (0.53, 0.16),
        "l_eye": (0.58, 0.16),
        "r_ear": (0.48, 0.18),
        "l_ear": (0.62, 0.16),
    },
}

_HAND_DELTA: dict[str, dict[str, tuple[float, float]]] = {
    "Rest": {},
    "On chest": {"r_wri": (0.10, -0.10), "l_wri": (-0.10, -0.10)},
    "In hair": {"r_wri": (0.10, -0.26), "l_wri": (-0.10, -0.26)},
    "Near face": {"r_wri": (0.08, -0.20), "l_wri": (-0.08, -0.20)},
    "Hold": {"r_wri": (0.08, -0.04), "l_wri": (-0.08, -0.04)},
    "Gesture": {"r_wri": (0.14, -0.12), "l_wri": (0.02, -0.02)},
    "Clasp": {"r_wri": (0.10, -0.06), "l_wri": (-0.10, -0.06)},
}

_FACE_TICK: dict[str, tuple[float, float]] = {
    "Front": (0.0, 0.0),
    "3/4": (0.08, 0.0),
    "Profile": (0.14, 0.01),
    "Tilt": (0.04, 0.05),
    "Look up": (0.0, -0.07),
    "Look down": (0.0, 0.07),
    "Close": (0.02, 0.02),
}


@dataclass(frozen=True)
class PoseResult:
    path: Path
    json_path: Path
    body: str
    hands: str
    face: str
    face_preserved: bool
    method: str
    face_bbox: tuple[int, int, int, int]
    keypoints: dict[str, tuple[float, float]]
    message: str


def body_labels() -> list[str]:
    return [p.label for p in BODY_PRESETS]


def hand_labels() -> list[str]:
    return [p.label for p in HAND_PRESETS]


def face_labels() -> list[str]:
    return [p.label for p in FACE_PRESETS]


def _preset_label(label: str, catalog: tuple[PosePreset, ...], default: str) -> str:
    text = (label or "").strip()
    for item in catalog:
        if item.label.lower() == text.lower():
            return item.label
    return default


def resolve_presets(body: str, hands: str, face: str) -> tuple[str, str, str]:
    return (
        _preset_label(body, BODY_PRESETS, DEFAULT_BODY),
        _preset_label(hands, HAND_PRESETS, DEFAULT_HANDS),
        _preset_label(face, FACE_PRESETS, DEFAULT_FACE),
    )


def compose_keypoints(body: str, hands: str, face: str) -> dict[str, tuple[float, float]]:
    body, hands, face = resolve_presets(body, hands, face)
    points = dict(_BODY[body])
    for key, (dx, dy) in _HAND_DELTA.get(hands, {}).items():
        if key in points:
            x, y = points[key]
            points[key] = (_clamp(x + dx), _clamp(y + dy))
    tick = _FACE_TICK.get(face, (0.0, 0.0))
    if tick != (0.0, 0.0):
        for key in FACE_KEYS:
            if key in points:
                x, y = points[key]
                points[key] = (_clamp(x + tick[0] * 0.35), _clamp(y + tick[1] * 0.35))
    return points


def _clamp(value: float) -> float:
    return max(0.03, min(0.97, float(value)))


def face_bbox_px(
    width: int, height: int, keypoints: dict[str, tuple[float, float]]
) -> tuple[int, int, int, int]:
    """Conservative oval over the head. Overlay never paints inside this."""
    xs: list[float] = []
    ys: list[float] = []
    for key in FACE_KEYS | {"neck"}:
        if key in keypoints:
            xs.append(keypoints[key][0] * width)
            ys.append(keypoints[key][1] * height)
    if not xs:
        cx, cy = width * 0.5, height * 0.20
        rw, rh = width * 0.16, height * 0.16
    else:
        cx = sum(xs) / len(xs)
        cy = min(ys) + (max(ys) - min(ys)) * 0.35
        rw = max(width * 0.14, (max(xs) - min(xs)) * 0.9 + width * 0.06)
        rh = max(height * 0.14, (max(ys) - min(ys)) * 1.15 + height * 0.06)
    x0 = int(max(0, cx - rw))
    y0 = int(max(0, cy - rh))
    x1 = int(min(width, cx + rw))
    y1 = int(min(height, cy + rh))
    return x0, y0, x1, y1


def apply_pose_to_still(
    source: Path | str,
    *,
    dest: Path,
    body: str = DEFAULT_BODY,
    hands: str = DEFAULT_HANDS,
    face: str = DEFAULT_FACE,
    face_lock: bool = True,
    micro: str = "",
    behavior: str = "",
) -> PoseResult:
    src = Path(source)
    if not src.is_file():
        raise PoseError("Drop a still first, then Apply pose.")
    body, hands, face = resolve_presets(body, hands, face)
    try:
        original = Image.open(src).convert("RGBA")
    except OSError as exc:
        raise PoseError(f"Could not read still: {exc}") from exc
    width, height = original.size
    keypoints = compose_keypoints(body, hands, face)
    overlay = Image.new("RGBA", original.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    line_w = max(3, min(width, height) // 110)
    joint_r = max(4, line_w + 1)

    def xy(name: str) -> tuple[int, int] | None:
        if name not in keypoints:
            return None
        x, y = keypoints[name]
        return int(x * width), int(y * height)

    for a, b in LIMBS:
        pa, pb = xy(a), xy(b)
        if pa and pb:
            draw.line([pa, pb], fill=LIMB_COLOR, width=line_w)
    for name in KEYPOINT_NAMES:
        if face_lock and name in FACE_KEYS:
            continue
        pt = xy(name)
        if pt:
            x, y = pt
            draw.ellipse(
                (x - joint_r, y - joint_r, x + joint_r, y + joint_r),
                fill=JOINT_COLOR,
            )
    bbox = face_bbox_px(width, height, keypoints)
    if face_lock:
        mask = Image.new("L", original.size, 0)
        ImageDraw.Draw(mask).ellipse(bbox, fill=255)
        overlay = Image.composite(
            Image.new("RGBA", original.size, (0, 0, 0, 0)), overlay, mask
        )
        tick_layer = Image.new("RGBA", original.size, (0, 0, 0, 0))
        _draw_face_tick(ImageDraw.Draw(tick_layer), bbox, face, width, height)
        overlay = Image.alpha_composite(overlay, tick_layer)
    composed = Image.alpha_composite(original, overlay).convert("RGB")
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    composed.save(dest, format="PNG")
    payload = {
        "kind": "film_lab_pose_guide",
        "method": "local_overlay",
        "not_video_puppeting": True,
        "still_first": True,
        "body": body,
        "hands": hands,
        "face": face,
        "micro_expression": micro or "",
        "behavior": behavior or "",
        "face_preserved": bool(face_lock),
        "face_bbox": list(bbox),
        "keypoints": {k: [round(v[0], 4), round(v[1], 4)] for k, v in keypoints.items()},
        "source_name": src.name,
        "notes": (
            "Still-first OpenPose-style guide. Face pixels kept for Character Bible / FaceID. "
            "Then Animate on Motion Desk (ComfyUI SVD). Not frame-by-frame video puppeting."
        ),
    }
    json_path = dest.with_name(dest.stem + ".pose.json")
    write_json(json_path, payload)
    from film_lab.performance import compose_performance

    perf = compose_performance(micro, behavior)
    extra = f" {perf}." if perf else ""
    message = (
        f"Pose applied on the still: {body} · {hands} · {face}.{extra} "
        "Face pixels kept (Character Bible / FaceID). "
        "Not video puppeting. Enhance, then Animate. Regenerate stays on."
    )
    return PoseResult(
        path=dest,
        json_path=json_path,
        body=body,
        hands=hands,
        face=face,
        face_preserved=bool(face_lock),
        method="local_overlay",
        face_bbox=bbox,
        keypoints=keypoints,
        message=message,
    )


def apply_pose_for_project(
    project: Project,
    source: Path | str,
    *,
    body: str = DEFAULT_BODY,
    hands: str = DEFAULT_HANDS,
    face: str = DEFAULT_FACE,
    micro: str = "",
    behavior: str = "",
) -> PoseResult:
    project.ensure_dirs()
    body, hands, face = resolve_presets(body, hands, face)
    name = f"pose_{slugify(body)}_{slugify(hands)}_{slugify(face)}_{new_id()}.png"
    dest = project.stills_dir / name
    return apply_pose_to_still(
        source,
        dest=dest,
        body=body,
        hands=hands,
        face=face,
        micro=micro,
        behavior=behavior,
    )


def _draw_face_tick(
    draw: ImageDraw.ImageDraw,
    bbox: tuple[int, int, int, int],
    face: str,
    width: int,
    height: int,
) -> None:
    """Direction hint *outside* the locked face oval. Never paints features."""
    x0, y0, x1, y1 = bbox
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    rx = (x1 - x0) / 2
    ry = (y1 - y0) / 2
    dx, dy = _FACE_TICK.get(face, (0.0, 0.0))
    if dx == 0.0 and dy == 0.0:
        return
    # Place the tick just outside the oval along the look vector.
    sx = 1.0 if dx > 0 else (-1.0 if dx < 0 else 1.0)
    sy = 1.0 if dy > 0 else (-1.0 if dy < 0 else 0.0)
    ox = cx + (rx + max(8, width * 0.02)) * sx
    oy = cy + (ry + max(8, height * 0.02)) * sy
    start = (int(ox), int(oy))
    end = (int(ox + dx * width * 0.35), int(oy + dy * height * 0.35))
    draw.line([start, end], fill=TICK_COLOR, width=max(3, min(width, height) // 140))


def detect_pose_nodes(object_info: dict[str, Any] | None) -> list[str]:
    keys = set(object_info or {})
    return [name for name in POSE_NODE_NAMES if name in keys]


def probe_pose() -> tuple[str, str]:
    """(Off|Local|Ready, message). Local overlay always works."""
    comfy = ComfyUII2VGenerator().probe()
    if not comfy.available:
        return (
            "Off",
            "ComfyUI sidecar Off. Local OpenPose-style overlay still works on the still. "
            f"ControlNet rewrite waits for `{comfy_url()}`. {comfy.message}",
        )
    try:
        from film_lab.generators.comfyui_i2v import _json

        info = _json("GET", f"{comfy_url()}/object_info")
        nodes = detect_pose_nodes(info if isinstance(info, dict) else {})
    except Exception:  # noqa: BLE001
        nodes = []
    if nodes:
        return (
            "Ready",
            f"OpenPose/ControlNet nodes on sidecar: {', '.join(nodes)}. "
            "Apply pose still writes a local guide unless you load a live graph. "
            "Film Lab will not fake a ControlNet rewrite.",
        )
    return (
        "Local",
        "Sidecar is up. No OpenPose/ControlNet nodes yet — still-first local overlay. "
        "Not video puppeting.",
    )


def workflow_is_live() -> bool:
    path = WORKFLOWS / "openpose_still.json"
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    return '"class_type"' in text and "film_lab_stub" not in text


def workflow_stub_note() -> str:
    return (
        "Optional graph: `workflows/pose/openpose_still.json`. "
        "Until it has ComfyUI `class_type` nodes, Apply pose is the local overlay. "
        "Sidecar `http://127.0.0.1:8188`. Then Animate (SVD-XT). Not video puppeting."
    )


def motion_step_html() -> str:
    steps = ("Upload", "Note", "Mark", "Pose adjust", "Enhance", "Animate")
    parts: list[str] = ["<ol class='fl-steps'>"]
    for i, label in enumerate(steps, start=1):
        if i > 1:
            parts.append("<li class='fl-step-arrow' aria-hidden='true'>→</li>")
        parts.append(
            f"<li class='fl-step'><span class='fl-step-num'>{i}</span><b>{label}</b></li>"
        )
    parts.append("</ol>")
    parts.append(
        "<p class='fl-step-later'>Then: Take Board click = play (pause never edits). "
        "Mark &amp; Direct = Fix this frame. Exit Direct keeps the old take.</p>"
    )
    return "".join(parts)


def pose_markdown() -> str:
    status, detail = probe_pose()
    lines = [
        "### Pose Desk — still-first, then Animate",
        "OpenPose / ControlNet-**style** guide on the **still**. "
        "Face lock stays via Character Bible / FaceID. Then Motion Desk Animate (ComfyUI SVD). "
        "**Not** frame-by-frame video puppeting. Zero credits.",
        "",
        f"**Sidecar:** {status}. {detail}",
        "",
        "- **Body** — stand, sit, lean in, kiss lean, recline, …",
        "- **Hands** — rest, on chest, in hair, near face (outside the lock), …",
        "- **Face** — front / 3/4 / profile ticks only. Features are not redrawn.",
        "- Apply writes `stills/pose_*.png` plus a `*.pose.json` sidecar.",
        "- Use the posed still on Motion Desk → Enhance → Animate. **Regenerate** stays on.",
        "",
        workflow_stub_note(),
    ]
    return "\n".join(lines)
