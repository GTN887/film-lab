"""LOCKED Environment from a photo — 3D Set Desk.

Upload a still → invent plausible missing edges → camera look-around /
zoom / aerial. Optional: place Character Bible actors on that plate and
look around with them.

Stored on this PC under data/projects/<name>/sets/, stills/, and takes/.
Offline. Deletable. Not a 3D mesh engine. Zero credits.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from film_lab.characters import (
    CharacterError,
    assert_adult_cast,
    load_selected_characters,
    resolve_refs,
)
from film_lab.envlock import apply_env_lock, load_env_lock, save_env_lock
from film_lab.filming import MODE_EXPLICIT, is_explicit_mode
from film_lab.project import IMAGE_SUFFIXES, Project
from film_lab.setdesk import CharacterMark, build_set_note, load_set_note, save_set_note
from film_lab.util import new_id, utc_now, write_json

ENV_CAMERAS: tuple[str, ...] = ("look-around", "zoom", "aerial")
DEFAULT_ENV_CAMERA = "look-around"

SET_INDEX = "index.json"

_CAMERA_TO_SET = {
    "look-around": "orbit",
    "zoom": "slow push-in",
    "aerial": "aerial",
}


class SetBuildError(RuntimeError):
    """Could not build or delete a locked environment."""


@dataclass
class BuiltSet:
    id: str
    title: str
    camera: str = DEFAULT_ENV_CAMERA
    source: str = ""
    expanded: str = ""
    views: list[str] = field(default_factory=list)
    take: str = ""
    character_ids: list[str] = field(default_factory=list)
    note: str = ""
    created_at: str = field(default_factory=utc_now)

    def folder_name(self) -> str:
        return self.id

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BuiltSet:
        views = [str(v) for v in (data.get("views") or []) if v]
        ids = [str(v) for v in (data.get("character_ids") or []) if v]
        return cls(
            id=str(data.get("id") or new_id()),
            title=str(data.get("title") or "Locked set"),
            camera=str(data.get("camera") or DEFAULT_ENV_CAMERA),
            source=str(data.get("source") or ""),
            expanded=str(data.get("expanded") or ""),
            views=views,
            take=str(data.get("take") or ""),
            character_ids=ids,
            note=str(data.get("note") or ""),
            created_at=str(data.get("created_at") or utc_now()),
        )


def storage_help(project: Project | None = None) -> str:
    """Document the on-disk folders. Show in README + 3D Set UI."""
    if project is not None:
        sets = project.sets_dir
        stills = project.stills_dir
        takes = project.takes_dir
    else:
        sets = Path("data") / "projects" / "<name>" / "sets"
        stills = Path("data") / "projects" / "<name>" / "stills"
        takes = Path("data") / "projects" / "<name>" / "takes"
    return (
        "**On this PC (offline, deletable):** "
        f"`{sets}` plates · `{stills}` copies · `{takes}` look-around clips. "
        "Also `env_lock.json` + `env_refs/` when the plate is locked. "
        "Delete this set removes those files. Nothing leaves the machine. Zero credits."
    )


def normalize_env_camera(raw: str | None) -> str:
    key = (raw or DEFAULT_ENV_CAMERA).strip().lower().replace("_", "-")
    aliases = {
        "look around": "look-around",
        "lookaround": "look-around",
        "orbit": "look-around",
        "push": "zoom",
        "slow push-in": "zoom",
        "drone": "aerial",
    }
    key = aliases.get(key, key)
    if key not in ENV_CAMERAS:
        raise SetBuildError("Camera must be look-around, zoom, or aerial.")
    return key


def invent_missing_areas(image: Image.Image) -> Image.Image:
    """Widen the plate and invent sky / floor / side continuation."""
    src = ImageOps.exif_transpose(image).convert("RGB")
    width, height = src.size
    left = max(24, int(width * 0.28))
    right = max(24, int(width * 0.28))
    top = max(24, int(height * 0.22))
    bottom = max(24, int(height * 0.18))
    canvas = Image.new("RGB", (width + left + right, height + top + bottom))
    top_color = _row_color(src, 0)
    bot_color = _row_color(src, height - 1)
    _fill_band(canvas, 0, 0, canvas.size[0], top, top_color, toward=(20, 28, 48))
    _fill_band(
        canvas,
        0,
        top + height,
        canvas.size[0],
        bottom,
        bot_color,
        toward=(28, 24, 20),
    )
    left_strip = src.crop((0, 0, max(4, width // 24), height)).resize(
        (left, height), Image.Resampling.LANCZOS
    )
    right_strip = src.crop((width - max(4, width // 24), 0, width, height)).resize(
        (right, height), Image.Resampling.LANCZOS
    )
    canvas.paste(left_strip.filter(ImageFilter.GaussianBlur(2.4)), (0, top))
    canvas.paste(right_strip.filter(ImageFilter.GaussianBlur(2.4)), (left + width, top))
    canvas.paste(src, (left, top))
    return _blend_seams(canvas, left, top, width, height)


def camera_view_crops(plate: Image.Image, camera: str) -> list[tuple[str, Image.Image]]:
    cam = normalize_env_camera(camera)
    width, height = plate.size
    views: list[tuple[str, Image.Image]] = []
    if cam == "look-around":
        span = int(width * 0.72)
        views.append(("look-left", plate.crop((0, 0, span, height))))
        mid0 = (width - span) // 2
        views.append(("look-center", plate.crop((mid0, 0, mid0 + span, height))))
        views.append(("look-right", plate.crop((width - span, 0, width, height))))
    elif cam == "zoom":
        views.append(("wide", plate.copy()))
        inset_x = int(width * 0.16)
        inset_y = int(height * 0.14)
        tight = plate.crop((inset_x, inset_y, width - inset_x, height - inset_y))
        views.append(
            (
                "zoom",
                tight.resize((width, height), Image.Resampling.LANCZOS),
            )
        )
    else:
        high = plate.crop((0, 0, width, int(height * 0.78)))
        views.append(
            ("aerial", high.resize((width, height), Image.Resampling.LANCZOS))
        )
        ground = plate.crop((0, int(height * 0.22), width, height))
        views.append(("ground", ground.resize((width, height), Image.Resampling.LANCZOS)))
    return views


def place_actors_on_plate(
    plate: Image.Image,
    actor_stills: list[Image.Image],
) -> Image.Image:
    """Stand bible refs on the invented floor. Soft local composite — not FaceID."""
    if not actor_stills:
        return plate
    out = plate.convert("RGBA")
    width, height = out.size
    count = len(actor_stills)
    for index, still in enumerate(actor_stills):
        figure = _figure_cut(still)
        target_h = max(48, int(height * 0.52))
        ratio = target_h / max(1, figure.size[1])
        target_w = max(24, int(figure.size[0] * ratio))
        figure = figure.resize((target_w, target_h), Image.Resampling.LANCZOS)
        if count == 1:
            x = (width - target_w) // 2
        else:
            slot = (index + 1) / (count + 1)
            x = int(width * slot - target_w / 2)
        y = height - target_h - max(8, int(height * 0.04))
        x = max(0, min(width - target_w, x))
        y = max(0, min(height - target_h, y))
        shadow = Image.new("RGBA", (target_w, max(8, target_h // 10)), (0, 0, 0, 70))
        out.paste(shadow, (x, y + target_h - shadow.size[1]), shadow)
        out.paste(figure, (x, y), figure)
    return out.convert("RGB")


def build_locked_environment(
    project: Project,
    photo: Path | str,
    *,
    camera: str = DEFAULT_ENV_CAMERA,
    character_ids: list[str] | None = None,
    filming_mode: str = "",
    title: str = "",
) -> BuiltSet:
    src = Path(photo)
    if not src.is_file() or src.suffix.lower() not in IMAGE_SUFFIXES:
        raise SetBuildError("Upload a photo (png / jpg / webp) to lock the environment.")
    cam = normalize_env_camera(camera)
    ids = _clean_ids(character_ids)
    profiles = load_selected_characters(project, ids) if ids else []
    if is_explicit_mode(filming_mode) and profiles:
        try:
            assert_adult_cast(
                profiles,
                intimacy_mode="explicit sex" if filming_mode == MODE_EXPLICIT else "",
                context="place actors on the locked set",
            )
        except CharacterError as exc:
            raise SetBuildError(str(exc)) from exc

    project.ensure_dirs()
    built = BuiltSet(
        id=f"set-{new_id()[:10]}",
        title=(title or src.stem or "Locked set").strip() or "Locked set",
        camera=cam,
        character_ids=[p.id for p in profiles],
    )
    folder = project.sets_dir / built.id
    folder.mkdir(parents=True, exist_ok=True)
    source_dest = folder / f"source{src.suffix.lower()}"
    if src.resolve() != source_dest.resolve():
        shutil.copy2(src, source_dest)
    built.source = source_dest.name

    original = Image.open(source_dest)
    expanded = invent_missing_areas(original)
    actor_pils: list[Image.Image] = []
    skipped: list[str] = []
    for profile in profiles:
        refs = resolve_refs(project, profile)
        if not refs:
            skipped.append(profile.name)
            continue
        actor_pils.append(Image.open(refs[0]))
    if actor_pils:
        expanded = place_actors_on_plate(expanded, actor_pils)
    expanded_path = folder / "expanded.png"
    expanded.save(expanded_path)
    built.expanded = expanded_path.name

    view_names: list[str] = []
    for label, frame in camera_view_crops(expanded, cam):
        dest = folder / f"{label}.png"
        frame.convert("RGB").save(dest)
        view_names.append(dest.name)
    built.views = view_names

    note_bits = [
        f"LOCKED Environment from photo ({cam})",
        "invented missing edges",
    ]
    if actor_pils:
        note_bits.append("bible actors: " + ", ".join(p.name for p in profiles))
    if skipped:
        note_bits.append("no pinned still for " + ", ".join(skipped))
    built.note = "; ".join(note_bits)

    take_path = _maybe_lookaround(expanded_path, project, built, cam)
    if take_path:
        built.take = take_path.name

    write_json(folder / "env.json", built.to_dict())
    _ingest_set_stills(project, built, folder)
    _lock_and_fold(project, expanded_path, built, profiles)
    _index_add(project, built)
    return built


def list_built_sets(project: Project) -> list[BuiltSet]:
    items: list[BuiltSet] = []
    for path in _index_paths(project):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and data.get("id"):
            items.append(BuiltSet.from_dict(data))
    items.sort(key=lambda b: b.created_at, reverse=True)
    return items


def built_set_choices(project: Project) -> list[str]:
    return [f"{b.id} — {b.title} ({b.camera})" for b in list_built_sets(project)]


def resolve_built_set(project: Project, choice: str | None) -> BuiltSet | None:
    text = (choice or "").strip()
    if not text:
        return None
    sid = text.split(" — ", 1)[0].strip()
    for item in list_built_sets(project):
        if item.id == sid:
            return item
    return None


def built_set_gallery(project: Project, built: BuiltSet | None) -> list[tuple[str, str]]:
    if built is None:
        return []
    folder = project.sets_dir / built.id
    items: list[tuple[str, str]] = []
    for name, label in (
        (built.expanded, "Expanded plate"),
        *[(v, Path(v).stem) for v in built.views],
    ):
        path = folder / name
        if path.is_file():
            items.append((str(path), label))
    return items


def built_set_take(project: Project, built: BuiltSet | None) -> str | None:
    if not built or not built.take:
        return None
    for folder in (project.takes_dir, project.sets_dir / built.id, project.outputs_dir):
        path = folder / Path(built.take).name
        if path.is_file():
            return str(path)
    return None


def delete_built_set(project: Project, choice: str | None) -> str:
    built = resolve_built_set(project, choice)
    if built is None:
        raise SetBuildError("Pick a built set on this PC to delete.")
    folder = project.sets_dir / built.id
    prefix = f"{built.id}-"
    if folder.is_dir():
        shutil.rmtree(folder, ignore_errors=True)
    for store in (project.stills_dir, project.takes_dir, project.outputs_dir):
        if not store.is_dir():
            continue
        for path in list(store.iterdir()):
            if path.name.startswith(prefix) or path.name.startswith(built.id):
                try:
                    path.unlink()
                except OSError:
                    pass
    lock = load_env_lock(project)
    if lock.still and (lock.still.startswith(prefix) or built.id in lock.still):
        lock.still = ""
        lock.locked = bool(lock.note)
        save_env_lock(project, lock)
    _index_remove(project, built.id)
    return built.id


def _maybe_lookaround(plate: Path, project: Project, built: BuiltSet, camera: str) -> Path | None:
    try:
        from film_lab.generators.ken_burns import render_camera_move
        from film_lab.generators.base import GeneratorUnavailable
    except ImportError:
        return None
    dest = project.takes_dir / f"{built.id}-{camera}.mp4"
    try:
        render_camera_move(plate, dest, camera, duration=4.0, strength=0.42)
    except (GeneratorUnavailable, OSError, ValueError):
        return None
    copy = project.outputs_dir / dest.name
    if dest.is_file() and dest.resolve() != copy.resolve():
        shutil.copy2(dest, copy)
        project.register_output(dest, generator="locked-environment", duration=4.0)
    return dest if dest.is_file() else None


def _ingest_set_stills(project: Project, built: BuiltSet, folder: Path) -> None:
    names = [built.expanded, *built.views]
    for name in names:
        src = folder / name
        if not src.is_file():
            continue
        dest = project.stills_dir / f"{built.id}-{name}"
        if src.resolve() != dest.resolve():
            shutil.copy2(src, dest)


def _lock_and_fold(
    project: Project,
    expanded: Path,
    built: BuiltSet,
    profiles,
) -> None:
    plate = expanded.parent / f"{built.id}-plate.png"
    if expanded.resolve() != plate.resolve():
        shutil.copy2(expanded, plate)
    apply_env_lock(
        project,
        still=plate,
        note=built.note,
    )
    note = load_set_note(project)
    placements = list(note.placements)
    for profile in profiles:
        placements = [m for m in placements if m.character_id != profile.id]
        placements.append(
            CharacterMark(
                character_id=profile.id,
                character_name=profile.name,
                role=getattr(profile, "role", "Adult") or "Adult",
                mark="in the locked set",
            )
        )
    save_set_note(
        project,
        build_set_note(
            camera=_CAMERA_TO_SET.get(built.camera, "orbit"),
            outdoor=note.outdoor,
            set_description=built.note,
            placements=placements,
        ),
    )


def _index_path(project: Project) -> Path:
    return project.sets_dir / SET_INDEX


def _index_paths(project: Project) -> list[Path]:
    root = project.sets_dir
    if not root.is_dir():
        return []
    found = sorted(root.glob("*/env.json"), reverse=True)
    return found


def _index_add(project: Project, built: BuiltSet) -> None:
    path = _index_path(project)
    rows = _index_rows(project)
    rows = [r for r in rows if r.get("id") != built.id]
    rows.insert(0, built.to_dict())
    write_json(path, {"sets": rows})


def _index_remove(project: Project, set_id: str) -> None:
    path = _index_path(project)
    rows = [r for r in _index_rows(project) if r.get("id") != set_id]
    write_json(path, {"sets": rows})


def _index_rows(project: Project) -> list[dict[str, Any]]:
    path = _index_path(project)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows = data.get("sets") if isinstance(data, dict) else data
    return [r for r in (rows or []) if isinstance(r, dict)]


def _clean_ids(raw) -> list[str]:
    ids: list[str] = []
    for item in raw or []:
        text = str(item or "").strip()
        if " — " in text:
            text = text.split(" — ", 1)[0].strip()
        if text and text not in ids:
            ids.append(text)
    return ids


def _row_color(image: Image.Image, y: int) -> tuple[int, int, int]:
    pixels = list(image.crop((0, y, image.size[0], y + 1)).getdata())
    if not pixels:
        return (32, 32, 32)
    r = sum(p[0] for p in pixels) // len(pixels)
    g = sum(p[1] for p in pixels) // len(pixels)
    b = sum(p[2] for p in pixels) // len(pixels)
    return (r, g, b)


def _fill_band(
    canvas: Image.Image,
    x: int,
    y: int,
    width: int,
    height: int,
    color: tuple[int, int, int],
    *,
    toward: tuple[int, int, int],
) -> None:
    if width <= 0 or height <= 0:
        return
    draw = ImageDraw.Draw(canvas)
    for row in range(height):
        t = row / max(1, height - 1)
        mix = (
            int(color[0] * (1 - t) + toward[0] * t),
            int(color[1] * (1 - t) + toward[1] * t),
            int(color[2] * (1 - t) + toward[2] * t),
        )
        draw.line([(x, y + row), (x + width, y + row)], fill=mix)


def _blend_seams(
    canvas: Image.Image,
    left: int,
    top: int,
    width: int,
    height: int,
) -> Image.Image:
    blurred = canvas.filter(ImageFilter.GaussianBlur(1.6))
    mask = Image.new("L", canvas.size, 0)
    draw = ImageDraw.Draw(mask)
    pad = 10
    draw.rectangle(
        (left - pad, top - pad, left + width + pad, top + height + pad),
        fill=90,
    )
    draw.rectangle((left, top, left + width, top + height), fill=0)
    mask = mask.filter(ImageFilter.GaussianBlur(6))
    return Image.composite(blurred, canvas, mask)


def _figure_cut(still: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(still).convert("RGBA")
    width, height = image.size
    if width > height:
        side = height
        x0 = (width - side) // 2
        image = image.crop((x0, 0, x0 + side, height))
        width, height = image.size
    crop_w = min(width, int(height * 0.55))
    crop_h = min(height, int(crop_w * 1.7))
    x0 = (width - crop_w) // 2
    y0 = max(0, height - crop_h)
    figure = image.crop((x0, y0, x0 + crop_w, y0 + crop_h))
    fade = Image.new("L", figure.size, 0)
    fade_draw = ImageDraw.Draw(fade)
    fade_draw.rounded_rectangle(
        (2, 2, figure.size[0] - 3, figure.size[1] - 3),
        radius=max(6, figure.size[0] // 12),
        fill=255,
    )
    figure.putalpha(fade.filter(ImageFilter.GaussianBlur(3.2)))
    return figure
