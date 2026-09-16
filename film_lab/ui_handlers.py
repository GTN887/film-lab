"""Gradio callbacks for the local studio. Layout stays in app.py."""

from __future__ import annotations

import random
import threading
import time
from pathlib import Path

import gradio as gr

from film_lab.characters import (
    CharacterError,
    CharacterProfile,
    assert_adult_cast,
    cast_prompt_block,
    character_choices,
    characters_dir,
    compose_local_prompt,
    ensure_studio_library,
    export_to_studio_library,
    import_studio_library,
    list_characters,
    load_character,
    load_selected_characters,
    matching_characters,
    new_character,
    pin_reference,
    refs_for_shot,
    resolve_refs,
    save_character,
    write_consistency_hook,
)
from film_lab.constants import (
    CHARACTER_TAGS,
    DEFAULT_LIGHTING,
    DEFAULT_PROJECT,
    STORY_INTIMACY,
)
from film_lab.duration import parse_duration_preset
from film_lab.examples_import import import_example_shots, import_studio_bundle
from film_lab.ffmpeg_support import ffmpeg_available
from film_lab.finish import apply_lut, apply_vfx, finish_output_path, lut_choices, resolve_lut
from film_lab.generators import (
    DEFAULT_GENERATOR_ID,
    FALLBACK_GENERATOR_ID,
    GENERATORS,
    get_generator,
)
from film_lab.bridge import (
    agent_panel_html,
    connect_connector,
    connectors_status_markdown,
    setup_prompt,
)
from film_lab.hub import effect_by_label, local_lot_html, local_lot_markdown
from film_lab.lighting import expand_lighting, mentor_markdown
from film_lab.luts import ensure_stock_luts
from film_lab.ugc import (
    UgcBrief,
    UgcError,
    assert_ugc_adult,
    brief_choices,
    build_shot_plan,
    generate_script,
    list_briefs,
    load_brief,
    plan_table,
    push_plan_to_shots,
    save_brief,
)
from film_lab.variations import expand_takes, fork_take, shot_has_output, take_gallery_items
from film_lab.music import (
    MOODS,
    import_music,
    list_music_files,
    load_cues,
    new_cue,
    probe_musicgen,
    render_bed,
)
from film_lab.playback import (
    MODE_PLAYBACK,
    chrome as playback_chrome,
    clip_path,
    enter_direct,
    exit_direct,
    freeze_at,
    pick_gallery_item,
)
from film_lab.project import Project, default_data_root
from film_lab.voice_notes import (
    VoiceNoteError,
    merge_note,
    transcribe,
)
from film_lab.animate_ux import (
    QUICK_DURATION,
    QUICK_PROMPT,
    QUICK_STRENGTH,
    generating_label,
    sanitize_motion_error,
    toast_html,
)
from film_lab.effects import (
    build_effect_shot,
    preset_by_label,
    scale_desk_mp4,
    unique_output,
    workflow_stub_note,
)
from film_lab.enhance import EnhanceError, enhance_prompt
from film_lab.extend import (
    BEAT_HEADERS,
    ExtendError,
    beat_table,
    build_sequence,
    duration_for_form,
    load_sequence,
    mark_clip,
    parse_target,
    plan_note,
    prepare_next_shot,
    sequence_status_md,
    stitch_sequence,
)
from film_lab.imagine_feed import append_turn, ref_chip_html, render_feed
from film_lab.performance import (
    DEFAULT_BEHAVIOR,
    DEFAULT_MICRO,
    DEFAULT_PROP,
    compose_performance,
    compose_writing_line,
    fold_micro_into_breath,
    merge_prop_note,
)
from film_lab.director_notes import (
    DEFAULT_EMOTION,
    DEFAULT_WARDROBE,
    DirectorNoteError,
    SAFETY_LINE,
    assert_notes_safe,
    cast_gallery_items,
    fold_desk,
    fold_into_seed,
    list_cast_faces,
    load_notes,
    notes_markdown,
    save_notes,
    set_world_note,
    upsert_director_note,
)
from film_lab.pose import PoseError, apply_pose_for_project, pose_markdown
from film_lab.motion_path import (
    MotionBlocked,
    generate_motion_mp4,
    motion_engine_markdown,
)
from film_lab.queue import GenerationQueue, generate_one
from film_lab.reel import (
    ReelEntry,
    add_entry,
    assemble_reel,
    load_reel,
    rebuild_from_scenes,
    reel_rows,
    set_status,
)
from film_lab.script import (
    REEL_STATUSES,
    export_scene,
    lines_from_table,
    lines_to_table,
    link_shot,
    list_scenes,
    load_scene,
    new_scene,
    save_scene,
    scene_choices,
)
from film_lab.shot_card import ShotCard, new_shot_id
from film_lab.stitch import mux_audio_under, stitch_clips
from film_lab.util import new_id, slugify
from film_lab.voice import (
    VOICE_BACKENDS,
    apply_voice_defaults,
    default_tts_voice_id,
    direction_for,
    import_vo,
    list_dialogue,
    persist_voice_sample,
    probe_voice,
    resolve_voice_profile,
    speak_tagged_lines,
    synthesize_line,
    synthesize_takes,
)
from film_lab.characters import resolved_living
from film_lab.genres import (
    DEFAULT_PRIMARY,
    GenreGuardError,
    check_genre_intimacy,
    examples_for,
    join_custom_tags,
    parse_custom_tags,
    preset_for,
)
from film_lab.intensity import (
    DEFAULT_INTENSITY,
    DEFAULT_PRESET,
    IMPLIED_SOFT,
    clamp_content_intensity,
    nearest_intensity_preset,
    preset_to_intensity,
)
from film_lab.living import (
    DEFAULT_LIVING_PRESET,
    LIVING_PRESET_LABELS,
    LivingBrief,
    living_from_form,
    living_preset,
    living_preset_brief,
    living_to_ui,
)
from film_lab.senses import (
    DEFAULT_SENSE_PRESET,
    PRESET_LABELS,
    SensoryBrief,
    clamp_intensity,
    parse_enabled_senses,
    preset_brief,
    sense_labels_for,
)
from film_lab.llm import (
    DEFAULT_DUAL_ROLES,
    DEFAULT_PROVIDER,
    PROVIDER_CLAUDE,
    PROVIDER_DUAL,
    PROVIDER_GEMINI,
    PROVIDER_GROK,
    PROVIDER_LOCAL,
    PROVIDER_OPENAI,
    dual_missing_keys,
    get_anthropic_key,
    get_gemini_key,
    get_openai_key,
    get_xai_key,
    leave_notice,
    writing_api_markdown as provider_status_markdown,
)
from film_lab.providers import (
    IMAGE_FAMILY_DEFAULT,
    TEXT_FAMILY_DEFAULT,
    family_to_provider,
    image_models_for,
    provider_to_family,
    resolve_image_pick,
    resolve_text_pick,
    resolve_video_pick,
    resolve_voice_provider,
    text_models_for,
)
from film_lab.writing import (
    API_LEAVE_NOTICE,
    ROLEPLAY_SPEAKERS,
    WRITING_MODES,
    ChatTurn,
    WritingDraft,
    WritingError,
    build_prompt_pack,
    draft_choices,
    export_draft,
    extract_dialogue_takes,
    generate_draft,
    list_drafts,
    load_draft,
    new_draft,
    probe_writing_api,
    push_draft_to_scene,
    save_draft,
)
from film_lab.char_sheet import (
    BibleSheetError,
    export_bible_sheet,
    ext_for_bible_export,
    import_bible_files,
    sheet_filename,
)
from film_lab.office import (
    OfficeError,
    ext_for_export_label,
    import_files_as_text,
)
from film_lab.write_fuse import (
    FuseError,
    WriteImportError,
    collect_sources,
    fuse_texts,
    mode_for_target,
    push_pages_to_shots,
    split_beats,
)

QUEUE_HEADERS = ["id", "name", "camera", "dur", "intimacy", "status", "message"]
REEL_HEADERS = ["#", "status", "scene", "shot", "clip", "dialogue", "music", "notes", "id"]
DIALOGUE_HEADERS = ["character", "parenthetical", "dialogue"]


def _as_paths(files) -> list[Path]:
    if not files:
        return []
    if not isinstance(files, list):
        files = [files]
    out: list[Path] = []
    for item in files:
        if item is None:
            continue
        if isinstance(item, dict):
            raw = item.get("path") or item.get("name") or item.get("video") or ""
            if not raw:
                continue
            path = Path(raw)
        elif isinstance(item, (str, Path)):
            path = Path(item)
        elif hasattr(item, "name"):
            path = Path(item.name)
        else:
            continue
        if path.is_file():
            out.append(path)
    return out


def _none_if_empty(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_seed(value) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _id_from_choice(choice: str | None) -> str:
    if not choice:
        return ""
    return str(choice).split(" — ", 1)[0].strip()


def ensure_default_project() -> Project:
    default_data_root().mkdir(parents=True, exist_ok=True)
    ensure_stock_luts()
    names = Project.list_names()
    if DEFAULT_PROJECT in names:
        project = Project.load(DEFAULT_PROJECT)
    else:
        project = Project.create(
            DEFAULT_PROJECT,
            description="Alison & Bradley bedroom scene studies",
        )
    ensure_studio_library()
    import_studio_bundle(project)
    import_studio_library(project)
    return project


def load_project(name: str) -> Project:
    if not name:
        return ensure_default_project()
    try:
        return Project.load(name)
    except FileNotFoundError:
        return Project.create(name)


def browse_library_ui(project_name: str, shelf: str):
    from film_lab.savelib import list_shelf, preview_paths, table_rows

    project = load_project(project_name)
    items = list_shelf(project, shelf)
    rows = table_rows(items)
    previews = preview_paths(items)
    if items:
        note = f"{len(items)} local file(s) in **{shelf}**. This PC is the library."
    else:
        note = (
            f"Empty **{shelf}** shelf. Ingest stills, generate a take, lock a set, "
            "or save a draft. Local-first — Drive is optional."
        )
    return rows, previews, note


def connect_drive_ui(kind: str, path: str):
    from film_lab.savelib import connect_folder, status_markdown

    saved, msg = connect_folder(kind, path)
    return saved, status_markdown(), msg


def backup_library_ui(project_name: str, onedrive: str, gdrive: str):
    from film_lab.savelib import backup_project, status_markdown

    project = load_project(project_name)
    msg = backup_project(project, onedrive=onedrive, gdrive=gdrive)
    return status_markdown(), msg


def library_status_ui():
    from film_lab.savelib import load_sync_config, status_markdown, suggest_drive_folders

    cfg = load_sync_config()
    one, gdrive = suggest_drive_folders()
    return (
        cfg.onedrive or one,
        cfg.gdrive or gdrive,
        status_markdown(cfg),
    )


def project_dropdown_update(selected: str | None = None) -> gr.Dropdown:
    names = Project.list_names()
    if not names:
        ensure_default_project()
        names = Project.list_names()
    value = selected if selected in names else (DEFAULT_PROJECT if DEFAULT_PROJECT in names else names[0])
    return gr.Dropdown(choices=names, value=value)


def still_dropdowns(project: Project) -> tuple[gr.Dropdown, gr.Dropdown]:
    names = project.still_choices()
    start = gr.Dropdown(choices=names, value=names[0] if names else None)
    return start, gr.Dropdown(choices=[""] + names, value="")


def shot_dropdown(project: Project, selected_id: str | None = None) -> gr.Dropdown:
    choices = [f"{s.id} — {s.name}" for s in project.list_shots()]
    value = None
    if selected_id:
        for label in choices:
            if label.startswith(selected_id):
                value = label
                break
    elif choices:
        value = choices[0]
    return gr.Dropdown(choices=choices, value=value)


def scene_dropdown(project: Project, selected_id: str | None = None) -> gr.Dropdown:
    choices = [""] + scene_choices(project)
    value = ""
    if selected_id:
        for label in choices:
            if label.startswith(selected_id):
                value = label
                break
    return gr.Dropdown(choices=choices, value=value)


def parent_dropdown(project: Project, selected_id: str | None = None) -> gr.Dropdown:
    from film_lab.genetics import adult_parent_choices

    choices = adult_parent_choices(project)
    value = None
    if selected_id:
        for label in choices:
            if label.startswith(selected_id):
                value = label
                break
    elif choices:
        value = choices[0]
    return gr.Dropdown(choices=choices, value=value)


def _parent_dropdowns(project: Project, actor_id: str | None = None, actress_id: str | None = None):
    picks = adult_ids_hint(project)
    return (
        parent_dropdown(project, actor_id or (picks[0] if picks else None)),
        parent_dropdown(project, actress_id or (picks[1] if len(picks) > 1 else (picks[0] if picks else None))),
    )


def adult_ids_hint(project: Project) -> list[str]:
    from film_lab.genetics import adult_parent_choices

    ids: list[str] = []
    for label in adult_parent_choices(project):
        cid = _id_from_choice(label)
        if cid and cid not in ids:
            ids.append(cid)
    return ids


def char_dropdown(project: Project, selected_id: str | None = None) -> gr.Dropdown:
    choices = character_choices(project)
    value = None
    if selected_id:
        for label in choices:
            if label.startswith(selected_id):
                value = label
                break
    elif choices:
        value = choices[0]
    return gr.Dropdown(choices=choices, value=value)


def gallery_choices(project: Project) -> list[str]:
    labels = []
    for clip in project.load_gallery():
        if Path(clip.path).is_file():
            labels.append(_clip_label(clip.path, clip.shot_name, clip.generator))
    return labels


def _clip_label(path: str, shot_name: str, generator: str) -> str:
    name = Path(path).name
    extra = f"{shot_name} · " if shot_name else ""
    gen = f" · {generator}" if generator else ""
    return f"{extra}{name}{gen} | {path}"


def _path_from_label(label: str) -> Path:
    return Path(label.rsplit(" | ", 1)[-1])


def status_markdown() -> str:
    from film_lab.offline import offline_status_line

    ff_ok, ff_msg = ffmpeg_available()
    voice_id, voice_msg = probe_voice()
    music_ok, music_msg = probe_musicgen()
    write_state, write_msg = probe_writing_api()
    lines = [
        "### Machine",
        "- **Film school lock:** personal study only. No subscriptions, credits, quotas, or paywalls.",
        f"- ffmpeg: {'ready' if ff_ok else 'missing'} — {ff_msg}",
        f"- voice: **{voice_id}** — {voice_msg}",
        f"- score: {'audiocraft present' if music_ok else 'import + local synth'} — {music_msg}",
        f"- writing: local templates **always on** · optional APIs **{write_state}** — {write_msg}",
        "- Film Lab credits: **none**. Optional Grok / Gemini / ChatGPT / Claude use keys you own.",
        f"- offline: **{offline_status_line()}**",
        "- lighting: local preset chips. Injected into Motion / bible. See Lighting Desk.",
        "- motion: still + prompt → local SVD-XT img2vid on ComfyUI. Ken Burns is Advanced only.",
    ]
    from film_lab.consistency import probe_face_lock

    lock_state, lock_msg = probe_face_lock()
    lines.append(f"- face lock: **{lock_state}** — {lock_msg}")
    from film_lab.consistency import probe_env_lock

    env_state, env_msg = probe_env_lock()
    lines.append(f"- environment lock: **{env_state}** — {env_msg}")
    for gen in GENERATORS.values():
        if gen.id == FALLBACK_GENERATOR_ID:
            continue
        probe = gen.probe()
        mark = "ready" if probe.available else "unavailable"
        lines.append(f"- {gen.label}: **{mark}** — {probe.message}")
    lines.append(
        "- Ken Burns CPU zoom: **Advanced only** (timing). Not a Motion Desk engine."
    )
    lines.append(
        "- Intimacy / sex modes are **director knobs**, including explicit / pornographic. "
        "Adults 18+ only. Nothing is filtered or uploaded."
    )
    return "\n".join(lines)


def tag_choices(project: Project) -> list[str]:
    names = list(CHARACTER_TAGS)
    for profile in list_characters(project):
        if profile.name not in names:
            names.append(profile.name)
    return names


def card_from_form(
    shot_id: str,
    name: str,
    start_frame: str | None,
    end_frame: str | None,
    duration: float,
    aspect_ratio: str,
    camera_move: str,
    strength: float,
    body_notes: str,
    intimacy: str,
    intensity_preset: str,
    content_intensity,
    tags: list[str] | None,
    lighting: str,
    negative: str,
    seed,
    intent: str,
    start_hint: str,
    end_hint: str,
    scene_choice: str | None = None,
    character_ids: list[str] | None = None,
    dialogue_cue: str = "",
    dialogue_start: float = 0.0,
    dialogue_wav: str | None = None,
    face_lock_strength=0.55,
) -> ShotCard:
    ids = []
    for item in character_ids or []:
        ids.append(_id_from_choice(item) if " — " in str(item) else str(item))
    return ShotCard(
        id=(shot_id or "").strip() or new_shot_id(),
        name=(name or "").strip() or "Untitled shot",
        start_frame=_none_if_empty(start_frame),
        end_frame=_none_if_empty(end_frame),
        start_frame_hint=start_hint or "",
        end_frame_hint=end_hint or "",
        duration=float(duration),
        aspect_ratio=aspect_ratio,
        camera_move=camera_move,
        subject_motion_strength=float(strength),
        body_motion_notes=body_notes or "",
        intimacy_mode=intimacy,
        intensity_preset=intensity_preset or nearest_intensity_preset(content_intensity),
        content_intensity=clamp_content_intensity(content_intensity),
        character_tags=list(tags or []),
        lighting=(lighting or "").strip(),
        negative_prompt=_none_if_empty(negative),
        seed=_parse_seed(seed),
        director_intent=intent or "",
        scene_id=_id_from_choice(scene_choice) or None,
        character_ids=ids,
        dialogue_cue=dialogue_cue or "",
        dialogue_start_s=float(dialogue_start or 0),
        dialogue_wav=_none_if_empty(dialogue_wav),
        face_lock_strength=face_lock_strength,
    )


def form_from_card(shot: ShotCard, project: Project | None = None) -> tuple:
    prompt = compose_local_prompt(shot, project) if project else shot.local_prompt()
    return (
        shot.id,
        shot.name,
        shot.start_frame,
        shot.end_frame or "",
        shot.duration,
        shot.aspect_ratio,
        shot.camera_move,
        shot.subject_motion_strength,
        shot.body_motion_notes,
        shot.intimacy_mode,
        shot.intensity_preset or nearest_intensity_preset(shot.content_intensity),
        shot.content_intensity,
        shot.character_tags,
        shot.lighting,
        shot.negative_prompt or "",
        shot.seed,
        shot.director_intent,
        shot.start_frame_hint,
        shot.end_frame_hint,
        shot.scene_id or "",
        shot.character_ids,
        shot.dialogue_cue,
        shot.dialogue_start_s,
        shot.dialogue_wav or "",
        shot.face_lock_strength,
        prompt,
    )


def refresh_core(project: Project):
    stills = [str(p) for p in project.list_stills()]
    start, end = still_dropdowns(project)
    return (
        stills,
        start,
        end,
        shot_dropdown(project),
        gr.CheckboxGroup(choices=gallery_choices(project), value=[]),
        scene_dropdown(project),
        char_dropdown(project),
        _reel_table(project),
        draft_dropdown(project),
        scene_dropdown(project),
        shot_dropdown(project),
    )


def _reel_table(project: Project):
    return reel_rows(load_reel(project))


def create_project(name: str, current: str):
    try:
        project = Project.create(name.strip())
        import_studio_bundle(project)
        msg = f"Project `{project.name}` is ready."
        selected = project.name
    except ValueError as exc:
        msg = str(exc)
        selected = current
        project = load_project(current)
    return (
        project_dropdown_update(selected),
        selected,
        *refresh_core(project),
        msg,
        local_lot_html(),
        load_still_notes_ui(selected),
        ugc_brief_dropdown(project),
        gr.update(choices=project.still_choices(), value=project.still_choices()[0] if project.still_choices() else None),
        *_quality_ui(project),
        *_aspect_ui(project),
    )


def on_project_change(name: str):
    project = load_project(name)
    stills = project.still_choices()
    return (
        name,
        *refresh_core(project),
        f"Opened `{project.name}`. Quality {project.quality}.",
        local_lot_html(),
        load_still_notes_ui(name),
        ugc_brief_dropdown(project),
        gr.update(choices=stills, value=stills[0] if stills else None),
        *_quality_ui(project),
        *_aspect_ui(project),
    )


def open_hub_tab(tab_id: str):
    return gr.update(selected=tab_id)


def apply_effect_shelf_ui(label: str):
    look = effect_by_label(label)
    return (
        gr.update(selected="finish"),
        look.lut,
        look.vfx,
        look.strength,
        True,
        True,
        f"Shelf look **{look.label}**. Pick a gallery clip and run finish. Zero credits.",
    )


def generate_effect_now(
    project_name: str,
    character,
    location,
    product,
    preset_label: str,
    aspect: str,
    resolution: str,
    use_extra: bool,
    extra: str,
    character_ids,
    image_family="",
    image_model="",
    lighting="",
):
    from film_lab.generators.comfyui_i2v import clear_generation_hooks, set_generation_hooks

    image_route = resolve_image_pick(image_family or IMAGE_FAMILY_DEFAULT, image_model)
    if not image_route.local_i2v:
        yield (
            gr.update(),
            gr.update(visible=False),
            generating_label(0),
            toast_html(image_route.message),
            image_route.message,
            gr.update(),
            None,
        )
        return

    project = load_project(project_name)
    faces = _as_paths(character)
    if not faces:
        yield (
            gr.update(),
            gr.update(visible=False),
            generating_label(0),
            toast_html("Upload a character still (PNG or JPG) first."),
            "Character still required.",
            gr.update(),
            None,
        )
        return
    locs = _as_paths(location)
    products = _as_paths(product)
    ingested = project.ingest_files(faces + locs + products)
    start_name = ingested[0].name if ingested else faces[0].name
    preset = preset_by_label(preset_label)
    shot = build_effect_shot(
        preset,
        aspect=aspect or "16:9",
        extra=extra or "",
        use_extra=bool(use_extra),
        has_location=bool(locs),
        has_product=bool(products),
        start_frame=start_name,
        character_ids=list(character_ids or []),
        lighting=lighting or "",
    )
    try:
        _guard_shot_cast(project, shot)
    except gr.Error as exc:
        yield (
            gr.update(),
            gr.update(visible=False),
            generating_label(0),
            toast_html(str(exc)),
            sanitize_motion_error(str(exc)),
            gr.update(),
            None,
        )
        return

    # Creator Generate is gated by the same runtime certification used by Diagnostics.
    # Do not start ComfyUI when the machine/workflow/model/ffmpeg path is not ready.
    gate_report = None
    if generator_id != FALLBACK_GENERATOR_ID:
        from film_lab.generation_gate import preflight_generation
        gate = preflight_generation(shot)
        gate_report = gate.report
        if not gate.allowed:
            yield _motion_pack(
                project, shot, overlay=False, toast=toast_html(gate.message),
                status=gate.message, feed_history=feed_history,
                ref_chip=ref_chip_html(attached),
            )
            return

    _CANCEL.clear()
    latest = {"pct": 8, "done": None, "err": None}

    def on_progress(pct: int) -> None:
        latest["pct"] = pct

    def work() -> None:
        try:
            set_generation_hooks(progress=on_progress, cancel=_CANCEL.is_set)
            output, note = generate_motion_mp4(
                project,
                shot,
                generator_id=DEFAULT_GENERATOR_ID,
                uploaded=faces,
                allow_fallback=False,
            )
            certification = None
            if gate_report is not None:
                from film_lab.render_certification import certify_generated_output
                certification = certify_generated_output(
                    project, output_path=output, preflight=gate_report,
                    expected_generator=DEFAULT_GENERATOR_ID,
                )
            dest = unique_output(project, f"fx_{preset.id}_{resolution}")
            try:
                scale_desk_mp4(output, dest, aspect=shot.aspect_ratio, resolution=resolution or "720")
            except Exception:
                dest = output
            project.register_output(dest, shot=shot, generator="effects")
            latest["done"] = (dest, note, certification)
        except Exception as exc:  # noqa: BLE001
            latest["err"] = exc
        finally:
            clear_generation_hooks()

    thread = threading.Thread(target=work, daemon=True)
    thread.start()
    stub = workflow_stub_note(preset)
    yield (
        gr.update(visible=True),
        gr.update(visible=True),
        generating_label(8),
        "",
        f"{stub} Generating **{preset.label}** on local SVD-XT. Adults 18+.",
        gr.update(),
        None,
    )
    while thread.is_alive():
        time.sleep(0.35)
        yield (
            gr.update(visible=True),
            gr.update(visible=True),
            generating_label(int(latest["pct"])),
            "",
            "Generating… local ComfyUI. Cancel anytime. Zero credits.",
            gr.update(),
            None,
        )
    if latest["err"] is not None:
        msg = sanitize_motion_error(str(latest["err"]))
        yield (
            gr.update(),
            gr.update(visible=False),
            generating_label(0),
            toast_html(msg),
            msg,
            gr.update(),
            None,
        )
        return
    dest, note, certification = latest["done"]
    gallery = gallery_choices(project)
    label = next((g for g in gallery if str(Path(dest).resolve()) in g), None)
    yield (
        gr.update(value=str(dest), visible=True),
        gr.update(visible=False),
        generating_label(0),
        "",
        f"{note} {preset.label} · {shot.aspect_ratio} · {resolution}p. {stub} Zero credits."
        + (f"\nCertification: {certification.status} · {certification.id}" if certification else ""),
        gr.CheckboxGroup(choices=gallery, value=[label] if label else []),
        str(dest),
    )


def still_notes_path(project) -> Path:
    return project.root / "still_desk.md"


def load_still_notes_ui(project_name: str) -> str:
    project = load_project(project_name)
    path = still_notes_path(project)
    if path.is_file():
        return path.read_text(encoding="utf-8")
    cast = cast_prompt_block(project)
    return (
        "Local still notes (this folder only).\n"
        "What to lock in the frame, what to generate later on Motion Desk.\n"
        "Adults 18+ only. Nothing is uploaded.\n"
        f"Active cast:\n{cast}\n"
    )


def save_still_notes_ui(project_name: str, text: str) -> str:
    project = load_project(project_name)
    still_notes_path(project).write_text(text or "", encoding="utf-8")
    return f"Saved still notes under `{project.name}/still_desk.md`."


def build_takes_ui(
    project_name: str,
    shot_choice: str,
    count,
    vary_seed,
    vary_camera,
    vary_motion,
):
    project = load_project(project_name)
    sid = _id_from_choice(shot_choice)
    if not sid:
        raise gr.Error("Pick a saved shot on Take Board.")
    source = project.load_shot(sid)
    notes = load_notes(project)
    try:
        assert_notes_safe(
            project,
            notes,
            intimacy=source.intimacy_mode,
            intensity=source.content_intensity,
            context="Take Board → Enhance → Pose → Animate",
        )
    except DirectorNoteError as exc:
        raise gr.Error(str(exc)) from exc
    source.director_intent = fold_desk(project, source.director_intent)
    created = expand_takes(
        project,
        source,
        count=int(count or 3),
        vary_seed=bool(vary_seed),
        vary_camera=bool(vary_camera),
        vary_motion=bool(vary_motion),
    )
    rows = [
        [
            s.id,
            s.name,
            s.camera_move,
            str(s.seed if s.seed is not None else ""),
            f"{s.subject_motion_strength:.2f}",
        ]
        for s in created
    ]
    hint = (
        f"Wrote {len(created)} take(s) from `{source.name}`. "
        "Director Note / World Note folded in. "
        "Open Motion Desk or Queue to generate. Zero credits."
    )
    dd = shot_dropdown(project, created[0].id)
    return dd, dd, rows, hint


def ugc_brief_dropdown(project, selected: str | None = None):
    choices = brief_choices(project)
    value = None
    if selected:
        for label in choices:
            if label.startswith(selected):
                value = label
                break
    elif choices:
        value = choices[0]
    return gr.Dropdown(choices=choices, value=value)


def _ugc_from_form(
    brief_id,
    product_name,
    product_notes,
    product_still,
    creator_name,
    creator_look,
    creator_age,
    hook,
    problem,
    product_line,
    proof,
    cta,
    provider,
) -> UgcBrief:
    return UgcBrief(
        id=(brief_id or "").strip(),
        product_name=product_name or "",
        product_notes=product_notes or "",
        product_still=_none_if_empty(product_still) or "",
        creator_name=creator_name or "",
        creator_look=creator_look or "",
        creator_age=creator_age,
        hook=hook or "",
        problem=problem or "",
        product=product_line or "",
        proof=proof or "",
        cta=cta or "",
        provider=provider,
    )


def _ugc_to_form(brief: UgcBrief):
    return (
        brief.id,
        brief.product_name,
        brief.product_notes,
        brief.product_still or "",
        brief.creator_name,
        brief.creator_look,
        brief.creator_age,
        brief.hook,
        brief.problem,
        brief.product,
        brief.proof,
        brief.cta,
        brief.provider,
        plan_table(build_shot_plan(brief)) if brief.hook else [],
    )


def ugc_write_script_ui(
    project_name,
    brief_id,
    product_name,
    product_notes,
    product_still,
    creator_name,
    creator_look,
    creator_age,
    hook,
    problem,
    product_line,
    proof,
    cta,
    provider,
):
    project = load_project(project_name)
    try:
        brief = _ugc_from_form(
            brief_id,
            product_name,
            product_notes,
            product_still,
            creator_name,
            creator_look,
            creator_age,
            hook,
            problem,
            product_line,
            proof,
            cta,
            provider,
        )
        brief = generate_script(brief, provider=provider, project=project)
        save_brief(project, brief)
    except UgcError as exc:
        raise gr.Error(str(exc)) from exc
    hint = (
        f"Script ready ({brief.provider}). Five spoken beats. Zero Film Lab credits. "
        "Build the 9:16 plan next."
    )
    if brief.provider != PROVIDER_LOCAL:
        hint += f" {leave_notice(brief.provider)}"
    return (*_ugc_to_form(brief), ugc_brief_dropdown(project, brief.id), hint)


def ugc_save_brief_ui(
    project_name,
    brief_id,
    product_name,
    product_notes,
    product_still,
    creator_name,
    creator_look,
    creator_age,
    hook,
    problem,
    product_line,
    proof,
    cta,
    provider,
):
    project = load_project(project_name)
    try:
        brief = _ugc_from_form(
            brief_id,
            product_name,
            product_notes,
            product_still,
            creator_name,
            creator_look,
            creator_age,
            hook,
            problem,
            product_line,
            proof,
            cta,
            provider,
        )
        if brief.hook:
            build_shot_plan(brief)
        save_brief(project, brief)
    except UgcError as exc:
        raise gr.Error(str(exc)) from exc
    return brief.id, ugc_brief_dropdown(project, brief.id), f"Saved UGC brief `{brief.id}`."


def ugc_load_brief_ui(project_name, choice):
    if not choice:
        raise gr.Error("Pick a saved UGC brief.")
    project = load_project(project_name)
    brief = load_brief(project, _id_from_choice(choice))
    return (*_ugc_to_form(brief), f"Loaded `{brief.product_name or brief.id}`.")


def ugc_push_shots_ui(
    project_name,
    brief_id,
    product_name,
    product_notes,
    product_still,
    creator_name,
    creator_look,
    creator_age,
    hook,
    problem,
    product_line,
    proof,
    cta,
    provider,
):
    project = load_project(project_name)
    try:
        brief = _ugc_from_form(
            brief_id,
            product_name,
            product_notes,
            product_still,
            creator_name,
            creator_look,
            creator_age,
            hook,
            problem,
            product_line,
            proof,
            cta,
            provider,
        )
        if not brief.hook:
            brief = generate_script(brief, provider=PROVIDER_LOCAL, project=project)
        shots = push_plan_to_shots(project, brief)
    except UgcError as exc:
        raise gr.Error(str(exc)) from exc
    rows = plan_table(build_shot_plan(brief))
    hint = (
        f"Wrote {len(shots)} vertical shots (9:16, ~{sum(s.duration for s in shots):.0f}s). "
        "Open Motion Desk to generate, Take Board for variants, Cinema Desk to stitch. "
        "6GB AMD: generate one beat at a time."
    )
    dd = shot_dropdown(project, shots[0].id)
    return (
        brief.id,
        rows,
        dd,
        dd,
        ugc_brief_dropdown(project, brief.id),
        hint,
    )


def ugc_ingest_product_ui(project_name, files):
    project = load_project(project_name)
    written = project.ingest_files(_as_paths(files))
    names = project.still_choices()
    value = written[-1].name if written else (names[-1] if names else "")
    msg = (
        f"Ingested product still `{value}`."
        if written
        else "No image ingested. Use png / jpg / webp."
    )
    return (
        gr.update(choices=names, value=value),
        gr.update(choices=names, value=names[0] if names else None),
        [str(p) for p in project.list_stills()],
        msg,
    )


def _product_avatar_id(choice: str) -> str:
    return _id_from_choice(choice) if choice else ""


def _product_start_update(project: Project, name: str):
    names = project.still_choices()
    value = name if name in names else (names[0] if names else None)
    return gr.update(choices=names, value=value)


def resolve_product_avatar_ui(project_name: str, bible_choice: str, upload):
    from film_lab.product import ProductError, resolve_avatar_still

    project = load_project(project_name)
    uploads = _as_paths(upload)
    try:
        path, label = resolve_avatar_still(
            project,
            character_id=_product_avatar_id(bible_choice),
            upload=uploads[0] if uploads else None,
        )
    except (ProductError, UgcError) as exc:
        return None, toast_html(str(exc)), str(exc)
    return str(path), "", f"Avatar ready ({label}). Adults 18+."


def compose_product_still_ui(
    project_name: str,
    product_file,
    bible_choice: str,
    avatar_upload,
    direction: str,
    product_name: str,
    product_notes: str,
    placement: str,
    aspect: str,
    quality: str,
    creator_age,
):
    from film_lab.product import (
        ProductError,
        compose_product_still,
        product_prompt,
        resolve_avatar_still,
    )

    project = load_project(project_name)
    try:
        assert_ugc_adult(creator_age)
        products = _as_paths(product_file)
        if not products:
            raise ProductError("Upload a product still first.")
        uploads = _as_paths(avatar_upload)
        avatar, who = resolve_avatar_still(
            project,
            character_id=_product_avatar_id(bible_choice),
            upload=uploads[0] if uploads else None,
        )
        dest = compose_product_still(
            project,
            avatar,
            products[0],
            aspect=aspect,
            quality=quality,
            placement=placement,
            name=product_name or "product",
        )
    except (ProductError, UgcError) as exc:
        return None, None, gr.update(), "", toast_html(str(exc)), str(exc)
    prompt = product_prompt(
        product_name=product_name,
        notes=product_notes,
        direction=direction,
        avatar_name=who,
        placement=placement,
    )
    msg = (
        f"Still composed at {aspect} · {quality}. Local overlay — not a fake rewrite. "
        "Enhance or Animate. Then Mark & Direct the take."
    )
    return str(dest), str(dest), _product_start_update(project, dest.name), prompt, "", msg


def enhance_product_ui(
    project_name: str,
    direction: str,
    product_name: str,
    product_notes: str,
    bible_choice: str,
    placement: str,
    aspect: str,
    enhance_family: str,
    enhance_model: str,
):
    from film_lab.product import product_prompt

    project = load_project(project_name)
    cid = _product_avatar_id(bible_choice)
    who = "the adult"
    if cid:
        try:
            who = load_character(project, cid).name
        except (OSError, CharacterError, TypeError, ValueError):
            who = cid
    seed = product_prompt(
        product_name=product_name,
        notes=product_notes,
        direction=direction,
        avatar_name=who,
        placement=placement,
    )
    try:
        result = enhance_prompt(
            project,
            seed,
            provider=enhance_family,
            model_label=enhance_model,
            character_ids=[cid] if cid else [],
            aspect=aspect or "9:16",
            camera="OTS",
            lighting="phone light / practical room",
            intimacy="none (story)",
            content_intensity=0.0,
        )
    except EnhanceError as exc:
        return seed, seed, toast_html(str(exc)), str(exc)
    return result.paragraph or seed, result.paragraph or seed, "", "Enhanced. Animate next. Zero credits."


def generate_product_now(
    project_name: str,
    product_file,
    bible_choice: str,
    avatar_upload,
    direction: str,
    product_name: str,
    product_notes: str,
    placement: str,
    aspect: str,
    quality: str,
    creator_age,
    video_family: str,
    video_model: str,
):
    """Compose the product still, then Animate. Old takes stay on the board."""
    from film_lab.product import (
        ProductError,
        build_product_shot,
        compose_product_still,
        product_prompt,
        resolve_avatar_still,
    )

    project = load_project(project_name)
    try:
        assert_ugc_adult(creator_age)
        products = _as_paths(product_file)
        if not products:
            raise ProductError("Upload a product still first.")
        uploads = _as_paths(avatar_upload)
        avatar, who = resolve_avatar_still(
            project,
            character_id=_product_avatar_id(bible_choice),
            upload=uploads[0] if uploads else None,
        )
        dest = compose_product_still(
            project,
            avatar,
            products[0],
            aspect=aspect,
            quality=quality,
            placement=placement,
            name=product_name or "product",
        )
        prompt = product_prompt(
            product_name=product_name,
            notes=product_notes,
            direction=direction,
            avatar_name=who,
            placement=placement,
        )
        cid = _product_avatar_id(bible_choice)
        shot = build_product_shot(
            project,
            still_name=dest.name,
            prompt=prompt,
            aspect=aspect,
            quality=quality,
            character_ids=[cid] if cid else [],
            product_name=product_name or "Product",
        )
        if cid:
            _guard_shot_cast(project, shot)
    except (ProductError, UgcError, CharacterError, gr.Error) as exc:
        yield None, None, None, gr.update(), str(exc), toast_html(str(exc)), str(exc), [], []
        return

    still_s = str(dest)
    start_upd = _product_start_update(project, dest.name)
    route = resolve_video_pick(video_family, video_model)
    if not route.local_i2v:
        yield (
            still_s,
            still_s,
            None,
            start_upd,
            prompt,
            toast_html(route.message),
            route.message,
            take_gallery_items(project),
            take_gallery_items(project),
        )
        return

    from film_lab.generators.comfyui_i2v import clear_generation_hooks, set_generation_hooks

    _CANCEL.clear()
    latest = {"pct": 8, "done": None, "err": None}

    def on_progress(pct: int) -> None:
        latest["pct"] = pct

    def work() -> None:
        try:
            set_generation_hooks(progress=on_progress, cancel=_CANCEL.is_set)
            output, note = generate_motion_mp4(
                project,
                shot,
                generator_id=DEFAULT_GENERATOR_ID,
                uploaded=[dest],
                allow_fallback=False,
            )
            latest["done"] = (output, note)
        except Exception as exc:  # noqa: BLE001
            latest["err"] = exc
        finally:
            clear_generation_hooks()

    thread = threading.Thread(target=work, daemon=True)
    thread.start()
    yield (
        still_s,
        still_s,
        None,
        start_upd,
        prompt,
        "",
        "Animating product take on local SVD-XT. Adults 18+. Zero credits.",
        take_gallery_items(project),
        take_gallery_items(project),
    )
    while thread.is_alive():
        time.sleep(0.35)
        yield (
            still_s,
            still_s,
            gr.update(),
            start_upd,
            prompt,
            "",
            generating_label(int(latest["pct"])),
            take_gallery_items(project),
            take_gallery_items(project),
        )
    if latest["err"] is not None:
        msg = sanitize_motion_error(str(latest["err"]))
        yield still_s, still_s, None, start_upd, prompt, toast_html(msg), msg, take_gallery_items(project), take_gallery_items(project)
        return
    output, note = latest["done"]
    video = str(output) if output else None
    msg = (
        f"{note} Product take · {shot.aspect_ratio} · {shot.resolution}. "
        "Mark & Direct to Fix this frame, then Regenerate. Old take stays."
    )
    yield (
        still_s,
        still_s,
        gr.update(value=video, visible=True) if video else None,
        start_upd,
        prompt,
        "",
        msg,
        take_gallery_items(project),
        take_gallery_items(project),
    )


def apply_safe_mode_ui():
    """480p / 5s. Works offline. Does not need Comfy restart."""
    from film_lab.offline import WORKS_OFFLINE, set_safe_mode
    from film_lab.quality import quality_debug_md

    set_safe_mode(True)
    note = f"Safe mode on: 480p · 5s. {WORKS_OFFLINE}. Use REPAIR.bat to restart Comfy / Film Lab."
    return "480p", "480p", "480p", "5s", quality_debug_md(), note


def apply_motion_subject_ui(subject: str):
    """Person keeps bible lock. Product / poster stills skip face lock."""
    from film_lab.consistency import DEFAULT_FACE_LOCK
    from film_lab.motion_scope import is_object_still

    if is_object_still(subject):
        return (
            gr.update(value=[]),
            gr.update(value=[]),
            STORY_INTIMACY,
            IMPLIED_SOFT,
            0.0,
            0.0,
            (
                "Object / poster still. Face lock off. Pose is optional. "
                "Animate on Motion. Product + person ads: UGC Ads Desk. No marketplace."
            ),
        )
    return (
        gr.update(value=["alison", "bradley"]),
        gr.update(value=list(CHARACTER_TAGS)),
        "covered sheets",
        DEFAULT_PRESET,
        DEFAULT_INTENSITY,
        DEFAULT_FACE_LOCK,
        "Person still. Pose / face lock available. Intimate / explicit: adult 18+ only.",
    )


def push_product_beats_ui(
    project_name: str,
    beat1_file,
    beat2_file,
    beat1_prompt: str,
    beat2_prompt: str,
    product_name: str,
    aspect: str,
    quality: str,
    fallback_product,
    fallback_person,
    creator_age,
):
    """Two shots: can opens alone → pick up and pour. Animate each on Motion."""
    from film_lab.motion_scope import MotionScopeError, build_product_beats
    from film_lab.ugc import UgcError, assert_ugc_adult

    project = load_project(project_name)
    try:
        assert_ugc_adult(creator_age)
        first = _as_paths(beat1_file) or _as_paths(fallback_product)
        second = _as_paths(beat2_file) or _as_paths(fallback_person) or first
        names: list[str] = []
        for src in (first[:1] if first else [], second[:1] if second else []):
            if not src:
                names.append("")
                continue
            written = project.ingest_files(src)
            names.append(written[-1].name if written else src[0].name)
        if not any(names):
            raise MotionScopeError(
                "Drop a product still for beat 1 (can / bottle / poster). "
                "Beat 2 can reuse it or use the product+person composite."
            )
        shots = build_product_beats(
            project,
            stills=names,
            prompts=[beat1_prompt, beat2_prompt],
            product_name=product_name or "Product",
            aspect=aspect,
            quality=quality,
        )
    except (MotionScopeError, UgcError) as exc:
        return (
            shot_dropdown(project),
            shot_dropdown(project),
            gr.update(),
            open_hub_tab("ugc"),
            toast_html(str(exc)),
            str(exc),
        )
    start = names[0] if names and names[0] else None
    msg = (
        f"Two beats on Motion: **{shots[0].name}** then **{shots[1].name}**. "
        "Animate each (any still → img2vid). Then Cinema stitch, "
        "or Mark & Direct the first take and Regenerate the pour. No marketplace."
    )
    return (
        shot_dropdown(project, shots[0].id),
        shot_dropdown(project, shots[0].id),
        _product_start_update(project, start or ""),
        open_hub_tab("motion"),
        "",
        msg,
    )


def open_product_direct_ui(project_name: str, video_path):
    """Land the product take on Take Board Playback. Mark & Direct is Fix this frame."""
    project = load_project(project_name)
    raw = video_path
    if isinstance(raw, dict):
        raw = raw.get("path") or raw.get("name") or ""
    path = str(raw or "")
    if not path or not Path(path).is_file():
        msg = "Animate a product take first, then Mark & Direct."
        return open_hub_tab("ugc"), None, toast_html(msg), msg
    return (
        open_hub_tab("takes"),
        path,
        "",
        "Product take on Take Board. Playback first. Mark & Direct · Fix this frame.",
    )


def ingest_stills(project_name: str, files, quality=None, aspect=None):
    from film_lab.constants import normalize_aspect
    from film_lab.quality import native_quality, normalize_quality, resize_still

    project = load_project(project_name)
    chosen = normalize_quality(quality or getattr(project, "quality", None))
    ratio = normalize_aspect(aspect or getattr(project, "aspect", None))
    project.set_quality(chosen)
    project.set_aspect(ratio)
    written = project.ingest_files(_as_paths(files))
    sized: list[Path] = []
    for path in written:
        dest = path.with_name(f"{path.stem}_{native_quality(chosen)}{path.suffix}")
        try:
            resize_still(path, dest, chosen, ratio)
            sized.append(dest)
        except OSError:
            sized.append(path)
    msg = (
        f"Ingested {len(written)} still(s) at {native_quality(chosen)} · {ratio} "
        f"(4K stills ingest at 720p; upscale on export) into `{project.name}`/stills/."
        if written
        else "No images ingested. Use png / jpg / webp / tiff."
    )
    stills = [str(p) for p in project.list_stills()]
    start, end = still_dropdowns(project)
    return stills, start, end, msg


def import_examples(project_name: str):
    project = load_project(project_name)
    msg = import_studio_bundle(project)
    return (
        shot_dropdown(project),
        scene_dropdown(project),
        char_dropdown(project),
        scene_dropdown(project),
        draft_dropdown(project),
        msg,
    )


def _guard_shot_cast(project: Project, shot: ShotCard) -> None:
    from film_lab.filming import FilmingError, assert_filming_safe

    profiles = matching_characters(project, shot)
    if not profiles and shot.character_ids:
        profiles = load_selected_characters(project, shot.character_ids)
    try:
        assert_filming_safe(
            getattr(project, "filming_mode", None),
            profiles,
            intimacy=shot.intimacy_mode,
            intensity=shot.content_intensity,
            context="generating or saving this shot",
        )
        assert_adult_cast(
            profiles,
            intimacy_mode=shot.intimacy_mode,
            content_intensity=shot.content_intensity,
            context="generating or saving this shot",
        )
    except (CharacterError, FilmingError) as exc:
        raise gr.Error(str(exc)) from exc


def _stamp_quality(shot, project, *, keep_existing: bool = False) -> None:
    from film_lab.quality import normalize_quality

    if keep_existing:
        existing = getattr(shot, "resolution", None)
        sid = getattr(shot, "id", None)
        if sid:
            try:
                existing = project.load_shot(sid).resolution or existing
            except (FileNotFoundError, OSError, ValueError):
                pass
        if existing:
            shot.resolution = normalize_quality(existing)
            return
    shot.resolution = normalize_quality(
        getattr(project, "quality", None) or getattr(shot, "resolution", None)
    )


def _quality_ui(project=None, quality: str | None = None):
    from film_lab.quality import quality_debug_md, normalize_quality

    q = normalize_quality(quality or (getattr(project, "quality", None) if project else None))
    return q, q, q, quality_debug_md()


def _aspect_ui(project=None, aspect: str | None = None):
    from film_lab.constants import DEFAULT_ASPECT, normalize_aspect

    ratio = normalize_aspect(
        aspect or (getattr(project, "aspect", None) if project else None) or DEFAULT_ASPECT
    )
    return ratio, ratio


def apply_aspect_ui(project_name: str, aspect: str):
    from film_lab.constants import normalize_aspect

    project = load_project(project_name)
    ratio = normalize_aspect(aspect)
    project.set_aspect(ratio)
    note = (
        f"Aspect **{ratio}**. Shot card stores it. "
        "Regenerate keeps this take unless you change the picker. Experiment freely."
    )
    return ratio, ratio, ratio, note


def apply_quality_ui(project_name: str, quality: str):
    from film_lab.quality import native_quality, normalize_quality, quality_debug_md

    q = normalize_quality(quality)
    project = load_project(project_name)
    project.set_quality(q)
    native = native_quality(q)
    if q == "4K":
        note = (
            f"Quality → **4K** (export). Native generate stays **{native}** on the RX 5600 XT. "
            "Never a native SVD 4K pass."
        )
    else:
        note = (
            f"Quality → **{q}**. Native generate {native}. "
            "RX 5600 XT: prefer 480p / 720p; 1080p if VRAM allows."
        )
    return q, q, q, quality_debug_md(), note


def _export_scaled(project, src: Path, quality: str | None, aspect: str = "16:9") -> Path:
    from film_lab.quality import normalize_quality, scale_media

    q = normalize_quality(quality or getattr(project, "quality", None))
    project.set_quality(q)
    if not src or not Path(src).is_file():
        return src
    src = Path(src)
    dest = project.outputs_dir / f"{src.stem}_{q}{src.suffix or '.mp4'}"
    if dest.resolve() == src.resolve():
        dest = project.outputs_dir / f"{src.stem}_export_{q}{src.suffix or '.mp4'}"
    try:
        scaled = scale_media(src, dest, q, aspect or "16:9")
        project.register_output(scaled, generator=f"export-{q}")
        return scaled
    except (OSError, ValueError):
        return src


def save_shot_ui(project_name: str, *form):
    project = load_project(project_name)
    shot = card_from_form(*form)
    _stamp_quality(shot, project, keep_existing=False)
    _guard_shot_cast(project, shot)
    project.save_shot(shot)
    if shot.scene_id:
        try:
            link_shot(project, shot.scene_id, shot.id)
        except FileNotFoundError:
            pass
    return (
        shot.id,
        shot_dropdown(project, shot.id),
        compose_local_prompt(shot, project),
        f"Saved shot `{shot.id}` — {shot.name}.",
    )


def new_shot_ui():
    shot = ShotCard(
        name="New shot",
        character_tags=list(CHARACTER_TAGS),
        character_ids=["alison", "bradley"],
        body_motion_notes="breathing",
    )
    return (*form_from_card(shot), "New blank shot. Assign a start still before generating.")


def load_shot_ui(project_name: str, choice: str):
    if not choice:
        raise gr.Error("Pick a saved shot first.")
    project = load_project(project_name)
    shot = project.load_shot(_id_from_choice(choice))
    values = list(form_from_card(shot, project))
    values[2] = gr.Dropdown(choices=project.still_choices(), value=shot.start_frame)
    values[3] = gr.Dropdown(choices=[""] + project.still_choices(), value=shot.end_frame or "")
    values[19] = scene_dropdown(project, shot.scene_id)
    project.set_quality(shot.resolution)
    project.set_aspect(shot.aspect_ratio)
    q, q2, q3, help_md = _quality_ui(project, shot.resolution)
    a1, a2 = _aspect_ui(project, shot.aspect_ratio)
    return (
        *values,
        q,
        q2,
        q3,
        help_md,
        a1,
        a2,
        f"Loaded `{shot.id}` — {shot.name}. Quality {shot.resolution} · {shot.aspect_ratio}.",
    )


def consistency_gallery(project_name: str, tags, character_ids):
    project = load_project(project_name)
    shot = ShotCard(
        character_tags=list(tags or []),
        character_ids=[_id_from_choice(x) if " — " in str(x) else str(x) for x in (character_ids or [])],
    )
    paths = [str(p) for p in refs_for_shot(project, shot)]
    note = (
        f"{len(paths)} pinned ref(s). Pin 3–10 per character on the Characters tab."
        if paths
        else "No consistency stills pinned for the selected characters yet."
    )
    return paths, note


_CANCEL = threading.Event()


def request_cancel():
    from film_lab.generators.comfyui_i2v import interrupt_comfy

    _CANCEL.set()
    return interrupt_comfy(), generating_label(0)


def generate_amd_now(
    project_name: str,
    video_family,
    video_model,
    image_family,
    image_model,
    duration_preset,
    quality,
    *form,
):
    if quality:
        load_project(project_name).set_quality(quality)
    route = resolve_video_pick(video_family, video_model)
    if not route.local_i2v:
        yield _image_fail_pack(project_name, form, route.message)
        return
    image = resolve_image_pick(image_family, image_model)
    if not image.local_i2v:
        yield _image_fail_pack(project_name, form, image.message)
        return
    yield from generate_now(
        project_name,
        DEFAULT_GENERATOR_ID,
        *_form_with_duration(form, duration_preset),
        mode="animate",
    )


def generate_quick_now(
    project_name: str,
    video_family,
    video_model,
    image_family,
    image_model,
    duration_preset,
    quality,
    *form,
):
    del duration_preset
    if quality:
        load_project(project_name).set_quality(quality)
    route = resolve_video_pick(video_family, video_model)
    if not route.local_i2v:
        yield _image_fail_pack(project_name, form, route.message)
        return
    image = resolve_image_pick(image_family, image_model)
    if not image.local_i2v:
        yield _image_fail_pack(project_name, form, image.message)
        return
    yield from generate_now(project_name, DEFAULT_GENERATOR_ID, *form, mode="quick")


def generate_fallback_now(
    project_name: str,
    video_family,
    video_model,
    image_family,
    image_model,
    duration_preset,
    quality,
    *form,
):
    if quality:
        load_project(project_name).set_quality(quality)
    route = resolve_video_pick(video_family, video_model)
    if not route.local_i2v:
        yield _image_fail_pack(project_name, form, route.message)
        return
    image = resolve_image_pick(image_family, image_model)
    if not image.local_i2v:
        yield _image_fail_pack(project_name, form, image.message)
        return
    yield from generate_now(
        project_name,
        FALLBACK_GENERATOR_ID,
        *_form_with_duration(form, duration_preset),
        mode="animate",
    )


def _form_with_duration(form, duration_preset):
    pick = parse_duration_preset(duration_preset)
    values = list(form)
    if not pick.is_long and len(values) >= 25:
        values[4] = float(pick.seconds)
    return values


def _new_regen_seed() -> int:
    return random.randint(1, 2_147_483_647)


def _image_fail_pack(project_name, form, message: str):
    project = load_project(project_name)
    values, _, history, attached = _split_motion_args(form)
    shot = card_from_form(*values) if len(values) >= 25 else ShotCard()
    return _motion_pack(
        project,
        shot,
        overlay=False,
        toast=toast_html(message),
        status=message,
        feed_history=history,
        ref_chip=ref_chip_html(attached),
    )


def _split_motion_args(form) -> tuple[list, list[Path], list, str]:
    """form_fields (25) + still + optional feed history + optional attached ref."""
    values = list(form)
    attached = ""
    history: list = []
    if len(values) >= 28:
        attached = str(values[-1] or "")
        raw_hist = values[-2]
        history = list(raw_hist) if isinstance(raw_hist, list) else []
        uploaded = _as_paths(values[-3])
        values = values[:25]
    elif len(values) >= 27:
        raw_hist = values[-1]
        history = list(raw_hist) if isinstance(raw_hist, list) else []
        uploaded = _as_paths(values[-2])
        values = values[:25]
    elif len(values) > 25:
        uploaded = _as_paths(values[25])
        values = values[:25]
    else:
        uploaded = []
    return values, uploaded, history, attached


def generate_now(
    project_name: str,
    generator_id: str,
    *form,
    mode: str = "animate",
    keep_quality: bool = False,
):
    from film_lab.generators.comfyui_i2v import clear_generation_hooks, set_generation_hooks

    project = load_project(project_name)
    values, uploaded, feed_history, attached = _split_motion_args(form)
    shot = card_from_form(*values)
    _stamp_quality(shot, project, keep_existing=keep_quality)
    project.set_aspect(shot.aspect_ratio)
    notes = load_notes(project)
    try:
        assert_notes_safe(
            project,
            notes,
            intimacy=shot.intimacy_mode,
            intensity=shot.content_intensity,
            context="Animate",
        )
    except DirectorNoteError as exc:
        pack = _motion_pack(
            project,
            shot,
            overlay=False,
            toast=toast_html(str(exc)),
            status=sanitize_motion_error(str(exc)),
            feed_history=feed_history,
            ref_chip=ref_chip_html(attached),
        )
        yield pack
        return
    shot.director_intent = fold_desk(project, shot.director_intent)
    if mode == "quick":
        shot.duration = QUICK_DURATION
        shot.subject_motion_strength = QUICK_STRENGTH
        if not (shot.director_intent or "").strip():
            shot.director_intent = QUICK_PROMPT
    try:
        _guard_shot_cast(project, shot)
    except gr.Error as exc:
        pack = _motion_pack(
            project,
            shot,
            overlay=False,
            toast=toast_html(str(exc)),
            status=sanitize_motion_error(str(exc)),
            feed_history=feed_history,
            ref_chip=ref_chip_html(attached),
        )
        yield pack
        return

    _CANCEL.clear()
    latest = {"pct": 8, "done": None, "err": None}

    def on_progress(pct: int) -> None:
        latest["pct"] = pct

    def work() -> None:
        try:
            set_generation_hooks(progress=on_progress, cancel=_CANCEL.is_set)
            output, note = generate_motion_mp4(
                project,
                shot,
                generator_id=generator_id,
                uploaded=uploaded,
                allow_fallback=generator_id == FALLBACK_GENERATOR_ID,
            )
            latest["done"] = (output, note)
        except Exception as exc:  # noqa: BLE001
            latest["err"] = exc
        finally:
            clear_generation_hooks()

    thread = threading.Thread(target=work, daemon=True)
    thread.start()
    yield _motion_pack(
        project,
        shot,
        overlay=True,
        percent=8,
        status="Animating on local SVD-XT. Adults 18+ allowed. No Film Lab NSFW filter.",
        feed_history=feed_history,
        generating=True,
        ref_chip=ref_chip_html(attached),
    )
    while thread.is_alive():
        time.sleep(0.35)
        yield _motion_pack(
            project,
            shot,
            overlay=True,
            percent=int(latest["pct"]),
            status="Generating… local ComfyUI. Cancel anytime.",
            feed_history=feed_history,
            generating=True,
            ref_chip=ref_chip_html(attached),
        )
    if latest["err"] is not None:
        err = latest["err"]
        msg = sanitize_motion_error(str(err))
        from film_lab.quality import oom_hint

        low = msg.lower()
        if any(
            token in low
            for token in (
                "oom",
                "out of memory",
                "memory",
                "alloc",
                "crash",
                "killed",
                "abort",
                "fail",
                "died",
                "dead",
            )
        ):
            msg = f"{msg}\n\n{oom_hint(shot.resolution)}"
        yield _motion_pack(
            project,
            shot,
            overlay=False,
            toast=toast_html(msg),
            status=msg,
            feed_history=feed_history,
            ref_chip=ref_chip_html(attached),
        )
        return
    output, note = latest["done"]
    download = output
    try:
        from film_lab.quality import is_4k

        if is_4k(shot.resolution) and output and Path(output).is_file():
            download = _export_scaled(project, Path(output), shot.resolution, shot.aspect_ratio)
    except (OSError, ValueError):
        download = output
    if shot.scene_id:
        try:
            link_shot(project, shot.scene_id, shot.id)
        except FileNotFoundError:
            pass
    yield _motion_pack(
        project,
        shot,
        overlay=False,
        video=output,
        download=download,
        status=(
            f"{note} {shot.duration:.1f}s · {shot.aspect_ratio} · {shot.resolution} · "
            f"{shot.camera_move} · {shot.intimacy_mode}. Zero credits."
        ),
        feed_history=feed_history,
        generating=False,
        ref_chip=ref_chip_html(attached),
    )


def _motion_pack(
    project,
    shot,
    *,
    overlay: bool,
    percent: int = 0,
    toast: str = "",
    video: Path | None = None,
    download: Path | None = None,
    status: str = "",
    feed_history=None,
    generating: bool = False,
    intent=None,
    enhance_before=None,
    ref_chip=None,
):
    gallery = gallery_choices(project)
    label = None
    video_s = str(video) if video else None
    download_s = str(download) if download else video_s
    if video_s:
        label = next((g for g in gallery if str(Path(video_s).resolve()) in g), None)
    start = gr.Dropdown(choices=project.still_choices(), value=shot.start_frame)
    if video_s:
        video_out = gr.update(value=video_s, visible=True)
        file_out = download_s
    elif overlay:
        video_out = gr.update(visible=True)
        file_out = gr.update()
    else:
        video_out = gr.update()
        file_out = gr.update()
    history = list(feed_history or [])
    return (
        shot.id,
        video_out,
        shot_dropdown(project, shot.id),
        gr.CheckboxGroup(choices=gallery, value=[label] if label else []),
        file_out,
        status,
        compose_local_prompt(shot, project),
        _reel_table(project),
        start,
        gr.update(visible=overlay),
        generating_label(percent) if overlay else generating_label(0),
        toast,
        render_feed(history, generating=generating),
        history,
        shot.director_intent if intent is None else intent,
        enhance_before if enhance_before is not None else gr.update(),
        ref_chip if ref_chip is not None else gr.update(),
        shot.seed,
        shot_dropdown(project, shot.id),
        take_gallery_items(project),
        take_gallery_items(project),
    )


def apply_pose_ui(
    project_name: str,
    still,
    body: str,
    hands: str,
    face: str,
    micro: str = "",
    behavior: str = "",
):
    """Still-first OpenPose-style guide. Face pixels stay. Then Enhance → Animate."""
    project = load_project(project_name)
    paths = _as_paths(still)
    empty_start, _end = still_dropdowns(project)
    if not paths:
        msg = "Drop a still first, then Apply pose."
        return (
            "",
            None,
            pose_markdown(),
            None,
            "",
            ref_chip_html(""),
            toast_html(msg),
            msg,
            empty_start,
        )
    try:
        result = apply_pose_for_project(
            project,
            paths[0],
            body=body,
            hands=hands,
            face=face,
            micro=micro,
            behavior=behavior,
        )
    except PoseError as exc:
        return (
            "",
            None,
            pose_markdown(),
            None,
            "",
            ref_chip_html(""),
            toast_html(str(exc)),
            str(exc),
            empty_start,
        )
    start, _end = still_dropdowns(project)
    posed = str(result.path)
    return (
        posed,
        posed,
        f"{result.message}\n\n{pose_markdown()}",
        posed,
        posed,
        ref_chip_html(posed),
        "",
        result.message,
        start,
    )


def apply_mark_ui(
    project_name: str,
    still,
    clip,
    editor,
    shape: str,
    cx,
    cy,
    size,
    target: str,
    note: str,
    prop_action: str,
    idea: str,
    intimacy: str,
    intensity,
):
    from film_lab.director_notes import fold_into_seed, load_notes
    from film_lab.mark import (
        MarkError,
        apply_region,
        assert_marks_safe,
        load_marks,
        marks_markdown,
    )
    from film_lab.setdesk import load_set_note

    project = load_project(project_name)
    paths = _as_paths(still) + _as_paths(clip)
    if not paths:
        msg = "Drop a still or a short clip, then Apply mark."
        md = marks_markdown(load_marks(project))
        return (
            None,
            None,
            None,
            None,
            idea or "",
            md,
            md,
            md,
            toast_html(msg),
            msg,
        )
    source = paths[0]
    resolved_note = merge_prop_note(note, prop_action)
    resolved_target = target
    if (prop_action or "").strip() and (prop_action or "").strip().lower() != "none":
        if not resolved_target or resolved_target in {"clothing", "prop"}:
            resolved_target = "prop action"
    try:
        assert_marks_safe(
            project,
            load_marks(project),
            intimacy=intimacy or "",
            intensity=intensity or 0,
            extra_note=resolved_note,
            context="Mark & Direct",
        )
        dest, marks, region = apply_region(
            project,
            source,
            shape=shape,
            target=resolved_target,
            note=resolved_note,
            cx=cx,
            cy=cy,
            size=size,
            editor=editor,
        )
        assert_marks_safe(
            project,
            marks,
            intimacy=intimacy or "",
            intensity=intensity or 0,
            extra_note=resolved_note,
            context="Mark & Direct",
        )
    except MarkError as exc:
        md = marks_markdown(load_marks(project))
        return (
            None,
            None,
            None,
            None,
            idea or "",
            md,
            md,
            md,
            toast_html(str(exc)),
            str(exc),
        )
    folded = fold_desk(project, idea or "")
    md = marks_markdown(marks)
    extra = _maybe_enter_dream_from_mark(
        project,
        source,
        resolved_target,
        resolved_note,
        intimacy=intimacy or "",
        intensity=intensity or 0,
        cx=cx,
        cy=cy,
    )
    msg = (
        f"Mark & Direct applied: {region.shape} on {region.target}. "
        "Stacked. Enhance → Pose → Animate / Regenerate so motion follows."
        f"{extra}"
    )
    marked = str(dest)
    return marked, marked, marked, marked, folded, md, md, md, "", msg


def mark_shape_ui(shape: str):
    from film_lab.mark import SHAPE_LASSO, SHAPE_POINTER, normalize_shape

    kind = normalize_shape(shape)
    pointer = kind == SHAPE_POINTER
    lasso = kind == SHAPE_LASSO
    return (
        gr.update(visible=lasso and not pointer),
        gr.update(visible=not lasso and not pointer),
        gr.update(visible=pointer),
    )


def pointer_go_to_ui(project_name, actor_choice, dest_choice, filming_mode):
    from film_lab.pointer import PointerError, generate_go_to
    from film_lab.variations import take_gallery_items

    project = load_project(project_name)
    try:
        take = generate_go_to(
            project,
            actor_choice,
            dest_choice,
            filming_mode=filming_mode or "",
        )
    except PointerError as exc:
        raise gr.Error(str(exc)) from exc
    items = take_gallery_items(project)
    msg = (
        f"Pointer / Go-to: {take.actor_name} → {take.destination}. "
        f"Take `{take.take.name}` recorded on Take Board. "
        "Playback first. Offline. Zero credits."
    )
    return (
        str(take.take),
        items,
        items,
        open_hub_tab("takes"),
        msg,
    )


def use_posed_still_ui(posed_path: str):
    """Land the posed still on Motion Desk. Face lock stays. Animate next."""
    path = (posed_path or "").strip()
    if not path or not Path(path).is_file():
        msg = "Apply pose first, then use the posed still on Motion Desk."
        return (
            open_hub_tab("pose"),
            None,
            "",
            ref_chip_html(""),
            toast_html(msg),
            msg,
        )
    name = Path(path).name
    msg = (
        f"{name} is the Motion reference. Face lock stays. "
        "Enhance, then Animate (SVD-XT). Not video puppeting. Regenerate stays on."
    )
    return (
        open_hub_tab("motion"),
        path,
        path,
        ref_chip_html(path),
        "",
        msg,
    )


def open_director_note_ui(project_name: str, evt: gr.SelectData):
    """Click a bible face → Director Note popup (performance)."""
    project = load_project(project_name)
    faces = list_cast_faces(project)
    if not faces:
        return (
            gr.update(visible=False),
            "",
            "### Director Note",
            DEFAULT_EMOTION,
            "",
            DEFAULT_WARDROBE,
            DEFAULT_MICRO,
            DEFAULT_BEHAVIOR,
            "No Character Bible faces yet. Add Alison / Bradley or a new adult.",
        )
    idx = getattr(evt, "index", 0)
    if isinstance(idx, (list, tuple)):
        idx = idx[0] if idx else 0
    try:
        idx = int(idx or 0)
    except (TypeError, ValueError):
        idx = 0
    face = faces[max(0, min(idx, len(faces) - 1))]
    notes = load_notes(project)
    existing = notes.director.get(face.id)
    micro, behavior = _note_perf_defaults(project, face.id, existing)
    return (
        gr.update(visible=True),
        face.id,
        f"### Director Note — {face.name}\nPerformance: emotion, micro-expression, full human behavior, wardrobe.",
        existing.emotion if existing else DEFAULT_EMOTION,
        existing.acting_beats if existing else "",
        existing.wardrobe_motion if existing else DEFAULT_WARDROBE,
        micro,
        behavior,
        f"{face.caption}. {SAFETY_LINE}",
    )


def _note_perf_defaults(project, character_id: str, existing) -> tuple[str, str]:
    if existing is not None:
        return (
            getattr(existing, "micro_expression", None) or DEFAULT_MICRO,
            getattr(existing, "behavior", None) or DEFAULT_BEHAVIOR,
        )
    try:
        profile = load_character(project, character_id)
    except (CharacterError, OSError, ValueError, FileNotFoundError):
        return DEFAULT_MICRO, DEFAULT_BEHAVIOR
    micro = (profile.micro_expression or "").strip() or DEFAULT_MICRO
    behavior = (profile.behavior or "").strip() or DEFAULT_BEHAVIOR
    return micro, behavior


def close_director_note_ui():
    return gr.update(visible=False)


def transcribe_into_note_ui(audio, current: str):
    """Mic → same note box as typed text. Apply / Regenerate unchanged."""
    existing = current or ""
    if not audio:
        return existing, "", ""
    try:
        spoken = transcribe(audio)
    except VoiceNoteError as exc:
        return existing, toast_html(str(exc)), str(exc)
    merged = merge_note(existing, spoken)
    msg = (
        "Voice added to the same note. Edit if you want, then Apply / Regenerate. "
        "Typed and spoken both count."
    )
    return merged, "", msg


def apply_director_note_ui(
    project_name: str,
    char_id: str,
    char_title: str,
    emotion: str,
    beats: str,
    wardrobe_motion: str,
    micro_expression: str,
    behavior: str,
    idea: str,
    intimacy: str,
    intensity,
):
    project = load_project(project_name)
    notes = load_notes(project)
    name = (char_title or "").replace("### Director Note — ", "").split("\n", 1)[0].strip()
    if not name:
        face = next((f for f in list_cast_faces(project) if f.id == (char_id or "").strip()), None)
        name = face.name if face else (char_id or "").strip()
    try:
        upsert_director_note(
            notes,
            character_id=char_id,
            character_name=name,
            emotion=emotion,
            acting_beats=beats,
            wardrobe_motion=wardrobe_motion,
            micro_expression=micro_expression,
            behavior=behavior,
        )
        assert_notes_safe(
            project,
            notes,
            intimacy=intimacy or "",
            intensity=intensity or 0,
            context="Director Note → Enhance → Pose → Animate",
        )
    except DirectorNoteError as exc:
        md = notes_markdown(notes)
        return (
            gr.update(visible=True),
            idea or "",
            md,
            md,
            toast_html(str(exc)),
            str(exc),
        )
    save_notes(project, notes)
    folded = fold_desk(project, idea or "")
    md = notes_markdown(notes)
    msg = (
        f"Director Note applied for {name}. Folded into Enhance → Pose → Animate. "
        f"{SAFETY_LINE}"
    )
    return gr.update(visible=False), folded, md, md, "", msg


def apply_world_note_ui(
    project_name: str,
    weather: str,
    thunder: str,
    earth: str,
    wind: str,
    setting: str,
    placement: str,
    outdoor: str,
    prop_action: str,
    idea: str,
    intimacy: str,
    intensity,
):
    project = load_project(project_name)
    notes = load_notes(project)
    set_world_note(
        notes,
        weather=weather,
        thunder=thunder,
        earth=earth,
        wind=wind,
        setting=setting,
        placement=placement,
        outdoor=outdoor,
        prop_action=prop_action,
    )
    try:
        assert_notes_safe(
            project,
            notes,
            intimacy=intimacy or "",
            intensity=intensity or 0,
            context="World Note → Enhance → Pose → Animate",
        )
    except DirectorNoteError as exc:
        md = notes_markdown(notes)
        return idea or "", md, md, toast_html(str(exc)), str(exc)
    save_notes(project, notes)
    folded = fold_desk(project, idea or "")
    md = notes_markdown(notes)
    msg = (
        "World Note applied (mise-en-scène / environment). "
        "Environment lock stays on the shot. "
        f"Folded into Enhance → Pose → Animate. {SAFETY_LINE}"
    )
    return folded, md, md, "", msg


def apply_env_lock_ui(
    project_name: str,
    still,
    style,
    geometry: str,
    strength,
    note: str,
    idea: str,
):
    from film_lab.consistency import probe_env_lock
    from film_lab.envlock import (
        apply_env_lock,
        env_gallery_items,
        env_markdown,
        resolve_env_still,
    )

    project = load_project(project_name)
    stills = _as_paths(still)
    styles = _as_paths(style)
    try:
        lock = apply_env_lock(
            project,
            still=stills[0] if stills else None,
            style_ref=styles[0] if styles else None,
            geometry=geometry,
            strength=float(strength or 0.45),
            note=note or "",
        )
    except ValueError as exc:
        raise gr.Error(str(exc)) from exc
    folded = fold_desk(project, idea or "")
    md = env_markdown(lock)
    items = env_gallery_items(project, lock)
    state, probe = probe_env_lock()
    resolved = resolve_env_still(project, lock)
    locked_path = str(resolved) if resolved else None
    start = gr.Dropdown(choices=project.still_choices(), value=lock.still or None)
    msg = (
        f"Environment lock applied. Sidecar **{state}**. {probe} "
        "World Note + 3D Set reuse this plate. Regenerate keeps the World lock. Zero credits."
    )
    return folded, md, md, md, items, items, items, locked_path, start, "", msg


def family_sheet_ui(project_name: str):
    project = load_project(project_name)
    items: list[tuple[str, str]] = []
    active = set(project.active_cast or ["alison", "bradley"])
    for profile in list_characters(project):
        if profile.id not in active:
            continue
        role = getattr(profile, "role", "Adult") or "Adult"
        for path in resolve_refs(project, profile):
            items.append((str(path), f"{profile.name} · {role}"))
    note = (
        f"Character sheet: {len(items)} ref(s) for active cast "
        f"({', '.join(sorted(active))}). Pin 3–10 per person. "
        "InstantID / FaceID stay stubs until Comfy lists those nodes."
        if items
        else "No character sheet refs yet. Pin stills on each bible entry (Alison, Bradley, family roles)."
    )
    return items, note


def apply_face_method_ui(project_name: str, method: str, strength):
    from film_lab.consistency import normalize_face_method, probe_face_lock

    project = load_project(project_name)
    resolved = normalize_face_method(method)
    project.set_cast(list(project.active_cast or []), face_lock_strength=strength)
    state, msg = probe_face_lock()
    for profile in list_characters(project):
        if profile.id in set(project.active_cast or ["alison", "bradley"]):
            write_consistency_hook(project, profile, method=resolved)
    honest = (
        f"Face method **{resolved}**. Sidecar **{state}**. {msg} "
        "Primary on the RX 5600 XT is start-still img2vid until InstantID / FaceID nodes exist. "
        "OOM → drop Quality. Zero credits."
    )
    return resolved, float(project.face_lock_strength), honest


def add_prompt_ui(image):
    """Attach the center still as the composer / feed reference."""
    paths = _as_paths(image)
    if not paths:
        return (
            "",
            ref_chip_html(""),
            toast_html("Drop a still first, then Add Prompt."),
            "No still to attach.",
        )
    path = paths[0]
    return (
        str(path),
        ref_chip_html(str(path)),
        "",
        f"Attached {path.name} as prompt ref. Type a short command, then Send.",
    )


def imagine_send(
    project_name: str,
    idea: str,
    enhance_family: str,
    enhance_model: str,
    video_family: str,
    video_model: str,
    image_family: str,
    image_model: str,
    duration_preset: str,
    quality: str,
    attached_ref: str,
    feed_history,
    *form,
):
    """Primary Motion Desk path: short command → visible enhance → SVD-XT clip."""
    project = load_project(project_name)
    if quality:
        project.set_quality(quality)
    text_route = resolve_text_pick(enhance_family, enhance_model)
    provider = text_route.backend
    if not text_route.wired:
        values = list(form)
        if len(values) > 25:
            values = values[:25]
        shot = card_from_form(*values) if len(values) >= 25 else ShotCard()
        history = [t for t in (feed_history or []) if isinstance(t, dict)]
        yield _with_extend_tail(
            _motion_pack(
                project,
                shot,
                overlay=False,
                toast=toast_html(text_route.message),
                status=text_route.message,
                feed_history=history,
                ref_chip=ref_chip_html(attached_ref),
            ),
            project,
            duration_preset,
        )
        return
    image_route = resolve_video_pick(video_family, video_model)
    values = list(form)
    uploaded: list[Path] = []
    if len(values) > 25:
        uploaded = _as_paths(values[25])
        values = values[:25]
    shot = card_from_form(*values)
    _stamp_quality(shot, project, keep_existing=False)
    ref_path = (attached_ref or "").strip()
    if not ref_path and uploaded:
        ref_path = str(uploaded[0])
    ref_name = Path(ref_path).name if ref_path else ""
    history = [t for t in (feed_history or []) if isinstance(t, dict)]
    seed = (idea or "").strip()
    if not seed:
        yield _with_extend_tail(
            _motion_pack(
                project,
                shot,
                overlay=False,
                toast=toast_html("Type a short command in the composer, then Send."),
                status="Short command required.",
                feed_history=history,
                ref_chip=ref_chip_html(ref_path),
            ),
            project,
            duration_preset,
        )
        return

    try:
        result = enhance_prompt(
            project,
            seed,
            provider=provider,
            model_label=enhance_model,
            character_ids=list(shot.character_ids or []),
            aspect=shot.aspect_ratio or "16:9",
            camera=shot.camera_move or "slow push-in",
            lighting=shot.lighting or "",
            intimacy=shot.intimacy_mode or "covered sheets",
            content_intensity=shot.content_intensity,
        )
    except EnhanceError as exc:
        yield _with_extend_tail(
            _motion_pack(
                project,
                shot,
                overlay=False,
                toast=toast_html(str(exc)),
                status=sanitize_motion_error(str(exc)),
                feed_history=history,
                ref_chip=ref_chip_html(ref_path),
            ),
            project,
            duration_preset,
        )
        return

    paragraph = (result.paragraph or result.prompt).strip()
    history = append_turn(
        history,
        user_text=seed,
        paragraph=paragraph,
        ref_name=ref_name,
    )
    shot.director_intent = result.prompt
    if not (shot.negative_prompt or "").strip():
        shot.negative_prompt = result.negative
    values[16] = result.prompt
    if len(values) > 14 and not (values[14] or "").strip():
        values[14] = result.negative
    pick = parse_duration_preset(duration_preset)
    if not pick.is_long:
        values[4] = float(pick.seconds)
        shot.duration = float(pick.seconds)

    yield _with_extend_tail(
        _motion_pack(
            project,
            shot,
            overlay=True,
            percent=0,
            status="Prompt Enhancement is in the feed. Starting local SVD-XT…",
            feed_history=history,
            generating=True,
            intent=result.prompt,
            enhance_before=result.seed,
            ref_chip=ref_chip_html(ref_path),
        ),
        project,
        duration_preset,
    )
    if not image_route.local_i2v:
        yield _with_extend_tail(
            _motion_pack(
                project,
                shot,
                overlay=False,
                toast=toast_html(image_route.message),
                status=image_route.message,
                feed_history=history,
                intent=result.prompt,
                enhance_before=result.seed,
                ref_chip=ref_chip_html(ref_path),
            ),
            project,
            duration_preset,
        )
        return
    still = form[25] if len(form) > 25 else (ref_path or None)
    if pick.is_long:
        yield from _auto_long_reel(
            project_name,
            idea,
            result.prompt,
            duration_preset,
            history,
            ref_path,
            values,
            still,
            paragraph=paragraph,
        )
        return
    for pack in generate_now(
        project_name,
        DEFAULT_GENERATOR_ID,
        *values,
        still,
        history,
        ref_path,
        mode="animate",
    ):
        yield _with_extend_tail(pack, project, duration_preset)


def _with_extend_tail(pack, project, duration_preset):
    pick = parse_duration_preset(duration_preset)
    seq = load_sequence(project)
    table = beat_table(seq) if seq else []
    if pick.is_long:
        note = sequence_status_md(seq, pick.seconds) if seq else plan_note(pick.seconds)
    else:
        note = (
            f"**{pick.label}** one SVD-XT pass. "
            "1 min / 2 min (60s reel / 120s reel) = last-frame chain + stitch. "
            "Off-prompt: Regenerate (new seed, same still + prompt). Zero credits."
        )
    return (*pack, table, note)


def _auto_long_reel(
    project_name: str,
    idea: str,
    intent: str,
    duration_preset: str,
    history,
    attached_ref: str,
    values,
    still,
    *,
    paragraph: str,
):
    project = load_project(project_name)
    pick = parse_duration_preset(duration_preset)
    shot = card_from_form(*values) if len(values) >= 25 else ShotCard()
    clip_s = duration_for_form(values[4] if len(values) > 4 else None)
    start_name = None
    stills = _as_paths(still)
    if attached_ref and Path(attached_ref).is_file():
        ingested = project.ingest_files([Path(attached_ref)])
        start_name = ingested[0].name if ingested else Path(attached_ref).name
    elif stills:
        ingested = project.ingest_files(stills)
        start_name = ingested[0].name if ingested else stills[0].name
    try:
        build_sequence(
            project,
            paragraph or intent,
            target_seconds=pick.seconds,
            clip_seconds=clip_s,
            aspect=shot.aspect_ratio or "16:9",
            intimacy=shot.intimacy_mode or "covered sheets",
            lighting=shot.lighting or "",
            camera=shot.camera_move or "slow push-in",
            character_ids=list(shot.character_ids or []),
            start_still=start_name,
        )
    except ExtendError as exc:
        yield _with_extend_tail(
            _motion_pack(
                project,
                shot,
                overlay=False,
                toast=toast_html(str(exc)),
                status=sanitize_motion_error(str(exc)),
                feed_history=history,
                ref_chip=ref_chip_html(attached_ref),
            ),
            project,
            duration_preset,
        )
        return
    form = [*values, still, history, attached_ref]
    yield from _run_extend_clips(
        project_name,
        idea,
        intent,
        duration_preset,
        history,
        attached_ref,
        form,
        remaining=True,
    )


def regenerate_motion_now(
    project_name: str,
    idea: str,
    enhance_family: str,
    enhance_model: str,
    video_family: str,
    video_model: str,
    image_family: str,
    image_model: str,
    duration_preset: str,
    quality: str,
    attached_ref: str,
    feed_history,
    *form,
):
    """New take: new seed + folded notes. Old take stays on Take Board."""
    del enhance_family, enhance_model, quality
    project = load_project(project_name)
    image_route = resolve_video_pick(video_family, video_model)
    values = list(form)
    uploaded: list[Path] = []
    if len(values) > 25:
        uploaded = _as_paths(values[25])
        values = values[:25]
    shot = card_from_form(*values) if len(values) >= 25 else ShotCard()
    if shot.id:
        try:
            shot.resolution = project.load_shot(shot.id).resolution
        except (FileNotFoundError, OSError, ValueError):
            pass
    prompt = (shot.director_intent or idea or "").strip()
    ref_path = (attached_ref or "").strip()
    if not ref_path and uploaded:
        ref_path = str(uploaded[0])
    history = [t for t in (feed_history or []) if isinstance(t, dict)]
    if not prompt:
        yield _with_extend_tail(
            _motion_pack(
                project,
                shot,
                overlay=False,
                toast=toast_html(
                    "Regenerate needs the same prompt — type one or Enhance first. "
                    "Then Regenerate rolls a new seed on this still."
                ),
                status="No prompt to regenerate.",
                feed_history=history,
                ref_chip=ref_chip_html(ref_path),
            ),
            project,
            duration_preset,
        )
        return
    if not image_route.local_i2v:
        yield _with_extend_tail(
            _motion_pack(
                project,
                shot,
                overlay=False,
                toast=toast_html(image_route.message),
                status=image_route.message,
                feed_history=history,
                ref_chip=ref_chip_html(ref_path),
            ),
            project,
            duration_preset,
        )
        return
    new_seed = _new_regen_seed()
    notes = load_notes(project)
    prompt = fold_desk(project, prompt)
    try:
        assert_notes_safe(
            project,
            notes,
            intimacy=shot.intimacy_mode,
            intensity=shot.content_intensity,
            context="Regenerate take",
        )
    except DirectorNoteError as exc:
        yield _with_extend_tail(
            _motion_pack(
                project,
                shot,
                overlay=False,
                toast=toast_html(str(exc)),
                status=sanitize_motion_error(str(exc)),
                feed_history=history,
                ref_chip=ref_chip_html(ref_path),
            ),
            project,
            duration_preset,
        )
        return
    kept = ""
    if shot.id and shot_has_output(project, shot.id):
        source = shot
        shot = fork_take(project, source, seed=new_seed)
        _stamp_quality(shot, project, keep_existing=True)
        values[0] = shot.id
        values[1] = shot.name
        kept = f" Kept `{source.name}` on Take Board."
    values[15] = new_seed
    values[16] = prompt
    shot.seed = new_seed
    shot.director_intent = prompt
    pick = parse_duration_preset(duration_preset)
    if not pick.is_long:
        values[4] = float(pick.seconds)
        shot.duration = float(pick.seconds)
    history = append_turn(
        history,
        user_text=f"Regenerate · seed {new_seed}",
        paragraph=(
            f"{prompt}\n\nRegenerate · seed {new_seed} · new take.{kept} "
            "Director Note + Pose apply first. If it still ignores the command, "
            "Enhance again or tighten negatives."
        ),
        ref_name=Path(ref_path).name if ref_path else "",
    )
    still = form[25] if len(form) > 25 else (ref_path or None)
    if pick.is_long:
        yield from _auto_long_reel(
            project_name,
            idea,
            prompt,
            duration_preset,
            history,
            ref_path,
            values,
            still,
            paragraph=prompt,
        )
        return
    for pack in generate_now(
        project_name,
        DEFAULT_GENERATOR_ID,
        *values,
        still,
        history,
        ref_path,
        mode="animate",
        keep_quality=True,
    ):
        yield _with_extend_tail(pack, project, duration_preset)


def apply_ugc_frame_ui():
    return "9:16", 2.5, "UGC 9:16 · 2.5s beat for 6GB. Drop a still, write the motion, Generate video."


def enhance_motion_ui(
    project_name: str,
    idea: str,
    current: str,
    enhance_family: str,
    enhance_model: str,
    aspect: str,
    camera: str,
    lighting: str,
    intimacy: str,
    character_ids,
    negative: str = "",
    feed_history=None,
    attached_ref: str = "",
    content_intensity=0.0,
):
    project = load_project(project_name)
    seed = (idea or "").strip() or (current or "").strip()
    history = [t for t in (feed_history or []) if isinstance(t, dict)]
    try:
        result = enhance_prompt(
            project,
            seed,
            provider=enhance_family,
            model_label=enhance_model,
            character_ids=list(character_ids or []),
            aspect=aspect or "16:9",
            camera=camera or "slow push-in",
            lighting=lighting or "",
            intimacy=intimacy or "covered sheets",
            content_intensity=content_intensity,
        )
    except EnhanceError as exc:
        return (
            seed,
            current or "",
            toast_html(str(exc)),
            sanitize_motion_error(str(exc)),
            negative or "",
            render_feed(history),
            history,
            ref_chip_html(attached_ref),
        )
    history = append_turn(
        history,
        user_text=result.seed,
        paragraph=(result.paragraph or result.prompt).strip(),
        ref_name=Path(attached_ref).name if attached_ref else "",
    )
    return (
        result.seed,
        result.prompt,
        "",
        result.note,
        (negative or "").strip() or result.negative,
        render_feed(history),
        history,
        ref_chip_html(attached_ref),
    )


def build_extend_plan_ui(
    project_name: str,
    idea: str,
    intent: str,
    provider: str,
    enhance_model: str,
    target_label: str,
    duration,
    aspect: str,
    camera: str,
    lighting: str,
    intimacy: str,
    character_ids,
    motion_image,
    feed_history,
    attached_ref: str,
):
    project = load_project(project_name)
    history = [t for t in (feed_history or []) if isinstance(t, dict)]
    seed = (intent or "").strip() or (idea or "").strip()
    target = parse_target(target_label)
    clip_s = duration_for_form(duration)
    if not seed:
        return (
            [],
            plan_note(target, clip_s),
            shot_dropdown(project),
            toast_html("Enhance a short command first, then build the shot list."),
            "Need an enhanced prompt.",
            render_feed(history),
            history,
        )
    paragraph = seed
    if (idea or "").strip() and len(seed) < 80:
        try:
            result = enhance_prompt(
                project,
                (idea or seed).strip(),
                provider=provider,
                model_label=enhance_model,
                character_ids=list(character_ids or []),
                aspect=aspect or "16:9",
                camera=camera or "slow push-in",
                lighting=lighting or "",
                intimacy=intimacy or "covered sheets",
            )
            paragraph = (result.paragraph or result.prompt).strip()
            seed = result.prompt
        except EnhanceError:
            paragraph = seed
    stills = _as_paths(motion_image)
    start_name = None
    if attached_ref and Path(attached_ref).is_file():
        ingested = project.ingest_files([Path(attached_ref)])
        start_name = ingested[0].name if ingested else Path(attached_ref).name
    elif stills:
        ingested = project.ingest_files(stills)
        start_name = ingested[0].name if ingested else stills[0].name
    try:
        seq = build_sequence(
            project,
            paragraph,
            target_seconds=target,
            clip_seconds=clip_s,
            aspect=aspect or "16:9",
            intimacy=intimacy or "covered sheets",
            lighting=lighting or "",
            camera=camera or "slow push-in",
            character_ids=list(character_ids or []),
            start_still=start_name,
        )
    except ExtendError as exc:
        return (
            [],
            plan_note(target, clip_s),
            shot_dropdown(project),
            toast_html(str(exc)),
            sanitize_motion_error(str(exc)),
            render_feed(history),
            history,
        )
    history = append_turn(
        history,
        user_text=(idea or "").strip() or f"{target}s reel",
        paragraph=(
            f"{paragraph}\n\nShot list: {len(seq.beats)} clips toward {target}s. "
            "Each SVD-XT pass is seconds. Continue from the last frame, then stitch."
        ),
        ref_name=Path(attached_ref).name if attached_ref else "",
    )
    return (
        beat_table(seq),
        sequence_status_md(seq, target),
        shot_dropdown(project, seq.beats[0].shot_id if seq.beats else None),
        "",
        (
            f"Built {len(seq.beats)} shots for a {target}s reel "
            f"({clip_s:.1f}s SVD passes + {seq.overlap:.1f}s crossfades). "
            "Continue from last frame, or generate remaining. Zero credits."
        ),
        render_feed(history),
        history,
        seed,
    )


def continue_extend_now(
    project_name: str,
    idea: str,
    intent: str,
    target_label: str,
    feed_history,
    attached_ref: str,
    *form,
):
    yield from _run_extend_clips(
        project_name,
        idea,
        intent,
        target_label,
        feed_history,
        attached_ref,
        form,
        remaining=False,
    )


def generate_extend_reel_now(
    project_name: str,
    idea: str,
    intent: str,
    target_label: str,
    feed_history,
    attached_ref: str,
    *form,
):
    yield from _run_extend_clips(
        project_name,
        idea,
        intent,
        target_label,
        feed_history,
        attached_ref,
        form,
        remaining=True,
    )


def _run_extend_clips(
    project_name: str,
    idea: str,
    intent: str,
    target_label: str,
    feed_history,
    attached_ref: str,
    form,
    *,
    remaining: bool,
):
    from film_lab.generators.comfyui_i2v import clear_generation_hooks, set_generation_hooks

    project = load_project(project_name)
    values, uploaded, _, _ = _split_motion_args(form)
    shot = card_from_form(*values) if len(values) >= 25 else ShotCard()
    history = [t for t in (feed_history or []) if isinstance(t, dict)]
    seq = load_sequence(project)
    target = parse_target(target_label)
    if seq is None:
        yield (
            *_motion_pack(
                project,
                shot,
                overlay=False,
                toast=toast_html("Build the shot list first (60s / 120s)."),
                status="No extend sequence.",
                feed_history=history,
                ref_chip=ref_chip_html(attached_ref),
            ),
            [],
            plan_note(target),
        )
        return

    _CANCEL.clear()
    first = True
    while True:
        if _CANCEL.is_set():
            yield (
                *_motion_pack(
                    project,
                    shot,
                    overlay=False,
                    status="Stopped. Shot list kept. Continue later.",
                    feed_history=history,
                    ref_chip=ref_chip_html(attached_ref),
                ),
                beat_table(seq),
                sequence_status_md(seq, target),
            )
            return
        try:
            next_shot, beat, still = prepare_next_shot(project, seq, uploaded=uploaded)
        except ExtendError as exc:
            if first and "already complete" in str(exc).lower():
                try:
                    dest = stitch_sequence(project, seq)
                except ExtendError as stitch_exc:
                    yield (
                        *_motion_pack(
                            project,
                            shot,
                            overlay=False,
                            toast=toast_html(str(stitch_exc)),
                            status=sanitize_motion_error(str(stitch_exc)),
                            feed_history=history,
                            ref_chip=ref_chip_html(attached_ref),
                        ),
                        beat_table(seq),
                        sequence_status_md(seq, target),
                    )
                    return
                yield (
                    *_motion_pack(
                        project,
                        shot,
                        overlay=False,
                        video=dest,
                        status=f"Sequence already complete. Stitched `{dest.name}`.",
                        feed_history=history,
                        ref_chip=ref_chip_html(attached_ref),
                    ),
                    beat_table(seq),
                    sequence_status_md(seq, target),
                )
                return
            yield (
                *_motion_pack(
                    project,
                    shot,
                    overlay=False,
                    toast=toast_html(str(exc)),
                    status=sanitize_motion_error(str(exc)),
                    feed_history=history,
                    ref_chip=ref_chip_html(attached_ref),
                ),
                beat_table(seq),
                sequence_status_md(seq, target),
            )
            return

        shot = next_shot
        n = len(seq.beats)
        done = seq.done_count()
        history = append_turn(
            history,
            user_text=(idea or "").strip() or f"clip {beat.index + 1}/{n}",
            paragraph=(
                f"{beat.prompt}\n\nClip {beat.index + 1}/{n} — continue from last frame. "
                "SVD-XT is seconds; the reel is the chain."
            ),
            ref_name=Path(attached_ref).name if attached_ref else "",
        )
        latest = {"pct": 8, "done": None, "err": None}

        def on_progress(pct: int) -> None:
            latest["pct"] = pct

        def work() -> None:
            try:
                set_generation_hooks(progress=on_progress, cancel=_CANCEL.is_set)
                output, note = generate_motion_mp4(
                    project,
                    shot,
                    generator_id=DEFAULT_GENERATOR_ID,
                    uploaded=[still] if still else uploaded,
                    allow_fallback=False,
                )
                latest["done"] = (output, note)
            except Exception as exc:  # noqa: BLE001
                latest["err"] = exc
            finally:
                clear_generation_hooks()

        thread = threading.Thread(target=work, daemon=True)
        thread.start()
        base_pct = int(100 * done / max(n, 1))
        yield (
            *_motion_pack(
                project,
                shot,
                overlay=True,
                percent=max(8, base_pct),
                status=f"Clip {beat.index + 1}/{n} on local SVD-XT. Adults 18+. No NSFW filter.",
                feed_history=history,
                generating=True,
                intent=shot.director_intent,
                enhance_before=idea or intent,
                ref_chip=ref_chip_html(attached_ref),
            ),
            beat_table(seq),
            sequence_status_md(seq, target),
        )
        while thread.is_alive():
            time.sleep(0.35)
            mix = min(99, base_pct + int(latest["pct"] * 0.2))
            yield (
                *_motion_pack(
                    project,
                    shot,
                    overlay=True,
                    percent=mix,
                    status=f"Generating… clip {beat.index + 1}/{n}. Cancel anytime.",
                    feed_history=history,
                    generating=True,
                    ref_chip=ref_chip_html(attached_ref),
                ),
                beat_table(seq),
                sequence_status_md(seq, target),
            )
        if latest["err"] is not None:
            msg = sanitize_motion_error(str(latest["err"]))
            yield (
                *_motion_pack(
                    project,
                    shot,
                    overlay=False,
                    toast=toast_html(msg),
                    status=msg,
                    feed_history=history,
                    ref_chip=ref_chip_html(attached_ref),
                ),
                beat_table(seq),
                sequence_status_md(seq, target),
            )
            return
        output, note = latest["done"]
        seq = mark_clip(project, seq, beat, output)
        first = False
        if not remaining:
            yield (
                *_motion_pack(
                    project,
                    shot,
                    overlay=False,
                    video=output,
                    status=(
                        f"{note} Clip {beat.index + 1}/{n}. "
                        f"{seq.done_count()} done. Continue or generate remaining + stitch."
                    ),
                    feed_history=history,
                    ref_chip=ref_chip_html(attached_ref),
                ),
                beat_table(seq),
                sequence_status_md(seq, target),
            )
            return
        if seq.next_index() is None:
            break

    try:
        dest = stitch_sequence(project, seq)
    except ExtendError as exc:
        yield (
            *_motion_pack(
                project,
                shot,
                overlay=False,
                toast=toast_html(str(exc)),
                status=sanitize_motion_error(str(exc)),
                feed_history=history,
                ref_chip=ref_chip_html(attached_ref),
            ),
            beat_table(seq),
            sequence_status_md(seq, target),
        )
        return
    yield (
        *_motion_pack(
            project,
            shot,
            overlay=False,
            video=dest,
            status=(
                f"Stitched {seq.done_count()} SVD clips → `{dest.name}` "
                f"(~{seq.target_seconds}s target). Zero credits."
            ),
            feed_history=history,
            ref_chip=ref_chip_html(attached_ref),
        ),
        beat_table(seq),
        sequence_status_md(seq, target),
    )


def auto_stitch_sequence_ui(project_name: str, quality: str | None = None):
    project = load_project(project_name)
    try:
        dest = stitch_sequence(project)
        dest = _export_scaled(project, dest, quality)
    except ExtendError as exc:
        raise gr.Error(sanitize_motion_error(str(exc))) from exc
    gallery = gallery_choices(project)
    label = next((g for g in gallery if str(dest.resolve()) in g), None)
    seq = load_sequence(project)
    q = quality or project.quality
    return (
        str(dest),
        str(dest),
        gr.CheckboxGroup(choices=gallery, value=[label] if label else []),
        f"Auto-stitched {len(seq.clip_paths()) if seq else 0} sequence clips → `{dest.name}` at {q}.",
        _reel_table(project),
    )


def enhance_writing_ui(
    project_name: str,
    idea: str,
    current: str,
    provider: str,
    character_ids,
    emotion: str,
    intimacy: str,
):
    project = load_project(project_name)
    seed = (idea or "").strip() or (current or "").strip()
    try:
        result = enhance_prompt(
            project,
            seed,
            provider=provider,
            character_ids=list(character_ids or []),
            emotion=emotion or "held, tender",
            intimacy=intimacy or "covered sheets",
            mode="pages",
        )
    except EnhanceError as exc:
        return seed, current or "", sanitize_motion_error(str(exc))
    return result.seed, result.packed(), result.note


def enqueue_shot(project_name: str, queue: GenerationQueue, *form):
    from film_lab.motion_path import ensure_motion_still

    project = load_project(project_name)
    shot = card_from_form(*form)
    _stamp_quality(shot, project, keep_existing=False)
    _guard_shot_cast(project, shot)
    try:
        ensure_motion_still(project, shot)
    except MotionBlocked as exc:
        raise gr.Error(str(exc)) from exc
    project.save_shot(shot)
    queue.enqueue(shot)
    return (
        queue,
        queue.rows(),
        shot.id,
        shot_dropdown(project, shot.id),
        f"Queued `{shot.name}`. Queue length: {len(queue.items)}.",
    )


def run_queue_ui(project_name: str, queue: GenerationQueue, generator_id: str, progress=gr.Progress()):
    project = load_project(project_name)
    generator = get_generator(generator_id)

    def cb(index: int, total: int, message: str) -> None:
        progress((index - 1) / max(total, 1), desc=message)

    queue.run(project, generator, progress=cb)
    done = sum(1 for i in queue.items if i.status == "done")
    err = sum(1 for i in queue.items if i.status == "error")
    last_video = None
    for item in reversed(queue.items):
        if item.output_path and Path(item.output_path).is_file():
            last_video = item.output_path
            break
    gallery = gallery_choices(project)
    return (
        queue,
        queue.rows(),
        last_video,
        gr.CheckboxGroup(choices=gallery, value=[]),
        last_video,
        f"Queue pass finished. {done} done, {err} error(s).",
        _reel_table(project),
    )


def clear_finished(queue: GenerationQueue):
    queue.clear_finished()
    return queue, queue.rows(), "Cleared finished / errored jobs."


def clear_queue(queue: GenerationQueue):
    queue.clear_all()
    return queue, queue.rows(), "Queue emptied."


def preview_clip(project_name: str, selected: list[str] | None, quality: str | None = None):
    if not selected:
        return None, None
    path = _path_from_label(selected[0])
    if not path.is_file():
        return None, None
    project = load_project(project_name)
    exported = _export_scaled(project, path, quality)
    return str(path), str(exported)


def stitch_selected(
    project_name: str,
    selected: list[str] | None,
    music_choice: str | None,
    quality: str | None = None,
):
    if not selected or len(selected) < 2:
        raise gr.Error("Select at least two gallery clips (in order) to stitch.")
    project = load_project(project_name)
    clips = [_path_from_label(label) for label in selected]
    dest = project.outputs_dir / f"stitch_{new_shot_id()}.mp4"
    try:
        stitch_clips(clips, dest)
        audio = _resolve_audio_choice(project, music_choice)
        if audio:
            muxed = dest.with_name(dest.stem + "_mux.mp4")
            mux_audio_under(dest, audio, muxed)
            dest = muxed
        dest = _export_scaled(project, dest, quality)
    except Exception as exc:  # noqa: BLE001
        raise gr.Error(str(exc)) from exc
    project.register_output(dest, generator="stitch")
    gallery = gallery_choices(project)
    label = next((g for g in gallery if str(dest.resolve()) in g), None)
    q = quality or project.quality
    return (
        str(dest),
        str(dest),
        gr.CheckboxGroup(choices=gallery, value=[label] if label else []),
        f"Stitched {len(clips)} clips → `{dest.name}` at {q}.",
        _reel_table(project),
    )


def _resolve_audio_choice(project: Project, choice: str | None) -> Path | None:
    if not choice:
        return None
    name = Path(str(choice)).name
    for folder in (project.audio_dir / "music", project.audio_dir / "beds", project.audio_dir / "dialogue"):
        path = folder / name
        if path.is_file():
            return path
    return None


# --- Characters ---


def load_character_ui(project_name: str, choice: str):
    if not choice:
        raise gr.Error("Pick a character.")
    project = load_project(project_name)
    profile = load_character(project, _id_from_choice(choice))
    refs = [str(p) for p in resolve_refs(project, profile)]
    return (
        profile.id,
        profile.name,
        getattr(profile, "role", "Adult") or "Adult",
        profile.age_band,
        profile.age_years if profile.age_years is not None else 28,
        profile.look_notes,
        profile.wardrobe,
        profile.rings_props,
        profile.personality,
        profile.emotion_baseline,
        profile.micro_expression or "none",
        profile.behavior or "none",
        profile.voice_notes,
        profile.voice_backend if profile.voice_backend in VOICE_BACKENDS else "auto",
        profile.voice_id,
        profile.voice_sample or "",
        profile.locked_descriptor,
        *living_ui_updates(profile.living_brief())[1:],
        refs,
        _belongs_status(project, profile),
    )


def _belongs_status(project, profile) -> str:
    from film_lab.genetics import belongs_line

    extra = belongs_line(profile, project)
    voice = profile.voice_id or default_tts_voice_id(profile.id) or "default"
    hint = (
        f"Loaded {profile.name}. Voice `{voice}`. "
        f"Consistency pack: {len(profile.reference_stills)} still(s)."
    )
    if extra:
        hint += f" {extra}"
    return hint


def save_character_ui(
    project_name,
    cid,
    name,
    role,
    age,
    age_years,
    look,
    wardrobe,
    rings_props,
    personality,
    emotion_baseline,
    micro_expression,
    behavior,
    voice,
    voice_backend,
    voice_id,
    voice_sample_file,
    descriptor,
    live_styles,
    live_custom,
    live_norms,
    live_income,
    live_housing,
    live_privacy,
    live_clean,
    live_hood,
    live_utils,
    live_deps,
    live_work,
    live_health,
    as_project_default,
):
    project = load_project(project_name)
    existing = None
    existing_refs: list[str] = []
    if cid and (project.root / "characters" / cid / "profile.json").exists():
        existing = load_character(project, cid)
        existing_refs = existing.reference_stills
    nest = living_from_form(
        False,
        live_styles,
        live_custom,
        live_norms,
        live_income,
        live_housing,
        live_privacy,
        live_clean,
        live_hood,
        live_utils,
        live_deps,
        live_work,
        live_health,
    )
    try:
        profile = CharacterProfile(
            id=(cid or "").strip() or new_character(name or "character").id,
            name=(name or "").strip() or "Unnamed",
            role=role or "Adult",
            age_band=age or "late 20s (adult)",
            age_years=age_years,
            look_notes=look or "",
            wardrobe=wardrobe or "",
            rings_props=rings_props or "",
            personality=personality or "",
            lighting_notes=existing.lighting_notes if existing else "",
            emotion_baseline=emotion_baseline or "",
            micro_expression=micro_expression or "",
            behavior=behavior or "",
            voice_notes=voice or "",
            voice_backend=(voice_backend or "").strip()
            or (existing.voice_backend if existing else "auto")
            or "auto",
            voice_id=(voice_id or "").strip()
            or (existing.voice_id if existing else "")
            or default_tts_voice_id((cid or "").strip()),
            voice_sample=existing.voice_sample if existing else "",
            locked_descriptor=descriptor or "",
            reference_stills=existing_refs,
            living=nest.to_dict(),
            parent_ids=list(existing.parent_ids) if existing else [],
        )
    except CharacterError as exc:
        raise gr.Error(str(exc)) from exc
    apply_voice_defaults(profile)
    save_character(project, profile)
    for src in _as_paths(voice_sample_file):
        persist_voice_sample(project, profile.id, src)
        profile = load_character(project, profile.id)
    export_to_studio_library(profile)
    extra = ""
    if as_project_default:
        project.set_living(nest)
        extra = " Also saved as project nest default."
    return (
        profile.id,
        char_dropdown(project, profile.id),
        f"Saved {profile.name} and wrote `data/characters/{profile.id}.json`. "
        f"Living + bible inject into writing, stills, UGC, and shots.{extra}",
        *_parent_dropdowns(project),
    )


def save_active_cast_ui(project_name, cast_ids, face_lock):
    project = load_project(project_name)
    ids = []
    for item in cast_ids or []:
        ids.append(_id_from_choice(item) if " — " in str(item) else str(item))
    project.set_cast(ids, face_lock_strength=face_lock)
    return (
        project.active_cast,
        project.face_lock_strength,
        f"Active cast: {', '.join(project.active_cast) or 'none'}. "
        f"Face lock {project.face_lock_strength:.2f}. Zero credits.",
    )


def import_character_sheet_ui(
    files,
    cid,
    name,
    role,
    age,
    age_years,
    look,
    wardrobe,
    rings_props,
    personality,
    emotion_baseline,
    micro_expression,
    behavior,
    voice,
    descriptor,
):
    """Word / PDF bio → Character Bible form. Not Excel."""
    try:
        parsed, names = import_bible_files(files)
    except BibleSheetError as exc:
        raise gr.Error(str(exc)) from exc
    years = parsed.get("age_years")
    if years not in (None, ""):
        try:
            years_val = int(round(float(years)))
        except (TypeError, ValueError):
            years_val = age_years
    else:
        years_val = age_years
    imported = ", ".join(f"`{n}`" for n in names)
    hint = (
        f"Imported {imported} into Character Bible. Review the fields, then Save profile. "
        "Word / PDF only — Excel stays on Writing Studio. Offline. Zero credits."
    )
    return (
        parsed.get("id") or cid,
        parsed.get("name") or name,
        parsed.get("role") or role,
        parsed.get("age_band") or age,
        years_val,
        parsed.get("look_notes") or look,
        parsed.get("wardrobe") or wardrobe,
        parsed.get("rings_props") or rings_props,
        parsed.get("personality") or personality,
        parsed.get("emotion_baseline") or emotion_baseline,
        parsed.get("micro_expression") or micro_expression,
        parsed.get("behavior") or behavior,
        parsed.get("voice_notes") or voice,
        parsed.get("locked_descriptor") or descriptor,
        hint,
    )


def export_character_sheet_ui(
    project_name,
    cid,
    name,
    role,
    age,
    age_years,
    look,
    wardrobe,
    rings_props,
    personality,
    emotion_baseline,
    micro_expression,
    behavior,
    voice,
    descriptor,
    fmt,
):
    """Export the typed bible as Word or PDF. Not Excel."""
    project = load_project(project_name)
    fields = {
        "id": (cid or "").strip(),
        "name": (name or "").strip() or "Character",
        "role": role or "Adult",
        "age_band": age or "",
        "age_years": age_years if age_years not in (None, "") else "",
        "look_notes": look or "",
        "wardrobe": wardrobe or "",
        "rings_props": rings_props or "",
        "personality": personality or "",
        "emotion_baseline": emotion_baseline or "",
        "micro_expression": micro_expression or "",
        "behavior": behavior or "",
        "voice_notes": voice or "",
        "locked_descriptor": descriptor or "",
    }
    if fields["id"] and (project.root / "characters" / fields["id"] / "profile.json").exists():
        existing = load_character(project, fields["id"])
        if existing.lighting_notes and not fields.get("lighting_notes"):
            fields["lighting_notes"] = existing.lighting_notes
        if existing.voice_backend:
            fields["voice_backend"] = existing.voice_backend
        if existing.voice_id:
            fields["voice_id"] = existing.voice_id
    try:
        ext = ext_for_bible_export(fmt)
        dest = (
            characters_dir(project)
            / (fields["id"] or slugify(fields["name"], "character"))
            / sheet_filename(fields["name"], fields["id"], ext)
        )
        export_bible_sheet(fields, dest)
    except BibleSheetError as exc:
        raise gr.Error(str(exc)) from exc
    return str(dest), f"Exported Character Bible `{dest.name}`. Word / PDF only."


def import_library_ui(project_name: str):
    project = load_project(project_name)
    ensure_studio_library()
    added = import_studio_library(project)
    ids = [p.id for p in list_characters(project)]
    return (
        char_dropdown(project),
        gr.update(choices=ids, value=list(project.active_cast)),
        f"Studio library → project. Added {len(added)} profile(s). "
        f"Cast files live in data/characters/.",
    )


def pin_refs_ui(project_name, choice, files, still_name):
    project = load_project(project_name)
    cid = _id_from_choice(choice)
    if not cid:
        raise gr.Error("Save or load a character first.")
    pinned = 0
    for path in _as_paths(files):
        pin_reference(project, cid, path)
        pinned += 1
    if still_name:
        still = project.resolve_still(still_name)
        if still:
            pin_reference(project, cid, still)
            pinned += 1
    profile = load_character(project, cid)
    refs = [str(p) for p in resolve_refs(project, profile)]
    return refs, f"Pinned {pinned}. Pack is {len(profile.reference_stills)}/{10}."


def fold_voice_micro_ui(micro, breath):
    return fold_micro_into_breath(breath, micro)


def inject_writing_performance_ui(notes, micro, behavior, prop):
    line = compose_writing_line(micro, behavior, prop)
    if not line:
        return notes or "", "Pick a micro-expression, behavior, or prop action first."
    merged = f"{line}\n{(notes or '').strip()}".strip()
    return (
        merged,
        "Injected into director notes. Micro-expression + behavior + prop action. "
        "Regular / story for under-18 roles. Intimate / explicit: adult 18+ ONLY.",
    )


def generate_kids_ui(project_name, actor_a, actress_b, age, kid_name=""):
    """Actor A + Actress B → blended Regular/story child bible card."""
    from film_lab.genetics import GeneticsError, belongs_line, generate_kids

    project = load_project(project_name)
    try:
        child, stills = generate_kids(
            project,
            actor_a,
            actress_b,
            age,
            name=kid_name,
        )
    except (GeneticsError, CharacterError) as exc:
        raise gr.Error(str(exc)) from exc
    refs = [str(p) for p in resolve_refs(project, child)]
    gallery = refs or [str(p) for p in stills]
    names = project.still_choices()
    start = names[-1] if names else None
    hint = (
        f"Family Genetics: saved **{child.name}** (`{child.id}`, {child.role} {child.age_years}). "
        f"{belongs_line(child, project)} "
        f"{len(stills)} blended still(s) on Still Desk + the bible pack. "
        "Regular / story only — never 18+ intimacy. Zero credits."
    )
    return (
        gallery,
        char_dropdown(project, child.id),
        child.id,
        child.name,
        child.role,
        child.age_band,
        child.age_years,
        child.look_notes,
        child.wardrobe,
        child.locked_descriptor,
        refs,
        gr.update(choices=names, value=start),
        [str(p) for p in project.list_stills()],
        hint,
        *_parent_dropdowns(project, child.parent_ids[0] if child.parent_ids else None, child.parent_ids[1] if len(child.parent_ids) > 1 else None),
    )


# --- Script ---


def load_scene_ui(project_name, choice):
    if not choice:
        raise gr.Error("Pick a scene.")
    project = load_project(project_name)
    scene = load_scene(project, _id_from_choice(choice))
    return (
        scene.id,
        scene.heading,
        scene.action,
        lines_to_table(scene.lines),
        scene.director_notes,
        scene.status,
        ", ".join(scene.shot_ids),
        scene.to_fountain(title=project.name),
        f"Loaded {scene.heading}.",
    )


def _scene_from_script_form(project, sid, heading, action, table, notes, status, shot_ids_text):
    scene = new_scene(heading or "INT. BEDROOM - NIGHT")
    if sid:
        scene.id = sid
        try:
            old = load_scene(project, sid)
            scene.primary_genre = old.primary_genre
            scene.secondary_genres = list(old.secondary_genres)
            scene.custom_genre_tags = list(old.custom_genre_tags)
            scene.tropes_checklist = old.tropes_checklist
            scene.living = dict(old.living or {})
            scene.created_at = old.created_at
        except (OSError, ValueError, FileNotFoundError):
            pass
    scene.action = action or ""
    scene.lines = lines_from_table(table)
    scene.director_notes = notes or ""
    scene.status = status or "idea"
    scene.shot_ids = [s.strip() for s in (shot_ids_text or "").split(",") if s.strip()]
    return scene


def save_scene_ui(project_name, sid, heading, action, table, notes, status, shot_ids_text):
    project = load_project(project_name)
    scene = _scene_from_script_form(
        project, sid, heading, action, table, notes, status, shot_ids_text
    )
    save_scene(project, scene)
    return (
        scene.id,
        scene_dropdown(project, scene.id),
        scene.to_fountain(title=project.name),
        f"Saved scene `{scene.id}`.",
    )


def new_scene_ui():
    scene = new_scene()
    return (
        scene.id,
        scene.heading,
        "",
        [["ALISON", "", ""], ["BRADLEY", "", ""]],
        "",
        "idea",
        "",
        scene.to_fountain(),
        "New scene. Write heading, action, and lines.",
    )


def export_scene_ui(project_name, sid, heading, action, table, notes, status, shot_ids_text, fmt):
    project = load_project(project_name)
    scene = _scene_from_script_form(
        project, sid, heading, action, table, notes, status, shot_ids_text
    )
    save_scene(project, scene)
    ext = {"fountain": ".fountain", "txt": ".txt", "pdf": ".pdf"}.get(fmt, ".fountain")
    dest = project.scenes_dir / f"{scene.id}{ext}"
    export_scene(project, scene, dest)
    return str(dest), f"Exported `{dest.name}`."


def link_shot_to_scene(project_name, scene_choice, shot_choice):
    project = load_project(project_name)
    sid = _id_from_choice(scene_choice)
    shot_id = _id_from_choice(shot_choice)
    if not sid or not shot_id:
        raise gr.Error("Pick a scene and a shot.")
    scene = link_shot(project, sid, shot_id)
    shot = project.load_shot(shot_id)
    shot.scene_id = sid
    project.save_shot(shot)
    return ", ".join(scene.shot_ids), f"Linked {shot_id} → {sid}."


# --- Voice ---


def speak_line_ui(
    project_name,
    voice_provider,
    character_choice,
    text,
    start_s,
    shot_choice,
    scene_choice,
    intention=None,
    breath=None,
    pace=None,
    register=None,
    intensity=None,
    backend="",
    voice_id="",
):
    if not (text or "").strip():
        raise gr.Error("Type a dialogue line first.")
    voice_route = resolve_voice_provider(voice_provider)
    if not voice_route.wired:
        raise gr.Error(voice_route.message)
    project = load_project(project_name)
    cid = _id_from_choice(character_choice)
    direction = direction_for(
        cid,
        intention=intention,
        breath=breath,
        pace=pace,
        register=register,
        intensity=intensity,
    )
    cue = synthesize_line(
        project,
        text.strip(),
        character_id=cid,
        scene_id=_id_from_choice(scene_choice) or None,
        shot_id=_id_from_choice(shot_choice) or None,
        start_s=float(start_s or 0),
        direction=direction,
        backend=backend or "auto",
        voice_id=voice_id or "",
    )
    if cue.shot_id:
        try:
            shot = project.load_shot(cue.shot_id)
            shot.dialogue_wav = cue.path
            shot.dialogue_cue = cue.text
            shot.dialogue_start_s = cue.start_s
            project.save_shot(shot)
        except FileNotFoundError:
            pass
    choices = [p.name for p in list_dialogue(project)]
    return (
        cue.path,
        gr.Dropdown(choices=choices, value=Path(cue.path).name),
        f"Take {cue.take} · {Path(cue.path).name} via **{cue.backend}** · "
        f"voice `{cue.voice_id or 'default'}` · {direction.line()}.",
    )


def voice_takes_ui(
    project_name,
    voice_provider,
    character_choice,
    text,
    start_s,
    shot_choice,
    scene_choice,
    intention,
    breath,
    pace,
    register,
    intensity,
    count,
    backend="",
    voice_id="",
):
    if not (text or "").strip():
        raise gr.Error("Type a dialogue line first.")
    voice_route = resolve_voice_provider(voice_provider)
    if not voice_route.wired:
        raise gr.Error(voice_route.message)
    project = load_project(project_name)
    cid = _id_from_choice(character_choice)
    direction = direction_for(
        cid,
        intention=intention,
        breath=breath,
        pace=pace,
        register=register,
        intensity=intensity,
    )
    cues = synthesize_takes(
        project,
        text.strip(),
        character_id=cid,
        scene_id=_id_from_choice(scene_choice) or None,
        shot_id=_id_from_choice(shot_choice) or None,
        start_s=float(start_s or 0),
        direction=direction,
        count=int(count or 3),
        backend=backend or "auto",
        voice_id=voice_id or "",
    )
    last = cues[-1]
    if last.shot_id:
        try:
            shot = project.load_shot(last.shot_id)
            shot.dialogue_wav = last.path
            shot.dialogue_cue = last.text
            shot.dialogue_start_s = last.start_s
            project.save_shot(shot)
        except FileNotFoundError:
            pass
    choices = [p.name for p in list_dialogue(project)]
    return (
        last.path,
        gr.Dropdown(choices=choices, value=Path(last.path).name),
        f"Wrote {len(cues)} acting take(s). Last `{Path(last.path).name}`. Zero credits.",
    )


def import_vo_ui(project_name, files):
    project = load_project(project_name)
    written = import_vo(project, _as_paths(files))
    choices = [p.name for p in list_dialogue(project)]
    return (
        str(written[0]) if written else None,
        gr.Dropdown(choices=choices, value=written[0].name if written else None),
        f"Imported {len(written)} recorded VO file(s)." if written else "No VO files imported.",
    )


def load_voice_direction_ui(project_name, character_choice):
    cid = _id_from_choice(character_choice)
    project = load_project(project_name) if project_name else None
    profile = resolve_voice_profile(project, cid)
    direction = profile.direction()
    sample_name = Path(profile.sample).name if profile.sample else ""
    return (
        direction.intention,
        direction.breath,
        direction.pace,
        direction.register,
        direction.intensity,
        profile.backend if profile.backend in VOICE_BACKENDS else "auto",
        profile.tts_voice_id,
        profile.sample or "",
        f"Loaded {cid or 'default'} Voice profile · TTS `{profile.tts_voice_id or 'default'}` · "
        f"sample {sample_name or 'none'}. Adults 18+ only.",
    )


def save_voice_profile_ui(
    project_name,
    character_choice,
    backend,
    voice_id,
    sample_file,
    intention,
    breath,
    pace,
    register,
    intensity,
):
    project = load_project(project_name)
    cid = _id_from_choice(character_choice)
    if not cid:
        raise gr.Error("Pick Alison, Bradley, or another bible character.")
    profile = load_character(project, cid)
    profile.voice_backend = (backend or "").strip() or "auto"
    if profile.voice_backend not in VOICE_BACKENDS:
        profile.voice_backend = "auto"
    profile.voice_id = (voice_id or "").strip() or default_tts_voice_id(cid)
    apply_voice_defaults(profile)
    save_character(project, profile)
    for src in _as_paths(sample_file):
        persist_voice_sample(project, cid, src)
        profile = load_character(project, cid)
    export_to_studio_library(profile)
    direction = direction_for(
        cid,
        intention=intention,
        breath=breath,
        pace=pace,
        register=register,
        intensity=intensity,
    )
    return (
        profile.voice_backend,
        profile.voice_id,
        profile.voice_sample or "",
        f"Saved {profile.name} Voice profile · TTS `{profile.voice_id}` · "
        f"{direction.line()}. Zero credits.",
    )


def import_vo_as_sample_ui(project_name, character_choice, files):
    project = load_project(project_name)
    cid = _id_from_choice(character_choice)
    if not cid:
        raise gr.Error("Pick a character to attach this sample.")
    written = import_vo(project, _as_paths(files))
    sample_path = ""
    if written:
        persist_voice_sample(project, cid, written[0])
        sample_path = str(written[0].resolve())
        try:
            sample_path = load_character(project, cid).voice_sample
        except Exception:
            pass
    choices = [p.name for p in list_dialogue(project)]
    return (
        str(written[0]) if written else None,
        gr.Dropdown(choices=choices, value=written[0].name if written else None),
        sample_path or "",
        f"Imported {len(written)} VO file(s) and set {cid}'s bible sample."
        if written
        else "No VO files imported.",
    )


def speak_tagged_ui(project_name, voice_provider, body, shot_choice, scene_choice):
    if not (body or "").strip():
        raise gr.Error("Paste tagged lines such as ALISON: Stay. / BRADLEY: I'm here.")
    voice_route = resolve_voice_provider(voice_provider)
    if not voice_route.wired:
        raise gr.Error(voice_route.message)
    project = load_project(project_name)
    takes = extract_dialogue_takes(body or "")
    if not takes:
        raise gr.Error("Tag each line as ALISON: … or BRADLEY: … so it routes to that voice.")
    scene_id = _id_from_choice(scene_choice) or None
    shot_id = _id_from_choice(shot_choice) or None
    cues = speak_tagged_lines(project, takes, scene_id=scene_id, shot_id=shot_id)
    if not cues:
        raise gr.Error("No speakable tagged lines found.")
    last = cues[-1]
    if shot_id:
        try:
            shot = project.load_shot(shot_id)
            shot.dialogue_wav = last.path
            shot.dialogue_cue = last.text
            shot.dialogue_start_s = last.start_s
            project.save_shot(shot)
        except FileNotFoundError:
            pass
    names = [p.name for p in list_dialogue(project)]
    ids = ", ".join(sorted({c.character_id or "?" for c in cues}))
    return (
        last.path,
        gr.Dropdown(choices=names, value=Path(last.path).name),
        f"Spoke {len(cues)} tagged line(s) as {ids}. Cinema muxes each cue. Zero credits.",
    )


# --- Music ---


def save_and_render_cue(project_name, name, mood, start, end, bpm, notes, intensity=0.35):
    project = load_project(project_name)
    length = float(end or 8) - float(start or 0)
    cue = new_cue(
        name or "lamp bed",
        mood=mood or MOODS[0],
        bpm=float(bpm or 62),
        length=length,
        intensity=float(intensity or 0.35),
    )
    cue.in_s = float(start or 0)
    cue.out_s = float(end or cue.in_s + 8)
    cue.notes = notes or ""
    path = render_bed(project, cue)
    return (
        path,
        _cue_table(project),
        gr.Dropdown(choices=_audio_names(project), value=path.name),
        f"Score bed `{path.name}` · {cue.mood} · intensity {cue.intensity:.2f} · {cue.bpm:.0f} BPM. "
        "Import stays the 6GB-safe path.",
    )


def apply_lighting_ui(project_name, preset_title, shot_choice=None):
    from film_lab.lighting import SKIP_LABEL, expand_lighting, is_lighting_skipped

    project = load_project(project_name)
    title = preset_title or SKIP_LABEL
    project.set_lighting(title)
    chip = expand_lighting(title)
    if shot_choice:
        sid = _id_from_choice(shot_choice)
        if sid:
            try:
                shot = project.load_shot(sid)
                shot.lighting = chip
                project.save_shot(shot)
            except FileNotFoundError:
                pass
    if is_lighting_skipped(title):
        msg = (
            "Lighting skipped. Optional — Still / Motion Enhance / Effects / Cinema "
            "will not force a chip."
        )
    else:
        msg = (
            f"Lighting lock **{title}**. Injected into Motion Enhance / Still / "
            "Effects / Cinema when you pick it. Zero credits."
        )
    return (
        title,
        chip,
        mentor_markdown(title),
        msg,
    )


def apply_still_lighting_ui(project_name, notes, pick):
    from film_lab.lighting import expand_lighting, is_lighting_skipped

    project = load_project(project_name)
    chip = expand_lighting(pick)
    body = (notes or "").strip()
    if is_lighting_skipped(pick) or not chip:
        return body, "Lighting skipped on Still Desk. Optional — never forced."
    line = f"Lighting (optional): {chip}"
    if line in body:
        return body, f"{pick} already in still notes."
    text = f"{body}\n{line}".strip() if body else line
    still_notes_path(project).write_text(text + "\n", encoding="utf-8")
    return text, f"Folded optional **{pick}** into still notes. Skip anytime."


def lighting_mentor_ui(preset_title):
    return mentor_markdown(preset_title)


def import_music_ui(project_name, files):
    project = load_project(project_name)
    written = import_music(project, _as_paths(files))
    return (
        gr.Dropdown(choices=_audio_names(project), value=written[0].name if written else None),
        f"Imported {len(written)} music file(s)." if written else "No audio files imported.",
    )


def save_scene_room_tone_ui(project_name, scene_id, audio_file, enabled, gain_db, fade_in_s, fade_out_s, director_note):
    """Persist a real Scene bed; UI success means the copied media and state exist."""
    from film_lab.room_tone import RoomToneStore
    project = load_project(project_name)
    paths = _as_paths([audio_file] if audio_file else [])
    if not paths:
        raise gr.Error("Choose a real room-tone audio recording first.")
    try:
        state = RoomToneStore(project).assign(scene_id, paths[0], enabled=bool(enabled), gain_db=float(gain_db),
            fade_in_s=float(fade_in_s), fade_out_s=float(fade_out_s), director_note=director_note or "")
    except (OSError, ValueError) as exc:
        raise gr.Error(str(exc)) from exc
    if not Path(state.media_path).is_file():
        raise gr.Error("Room-tone assignment did not create persistent project media.")
    md = f"**PASS / REAL** · Scene `{state.scene_id}` · `{Path(state.media_path).name}` · {state.gain_db:.1f} dB · Cinema {'enabled' if state.enabled else 'disabled'}"
    return state.media_path, md, f"Room tone assigned persistently to Scene {state.scene_id}."


def _cue_table(project: Project) -> list[list[str]]:
    return [
        [
            c.id,
            c.name,
            c.mood,
            f"{c.in_s:.1f}",
            f"{c.out_s:.1f}",
            f"{c.bpm:.0f}",
            f"{getattr(c, 'intensity', 0.35):.2f}",
            Path(c.path).name if c.path else "",
        ]
        for c in load_cues(project)
    ]


def _audio_names(project: Project) -> list[str]:
    return [p.name for p in list_music_files(project)] + [p.name for p in list_dialogue(project)]


# --- Finish ---


def apply_finish_ui(
    project_name,
    selected,
    lut_name,
    vfx_op,
    strength,
    speed,
    apply_lut_flag,
    apply_vfx_flag,
    quality=None,
):
    project = load_project(project_name)
    if not selected:
        raise gr.Error("Select a gallery clip (or ingest a still and generate first).")
    src = _path_from_label(selected[0])
    if not src.is_file():
        raise gr.Error(f"Missing file: {src}")
    current = src
    notes: list[str] = []
    if apply_lut_flag and lut_name:
        dest = finish_output_path(project, current, "lut")
        apply_lut(current, resolve_lut(project, lut_name), dest)
        current = dest
        notes.append(f"LUT {lut_name}")
    if apply_vfx_flag:
        dest = finish_output_path(project, current, vfx_op)
        apply_vfx(current, dest, vfx_op, strength=float(strength or 0.5), speed=float(speed or 1.0))
        current = dest
        notes.append(vfx_op)
    if current == src:
        raise gr.Error("Tick Apply LUT and/or Apply VFX.")
    current = _export_scaled(project, current, quality)
    q = quality or project.quality
    notes.append(q)
    project.register_output(current, generator="finish")
    gallery = gallery_choices(project)
    label = next((g for g in gallery if str(current.resolve()) in g), None)
    return (
        str(current),
        str(current),
        gr.CheckboxGroup(choices=gallery, value=[label] if label else []),
        "Finish: " + ", ".join(notes) + f" → `{current.name}`.",
    )


# --- Reel ---


def rebuild_reel_ui(project_name):
    project = load_project(project_name)
    entries = rebuild_from_scenes(project)
    return reel_rows(entries), f"Reel rebuilt from scenes ({len(entries)} row(s))."


def add_shot_to_reel(project_name, shot_choice, status):
    project = load_project(project_name)
    shot_id = _id_from_choice(shot_choice)
    if not shot_id:
        raise gr.Error("Pick a shot.")
    shot = project.load_shot(shot_id)
    clip = None
    for item in project.load_gallery():
        if item.shot_id == shot_id:
            clip = item.path
            break
    entry = ReelEntry(
        id=new_id(),
        order=len(load_reel(project)),
        scene_id=shot.scene_id,
        shot_id=shot_id,
        clip_path=clip,
        dialogue_wav=shot.dialogue_wav,
        status=status or ("generated" if clip else "idea"),
        notes=shot.name,
    )
    entries = add_entry(project, entry)
    return reel_rows(entries), f"Added {shot.name} to the reel."


def set_reel_status(project_name, entry_id, status):
    project = load_project(project_name)
    if not (entry_id or "").strip():
        raise gr.Error("Paste a reel row id.")
    entries = set_status(project, entry_id.strip(), status)
    return reel_rows(entries), f"Set {entry_id} → {status}."


def assemble_reel_ui(project_name, music_choice, include_dialogue, quality=None, lighting=""):
    from film_lab.lighting import expand_lighting, is_lighting_skipped

    project = load_project(project_name)
    music = _resolve_audio_choice(project, music_choice)
    try:
        dest = assemble_reel(project, music_path=music, include_dialogue=bool(include_dialogue))
        dest = _export_scaled(project, dest, quality)
    except Exception as exc:  # noqa: BLE001
        raise gr.Error(str(exc)) from exc
    gallery = gallery_choices(project)
    q = quality or project.quality
    light = expand_lighting(lighting)
    if light and not is_lighting_skipped(lighting):
        project.set_lighting(lighting)
        extra = (
            f" Lighting note **{lighting}** stamped on the project "
            "(Cinema does not re-light clips — bake it on Motion Enhance if you regenerate)."
        )
    else:
        extra = " Lighting skipped (optional)."
    return (
        str(dest),
        str(dest),
        gr.CheckboxGroup(choices=gallery, value=[]),
        reel_rows(load_reel(project)),
        f"Assembled reel → `{dest.name}` at {q}. Per-character dialogue muxed when ticked.{extra} Zero credits.",
    )


# --- Writing Studio ---


def writing_api_markdown() -> str:
    return provider_status_markdown()


def draft_dropdown(project: Project, selected_id: str | None = None) -> gr.Dropdown:
    choices = draft_choices(project)
    value = None
    if selected_id:
        for label in choices:
            if label.startswith(selected_id):
                value = label
                break
    elif choices:
        value = choices[0]
    return gr.Dropdown(choices=choices, value=value)


def _draft_from_form(
    draft_id: str,
    title: str,
    mode: str,
    provider: str,
    dual_roles: str,
    primary_genre: str,
    secondary_genres,
    custom_genre_tags,
    tropes_checklist: str,
    primary_emotion: str,
    secondary_emotion: str,
    emotion_intensity,
    inner_state: str,
    outer_behavior: str,
    relationship_temp: str,
    enabled_senses,
    touch_notes: str,
    smell_notes: str,
    taste_notes: str,
    hearing_notes: str,
    sight_notes: str,
    sensory_pass,
    env_location: str,
    env_time: str,
    env_weather: str,
    env_light: str,
    env_ambient: str,
    env_blocking: str,
    env_props: str,
    live_override,
    live_styles,
    live_custom,
    live_norms,
    live_income,
    live_housing,
    live_privacy,
    live_clean,
    live_hood,
    live_utils,
    live_deps,
    live_work,
    live_health,
    scene_choice: str | None,
    character_ids,
    source: str,
    notes: str,
    tone: str,
    pacing: str,
    intimacy: str,
    intensity_preset: str,
    content_intensity,
    speaker: str,
    body: str,
    system_prompt: str,
    user_prompt: str,
    turns: list | None = None,
) -> WritingDraft:
    ids = []
    for item in character_ids or []:
        ids.append(_id_from_choice(item) if " — " in str(item) else str(item))
    parsed_turns: list[ChatTurn] = []
    for turn in turns or []:
        if isinstance(turn, ChatTurn):
            parsed_turns.append(turn)
        elif isinstance(turn, dict):
            parsed_turns.append(
                ChatTurn(
                    role=str(turn.get("role", "user")),
                    speaker=str(turn.get("speaker", "")),
                    content=str(turn.get("content", "")),
                )
            )
    return WritingDraft(
        id=(draft_id or "").strip() or new_id(),
        title=(title or "").strip() or "Untitled draft",
        mode=mode if mode in WRITING_MODES else "screenplay",
        provider=provider or DEFAULT_PROVIDER,
        dual_roles=dual_roles or DEFAULT_DUAL_ROLES,
        scene_id=_id_from_choice(scene_choice) or None,
        character_ids=ids or ["alison", "bradley"],
        source=source or "",
        notes=notes or "",
        tone=tone or "",
        pacing=pacing or "",
        intimacy_mode=intimacy or "covered sheets",
        intensity_preset=intensity_preset or nearest_intensity_preset(content_intensity),
        content_intensity=clamp_content_intensity(content_intensity, DEFAULT_INTENSITY),
        roleplay_speaker=speaker if speaker in ROLEPLAY_SPEAKERS else "Director",
        primary_genre=(primary_genre or "").strip() or DEFAULT_PRIMARY,
        secondary_genres=list(secondary_genres or []),
        custom_genre_tags=parse_custom_tags(custom_genre_tags),
        tropes_checklist=tropes_checklist or "",
        primary_emotion=primary_emotion or "tenderness",
        secondary_emotion=secondary_emotion or "",
        emotion_intensity=clamp_intensity(emotion_intensity),
        inner_state=inner_state or "",
        outer_behavior=outer_behavior or "",
        relationship_temp=relationship_temp or "newlywed tenderness",
        enabled_senses=parse_enabled_senses(list(enabled_senses or [])),
        touch_notes=touch_notes or "",
        smell_notes=smell_notes or "",
        taste_notes=taste_notes or "",
        hearing_notes=hearing_notes or "",
        sight_notes=sight_notes or "",
        sensory_pass=bool(sensory_pass),
        env_location=env_location or "",
        env_time=env_time or "",
        env_weather=env_weather or "",
        env_light=env_light or "",
        env_ambient=env_ambient or "",
        env_blocking=env_blocking or "",
        env_props=env_props or "",
        living=living_from_form(
            live_override, live_styles, live_custom, live_norms, live_income, live_housing,
            live_privacy, live_clean, live_hood, live_utils, live_deps, live_work, live_health,
        ).to_dict(),
        living_override=bool(live_override),
        body=body or "",
        system_prompt=system_prompt or "",
        user_prompt=user_prompt or "",
        turns=parsed_turns,
    )


def _guard_draft(draft: WritingDraft) -> str:
    try:
        return check_genre_intimacy(
            draft.primary_genre,
            draft.secondary_genres,
            draft.custom_genre_tags,
            draft.intimacy_mode,
            draft.title,
            draft.source,
            draft.notes,
            draft.tropes_checklist,
            draft.body,
            content_intensity=draft.content_intensity,
        )
    except GenreGuardError as exc:
        raise gr.Error(str(exc)) from exc


def examples_dropdown(primary: str | None, secondary=None, selected: str | None = None):
    """Update example-prompt choices without replacing the widget.

    Returning a brand-new Dropdown can land on a sibling dropdown in Gradio
    (the room-preset list is the next one in the Writing tab). ``gr.update``
    keeps the target stable. ``allow_custom_value`` stops a stale sentence
    from crashing preprocess when the genre filter changes.
    """
    choices = examples_for(primary, list(secondary or []))
    value = selected if selected in choices else (choices[0] if choices else None)
    return gr.update(choices=choices, value=value, label="Example prompts (filtered by genre)")


def apply_genre_preset_ui(primary, secondary):
    preset = preset_for(primary, list(secondary or []))
    note = ""
    try:
        note = check_genre_intimacy(primary, list(secondary or []), [], "covered sheets")
    except GenreGuardError as exc:
        raise gr.Error(str(exc)) from exc
    hint = f"Applied genre preset for **{primary or DEFAULT_PRIMARY}**."
    if note:
        hint += f" {note}"
    return (
        preset["tone"],
        preset["pacing"],
        preset["tropes"],
        examples_dropdown(primary, secondary),
        hint,
    )


def filter_genre_examples_ui(primary, secondary):
    return examples_dropdown(primary, secondary)


def _living_preset_label(raw) -> str:
    if isinstance(raw, (list, tuple)) and raw:
        raw = raw[0]
    text = str(raw or "").strip()
    return text if text in LIVING_PRESET_LABELS else DEFAULT_LIVING_PRESET


def _ui_value(value):
    """Keep the target widget; do not reconstruct siblings (Gradio 5)."""
    return gr.update(value=value)


def living_ui_updates(brief: LivingBrief) -> tuple:
    return tuple(_ui_value(item) for item in living_to_ui(brief))


def apply_living_preset_ui(preset_label):
    spec = living_preset(_living_preset_label(preset_label))
    brief = LivingBrief.from_dict(spec.brief.to_dict())
    brief.override = True
    hint = (
        f"Applied **{spec.label}**. Override is on so this nest injects. "
        "Environment fields updated to match the nest."
    )
    return (
        *living_ui_updates(brief),
        _ui_value(spec.env_location or ""),
        _ui_value(spec.env_light or ""),
        _ui_value(spec.env_ambient or ""),
        _ui_value(spec.env_blocking or ""),
        _ui_value(spec.env_props or ""),
        hint,
    )


def _guard_explicit_adults(project_name: str, intensity, intimacy, character_ids=None) -> None:
    from film_lab.director_notes import EXPLICIT_INTENSITY_MIN, assert_notes_safe, load_notes

    try:
        value = float(intensity or 0)
    except (TypeError, ValueError):
        value = 0.0
    if value < EXPLICIT_INTENSITY_MIN and not notes_need_adult_local(intimacy, value):
        return
    project = load_project(project_name)
    notes = load_notes(project)
    assert_notes_safe(
        project,
        notes,
        intimacy=intimacy or "",
        intensity=value,
        context="explicit intensity dial",
    )
    ids = []
    for item in character_ids or []:
        ids.append(_id_from_choice(item) if " — " in str(item) else str(item))
    profiles = matching_characters(
        project,
        ShotCard(character_ids=ids or list(project.active_cast or [])),
    )
    if not profiles:
        profiles = load_selected_characters(project, ids or list(project.active_cast or []))
    from film_lab.filming import FilmingError, assert_filming_safe

    try:
        assert_filming_safe(
            getattr(project, "filming_mode", None),
            profiles,
            intimacy=intimacy or "",
            intensity=value,
            context="explicit intensity dial",
        )
        assert_adult_cast(
            profiles,
            intimacy_mode=intimacy or "",
            content_intensity=value,
            context="explicit intensity dial",
        )
    except FilmingError as exc:
        raise CharacterError(str(exc)) from exc


def notes_need_adult_local(intimacy, intensity) -> bool:
    from film_lab.director_notes import notes_need_adult

    return notes_need_adult(intimacy, intensity)


def apply_intensity_preset_ui(preset, project_name=None, intimacy="", character_ids=None):
    value = preset_to_intensity(preset)
    if project_name:
        try:
            _guard_explicit_adults(project_name, value, intimacy, character_ids)
        except (DirectorNoteError, CharacterError) as exc:
            raise gr.Error(str(exc)) from exc
    return value


def _shot_from_clip_path(project: Project, path: str):
    if not path:
        return None
    try:
        resolved = Path(path).resolve()
    except OSError:
        return None
    for clip in project.load_gallery():
        try:
            if Path(clip.path).resolve() != resolved:
                continue
        except OSError:
            continue
        if not clip.shot_id:
            return None
        try:
            return project.load_shot(clip.shot_id)
        except (OSError, ValueError, FileNotFoundError):
            return None
    return None


def _direct_chrome(mode: str, *, player=None, frame=None, toast="", status="", source=None):
    look = playback_chrome(mode)
    return (
        open_hub_tab("takes"),
        player,
        look["mode"],
        look["banner"],
        look["help"],
        gr.update(visible=look["panel"]),
        gr.update(visible=look["enter"]),
        gr.update(visible=look["exit"]),
        frame,
        toast,
        status,
        source if source is not None else gr.update(),
    )


def play_take_ui(project_name: str, evt: gr.SelectData):
    """Click a take → PLAYBACK only. Pause freezes. It does not edit."""
    project = load_project(project_name)
    items = take_gallery_items(project)
    if not items:
        msg = "No takes yet. Animate first, then click a take to play."
        return _direct_chrome(
            MODE_PLAYBACK,
            player=None,
            frame=None,
            toast=toast_html(msg),
            status=msg,
            source=shot_dropdown(project),
        )
    picked = pick_gallery_item(items, getattr(evt, "index", 0))
    path, caption = picked if picked else items[0]
    clip_shot = _shot_from_clip_path(project, path)
    msg = (
        f"Playing `{caption}`. Pause freezes. It does not edit. "
        "Mark & Direct · Fix this frame."
    )
    return _direct_chrome(
        MODE_PLAYBACK,
        player=path,
        frame=None,
        toast="",
        status=msg,
        source=shot_dropdown(project, clip_shot.id if clip_shot else None),
    )


def enter_direct_ui(project_name: str, clip, seconds=0.0):
    """Only Mark & Direct enters Direct. Pause never does this."""
    project = load_project(project_name)
    path = clip_path(clip)
    try:
        frame = freeze_at(project, path, seconds)
    except FileNotFoundError as exc:
        msg = str(exc)
        return _direct_chrome(
            MODE_PLAYBACK,
            player=path or None,
            frame=None,
            toast=toast_html(msg),
            status=msg,
        )
    mode = enter_direct()
    return _direct_chrome(
        mode,
        player=path,
        frame=frame,
        toast="",
        status=(
            "Directing — changes will make a new take. "
            "Pause or scrub, mark the region, note, Apply / Regenerate."
        ),
    )


def freeze_direct_ui(project_name: str, clip, seconds=0.0):
    """Pull the marked second. Does not run while only paused in Playback."""
    project = load_project(project_name)
    path = clip_path(clip)
    try:
        frame = freeze_at(project, path, seconds)
    except FileNotFoundError as exc:
        return None, toast_html(str(exc)), str(exc)
    msg = f"Frame at {float(seconds or 0):.1f}s ready to mark. Circle / square / lasso, then note."
    return frame, "", msg


def exit_direct_ui(project_name: str, clip):
    """Leave Direct. Playback again. The old take stays on the board."""
    del project_name
    path = clip_path(clip)
    msg = "Back to Playback. The old take stays on the board. Pause still does not edit."
    return _direct_chrome(
        exit_direct(),
        player=path or None,
        frame=None,
        toast="",
        status=msg,
    )


def apply_take_mark_ui(
    project_name: str,
    still,
    clip,
    editor,
    shape: str,
    cx,
    cy,
    size,
    target: str,
    note: str,
    prop_action: str,
    idea: str,
    intimacy: str,
    intensity,
):
    """Apply a region on the Take Board Direct frame. Does not jump desks."""
    marked, _md, preview, _mk, folded, _s1, _s2, md, toast, msg = apply_mark_ui(
        project_name,
        still,
        clip,
        editor,
        shape,
        cx,
        cy,
        size,
        target,
        note,
        prop_action,
        idea,
        intimacy,
        intensity,
    )
    frame = marked if marked else gr.update()
    shown = preview if preview else marked
    from film_lab.dream import dream_markdown, load_dream

    dream_md = dream_markdown(load_dream(load_project(project_name)))
    return frame, shown, folded, md, toast, msg, dream_md


def _maybe_enter_dream_from_mark(
    project,
    source,
    target: str,
    note: str,
    *,
    intimacy: str = "",
    intensity=0,
    cx=0.50,
    cy=0.28,
) -> str:
    from film_lab.dream import DreamError, enter_dream, is_enter_dream
    from film_lab.project import VIDEO_SUFFIXES

    if not is_enter_dream(target, note):
        return ""
    path = Path(str(source))
    clip = str(path) if path.suffix.lower() in VIDEO_SUFFIXES else ""
    still = str(path) if not clip else ""
    try:
        enter_dream(
            project,
            parent_clip=clip,
            parent_still=still,
            sleeper_id=(project.active_cast or ["alison"])[0],
            character_ids=list(project.active_cast or []),
            intimacy=intimacy or "",
            intensity=intensity or 0,
            cx=float(cx or 0.50),
            cy=float(cy or 0.28),
        )
    except (DreamError, CharacterError) as exc:
        return f" {exc}"
    return (
        " Dream take opened. Linked child scenes on Take Board "
        "(sleep → dream → wake). Mark head = Enter dream."
    )


def head_note_hint_ui(target, note):
    from film_lab.dream import hint_head_note

    return hint_head_note(target, note)


def _dream_cast_ids(cast_ids) -> list[str]:
    ids: list[str] = []
    for item in cast_ids or []:
        ids.append(_id_from_choice(item) if " — " in str(item) else str(item))
    return [i for i in ids if i]


def _parent_from_player(still, clip) -> tuple[str, str]:
    from film_lab.playback import clip_path as _clip

    paths = _as_paths(still) + _as_paths(clip)
    video = _clip(clip) if clip else ""
    if video and Path(video).is_file():
        paths.append(Path(video))
    parent_clip = ""
    parent_still = ""
    for path in paths:
        suffix = path.suffix.lower()
        if suffix in {".mp4", ".webm", ".mov", ".mkv"} and not parent_clip:
            parent_clip = str(path)
        elif not parent_still:
            parent_still = str(path)
    return parent_clip, parent_still


def _dream_open_msg(layer) -> str:
    n = len(getattr(layer, "children", []) or [])
    who = getattr(layer, "sleeper_id", "") or "the sleeper"
    vision = getattr(layer, "inner_vision", "dream") or "dream"
    text = getattr(layer, "text_style", "none") or "none"
    if getattr(layer, "presentation", "") == "thought bubble":
        return (
            f"Thought bubble on the sleeping shot ({vision}; {text}). "
            f"{n} layer(s) + wake under {who}. "
            "Still, mini-clip, or styled text stays over the sleeper. "
            "Inspired-only original characters."
        )
    return (
        f"Enter dream — they are inside the {vision} sequence under {who}: "
        f"{n} layer(s) + wake. Animate the DREAM cards, then Stitch sleep → dream → wake. "
        "Inspired-only original characters."
    )


def open_dream_about_ui(
    project_name: str,
    evt: gr.SelectData,
    clip=None,
    presentation=None,
    vision=None,
    text_style=None,
):
    """Pause a take, click the person → Dream about… popup."""
    from film_lab.director_notes import list_cast_faces
    from film_lab.dream import (
        bible_actor_labels,
        dream_about_heading,
        normalize_presentation,
        normalize_text_style,
        normalize_vision,
        steps_markdown,
    )
    from film_lab.playback import clip_path as _clip

    project = load_project(project_name)
    faces = list_cast_faces(project)
    labels = bible_actor_labels(project)
    empty_cast = gr.update(choices=labels, value=[])
    style = normalize_presentation(presentation)
    inner = normalize_vision(vision)
    text = normalize_text_style(text_style)
    if not faces:
        msg = "No Character Bible faces yet. Add Alison / Bradley or a new adult."
        return (
            gr.update(visible=False),
            "",
            "### Dream about…",
            "",
            empty_cast,
            [],
            steps_markdown([]),
            "Beat 1 — first dream layer",
            "",
            "",
            style,
            inner,
            text,
            msg,
        )
    idx = getattr(evt, "index", 0)
    if isinstance(idx, (list, tuple)):
        idx = idx[0] if idx else 0
    try:
        idx = int(idx or 0)
    except (TypeError, ValueError):
        idx = 0
    face = faces[max(0, min(idx, len(faces) - 1))]
    playing = _clip(clip) if clip else ""
    hint = (
        f"Dream about {face.name}. Pick Dream style (Enter dream or Thought bubble), "
        "Actor A / B / C, type the dream, add layers one by one, drop image or video "
        "look-refs, then Open dream sequence."
    )
    if not playing:
        hint += " Pause a sleeping take first so the sequence links under this sleeper."
    defaults = [lab for lab in labels if not lab.startswith(f"{face.id} —")]
    return (
        gr.update(visible=True),
        face.id,
        dream_about_heading(face.name),
        "",
        gr.update(choices=labels, value=defaults or labels),
        [],
        steps_markdown([]),
        "Beat 1 — first dream layer",
        "",
        "",
        style,
        inner,
        text,
        hint,
    )


def close_dream_about_ui():
    return gr.update(visible=False)


def add_dream_step_ui(steps, title, prompt, about):
    from film_lab.dream import normalize_steps, steps_markdown, title_from_chunk

    text = (prompt or "").strip() or (about or "").strip()
    name = (title or "").strip() or title_from_chunk(text)
    if not text:
        return (
            steps or [],
            steps_markdown(steps),
            "Beat 1 — type the layer first",
            title or "",
            prompt or "",
            "Type this dream layer (or Dream about…), then Add this beat.",
        )
    rows = normalize_steps(steps)
    rows.append({"title": name, "prompt": text})
    nxt = len(rows) + 1
    return (
        rows,
        steps_markdown(rows),
        f"Beat {nxt} — next dream layer",
        "",
        "",
        f"Added layer {len(rows)}: {name}. Add another, or Open dream sequence.",
    )


def open_dream_sequence_ui(
    project_name: str,
    still,
    clip,
    sleeper,
    about,
    cast_ids,
    refs,
    steps,
    presentation,
    vision,
    text_style,
    intimacy,
    intensity,
):
    from film_lab.dream import (
        DreamError,
        dream_board_items,
        dream_markdown,
        enter_dream,
        persist_look_refs,
    )

    project = load_project(project_name)
    parent_clip, parent_still = _parent_from_player(still, clip)
    shot = _shot_from_clip_path(project, parent_clip)
    look = persist_look_refs(project, refs)
    try:
        layer = enter_dream(
            project,
            parent_clip=parent_clip,
            parent_still=parent_still,
            parent_shot_id=shot.id if shot else "",
            sleeper_id=_id_from_choice(sleeper) or (sleeper or ""),
            about=about or "",
            steps=steps,
            look_refs=look,
            character_ids=_dream_cast_ids(cast_ids),
            presentation=presentation or "",
            inner_vision=vision or "",
            text_style=text_style or "",
            intimacy=intimacy or "",
            intensity=intensity or 0,
        )
    except (DreamError, CharacterError) as exc:
        from film_lab.dream import load_dream

        msg = str(exc)
        return (
            gr.update(visible=True),
            dream_markdown(load_dream(project)),
            dream_board_items(project),
            take_gallery_items(project),
            None,
            toast_html(msg),
            msg,
            open_hub_tab("takes"),
        )
    bubble = layer.bubble_still if layer.bubble_still and Path(layer.bubble_still).is_file() else None
    msg = _dream_open_msg(layer)
    return (
        gr.update(visible=False),
        dream_markdown(layer),
        dream_board_items(project),
        take_gallery_items(project),
        bubble,
        "",
        msg,
        open_hub_tab("takes"),
    )


def play_dream_seq_ui(project_name: str, evt: gr.SelectData):
    """Click a SLEEP / DREAM / WAKE card. Video plays. Still → Motion to Animate."""
    from film_lab.dream import dream_board_items
    from film_lab.project import VIDEO_SUFFIXES
    from film_lab.playback import pick_gallery_item

    project = load_project(project_name)
    items = dream_board_items(project)
    picked = pick_gallery_item(items, getattr(evt, "index", 0))
    if not picked:
        msg = "No dream sequence yet. Pause a take, click the person, Dream about…"
        return None, None, "", ref_chip_html(""), open_hub_tab("takes"), toast_html(msg), msg
    path, label = picked
    suffix = Path(path).suffix.lower()
    if suffix in VIDEO_SUFFIXES or suffix in {".mkv"}:
        msg = f"Playing `{label}`. Pause never edits. Animate missing layers on Motion Desk."
        return path, None, "", ref_chip_html(""), open_hub_tab("takes"), "", msg
    from film_lab.dream import load_dream

    layer = load_dream(project)
    bubble = (layer.bubble_still or "").strip()
    clip = (layer.bubble_clip or "").strip()
    if bubble and clip and Path(clip).is_file():
        try:
            same = Path(path).resolve() == Path(bubble).resolve()
        except OSError:
            same = Path(path) == Path(bubble)
        if same:
            msg = "Playing thought-bubble mini-clip on the sleeping shot."
            return clip, None, "", ref_chip_html(""), open_hub_tab("takes"), "", msg
    msg = (
        f"`{label}` is a dream layer still. Animate it on Motion Desk, "
        "then Stitch sleep → dream → wake."
    )
    return (
        None,
        path,
        path,
        ref_chip_html(path),
        open_hub_tab("motion"),
        "",
        msg,
    )


def enter_dream_ui(
    project_name: str,
    still,
    clip,
    sleeper,
    titles,
    cast_ids,
    presentation,
    vision,
    text_style,
    intimacy,
    intensity,
):
    from film_lab.dream import (
        DreamError,
        dream_board_items,
        dream_markdown,
        enter_dream,
        parse_dream_titles,
    )

    project = load_project(project_name)
    parent_clip, parent_still = _parent_from_player(still, clip)
    shot = _shot_from_clip_path(project, parent_clip)
    ids = _dream_cast_ids(cast_ids)
    try:
        layer = enter_dream(
            project,
            parent_clip=parent_clip,
            parent_still=parent_still,
            parent_shot_id=shot.id if shot else "",
            sleeper_id=_id_from_choice(sleeper) or (sleeper or ""),
            titles=parse_dream_titles(titles),
            character_ids=ids,
            presentation=presentation or "",
            inner_vision=vision or "",
            text_style=text_style or "",
            intimacy=intimacy or "",
            intensity=intensity or 0,
        )
    except (DreamError, CharacterError) as exc:
        from film_lab.dream import load_dream

        msg = str(exc)
        return (
            dream_markdown(load_dream(project)),
            None,
            take_gallery_items(project),
            dream_board_items(project),
            toast_html(msg),
            msg,
            open_hub_tab("takes"),
        )
    bubble = layer.bubble_still if layer.bubble_still and Path(layer.bubble_still).is_file() else None
    msg = _dream_open_msg(layer)
    return (
        dream_markdown(layer),
        bubble,
        take_gallery_items(project),
        dream_board_items(project),
        "",
        msg,
        open_hub_tab("takes"),
    )


def fill_dream_sheet_ui(project_name, sleeper, titles, cast_ids, notes):
    from film_lab.dream import INSPIRED_LINE, dream_beat_sheet, parse_dream_titles

    project = load_project(project_name)
    ids = []
    for item in cast_ids or []:
        ids.append(_id_from_choice(item) if " — " in str(item) else str(item))
    body = dream_beat_sheet(
        project,
        sleeper_id=_id_from_choice(sleeper) or (sleeper or ""),
        titles=parse_dream_titles(titles),
        character_ids=ids,
    )
    merged = (notes or "").strip()
    if INSPIRED_LINE not in merged:
        merged = f"{INSPIRED_LINE}\n{merged}".strip()
    return (
        body,
        "director_rewrite",
        merged,
        "Dream beat sheet filled (director rewrite — not a sixth mode). "
        "Edit, then Plan dream shots. Inspired-only original characters.",
    )


def plan_dream_shots_ui(
    project_name,
    title,
    body,
    sleeper,
    titles,
    character_ids,
    intimacy,
    content_intensity,
):
    from film_lab.dream import (
        dream_beat_sheet,
        dream_board_items,
        dream_markdown,
        link_planned_shots,
        load_dream,
        parse_dream_titles,
        save_dream,
    )
    from film_lab.variations import take_gallery_items as _takes

    project = load_project(project_name)
    ids = []
    for item in character_ids or []:
        ids.append(_id_from_choice(item) if " — " in str(item) else str(item))
    pages = (body or "").strip()
    if not pages:
        pages = dream_beat_sheet(
            project,
            sleeper_id=_id_from_choice(sleeper) or (sleeper or ""),
            titles=parse_dream_titles(titles),
            character_ids=ids,
        )
    try:
        _guard_explicit_adults(project_name, content_intensity, intimacy, character_ids)
    except (DirectorNoteError, CharacterError) as exc:
        raise gr.Error(str(exc)) from exc
    try:
        shots = push_pages_to_shots(
            project,
            pages,
            title=title or "Dream",
            character_ids=ids,
            intimacy=intimacy,
            intensity=content_intensity,
        )
    except FuseError as exc:
        raise gr.Error(str(exc)) from exc
    layer = load_dream(project)
    layer = link_planned_shots(
        layer,
        shots,
        sleeper_id=_id_from_choice(sleeper) or layer.sleeper_id,
    )
    save_dream(project, layer)
    first = shots[0]
    hint = (
        f"Dream shots: {len(shots)} cards linked as child scenes. "
        f"First `{first.id}` — {first.name}. Animate, then Stitch sleep → dream → wake. "
        "Inspired-only original characters. Zero credits."
    )
    dd = shot_dropdown(project, first.id)
    return (
        dd,
        dd,
        _takes(project),
        dream_board_items(project),
        dream_markdown(layer),
        pages,
        "director_rewrite",
        open_hub_tab("takes"),
        hint,
    )


def stitch_dream_ui(project_name: str):
    from film_lab.dream import (
        DreamError,
        dream_board_items,
        dream_markdown,
        load_dream,
        stitch_dream_reel,
    )
    from film_lab.variations import take_gallery_items as _takes

    project = load_project(project_name)
    layer = load_dream(project)
    seq = dream_board_items(project)
    try:
        dest = stitch_dream_reel(project, layer)
    except DreamError as exc:
        msg = str(exc)
        return None, _takes(project), seq, dream_markdown(layer), toast_html(msg), msg
    except Exception as exc:  # noqa: BLE001
        msg = str(exc)
        return None, _takes(project), seq, dream_markdown(layer), toast_html(msg), msg
    msg = (
        f"Stitched sleep → dream → wake → `{dest.name}`. "
        "Inspired-only original characters. Zero credits."
    )
    return (
        str(dest),
        _takes(project),
        dream_board_items(project),
        dream_markdown(load_dream(project)),
        "",
        msg,
    )


def regenerate_direct_now(
    project_name: str,
    idea: str,
    enhance_family: str,
    enhance_model: str,
    video_family: str,
    video_model: str,
    image_family: str,
    image_model: str,
    duration_preset: str,
    quality: str,
    attached_ref: str,
    feed_history,
    take_clip,
    mark_frame,
    *form,
):
    """Direct Regenerate — fork a new take. Old clip stays on the board."""
    project = load_project(project_name)
    path = clip_path(take_clip)
    values = list(form)
    shot = _shot_from_clip_path(project, path)
    if shot:
        packed = list(form_from_card(shot, project)[:25])
        still = values[25] if len(values) > 25 else None
        values = packed + [still]
    frames = _as_paths(mark_frame)
    if frames:
        if len(values) > 25:
            values[25] = str(frames[0])
        else:
            values.append(str(frames[0]))
    if not path and not frames:
        pack = _motion_pack(
            project,
            shot or ShotCard(),
            overlay=False,
            toast=toast_html(
                "Play a take, press Mark & Direct, then Apply / Regenerate. "
                "Pause alone does not edit."
            ),
            status="Play a take first, then Mark & Direct.",
            feed_history=[t for t in (feed_history or []) if isinstance(t, dict)],
            ref_chip=ref_chip_html(attached_ref or ""),
        )
        yield (*pack, path or None, open_hub_tab("takes"))
        return
    for pack in regenerate_motion_now(
        project_name,
        idea,
        enhance_family,
        enhance_model,
        video_family,
        video_model,
        image_family,
        image_model,
        duration_preset,
        quality,
        attached_ref,
        feed_history,
        *values,
    ):
        video = pack[1]
        yield (*pack, video, open_hub_tab("takes"))


def open_take_loop_ui(project_name: str, evt: gr.SelectData):
    """Motion gallery only — Director Note + Pose. Not Take Board play."""
    project = load_project(project_name)
    items = take_gallery_items(project)
    if not items:
        msg = "No takes yet. Animate first, then click the take."
        return (
            open_hub_tab("motion"),
            gr.update(),
            None,
            "",
            ref_chip_html(""),
            gr.update(visible=False),
            "",
            "### Director Note",
            DEFAULT_EMOTION,
            "",
            DEFAULT_WARDROBE,
            DEFAULT_MICRO,
            DEFAULT_BEHAVIOR,
            toast_html(msg),
            msg,
            shot_dropdown(project),
        )
    idx = getattr(evt, "index", 0)
    if isinstance(idx, (list, tuple)):
        idx = idx[0] if idx else 0
    try:
        idx = int(idx or 0)
    except (TypeError, ValueError):
        idx = 0
    path, caption = items[max(0, min(idx, len(items) - 1))]
    return _load_take_for_revise(project, path, caption)


def revise_current_take_ui(project_name: str, video_path, shot_id: str):
    project = load_project(project_name)
    path = ""
    if video_path:
        raw = video_path
        if isinstance(raw, dict):
            raw = raw.get("path") or raw.get("name") or ""
        path = str(raw or "")
    if not path or not Path(path).is_file():
        msg = "Animate a take first, then click it to revise."
        return (
            open_hub_tab("motion"),
            gr.update(),
            None,
            "",
            ref_chip_html(""),
            gr.update(visible=True),
            "",
            "### Director Note",
            DEFAULT_EMOTION,
            "",
            DEFAULT_WARDROBE,
            DEFAULT_MICRO,
            DEFAULT_BEHAVIOR,
            toast_html(msg),
            msg,
            shot_dropdown(project, shot_id),
        )
    caption = shot_id or Path(path).name
    return _load_take_for_revise(project, path, caption)


def _load_take_for_revise(project: Project, path: str, caption: str):
    clip_shot = None
    for clip in project.load_gallery():
        if Path(clip.path).resolve() == Path(path).resolve():
            if clip.shot_id:
                try:
                    clip_shot = project.load_shot(clip.shot_id)
                except (OSError, ValueError, FileNotFoundError):
                    clip_shot = None
            break
    still = None
    if clip_shot and clip_shot.start_frame:
        resolved = project.resolve_still(clip_shot.start_frame)
        still = str(resolved) if resolved else None
    faces = list_cast_faces(project)
    notes = load_notes(project)
    face = faces[0] if faces else None
    if face and notes.director:
        picked = next((f for f in faces if f.id in notes.director), face)
        face = picked
    existing = notes.director.get(face.id) if face else None
    title = (
        f"### Director Note — {face.name}\nRevise this take: performance + wardrobe through motion."
        if face
        else "### Director Note"
    )
    msg = (
        f"Take `{caption}` loaded. Edit Director Note and Pose adjust, then "
        f"**Regenerate** — the old take stays on Take Board. {SAFETY_LINE}"
    )
    return (
        open_hub_tab("motion"),
        gr.update(value=path, visible=True),
        still,
        still or "",
        ref_chip_html(still or ""),
        gr.update(visible=True),
        face.id if face else "",
        title,
        existing.emotion if existing else DEFAULT_EMOTION,
        existing.acting_beats if existing else "",
        existing.wardrobe_motion if existing else DEFAULT_WARDROBE,
        existing.micro_expression if existing else DEFAULT_MICRO,
        existing.behavior if existing else DEFAULT_BEHAVIOR,
        "",
        msg,
        shot_dropdown(project, clip_shot.id if clip_shot else None),
    )


def inherit_living_ui(project_name, character_ids, scene_choice):
    project = load_project(project_name)
    ids = []
    for item in character_ids or []:
        ids.append(_id_from_choice(item) if " — " in str(item) else str(item))
    scene_living = None
    sid = _id_from_choice(scene_choice)
    if sid:
        try:
            scene_living = load_scene(project, sid).living_brief()
        except (OSError, ValueError, FileNotFoundError):
            scene_living = None
    nest = resolved_living(project, ids or ["alison", "bradley"], scene_living=scene_living)
    nest.override = False
    return (
        *living_ui_updates(nest),
        f"Inherited nest from bible / scene / project: **{nest.style_line()}**.",
    )


def apply_char_living_preset_ui(preset_label):
    label = _living_preset_label(preset_label)
    brief = living_preset_brief(label)
    return (*living_ui_updates(brief)[1:], f"Applied **{label}** to this character.")


def insert_genre_example_ui(example, source):
    seed = (example or "").strip()
    if not seed:
        return source or ""
    existing = source or ""
    if seed in existing:
        return existing
    return (existing.rstrip() + "\n\n" + seed).strip()


def _brief_to_ui(brief: SensoryBrief) -> tuple:
    return (
        brief.primary_emotion,
        brief.secondary_emotion,
        brief.intensity,
        brief.inner_state,
        brief.outer_behavior,
        brief.relationship_temp,
        sense_labels_for(brief.enabled_senses),
        brief.touch_notes,
        brief.smell_notes,
        brief.taste_notes,
        brief.hearing_notes,
        brief.sight_notes,
        brief.sensory_pass,
        brief.location,
        brief.time_of_day,
        brief.weather,
        brief.light,
        brief.ambient_sound,
        brief.blocking,
        brief.props,
    )


def apply_sense_preset_ui(preset_label):
    label = preset_label if preset_label in PRESET_LABELS else DEFAULT_SENSE_PRESET
    brief = preset_brief(label)
    hint = (
        f"Applied **{label}**. Emotion, senses, and environment are filled — edit anything. "
        "Genre stays as you set it. Sensory pass is on for this preset."
    )
    return (*_brief_to_ui(brief), hint)


def _pack_from_draft(project, draft):
    return build_prompt_pack(
        project,
        mode=draft.mode,
        source=draft.source,
        notes=draft.notes,
        scene_id=draft.scene_id,
        character_ids=draft.character_ids,
        tone=draft.tone,
        pacing=draft.pacing,
        intimacy_mode=draft.intimacy_mode,
        intensity_preset=draft.intensity_preset,
        content_intensity=draft.content_intensity,
        roleplay_speaker=draft.roleplay_speaker,
        turns=draft.turns,
        primary_genre=draft.primary_genre,
        secondary_genres=draft.secondary_genres,
        custom_genre_tags=draft.custom_genre_tags,
        tropes_checklist=draft.tropes_checklist,
        sensory=draft.sensory_brief(),
        living=draft.living_brief(),
    )


def _chatbot_from_turns(turns: list[ChatTurn]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for turn in turns:
        role = "assistant" if turn.role == "assistant" else "user"
        label = f"**{turn.speaker}.** " if turn.speaker else ""
        rows.append({"role": role, "content": label + turn.content})
    return rows


def pull_scene_into_writing(project_name: str, scene_choice: str):
    project = load_project(project_name)
    sid = _id_from_choice(scene_choice)
    if not sid:
        raise gr.Error("Pick a scene on the Script desk first.")
    scene = load_scene(project, sid)
    fountain = scene.to_fountain(title=project.name)
    primary = scene.primary_genre or DEFAULT_PRIMARY
    secondary = list(scene.secondary_genres)
    return (
        fountain,
        scene.director_notes,
        primary,
        secondary,
        join_custom_tags(scene.custom_genre_tags),
        scene.tropes_checklist,
        examples_dropdown(primary, secondary),
        f"Loaded `{scene.heading}` into the writing source. Genre: {primary}.",
    )


def build_writing_prompt_ui(
    project_name,
    draft_id,
    title,
    mode,
    provider,
    dual_roles,
    primary_genre,
    secondary_genres,
    custom_genre_tags,
    tropes_checklist,
    primary_emotion,
    secondary_emotion,
    emotion_intensity,
    inner_state,
    outer_behavior,
    relationship_temp,
    enabled_senses,
    touch_notes,
    smell_notes,
    taste_notes,
    hearing_notes,
    sight_notes,
    sensory_pass,
    env_location,
    env_time,
    env_weather,
    env_light,
    env_ambient,
    env_blocking,
    env_props,
    live_override,
    live_styles,
    live_custom,
    live_norms,
    live_income,
    live_housing,
    live_privacy,
    live_clean,
    live_hood,
    live_utils,
    live_deps,
    live_work,
    live_health,
    scene_choice,
    character_ids,
    source,
    notes,
    tone,
    pacing,
    intimacy,
    intensity_preset,
    content_intensity,
    speaker,
    body,
    history,
):
    project = load_project(project_name)
    draft = _draft_from_form(
        draft_id, title, mode, provider, dual_roles, primary_genre, secondary_genres, custom_genre_tags, tropes_checklist,
        primary_emotion, secondary_emotion, emotion_intensity, inner_state, outer_behavior, relationship_temp,
        enabled_senses, touch_notes, smell_notes, taste_notes, hearing_notes, sight_notes,
        sensory_pass, env_location, env_time, env_weather, env_light, env_ambient, env_blocking, env_props,
        live_override, live_styles, live_custom, live_norms, live_income, live_housing, live_privacy,
        live_clean, live_hood, live_utils, live_deps, live_work, live_health,
        scene_choice, character_ids, source, notes,
        tone, pacing, intimacy, intensity_preset, content_intensity, speaker, body, "", "", history,
    )
    note = _guard_draft(draft)
    try:
        system, user = _pack_from_draft(project, draft)
    except (GenreGuardError, CharacterError) as exc:
        raise gr.Error(str(exc)) from exc
    draft.system_prompt = system
    draft.user_prompt = user
    save_draft(project, draft)
    state, _ = probe_writing_api()
    hint = (
        f"Prompt pack built and saved as `{draft.id}`. API **{state}**. "
        + (API_LEAVE_NOTICE if state == "Ready" else "Paste a draft from chat, or set a key to generate.")
    )
    if note:
        hint += f" {note}"
    return draft.id, system, user, draft_dropdown(project, draft.id), hint


def generate_writing_ui(
    project_name,
    draft_id,
    title,
    mode,
    provider,
    dual_roles,
    primary_genre,
    secondary_genres,
    custom_genre_tags,
    tropes_checklist,
    primary_emotion,
    secondary_emotion,
    emotion_intensity,
    inner_state,
    outer_behavior,
    relationship_temp,
    enabled_senses,
    touch_notes,
    smell_notes,
    taste_notes,
    hearing_notes,
    sight_notes,
    sensory_pass,
    env_location,
    env_time,
    env_weather,
    env_light,
    env_ambient,
    env_blocking,
    env_props,
    live_override,
    live_styles,
    live_custom,
    live_norms,
    live_income,
    live_housing,
    live_privacy,
    live_clean,
    live_hood,
    live_utils,
    live_deps,
    live_work,
    live_health,
    scene_choice,
    character_ids,
    source,
    notes,
    tone,
    pacing,
    intimacy,
    intensity_preset,
    content_intensity,
    speaker,
    body,
    history,
    rp_line,
    api_model="",
):
    project = load_project(project_name)
    turns = list(history or [])
    if mode == "roleplay" and (rp_line or "").strip():
        turns.append(ChatTurn(role="user", speaker=speaker or "Director", content=rp_line.strip()))
    draft = _draft_from_form(
        draft_id, title, mode, provider, dual_roles, primary_genre, secondary_genres, custom_genre_tags, tropes_checklist,
        primary_emotion, secondary_emotion, emotion_intensity, inner_state, outer_behavior, relationship_temp,
        enabled_senses, touch_notes, smell_notes, taste_notes, hearing_notes, sight_notes,
        sensory_pass, env_location, env_time, env_weather, env_light, env_ambient, env_blocking, env_props,
        live_override, live_styles, live_custom, live_norms, live_income, live_housing, live_privacy,
        live_clean, live_hood, live_utils, live_deps, live_work, live_health,
        scene_choice, character_ids, source, notes,
        tone, pacing, intimacy, intensity_preset, content_intensity, speaker, body, "", "", turns,
    )
    route = resolve_text_pick(provider_to_family(draft.provider), api_model)
    draft.api_model = route.api_id
    note = _guard_draft(draft)
    try:
        system, user = _pack_from_draft(project, draft)
    except (GenreGuardError, CharacterError) as exc:
        raise gr.Error(str(exc)) from exc
    draft.system_prompt = system
    draft.user_prompt = user
    prov = draft.provider
    dual_gap = dual_missing_keys(draft.dual_roles) if prov == PROVIDER_DUAL else []
    missing = (
        (prov == PROVIDER_GROK and not get_xai_key())
        or (prov == PROVIDER_GEMINI and not get_gemini_key())
        or (prov == PROVIDER_OPENAI and not get_openai_key())
        or (prov == PROVIDER_CLAUDE and not get_anthropic_key())
        or (prov == PROVIDER_DUAL and bool(dual_gap))
    )
    if missing:
        save_draft(project, draft)
        if prov == PROVIDER_DUAL:
            hint = (
                "Dual needs the keys for the two roles you pick. Missing: "
                + ", ".join(dual_gap)
                + ". Missing provider stays Off. Pack saved locally. No Film Lab credits."
            )
        elif prov == PROVIDER_GEMINI:
            hint = (
                "Gemini is Off. Set FILM_LAB_GEMINI_API_KEY (or GEMINI_API_KEY / GOOGLE_API_KEY). "
                "Pack saved locally. No Film Lab credits."
            )
        elif prov == PROVIDER_OPENAI:
            hint = (
                "ChatGPT is Off. Set FILM_LAB_OPENAI_API_KEY (or OPENAI_API_KEY). "
                "Pack saved locally. No Film Lab credits."
            )
        elif prov == PROVIDER_CLAUDE:
            hint = (
                "Claude is Off. Set FILM_LAB_ANTHROPIC_API_KEY (or ANTHROPIC_API_KEY). "
                "Pack saved locally. No Film Lab credits."
            )
        else:
            hint = (
                "Grok is Off. Set FILM_LAB_XAI_API_KEY (or XAI_API_KEY). "
                "Pack saved locally. No Film Lab credits."
            )
        if note:
            hint += f" {note}"
        return (
            draft.id,
            draft.body,
            system,
            user,
            _chatbot_from_turns(draft.turns),
            draft.turns,
            draft_dropdown(project, draft.id),
            hint,
        )
    try:
        draft = generate_draft(project, draft)
    except (GenreGuardError, CharacterError) as exc:
        raise gr.Error(str(exc)) from exc
    except WritingError as exc:
        save_draft(project, draft)
        raise gr.Error(str(exc)) from exc
    if draft.provider == PROVIDER_LOCAL:
        hint = (
            f"Local pages written (`{draft.model}`). Nothing left this machine. "
            f"Saved `{draft.id}`. No Film Lab credits."
        )
    else:
        hint = f"Generated with `{draft.model}`. {leave_notice(draft.provider)} Saved `{draft.id}`."
    if note:
        hint += f" {note}"
    return (
        draft.id,
        draft.body,
        draft.system_prompt,
        draft.user_prompt,
        _chatbot_from_turns(draft.turns),
        draft.turns,
        draft_dropdown(project, draft.id),
        hint,
    )


def get_api_key_safe():
    from film_lab.writing import get_api_key

    return get_api_key()


def save_writing_ui(
    project_name,
    draft_id,
    title,
    mode,
    provider,
    dual_roles,
    primary_genre,
    secondary_genres,
    custom_genre_tags,
    tropes_checklist,
    primary_emotion,
    secondary_emotion,
    emotion_intensity,
    inner_state,
    outer_behavior,
    relationship_temp,
    enabled_senses,
    touch_notes,
    smell_notes,
    taste_notes,
    hearing_notes,
    sight_notes,
    sensory_pass,
    env_location,
    env_time,
    env_weather,
    env_light,
    env_ambient,
    env_blocking,
    env_props,
    live_override,
    live_styles,
    live_custom,
    live_norms,
    live_income,
    live_housing,
    live_privacy,
    live_clean,
    live_hood,
    live_utils,
    live_deps,
    live_work,
    live_health,
    scene_choice,
    character_ids,
    source,
    notes,
    tone,
    pacing,
    intimacy,
    intensity_preset,
    content_intensity,
    speaker,
    body,
    system_prompt,
    user_prompt,
    history,
):
    project = load_project(project_name)
    draft = _draft_from_form(
        draft_id, title, mode, provider, dual_roles, primary_genre, secondary_genres, custom_genre_tags, tropes_checklist,
        primary_emotion, secondary_emotion, emotion_intensity, inner_state, outer_behavior, relationship_temp,
        enabled_senses, touch_notes, smell_notes, taste_notes, hearing_notes, sight_notes,
        sensory_pass, env_location, env_time, env_weather, env_light, env_ambient, env_blocking, env_props,
        live_override, live_styles, live_custom, live_norms, live_income, live_housing, live_privacy,
        live_clean, live_hood, live_utils, live_deps, live_work, live_health,
        scene_choice, character_ids, source, notes,
        tone, pacing, intimacy, intensity_preset, content_intensity, speaker, body, system_prompt, user_prompt, history,
    )
    note = _guard_draft(draft)
    save_draft(project, draft)
    hint = f"Saved draft `{draft.id}` — {draft.title}."
    if note:
        hint += f" {note}"
    return draft.id, draft_dropdown(project, draft.id), hint


def load_writing_ui(project_name, choice):
    if not choice:
        raise gr.Error("Pick a saved draft.")
    project = load_project(project_name)
    draft = load_draft(project, _id_from_choice(choice))
    scene_value = ""
    for label in scene_choices(project):
        if label.startswith(draft.scene_id or ""):
            scene_value = label
            break
    return (
        draft.id,
        draft.title,
        draft.mode,
        draft.provider or DEFAULT_PROVIDER,
        draft.dual_roles or DEFAULT_DUAL_ROLES,
        draft.primary_genre or DEFAULT_PRIMARY,
        list(draft.secondary_genres),
        join_custom_tags(draft.custom_genre_tags),
        draft.tropes_checklist,
        *_brief_to_ui(draft.sensory_brief()),
        *living_ui_updates(draft.living_brief()),
        scene_dropdown(project, draft.scene_id),
        draft.character_ids,
        draft.source,
        draft.notes,
        draft.tone,
        draft.pacing,
        draft.intimacy_mode,
        draft.intensity_preset or DEFAULT_PRESET,
        draft.content_intensity,
        draft.roleplay_speaker,
        draft.body,
        draft.system_prompt,
        draft.user_prompt,
        _chatbot_from_turns(draft.turns),
        draft.turns,
        examples_dropdown(draft.primary_genre, draft.secondary_genres),
        f"Loaded `{draft.id}` — {draft.title}.",
    )


def new_writing_ui():
    draft = new_draft("Bedroom study", "screenplay")
    return (
        draft.id,
        draft.title,
        draft.mode,
        draft.provider or DEFAULT_PROVIDER,
        draft.dual_roles or DEFAULT_DUAL_ROLES,
        draft.primary_genre,
        [],
        "",
        "",
        *_brief_to_ui(draft.sensory_brief()),
        *living_ui_updates(draft.living_brief()),
        "",
        ["alison", "bradley"],
        "",
        "",
        "",
        "",
        "covered sheets",
        DEFAULT_PRESET,
        DEFAULT_INTENSITY,
        "Director",
        "",
        "",
        "",
        [],
        [],
        examples_dropdown(draft.primary_genre, []),
        "New draft. Import & Fuse, paste from chat, or generate if the API is Ready.",
    )


def export_writing_ui(
    project_name,
    draft_id,
    title,
    mode,
    provider,
    dual_roles,
    primary_genre,
    secondary_genres,
    custom_genre_tags,
    tropes_checklist,
    primary_emotion,
    secondary_emotion,
    emotion_intensity,
    inner_state,
    outer_behavior,
    relationship_temp,
    enabled_senses,
    touch_notes,
    smell_notes,
    taste_notes,
    hearing_notes,
    sight_notes,
    sensory_pass,
    env_location,
    env_time,
    env_weather,
    env_light,
    env_ambient,
    env_blocking,
    env_props,
    live_override,
    live_styles,
    live_custom,
    live_norms,
    live_income,
    live_housing,
    live_privacy,
    live_clean,
    live_hood,
    live_utils,
    live_deps,
    live_work,
    live_health,
    scene_choice,
    character_ids,
    source,
    notes,
    tone,
    pacing,
    intimacy,
    intensity_preset,
    content_intensity,
    speaker,
    body,
    system_prompt,
    user_prompt,
    history,
    fmt,
):
    project = load_project(project_name)
    draft = _draft_from_form(
        draft_id, title, mode, provider, dual_roles, primary_genre, secondary_genres, custom_genre_tags, tropes_checklist,
        primary_emotion, secondary_emotion, emotion_intensity, inner_state, outer_behavior, relationship_temp,
        enabled_senses, touch_notes, smell_notes, taste_notes, hearing_notes, sight_notes,
        sensory_pass, env_location, env_time, env_weather, env_light, env_ambient, env_blocking, env_props,
        live_override, live_styles, live_custom, live_norms, live_income, live_housing, live_privacy,
        live_clean, live_hood, live_utils, live_deps, live_work, live_health,
        scene_choice, character_ids, source, notes,
        tone, pacing, intimacy, intensity_preset, content_intensity, speaker, body, system_prompt, user_prompt, history,
    )
    save_draft(project, draft)
    try:
        ext = ext_for_export_label(fmt)
    except OfficeError as exc:
        raise gr.Error(str(exc)) from exc
    dest = writing_dir_safe(project) / f"{slugify(draft.title, draft.id)}{ext}"
    try:
        export_draft(project, draft, dest)
    except WritingError as exc:
        raise gr.Error(str(exc)) from exc
    return str(dest), f"Exported `{dest.name}`."


def writing_dir_safe(project: Project) -> Path:
    from film_lab.writing import writing_dir

    folder = writing_dir(project)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def push_writing_to_scene_ui(
    project_name,
    draft_id,
    title,
    mode,
    provider,
    dual_roles,
    primary_genre,
    secondary_genres,
    custom_genre_tags,
    tropes_checklist,
    primary_emotion,
    secondary_emotion,
    emotion_intensity,
    inner_state,
    outer_behavior,
    relationship_temp,
    enabled_senses,
    touch_notes,
    smell_notes,
    taste_notes,
    hearing_notes,
    sight_notes,
    sensory_pass,
    env_location,
    env_time,
    env_weather,
    env_light,
    env_ambient,
    env_blocking,
    env_props,
    live_override,
    live_styles,
    live_custom,
    live_norms,
    live_income,
    live_housing,
    live_privacy,
    live_clean,
    live_hood,
    live_utils,
    live_deps,
    live_work,
    live_health,
    scene_choice,
    character_ids,
    source,
    notes,
    tone,
    pacing,
    intimacy,
    intensity_preset,
    content_intensity,
    speaker,
    body,
    system_prompt,
    user_prompt,
    history,
):
    project = load_project(project_name)
    draft = _draft_from_form(
        draft_id, title, mode, provider, dual_roles, primary_genre, secondary_genres, custom_genre_tags, tropes_checklist,
        primary_emotion, secondary_emotion, emotion_intensity, inner_state, outer_behavior, relationship_temp,
        enabled_senses, touch_notes, smell_notes, taste_notes, hearing_notes, sight_notes,
        sensory_pass, env_location, env_time, env_weather, env_light, env_ambient, env_blocking, env_props,
        live_override, live_styles, live_custom, live_norms, live_income, live_housing, live_privacy,
        live_clean, live_hood, live_utils, live_deps, live_work, live_health,
        scene_choice, character_ids, source, notes,
        tone, pacing, intimacy, intensity_preset, content_intensity, speaker, body, system_prompt, user_prompt, history,
    )
    if not (draft.body or "").strip():
        raise gr.Error("Draft body is empty. Generate, or paste pages first.")
    save_draft(project, draft)
    scene = push_draft_to_scene(project, draft)
    return (
        draft.id,
        scene_dropdown(project, scene.id),
        f"Pushed draft into Script scene `{scene.id}` — {scene.heading}.",
    )


def import_writing_ui(files):
    """Upload PDF / Word / PowerPoint / Excel / text → draft body (view)."""
    try:
        body, names = import_files_as_text(files)
    except OfficeError as exc:
        raise gr.Error(str(exc)) from exc
    listed = ", ".join(f"`{n}`" for n in names)
    hint = (
        f"Imported {listed} into the draft. View / edit below. "
        "Then Fuse, Plan shots, or Export. Offline. Zero credits."
    )
    return body, hint


def fuse_writing_ui(paste_a, paste_b, paste_c, files, target, title=""):
    """Paste / import drafts → one local body. No API."""
    del title
    try:
        sources, notes = collect_sources(paste_a, paste_b, paste_c, files)
        body = fuse_texts(sources, target)
        mode = mode_for_target(target)
    except (WriteImportError, FuseError) as exc:
        raise gr.Error(str(exc)) from exc
    kind = "Fused" if len(sources) > 1 else "Imported"
    hint = (
        f"{kind} {len(sources)} draft(s) into **{mode_for_target(target)}**. "
        "Edit the body, then Plan shots → Motion Desk. Offline. Zero credits."
    )
    if notes:
        hint += " " + " ".join(notes)
    return body, mode, hint


def plan_writing_shots_ui(
    project_name,
    title,
    body,
    character_ids,
    intimacy,
    content_intensity,
):
    """Edited pages → short ShotCards, then open Motion Desk."""
    project = load_project(project_name)
    if not (body or "").strip():
        raise gr.Error("Draft body is empty. Fuse, import, or paste pages first.")
    try:
        _guard_explicit_adults(project_name, content_intensity, intimacy, character_ids)
    except (DirectorNoteError, CharacterError) as exc:
        raise gr.Error(str(exc)) from exc
    try:
        shots = push_pages_to_shots(
            project,
            body,
            title=title or "Draft",
            character_ids=list(character_ids or []),
            intimacy=intimacy,
            intensity=content_intensity,
        )
    except FuseError as exc:
        raise gr.Error(str(exc)) from exc
    first = shots[0]
    extra = ""
    planned = len(split_beats(body))
    if planned > len(shots):
        extra = f" Capped at {len(shots)} of {planned} beats (6GB)."
    hint = (
        f"Plan shots: {len(shots)} cards (~2.5s) from the draft. "
        f"First `{first.id}` — {first.name} on Motion Desk. "
        "Animate, then Open Take Board."
        f"{extra} Zero credits."
    )
    dd = shot_dropdown(project, first.id)
    return dd, dd, open_hub_tab("motion"), hint


def save_takes_voice_ui(project_name, body, scene_choice, character_ids):
    project = load_project(project_name)
    takes = extract_dialogue_takes(body or "")
    if not takes:
        raise gr.Error("No CHARACTER / dialogue lines found to send to Voice.")
    scene_id = _id_from_choice(scene_choice) or None
    cues = speak_tagged_lines(project, takes, scene_id=scene_id)
    last_wav = cues[-1].path if cues else None
    names = [p.name for p in list_dialogue(project)]
    last_line = takes[-1].text
    ids = ", ".join(sorted({c.character_id or "?" for c in cues}))
    return (
        last_wav,
        last_line,
        gr.Dropdown(choices=names, value=Path(last_wav).name if last_wav else None),
        f"Sent {len(cues)} tagged line(s) to Voice as {ids} (local TTS / placeholder). Zero credits.",
    )


def text_family_change_ui(family):
    models = text_models_for(family)
    return gr.Dropdown(choices=models, value=models[0]), family_to_provider(family)


def image_family_change_ui(family):
    models = image_models_for(family)
    return gr.Dropdown(choices=models, value=models[0])


def writing_provider_models_ui(provider):
    models = text_models_for(provider_to_family(provider))
    return gr.Dropdown(choices=models, value=models[0])


def select_bridge_ui(agent, mode):
    return agent_panel_html(agent, mode), setup_prompt(agent, mode)


def refresh_bridge_ui(agent, mode):
    return (
        agent_panel_html(agent, mode),
        setup_prompt(agent, mode),
        connectors_status_markdown(),
    )


def connect_bridge_ui(agent, mode):
    return (
        agent_panel_html(agent, mode),
        setup_prompt(agent, mode),
        connect_connector(agent, mode),
    )


def still_cloud_ui(family, model):
    route = resolve_image_pick(family, model)
    return route.message


def apply_role_defaults_ui(role: str):
    from film_lab.filming import default_band_for_role, default_years_for_role, normalize_role

    resolved = normalize_role(role)
    return resolved, default_band_for_role(resolved), default_years_for_role(resolved)


def apply_filming_mode_ui(project_name: str, mode: str, character_ids=None):
    """Toggle Regular vs 18+ tools only. Never swap CSS, Gradio theme, or desk skin."""
    from film_lab.constants import STORY_INTIMACY
    from film_lab.filming import (
        FilmingError,
        MODE_REGULAR,
        assert_explicit_cast,
        filming_help,
        is_explicit_mode,
        normalize_mode,
    )
    from film_lab.intensity import IMPLIED_SOFT, PRESET_VALUES

    project = load_project(project_name)
    resolved = normalize_mode(mode)
    ids = []
    for item in character_ids or []:
        ids.append(_id_from_choice(item) if " — " in str(item) else str(item))
    profiles = load_selected_characters(project, ids or list(project.active_cast or []))
    try:
        if is_explicit_mode(resolved):
            assert_explicit_cast(profiles, context="switching to 18+ Explicit")
        project.set_filming_mode(resolved)
    except FilmingError as exc:
        raise gr.Error(str(exc)) from exc
    explicit = is_explicit_mode(resolved)
    intimacy = "covered sheets" if explicit else STORY_INTIMACY
    preset = DEFAULT_PRESET if explicit else IMPLIED_SOFT
    intensity = DEFAULT_INTENSITY if explicit else PRESET_VALUES[IMPLIED_SOFT]
    msg = (
        f"Filming mode: **{resolved}**. {filming_help()}"
        if explicit
        else (
            f"Filming mode: **{MODE_REGULAR}**. Intimate / nude / sex tools are locked. "
            f"Family roles (Mom, Dad, Teen, Adult, Child, Infant) are for non-sexual story only."
        )
    )
    return (
        resolved,
        resolved,
        resolved,
        resolved,
        gr.update(visible=explicit),
        gr.update(visible=explicit),
        intimacy,
        intimacy,
        preset,
        intensity,
        preset,
        intensity,
        msg,
    )


def apply_set_note_ui(
    project_name: str,
    camera: str,
    outdoor: str,
    set_description: str,
    mark_role: str,
    mark_who: str,
    mark_where: str,
    idea: str,
    world_outdoor: str,
):
    from film_lab.director_notes import DEFAULT_OUTDOOR
    from film_lab.filming import normalize_role
    from film_lab.setdesk import (
        CharacterMark,
        SetDeskError,
        build_set_note,
        load_set_note,
        save_set_note,
        set_markdown,
    )

    project = load_project(project_name)
    note = load_set_note(project)
    who = (mark_who or "").strip()
    where = (mark_where or "").strip()
    if who or where:
        cid = _id_from_choice(who) if " — " in who else (who.lower().replace(" ", "-") if who else "")
        name = who.split(" — ", 1)[-1] if " — " in who else (who or cid)
        existing = [m for m in note.placements if m.character_id != cid]
        existing.append(
            CharacterMark(
                character_id=cid or name or "mark",
                character_name=name or cid,
                role=normalize_role(mark_role),
                mark=where,
            )
        )
        note.placements = existing
    try:
        built = build_set_note(
            camera=camera,
            outdoor=outdoor,
            set_description=set_description,
            placements=note.placements,
        )
    except SetDeskError as exc:
        raise gr.Error(str(exc)) from exc
    save_set_note(project, built)
    from film_lab.constants import CAMERA_MOVES

    folded = fold_desk(project, idea or "")
    plate = outdoor if outdoor and outdoor != "none" else (world_outdoor or DEFAULT_OUTDOOR)
    shot_cam = built.camera if built.camera in CAMERA_MOVES else "slow push-in"
    msg = (
        f"3D Set applied ({built.camera}"
        + (f", {built.outdoor}" if built.outdoor != "none" else "")
        + "). Camera + SET NOTE folded into Enhance → Pose → Animate. "
        "Regenerate for a new angle. Not a 3D engine."
    )
    return folded, set_markdown(built), plate, shot_cam, msg


def build_locked_env_ui(
    project_name,
    photo,
    camera,
    place_actors,
    character_ids,
    filming_mode,
    idea,
):
    from film_lab.envlock import env_gallery_items, env_markdown, load_env_lock, resolve_env_still
    from film_lab.setbuild import (
        SetBuildError,
        build_locked_environment,
        built_set_choices,
        built_set_gallery,
        built_set_take,
        storage_help,
    )

    project = load_project(project_name)
    paths = _as_paths(photo)
    if not paths:
        raise gr.Error("Upload a photo to build the LOCKED Environment.")
    ids = list(character_ids or []) if place_actors else []
    try:
        built = build_locked_environment(
            project,
            paths[0],
            camera=camera,
            character_ids=ids,
            filming_mode=filming_mode or "",
        )
    except SetBuildError as exc:
        raise gr.Error(str(exc)) from exc
    lock = load_env_lock(project)
    resolved = resolve_env_still(project, lock)
    items = built_set_gallery(project, built)
    env_items = env_gallery_items(project, lock)
    take = built_set_take(project, built)
    folded = fold_desk(project, idea or "")
    pick = gr.Dropdown(
        choices=built_set_choices(project),
        value=f"{built.id} — {built.title} ({built.camera})",
    )
    start = gr.Dropdown(choices=project.still_choices(), value=lock.still or None)
    locked_path = str(resolved) if resolved else None
    hint = (
        f"LOCKED Environment `{built.id}` — {built.camera}. "
        f"{built.note}. Stored on this PC under sets / stills / takes. "
        "Offline. Deletable. Zero credits."
    )
    return (
        folded,
        storage_help(project),
        items,
        take,
        pick,
        env_markdown(lock),
        env_markdown(lock),
        env_markdown(lock),
        env_items,
        env_items,
        env_items,
        locked_path,
        start,
        hint,
    )


def load_locked_env_ui(project_name, choice):
    from film_lab.setbuild import (
        built_set_gallery,
        built_set_take,
        resolve_built_set,
        storage_help,
    )

    project = load_project(project_name)
    built = resolve_built_set(project, choice)
    if built is None:
        raise gr.Error("Pick a built set on this PC.")
    return (
        storage_help(project),
        built_set_gallery(project, built),
        built_set_take(project, built),
        f"Loaded `{built.id}` from this PC. {built.note}",
    )


def delete_locked_env_ui(project_name, choice, idea):
    from film_lab.envlock import env_gallery_items, env_markdown, load_env_lock, resolve_env_still
    from film_lab.setbuild import (
        SetBuildError,
        built_set_choices,
        delete_built_set,
        storage_help,
    )

    project = load_project(project_name)
    try:
        deleted = delete_built_set(project, choice)
    except SetBuildError as exc:
        raise gr.Error(str(exc)) from exc
    lock = load_env_lock(project)
    resolved = resolve_env_still(project, lock)
    pick = gr.Dropdown(choices=built_set_choices(project), value=None)
    start = gr.Dropdown(choices=project.still_choices(), value=lock.still or None)
    env_items = env_gallery_items(project, lock)
    folded = fold_desk(project, idea or "")
    hint = (
        f"Deleted `{deleted}` from this PC (sets / stills / takes). "
        "Offline. Zero credits."
    )
    return (
        folded,
        storage_help(project),
        [],
        None,
        pick,
        env_markdown(lock),
        env_markdown(lock),
        env_markdown(lock),
        env_items,
        env_items,
        env_items,
        str(resolved) if resolved else None,
        start,
        hint,
    )

# --- Authoritative persistent Take Board callbacks ---
def production_take_select_ui(project_name: str, evt: gr.SelectData):
    """Resolve a clicked legacy gallery clip to its durable Production Take, when registered."""
    from film_lab.production import ProductionStore
    project = load_project(project_name)
    items = take_gallery_items(project)
    picked = pick_gallery_item(items, getattr(evt, "index", 0)) if items else None
    media = Path(picked[0]).resolve() if picked else None
    store = ProductionStore(project)
    take = next((t for t in store.list_takes(existing_media_only=False) if media and Path(t.media_path).resolve() == media), None)
    if take is None:
        return "", "**Persistent Take:** not registered yet", "", "", "HARD_CUT", 0.0, 0.0, 0.0, 0.0
    detail = f"**Persistent Take:** `{take.id}` · **{take.status.title()}** · Scene `{take.scene_id or '—'}` · Shot `{take.shot_id}`"
    intent = take.metadata.get("audio_cut_intent", {}) if isinstance(take.metadata, dict) else {}
    intent = intent if isinstance(intent, dict) else {}
    style = "J_L_CUT" if intent.get("j_cut") and intent.get("l_cut") else "J_CUT" if intent.get("j_cut") else "L_CUT" if intent.get("l_cut") else "HARD_CUT"
    return take.id, detail, take.director_notes, ", ".join(take.tags), style, float(intent.get("j_cut_lead_s", 0.0) or 0.0), float(intent.get("l_cut_tail_s", 0.0) or 0.0), float(intent.get("picture_in_s", 0.0) or 0.0), float(intent.get("picture_out_s", 0.0) or 0.0)


def production_audio_cut_ui(project_name: str, take_id: str, style: str, j_lead: float, l_tail: float, picture_in: float, picture_out: float):
    """Persist explicit, bounded Director J/L timing on the incoming Take."""
    from film_lab.take_board import save_audio_cut_intent, TakeBoardError
    if not take_id:
        msg = "Choose a registered incoming Take before saving audio cut direction."
        return "**Persistent Take:** none selected", toast_html(msg), msg
    project = load_project(project_name)
    try:
        take = save_audio_cut_intent(project, take_id, style=style, j_cut_lead_s=j_lead, l_cut_tail_s=l_tail, picture_in_s=picture_in, picture_out_s=picture_out)
        detail = f"**Persistent Take:** `{take.id}` · **{take.status.title()}** · Audio cut `{style}`"
        msg = f"Audio cut direction saved on incoming Take {take.id}."
        return detail, "", msg
    except (KeyError, ValueError, TakeBoardError) as exc:
        msg = str(exc)
        return gr.update(), toast_html(msg), msg


def production_take_action_ui(project_name: str, take_id: str, action: str, notes: str = "", tags_text: str = ""):
    """Apply a real persistent Take Board action; never report success without a durable Take."""
    from film_lab.take_board import select_take, review_take, reject_take, save_take_direction, TakeBoardError
    if not take_id:
        msg = "Choose a registered Take first. New generated/imported videos register automatically."
        return "**Persistent Take:** none selected", toast_html(msg), msg
    project = load_project(project_name)
    try:
        tags = [x.strip() for x in (tags_text or "").split(",") if x.strip()]
        if action == "selected":
            take = select_take(project, take_id)
        elif action == "review":
            take = review_take(project, take_id)
        elif action == "rejected":
            take = reject_take(project, take_id)
        elif action == "save":
            take = save_take_direction(project, take_id, director_notes=notes or "", tags=tags)
        else:
            raise TakeBoardError(f"Unknown Take action: {action}")
        detail = f"**Persistent Take:** `{take.id}` · **{take.status.title()}** · Scene `{take.scene_id or '—'}` · Shot `{take.shot_id}`"
        msg = f"Take {take.id} saved as {take.status}."
        return detail, "", msg
    except (KeyError, ValueError, TakeBoardError) as exc:
        msg = str(exc)
        return gr.update(), toast_html(msg), msg


def production_cinema_export_ui(project_name: str):
    """Export only durable Selected Takes through the real Cinema path."""
    from film_lab.take_board import export_selected_to_cinema, TakeBoardError
    project = load_project(project_name)
    try:
        out = export_selected_to_cinema(project)
        msg = f"Cinema export created: `{out.name}`"
        return str(out), "", msg
    except TakeBoardError as exc:
        msg = str(exc)
        return None, toast_html(msg), msg


def creator_acceptance_ui(project_name: str) -> str:
    """Creator-safe summary of the latest automatic real-render certification."""
    from film_lab.creator_acceptance import creator_markdown, latest_acceptance
    project = load_project(project_name)
    return creator_markdown(latest_acceptance(project))

# --- Creator-first Director Command Home ------------------------------------
def _director_plan_markdown(plan) -> str:
    changes = plan.scene_changes or {}
    rows = [
        "### Production Plan",
        f"**Scene:** `{plan.scene_id}`  ·  **Shot:** `{plan.shot_id}`",
        f"**Camera:** {plan.camera_move}",
        f"**Direction:** {plan.shot_direction}",
    ]
    world = []
    for key in ("time_of_day", "weather", "lighting"):
        if changes.get(key):
            world.append(f"{key.replace('_', ' ').title()}: {changes[key]}")
    if world:
        rows.append("**Scene World:** " + " · ".join(world))
    if plan.requested_actions:
        rows.append("**Production controls:** " + ", ".join(plan.requested_actions))
    context = getattr(plan, "production_context", {}) or {}
    chars = context.get("characters") or []
    if chars:
        labels = [f"{c.get('name','Character')} (`{c.get('id','unbound')}`)" for c in chars]
        rows.append("**Existing Characters:** " + ", ".join(labels))
    prior = context.get("previous_selected_take")
    if prior:
        rows.append(f"**Continuity source:** selected Take `{prior.get('id')}` from Shot `{prior.get('shot_id')}`")
    for warning in getattr(plan, "continuity_warnings", []) or []:
        rows.append(f"**Continuity:** {warning}")
    for warning in getattr(plan, "capability_warnings", []) or []:
        rows.append(f"**Capability warning:** {warning}")
    rows.append("\nReview this plan. Nothing is applied until you choose **Apply Plan** or **Create Scene / Prepare Generate**.")
    return "\n\n".join(rows)


def director_home_plan_ui(project_name: str, instruction: str, scene_id: str, shot_id: str):
    """Create and persist a reviewable Director plan without changing production state."""
    from film_lab.director_command import DirectorCommandStore

    project = load_project(project_name)
    try:
        plan = DirectorCommandStore(project).plan(
            instruction,
            scene_id=(scene_id or "scene-1").strip(),
            shot_id=(shot_id or "shot-1").strip(),
        )
    except ValueError as exc:
        return "", f"### Production Plan\n\n**Needs direction:** {exc}", str(exc)
    return plan.id, _director_plan_markdown(plan), f"Director plan `{plan.id}` is ready for review."


def director_home_apply_ui(project_name: str, plan_id: str):
    """Apply an explicitly reviewed Director plan to Scene World + Shot state."""
    from film_lab.director_command import DirectorCommandStore

    if not (plan_id or "").strip():
        return "### Production Plan\n\nCreate a plan first.", "No Director plan selected."
    project = load_project(project_name)
    try:
        plan, shot = DirectorCommandStore(project).apply(plan_id.strip())
    except KeyError:
        return "### Production Plan\n\nThe selected plan no longer exists.", "Director plan not found."
    md = _director_plan_markdown(plan) + "\n\n**APPLIED** — Scene World and Shot production state have been updated."
    return md, f"Applied Director plan `{plan.id}` to {shot.scene_id} / {shot.id}."

# --- Director Timeline Editor ------------------------------------------------
def director_timeline_refresh_ui(project_name: str, scene_id: str, shot_id: str):
    from film_lab.director_timeline_editor import timeline_rows, inspector
    project=load_project(project_name); scene=(scene_id or "scene-1").strip(); shot=(shot_id or "shot-1").strip()
    rows=timeline_rows(project,scene,shot); info=inspector(project,scene,shot)
    from film_lab.production import ProductionStore
    selected=[t for t in ProductionStore(project).list_takes(shot_id=shot, existing_media_only=False) if t.status=="selected"]
    take=f"Selected Take: `{selected[0].id}`" if selected else "Selected Take: none yet"
    md=f"**Persistent Director Timeline** · {len(rows)} events · {len(info['characters'])} Characters · {take}. Edits below write to project state immediately."
    return rows,md

def director_timeline_add_performance_ui(project_name,scene_id,shot_id,character_id,character_name,time_s,emotion,expression,gaze,posture,gesture,action,intensity):
    from film_lab.director_timeline_editor import add_performance_beat, timeline_rows
    project=load_project(project_name)
    try:
        val=None if intensity in (None,"") else float(intensity)
        add_performance_beat(project,scene_id,shot_id,character_id,character_name,float(time_s),emotion=emotion or "",expression=expression or "",gaze=gaze or "",posture=posture or "",gesture=gesture or "",action=action or "",intensity=val)
        return timeline_rows(project,scene_id,shot_id),"Performance beat saved to persistent production state.",""
    except Exception as exc: return gr.update(),str(exc),toast_html(str(exc))

def director_timeline_add_camera_ui(project_name,scene_id,shot_id,time_s,move,framing,lens,focus,follow,speed,note):
    from film_lab.director_timeline_editor import add_camera_beat, timeline_rows
    project=load_project(project_name)
    try:
        val=None if speed in (None,"") else float(speed)
        add_camera_beat(project,scene_id,shot_id,float(time_s),move=move or "",framing=framing or "",lens=lens or "",focus_target=focus or "",follow_character_id=follow or "",speed=val,note=note or "")
        return timeline_rows(project,scene_id,shot_id),"Camera beat saved to persistent production state.",""
    except Exception as exc: return gr.update(),str(exc),toast_html(str(exc))

def director_timeline_move_ui(project_name,scene_id,shot_id,lane,character_id,index,new_time_s):
    from film_lab.director_timeline_editor import move_event, move_performance_keyframe, timeline_rows
    project=load_project(project_name)
    try:
        idx=int(index); t=float(new_time_s)
        if lane=="performance": move_performance_keyframe(project,scene_id,shot_id,character_id,idx,t)
        else: move_event(project,scene_id,shot_id,lane,idx,t)
        return timeline_rows(project,scene_id,shot_id),f"{lane.title()} event moved to {t:.2f}s and persisted.",""
    except Exception as exc: return gr.update(),str(exc),toast_html(str(exc))

def director_timeline_visual_ui(project_name: str, scene_id: str, shot_id: str):
    from film_lab.director_timeline_editor import visual_timeline_html
    return visual_timeline_html(load_project(project_name),(scene_id or "scene-1").strip(),(shot_id or "shot-1").strip())


def director_timeline_drag_ui(project_name: str, scene_id: str, shot_id: str, payload: str):
    """Persist one graphical drag using the same tested move functions as Move & Save."""
    import json
    from film_lab.director_timeline_editor import move_event, move_performance_keyframe, timeline_rows, visual_timeline_html
    project=load_project(project_name); scene=(scene_id or "scene-1").strip(); shot=(shot_id or "shot-1").strip()
    try:
        data=json.loads(payload or "{}"); lane=str(data["lane"]); cid=str(data.get("character_id") or ""); idx=int(data["index"]); t=float(data["new_time_s"])
        if lane=="performance": move_performance_keyframe(project,scene,shot,cid,idx,t)
        else: move_event(project,scene,shot,lane,idx,t)
        return timeline_rows(project,scene,shot),visual_timeline_html(project,scene,shot),f"{lane.title()} beat moved to {t:.3f}s and saved.",""
    except Exception as exc:
        return gr.update(),gr.update(),str(exc),toast_html(str(exc))

# --- Director Timeline Playback Synchronization -----------------------------
def director_timeline_playback_ui(project_name: str, scene_id: str, shot_id: str):
    from film_lab.playback_sync import resolve_playback, playback_status
    from film_lab.director_timeline_editor import visual_timeline_html
    project=load_project(project_name); scene=(scene_id or "scene-1").strip(); shot=(shot_id or "shot-1").strip()
    state=resolve_playback(project,scene,shot)
    maximum=max(1.0,float(state.duration_s or 0),float(state.playhead_s or 0)+1.0)
    return (state.media_path or None, gr.update(value=state.playhead_s,maximum=maximum),
            visual_timeline_html(project,scene,shot,state.playhead_s), playback_status(state))

def director_timeline_scrub_ui(project_name: str, scene_id: str, shot_id: str, seconds):
    from film_lab.playback_sync import PlaybackSyncStore, playback_status
    from film_lab.director_timeline_editor import visual_timeline_html
    project=load_project(project_name); scene=(scene_id or "scene-1").strip(); shot=(shot_id or "shot-1").strip()
    state=PlaybackSyncStore(project).save_playhead(scene,shot,float(seconds or 0))
    return visual_timeline_html(project,scene,shot,state.playhead_s), playback_status(state)

def director_timeline_frame_ui(project_name: str, scene_id: str, shot_id: str, seconds):
    """Freeze the selected Take at the persisted playhead for Mark & Direct preparation."""
    from film_lab.playback_sync import PlaybackSyncStore
    from film_lab.playback import freeze_at
    project=load_project(project_name); scene=(scene_id or "scene-1").strip(); shot=(shot_id or "shot-1").strip()
    state=PlaybackSyncStore(project).save_playhead(scene,shot,float(seconds or 0))
    if not state.media_path:
        msg="Select a real Take for this Scene/Shot on Take Board first."
        return None,msg,toast_html(msg)
    try:
        frame=freeze_at(project,state.media_path,state.playhead_s)
        return frame,f"Frame {state.playhead_s:.3f}s prepared from `{state.take_id}`. Open Mark & Direct to direct this frame.",""
    except Exception as exc:
        return None,str(exc),toast_html(str(exc))

# --- Director Preview & Regeneration Loop -----------------------------------
def director_preview_regenerate_ui(project_name, scene_id, shot_id, seconds, instruction, character_id, region_id, generator_id):
    from film_lab.director_preview_regeneration import regenerate_preview
    project=load_project(project_name)
    try:
        review=regenerate_preview(project,scene_id=(scene_id or "scene-1").strip(),shot_id=(shot_id or "shot-1").strip(),playhead_s=float(seconds or 0),director_instruction=instruction or "",character_id=character_id or "",region_id=region_id or "",generator=get_generator(generator_id))
        take=ProductionStore(project).get_take(review.candidate_take_id)
        report=(take.metadata or {}).get("continuity_report",{})
        scopes=", ".join(report.get("requested_changes",[]) or ["unspecified"])
        visual=report.get("visual_certification","NOT_TESTED")
        full_take=report.get("full_take_scan","NOT_TESTED")
        events=report.get("full_take_events",[]) or []
        event_note=(f" {len(events)} temporal continuity event(s) flagged." if events else "")
        msg=f"Candidate `{review.candidate_take_id}` generated from `{review.source_take_id}` at {review.playhead_s:.3f}s. Requested change: {scopes}. Paused-frame certification: {visual}. Full-Take scan: {full_take}.{event_note} Source is untouched; compare A/B before choosing."
        return review.source_media_path,review.candidate_media_path,msg,msg,""
    except Exception as exc:
        return None,None,f"Regeneration failed: {exc}",str(exc),toast_html(str(exc))

def director_preview_accept_ui(project_name):
    from film_lab.director_preview_regeneration import DirectorPreviewStore, accept_candidate
    project=load_project(project_name)
    try:
        review=DirectorPreviewStore(project).load(); take=accept_candidate(project,review)
        msg=f"Candidate `{take.id}` is now the Selected Take. Playhead remains at {review.playhead_s:.3f}s for continued direction."
        return msg,msg,""
    except Exception as exc: return str(exc),str(exc),toast_html(str(exc))

def director_preview_reject_ui(project_name):
    from film_lab.director_preview_regeneration import DirectorPreviewStore
    from film_lab.production import ProductionStore
    project=load_project(project_name)
    try:
        review=DirectorPreviewStore(project).load()
        if review is None: raise ValueError("No Director A/B review is ready.")
        ProductionStore(project).set_status(review.candidate_take_id,"rejected")
        msg=f"Candidate `{review.candidate_take_id}` rejected. Source `{review.source_take_id}` remains selected."
        return msg,msg,""
    except Exception as exc: return str(exc),str(exc),toast_html(str(exc))


# --- Automated Take Quality Control & Repair Decisions ----------------------
def take_quality_control_ui(project_name):
    from film_lab.director_preview_regeneration import DirectorPreviewStore
    from film_lab.take_quality_control import diagnose_take
    project=load_project(project_name)
    try:
        review=DirectorPreviewStore(project).load()
        if review is None: raise ValueError("No Director A/B candidate is ready for Quality Control.")
        d=diagnose_take(project,review.candidate_take_id)
        when=f" at {d.time_s:.3f}s" if d.time_s is not None else ""
        msg=(f"### Director Quality Control — {d.status}\n**Recommended repair:** {d.strategy}{when}  \n"
             f"**Confidence:** {d.confidence}  \n**Diagnosis:** {d.reason}  \n"
             f"**Preserve:** {', '.join(d.preserve)}  \n**Automatic action:** {d.automatic_action}  \n"
             "Film Lab will not select or replace the current Take automatically. Creator approval remains required.")
        return msg,msg,""
    except Exception as exc: return str(exc),str(exc),toast_html(str(exc))

def take_quality_control_repair_ui(project_name,generator_id):
    from film_lab.take_quality_control import TakeQualityControlStore, execute_recommended_repair
    from film_lab.director_preview_regeneration import DirectorPreviewStore, ABReview
    project=load_project(project_name)
    try:
        d=TakeQualityControlStore(project).load()
        if d is None: raise ValueError("Run Director Quality Control first.")
        source=ProductionStore(project).get_take(d.candidate_take_id)
        new,report=execute_recommended_repair(project,generator=get_generator(generator_id),decision=d)
        playhead=d.time_s or 0.0
        ab=ABReview(source.scene_id,source.shot_id,source.id,new.id,source.media_path,new.media_path,playhead,{"quality_control_decision":d.to_dict()},status="READY_FOR_QC_AB_REVIEW")
        DirectorPreviewStore(project).save(ab)
        msg=(f"Quality Control forked candidate `{new.id}` using {d.strategy}. Source `{source.id}` is untouched. "
             f"Rescan status: {report.get('status','NOT_TESTED')}. Compare A/B before selecting.")
        return source.media_path,new.media_path,msg,msg,""
    except Exception as exc: return None,None,str(exc),str(exc),toast_html(str(exc))

# --- Continuity Problem Localization & Repair -------------------------------
def continuity_localize_repair_ui(project_name, event_index, instruction):
    from film_lab.director_preview_regeneration import DirectorPreviewStore
    from film_lab.continuity_problem_repair import localize_candidate_problem
    project=load_project(project_name)
    try:
        review=DirectorPreviewStore(project).load()
        if review is None: raise ValueError("No Director A/B candidate is ready for continuity repair.")
        plan=localize_candidate_problem(project,review.candidate_take_id,event_index=int(event_index or 0),instruction=instruction or "")
        target=f" target `{plan.target_label}`" if plan.target_label else ""
        msg=f"Repair localized at {plan.time_s:.3f}s (window {plan.window_start_s:.3f}–{plan.window_end_s:.3f}s){target}. Temporal patching: NOT ENFORCED. Ready to fork a repair candidate."
        return plan.time_s,msg,msg,""
    except Exception as exc: return event_index,str(exc),str(exc),toast_html(str(exc))

def continuity_execute_repair_ui(project_name, generator_id):
    from film_lab.continuity_problem_repair import RepairPlanStore, execute_repair
    from film_lab.director_preview_regeneration import DirectorPreviewStore, ABReview
    project=load_project(project_name)
    try:
        plan=RepairPlanStore(project).load()
        if plan is None: raise ValueError("Localize a continuity problem first.")
        source=ProductionStore(project).get_take(plan.candidate_take_id)
        new,scan=execute_repair(project,generator=get_generator(generator_id),plan=plan)
        review=ABReview(source.scene_id,source.shot_id,source.id,new.id,source.media_path,new.media_path,plan.time_s,{"continuity_repair_plan":plan.to_dict()},status="READY_FOR_REPAIR_AB_REVIEW")
        DirectorPreviewStore(project).save(review)
        events=len(scan.get("events",[]) or []); status=scan.get("status","NOT_TESTED")
        msg=f"Repair candidate `{new.id}` forked at {plan.time_s:.3f}s. Repair rescan: {status} ({events} event(s)). Source candidate `{source.id}` is untouched. Temporal-only splice remains NOT ENFORCED; compare A/B before choosing."
        return source.media_path,new.media_path,msg,msg,""
    except Exception as exc: return None,None,str(exc),str(exc),toast_html(str(exc))

# --- Temporal Segment Repair & Seamless Reassembly ---------------------------
def continuity_reassemble_segment_ui(project_name):
    from film_lab.continuity_problem_repair import RepairPlanStore
    from film_lab.temporal_segment_repair import reassemble_from_repair_plan
    from film_lab.director_preview_regeneration import DirectorPreviewStore, ABReview
    project=load_project(project_name)
    try:
        plan=RepairPlanStore(project).load()
        review=DirectorPreviewStore(project).load()
        if plan is None: raise ValueError("No localized continuity repair plan is ready.")
        if review is None or review.candidate_take_id == plan.candidate_take_id:
            raise ValueError("Generate a repair candidate before temporal reassembly.")
        repair=ProductionStore(project).get_take(review.candidate_take_id)
        assembled,result=reassemble_from_repair_plan(project,repair.id)
        ab=ABReview(assembled.scene_id,assembled.shot_id,plan.candidate_take_id,assembled.id,
                    ProductionStore(project).get_take(plan.candidate_take_id).media_path,assembled.media_path,
                    plan.time_s,{"temporal_segment_repair":result.to_dict()},status="READY_FOR_SEGMENT_REPAIR_AB_REVIEW")
        DirectorPreviewStore(project).save(ab)
        msg=(f"Temporal visual repair assembled as `{assembled.id}`. Only {result.window_start_s:.3f}–{result.window_end_s:.3f}s "
             f"was replaced; source video outside the window and source audio were preserved. Boundary check: {result.boundary_status}. Compare A/B before selecting.")
        return ab.source_media_path,ab.candidate_media_path,msg,msg,""
    except Exception as exc:
        return None,None,str(exc),str(exc),toast_html(str(exc))


def continuity_reassemble_audio_segment_ui(project_name):
    """Reassemble localized video+audio only when both audio streams are proven."""
    from film_lab.continuity_problem_repair import RepairPlanStore
    from film_lab.temporal_segment_repair import reassemble_audio_visual_from_repair_plan
    from film_lab.director_preview_regeneration import DirectorPreviewStore, ABReview
    project=load_project(project_name)
    try:
        plan=RepairPlanStore(project).load(); review=DirectorPreviewStore(project).load()
        if plan is None: raise ValueError("No localized continuity repair plan is ready.")
        if review is None or review.candidate_take_id == plan.candidate_take_id:
            raise ValueError("Generate a repair candidate before temporal A/V reassembly.")
        store=ProductionStore(project); repair=store.get_take(review.candidate_take_id)
        assembled,result=reassemble_audio_visual_from_repair_plan(project,repair.id)
        ab=ABReview(assembled.scene_id,assembled.shot_id,plan.candidate_take_id,assembled.id,
                    store.get_take(plan.candidate_take_id).media_path,assembled.media_path,
                    plan.time_s,{"temporal_segment_repair":result.to_dict()},status="READY_FOR_SEGMENT_AV_REPAIR_AB_REVIEW")
        DirectorPreviewStore(project).save(ab)
        msg=(f"Temporal A/V repair assembled as `{assembled.id}`. Only {result.window_start_s:.3f}–{result.window_end_s:.3f}s "
             f"of video and audio were replaced; media outside the window was preserved. Audio patch: ENFORCED. "
             f"Boundary visual check: {result.boundary_status}. Compare A/B before selecting.")
        return ab.source_media_path,ab.candidate_media_path,msg,msg,""
    except Exception as exc:
        return None,None,str(exc),str(exc),toast_html(str(exc))


def continuity_seam_blend_ui(project_name, blend_duration_s=0.12):
    """Blend localized repair entry/exit seams with real FFmpeg xfade/acrossfade."""
    from film_lab.continuity_problem_repair import RepairPlanStore
    from film_lab.intelligent_seam_blending import reassemble_blended_from_repair_plan
    from film_lab.director_preview_regeneration import DirectorPreviewStore, ABReview
    project=load_project(project_name)
    try:
        plan=RepairPlanStore(project).load(); review=DirectorPreviewStore(project).load()
        if plan is None: raise ValueError("No localized continuity repair plan is ready.")
        if review is None or review.candidate_take_id == plan.candidate_take_id:
            raise ValueError("Generate a repair candidate before intelligent seam blending.")
        store=ProductionStore(project); repair=store.get_take(review.candidate_take_id)
        assembled,result=reassemble_blended_from_repair_plan(project,repair.id,float(blend_duration_s or .12))
        ab=ABReview(assembled.scene_id,assembled.shot_id,plan.candidate_take_id,assembled.id,
                    store.get_take(plan.candidate_take_id).media_path,assembled.media_path,
                    plan.time_s,{"intelligent_seam_blending":result.to_dict()},status="READY_FOR_SEAM_BLEND_AB_REVIEW")
        DirectorPreviewStore(project).save(ab)
        msg=(f"Intelligent seam blend assembled as `{assembled.id}`. Visual xfade: {result.visual_blend_status}; "
             f"audio crossfade: {result.audio_blend_status}; boundary certification: {result.boundary_certification_status}. "
             "Automated seam evidence does not certify semantic identity or audible perfection; compare A/B before selecting.")
        return ab.source_media_path,ab.candidate_media_path,msg,msg,""
    except Exception as exc:
        return None,None,str(exc),str(exc),toast_html(str(exc))


def continuity_optical_flow_ui(project_name, blend_duration_s=0.10, interpolation_fps=60):
    """Apply capability-gated optical-flow interpolation to a localized repair."""
    from film_lab.continuity_problem_repair import RepairPlanStore
    from film_lab.intelligent_seam_blending import reassemble_optical_flow_from_repair_plan
    from film_lab.director_preview_regeneration import DirectorPreviewStore, ABReview
    project=load_project(project_name)
    try:
        plan=RepairPlanStore(project).load(); review=DirectorPreviewStore(project).load()
        if plan is None: raise ValueError("No localized continuity repair plan is ready.")
        if review is None or review.candidate_take_id == plan.candidate_take_id:
            raise ValueError("Generate a repair candidate before optical-flow alignment.")
        store=ProductionStore(project); repair=store.get_take(review.candidate_take_id)
        assembled,result=reassemble_optical_flow_from_repair_plan(project,repair.id,float(blend_duration_s or .10),float(interpolation_fps or 60))
        ab=ABReview(assembled.scene_id,assembled.shot_id,plan.candidate_take_id,assembled.id,
                    store.get_take(plan.candidate_take_id).media_path,assembled.media_path,
                    plan.time_s,{"optical_flow_transition_alignment":result},status="READY_FOR_OPTICAL_FLOW_AB_REVIEW")
        DirectorPreviewStore(project).save(ab)
        msg=(f"Optical-flow repair assembled as `{assembled.id}`. Interpolation: {result.get('optical_flow_status')}; "
             f"FPS: {result.get('interpolation_fps')}; boundary certification: {result.get('boundary_certification_status')}. "
             "Motion-compensated interpolation executed, but semantic identity and perceived quality still require A/B visual acceptance.")
        return ab.source_media_path,ab.candidate_media_path,msg,msg,""
    except Exception as exc:
        return None,None,str(exc),str(exc),toast_html(str(exc))

def continuity_motion_retime_ui(project_name, blend_duration_s=0.12):
    """Align repair timing to source boundary motion, then blend and certify."""
    from film_lab.continuity_problem_repair import RepairPlanStore
    from film_lab.intelligent_seam_blending import reassemble_motion_aligned_from_repair_plan
    from film_lab.director_preview_regeneration import DirectorPreviewStore, ABReview
    project=load_project(project_name)
    try:
        plan=RepairPlanStore(project).load(); review=DirectorPreviewStore(project).load()
        if plan is None: raise ValueError("No localized continuity repair plan is ready.")
        if review is None or review.candidate_take_id == plan.candidate_take_id:
            raise ValueError("Generate a repair candidate before motion retiming/alignment.")
        store=ProductionStore(project); repair=store.get_take(review.candidate_take_id)
        assembled,result=reassemble_motion_aligned_from_repair_plan(project,repair.id,float(blend_duration_s or .12))
        ab=ABReview(assembled.scene_id,assembled.shot_id,plan.candidate_take_id,assembled.id,
                    store.get_take(plan.candidate_take_id).media_path,assembled.media_path,
                    plan.time_s,{"motion_retiming_transition_alignment":result},status="READY_FOR_MOTION_RETIME_AB_REVIEW")
        DirectorPreviewStore(project).save(ab)
        rp=result.get("retiming_plan",{})
        msg=(f"Motion-aligned repair assembled as `{assembled.id}`. Retiming: {result.get('retiming_status')}; "
             f"speed factor: {result.get('applied_speed_factor')}; boundary certification: {result.get('boundary_certification_status')}. "
             "This is temporal alignment, not optical-flow interpolation. Compare A/B before selecting.")
        return ab.source_media_path,ab.candidate_media_path,msg,msg,""
    except Exception as exc:
        return None,None,str(exc),str(exc),toast_html(str(exc))


# --- Shot Readiness & Director Take Ranking ---------------------------------
def shot_readiness_ui(project_name,scene_id,shot_id):
    from film_lab.shot_readiness import evaluate_shot, format_shot_readiness
    project=load_project(project_name)
    try:
        report=evaluate_shot(project,str(scene_id or "scene_001"),str(shot_id or "shot_001"))
        msg=format_shot_readiness(report)
        return msg,msg,""
    except Exception as exc: return str(exc),str(exc),toast_html(str(exc))

# --- Autonomous Repair Planning & Multi-Pass QC ----------------------------
def autonomous_multi_pass_repair_ui(project_name,generator_id,max_passes,min_improvement):
    from film_lab.autonomous_repair_planner import run_multi_pass_repair, format_multi_pass_report
    project=load_project(project_name)
    try:
        plan=run_multi_pass_repair(project,generator=get_generator(generator_id),max_passes=int(max_passes or 3),min_improvement=float(min_improvement or 0.5))
        msg=format_multi_pass_report(plan)
        return msg,msg,""
    except Exception as exc: return str(exc),str(exc),toast_html(str(exc))

# --- Scene Assembly Intelligence --------------------------------------------
def scene_assembly_ui(project_name,scene_id):
    from film_lab.scene_assembly_intelligence import evaluate_scene, format_scene_assembly
    project=load_project(project_name)
    try:
        report=evaluate_scene(project,str(scene_id or 'scene_001'))
        msg=format_scene_assembly(report)
        return msg,msg,''
    except Exception as exc:
        return str(exc),str(exc),toast_html(str(exc))
