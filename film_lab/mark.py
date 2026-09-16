"""Mark & Direct — region edit on a still or a short-clip frame.

Draw circle / square / lasso. One region note at a time, stackable.
Apply writes a masked still + MARK NOTE, then Animate / Regenerate so
motion follows. Local overlay always works. Optional Comfy inpaint is a
stub — Film Lab never fakes an inpaint rewrite. Respects Regular vs
18+ Explicit. Zero credits.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from film_lab.ffmpeg_support import FFmpegError, run_ffmpeg
from film_lab.filming import FilmingError, assert_filming_safe, asks_sex_tools
from film_lab.generators.comfyui_i2v import ComfyUII2VGenerator, comfy_url
from film_lab.project import IMAGE_SUFFIXES, VIDEO_SUFFIXES, Project
from film_lab.util import new_id, write_json

MARKS_FILE = "mark_direct.json"
WORKFLOWS = Path(__file__).resolve().parents[1] / "workflows" / "mark"

SHAPE_CIRCLE = "circle"
SHAPE_SQUARE = "square"
SHAPE_LASSO = "lasso"
SHAPE_POINTER = "pointer"
SHAPES: tuple[str, ...] = (SHAPE_CIRCLE, SHAPE_SQUARE, SHAPE_LASSO, SHAPE_POINTER)
DEFAULT_SHAPE = SHAPE_CIRCLE

TARGETS: tuple[str, ...] = (
    "clothing",
    "body",
    "face emotion",
    "head",
    "hands",
    "prop",
    "prop action",
    "other",
)
DEFAULT_TARGET = "clothing"

# Film Lab purple + soft cyan — not a hosted-product lime.
STROKE = (139, 108, 255, 220)
FILL = (126, 232, 232, 70)
FACE_RING = (126, 232, 232, 230)

INPAINT_NODES: tuple[str, ...] = (
    "VAEEncodeForInpaint",
    "SetLatentNoiseMask",
    "InpaintModelConditioning",
    "VAEInpaint",
)

_SEX = re.compile(
    r"\b(nude|naked|sex|sexual|porn|undress|genital|penetration|"
    r"explicit sex|bare skin|remove clothes|take off|into explicit)\b",
    re.I,
)
_MARK_LINE = re.compile(r"^MARK NOTE \([^)]+\):.*$", re.M)


class MarkError(ValueError):
    """Bad still, empty lasso, or safety gate."""


@dataclass
class RegionMark:
    id: str
    shape: str = DEFAULT_SHAPE
    target: str = DEFAULT_TARGET
    note: str = ""
    cx: float = 0.50
    cy: float = 0.42
    size: float = 0.28
    mask_name: str = ""
    character_id: str = ""

    def line(self) -> str:
        note = " ".join((self.note or "").split())
        body = f"{self.shape} on {self.target}"
        if note:
            body = f"{body}; {note}"
        return f"MARK NOTE ({self.target}): {body}"


@dataclass
class ProjectMarks:
    regions: list[RegionMark] = field(default_factory=list)

    def render_block(self) -> str:
        return "\n".join(r.line() for r in self.regions if r.note or r.target)

    def to_dict(self) -> dict[str, Any]:
        return {"regions": [asdict(r) for r in self.regions]}


def normalize_shape(shape: str | None) -> str:
    text = (shape or "").strip().lower()
    return text if text in SHAPES else DEFAULT_SHAPE


def normalize_target(target: str | None) -> str:
    text = (target or "").strip().lower()
    return text if text in TARGETS else DEFAULT_TARGET


def marks_path(project: Project) -> Path:
    return project.root / MARKS_FILE


def load_marks(project: Project) -> ProjectMarks:
    path = marks_path(project)
    if not path.is_file():
        return ProjectMarks()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ProjectMarks()
    if not isinstance(data, dict):
        return ProjectMarks()
    found: list[RegionMark] = []
    raw = data.get("regions") or []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            rid = str(item.get("id") or "").strip() or new_id()
            found.append(
                RegionMark(
                    id=rid,
                    shape=normalize_shape(str(item.get("shape") or "")),
                    target=normalize_target(str(item.get("target") or "")),
                    note=str(item.get("note") or ""),
                    cx=_clamp01(item.get("cx"), 0.50),
                    cy=_clamp01(item.get("cy"), 0.42),
                    size=_clamp01(item.get("size"), 0.28, lo=0.04),
                    mask_name=str(item.get("mask_name") or ""),
                    character_id=str(item.get("character_id") or ""),
                )
            )
    return ProjectMarks(regions=found)


def save_marks(project: Project, marks: ProjectMarks) -> Path:
    project.ensure_dirs()
    path = marks_path(project)
    write_json(path, marks.to_dict())
    return path


def marks_markdown(marks: ProjectMarks | None = None) -> str:
    block = marks.render_block() if marks and marks.regions else ""
    head = (
        "### Mark & Direct\n"
        "Circle / square / lasso / **pointer** on the **still** or a short-clip frame. "
        "One region note at a time — stackable. Apply is regional inpaint / "
        "masked prompt (local overlay always; Comfy inpaint is optional and "
        "never faked). Then **Animate / Regenerate** so motion follows. "
        "Mark the **head** on a sleeping take to **Enter dream** (linked child scenes). "
        "Works with Pose + Director Note. Regular vs 18+ Explicit still applies."
    )
    if not block:
        return head + "\n\nNo regions yet. Draw a mark, write the note, Apply."
    return f"{head}\n\n{block}"


def mark_shot_bits(marks: ProjectMarks) -> list[str]:
    bits: list[str] = []
    for region in marks.regions:
        note = " ".join((region.note or "").split())
        bit = f"region {region.target} ({region.shape})"
        if note:
            bit = f"{bit}: {note}"
        bits.append(bit)
    return bits


def region_asks_sex(region: RegionMark) -> bool:
    blob = f"{region.target} {region.note}"
    return bool(_SEX.search(blob))


def marks_ask_sex(marks: ProjectMarks | None, text: str = "") -> bool:
    if _SEX.search(text or ""):
        return True
    if marks is None:
        return False
    return any(region_asks_sex(r) for r in marks.regions)


def assert_marks_safe(
    project: Project,
    marks: ProjectMarks,
    *,
    intimacy: str = "",
    intensity: float = 0.0,
    extra_note: str = "",
    context: str = "Mark & Direct",
) -> None:
    from film_lab.characters import load_selected_characters

    sex = marks_ask_sex(marks, extra_note) or asks_sex_tools(intimacy, intensity)
    if not sex:
        return
    ids = list(project.active_cast or [])
    profiles = load_selected_characters(project, ids)
    try:
        assert_filming_safe(
            getattr(project, "filming_mode", None),
            profiles,
            intimacy=intimacy if asks_sex_tools(intimacy, intensity) else ("intimate sex" if sex else ""),
            intensity=intensity if asks_sex_tools(intimacy, intensity) else (0.9 if sex else 0),
            context=context,
        )
    except FilmingError as exc:
        raise MarkError(str(exc)) from exc


def strip_mark_blocks(text: str) -> str:
    return _MARK_LINE.sub("", text or "")


def fold_marks_into_seed(seed: str, marks: ProjectMarks) -> str:
    from film_lab.director_notes import strip_note_blocks

    base = strip_note_blocks(strip_mark_blocks(seed)).strip()
    block = marks.render_block()
    if not block:
        return base
    if not base:
        return block
    return f"{base}\n\n{block}"


def still_from_source(source: Path | str, dest: Path, seconds: float = 0.0) -> Path:
    """Accept a still or pull a frame from a short clip at ``seconds``."""
    src = Path(source)
    if not src.is_file():
        raise MarkError("Drop a still or a short clip first.")
    suffix = src.suffix.lower()
    dest.parent.mkdir(parents=True, exist_ok=True)
    if suffix in IMAGE_SUFFIXES:
        if src.resolve() != dest.resolve():
            Image.open(src).convert("RGB").save(dest, format="PNG")
        return dest
    if suffix not in VIDEO_SUFFIXES:
        raise MarkError("Mark & Direct needs a still (png / jpg / webp) or a short clip (mp4 / webm / mov).")
    try:
        args = ["-y"]
        if float(seconds or 0) > 0:
            args += ["-ss", f"{float(seconds):.3f}"]
        args += ["-i", str(src), "-vframes", "1", str(dest)]
        run_ffmpeg(args)
    except FFmpegError as exc:
        raise MarkError(f"Could not pull a frame from the clip. {exc}") from exc
    if not dest.is_file():
        raise MarkError("Could not pull a frame from the clip.")
    return dest


def mask_from_editor(editor: Any, width: int, height: int) -> Image.Image | None:
    """Brush / lasso alpha from ImageEditor layers or a painted image."""
    if editor is None or editor == "":
        return None
    images: list[Image.Image] = []
    if isinstance(editor, dict):
        for key in ("layers",):
            layers = editor.get(key) or []
            if isinstance(layers, list):
                for layer in layers:
                    img = _as_image(layer)
                    if img is not None:
                        images.append(img)
        for key in ("composite", "background"):
            img = _as_image(editor.get(key))
            if img is not None and key == "composite":
                images.append(img)
    else:
        img = _as_image(editor)
        if img is not None:
            images.append(img)
    if not images:
        return None
    mask = Image.new("L", (width, height), 0)
    for img in images:
        fitted = img.convert("RGBA").resize((width, height), Image.Resampling.NEAREST)
        alpha = fitted.split()[-1]
        # Treat painted / non-transparent pixels as the lasso.
        mask = Image.composite(alpha.point(lambda p: 255 if p > 12 else 0), mask, alpha)
    if not any(mask.getdata()):
        return None
    return mask


def apply_region(
    project: Project,
    source: Path | str,
    *,
    shape: str,
    target: str,
    note: str,
    cx: float = 0.50,
    cy: float = 0.42,
    size: float = 0.28,
    editor: Any = None,
    character_id: str = "",
) -> tuple[Path, ProjectMarks, RegionMark]:
    project.ensure_dirs()
    shape_n = normalize_shape(shape)
    target_n = normalize_target(target)
    text = (note or "").strip()
    if shape_n == SHAPE_POINTER:
        raise MarkError(
            "Pointer / Go-to: click Actor A, point at a destination (bathroom / locked set), "
            "then Generate go-to take. That records on Take Board."
        )
    if not text:
        raise MarkError("Write a region note (clothing, body, face emotion, …) before Apply.")
    frame = project.stills_dir / f"mark_src_{new_id()}.png"
    still_from_source(source, frame)
    image = Image.open(frame).convert("RGB")
    width, height = image.size
    mask_name = ""
    if shape_n == SHAPE_LASSO:
        mask = mask_from_editor(editor, width, height)
        if mask is None:
            raise MarkError("Lasso needs a brush stroke on the still. Paint the region, then Apply.")
        mask_dir = project.stills_dir / "mark_masks"
        mask_dir.mkdir(parents=True, exist_ok=True)
        mask_name = f"{new_id()}.png"
        mask.save(mask_dir / mask_name, format="PNG")
    region = RegionMark(
        id=new_id(),
        shape=shape_n,
        target=target_n,
        note=text,
        cx=_clamp01(cx, 0.50),
        cy=_clamp01(cy, 0.42),
        size=_clamp01(size, 0.28, lo=0.04),
        mask_name=mask_name,
        character_id=(character_id or "").strip(),
    )
    marks = load_marks(project)
    marks.regions.append(region)
    dest = project.stills_dir / f"mark_{region.id}.png"
    paint_regions(image, marks, dest, project=project)
    sidecar = {
        "kind": "film_lab_mark_direct",
        "method": "local_mask_prompt",
        "not_fake_inpaint": True,
        "region": asdict(region),
        "stack": [r.id for r in marks.regions],
        "notes": (
            "Regional inpaint / masked prompt on the still or clip frame. "
            "Then Animate / Regenerate. Comfy inpaint is optional and never faked."
        ),
    }
    write_json(dest.with_name(dest.stem + ".mark.json"), sidecar)
    save_marks(project, marks)
    return dest, marks, region


def paint_regions(
    image: Image.Image,
    marks: ProjectMarks,
    dest: Path,
    *,
    project: Project | None = None,
) -> Path:
    base = image.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    width, height = base.size
    for region in marks.regions:
        if region.shape == SHAPE_LASSO and region.mask_name and project is not None:
            mask_path = project.stills_dir / "mark_masks" / region.mask_name
            if mask_path.is_file():
                mask = Image.open(mask_path).convert("L").resize(base.size, Image.Resampling.NEAREST)
                wash = Image.new("RGBA", base.size, FILL)
                overlay = Image.composite(wash, overlay, mask)
                # Stroke the lasso bounds with a simple edge pass.
                edge = mask.filter(__edge_filter())
                ring = Image.new("RGBA", base.size, STROKE)
                overlay = Image.composite(ring, overlay, edge)
                continue
        box = _shape_box(region, width, height)
        if region.target == "face emotion":
            draw.ellipse(box, outline=FACE_RING, width=max(3, min(width, height) // 120))
        elif region.shape == SHAPE_SQUARE:
            draw.rectangle(box, outline=STROKE, fill=FILL, width=max(3, min(width, height) // 140))
        else:
            draw.ellipse(box, outline=STROKE, fill=FILL, width=max(3, min(width, height) // 140))
    composed = Image.alpha_composite(base, overlay).convert("RGB")
    dest.parent.mkdir(parents=True, exist_ok=True)
    composed.save(dest, format="PNG")
    return dest


def _edge_filter():
    from PIL import ImageFilter

    return ImageFilter.FIND_EDGES


def _shape_box(region: RegionMark, width: int, height: int) -> tuple[int, int, int, int]:
    rx = max(8, int(width * region.size * 0.5))
    ry = max(8, int(height * region.size * 0.5))
    if region.shape == SHAPE_SQUARE:
        r = min(rx, ry)
        rx = ry = r
    cx = int(width * region.cx)
    cy = int(height * region.cy)
    return (cx - rx, cy - ry, cx + rx, cy + ry)


def _clamp01(value: object, default: float, *, lo: float = 0.0) -> float:
    try:
        return max(lo, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def _as_image(item: Any) -> Image.Image | None:
    if item is None or item == "":
        return None
    if isinstance(item, Image.Image):
        return item
    if isinstance(item, (str, Path)):
        path = Path(item)
        if path.is_file():
            return Image.open(path)
        return None
    if isinstance(item, dict):
        for key in ("image", "path", "composite", "value"):
            if key in item:
                found = _as_image(item[key])
                if found is not None:
                    return found
        return None
    try:
        import numpy as np

        if isinstance(item, np.ndarray):
            arr = item
            if arr.ndim == 2:
                return Image.fromarray(arr.astype("uint8"), "L")
            if arr.ndim == 3 and arr.shape[2] == 4:
                return Image.fromarray(arr.astype("uint8"), "RGBA")
            if arr.ndim == 3:
                return Image.fromarray(arr.astype("uint8"), "RGB")
    except ImportError:
        return None
    return None


def detect_inpaint_nodes(object_info: dict[str, Any] | None) -> list[str]:
    keys = set(object_info or {})
    return [name for name in INPAINT_NODES if name in keys]


def probe_mark() -> tuple[str, str]:
    comfy = ComfyUII2VGenerator().probe()
    if not comfy.available:
        return (
            "Off",
            "ComfyUI sidecar Off. Local masked-prompt overlay still works. "
            f"Inpaint rewrite waits for `{comfy_url()}`. {comfy.message}",
        )
    try:
        from film_lab.generators.comfyui_i2v import _json

        info = _json("GET", f"{comfy_url()}/object_info")
        nodes = detect_inpaint_nodes(info if isinstance(info, dict) else {})
    except Exception:  # noqa: BLE001
        nodes = []
    if nodes:
        return (
            "Ready",
            f"Inpaint nodes on sidecar: {', '.join(nodes)}. "
            "Apply still writes a local mask + MARK NOTE unless you load a live graph. "
            "Film Lab will not fake an inpaint rewrite.",
        )
    return (
        "Local",
        "Sidecar is up. No inpaint nodes yet — Mark & Direct is local mask + prompt. "
        "Then Animate / Regenerate.",
    )


def workflow_stub_note() -> str:
    return (
        "Optional graph: `workflows/mark/inpaint_region.json`. "
        "Until it has ComfyUI `class_type` nodes, Apply is the local mask + MARK NOTE. "
        "Sidecar `http://127.0.0.1:8188`. Then Animate (SVD-XT)."
    )
