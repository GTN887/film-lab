#!/usr/bin/env python3
"""Film Lab — Liam's private local film studio (original software)."""

from __future__ import annotations

import os
from pathlib import Path

import gradio as gr

from film_lab.constants import (
    ASPECT_RATIOS,
    DEFAULT_ASPECT,
    aspect_dropdown_choices,
    CAMERA_MOVES,
    CHARACTER_TAGS,
    DEFAULT_DURATION,
    DEFAULT_LIGHTING,
    DEFAULT_PROJECT,
    INTIMACY_MODES,
    LOCAL_BANNER,
    MAX_DURATION,
    MIN_DURATION,
)
from film_lab.generators import (
    DEFAULT_GENERATOR_ID,
    generator_dropdown_choices,
)
from film_lab.luts import ensure_stock_luts
from film_lab.music import MOODS
from film_lab.project import Project, default_data_root
from film_lab.queue import GenerationQueue
from film_lab.script import REEL_STATUSES
from film_lab.genres import DEFAULT_PRIMARY, GENRE_LABELS, PRIMARY_CHOICES, examples_for
from film_lab.intensity import (
    DEFAULT_INTENSITY,
    DEFAULT_PRESET,
    INTENSITY_PRESETS,
    intensity_ui_help,
)
from film_lab.living import (
    CLEANLINESS,
    DEFAULT_LIVING_PRESET,
    DEPENDENTS,
    HOUSING_QUALITY,
    INCOME_BANDS,
    LIVING_PRESET_LABELS,
    LIVING_STYLES,
    NEIGHBORHOODS,
    PRIVACY_LEVELS,
    UTILITIES,
    WORK_PATTERNS,
    living_preset_brief,
)
from film_lab.senses import (
    DEFAULT_SENSE_PRESET,
    EMOTIONS,
    LIGHTS,
    PRESET_LABELS,
    RELATIONSHIP_TEMPS,
    SENSE_CHOICES,
    TIMES_OF_DAY,
    WEATHERS,
    sense_labels_for,
    preset_brief,
)
from film_lab.bridge import (
    AGENT_TAB_LABELS,
    BRIDGE_MODES,
    DEFAULT_AGENT,
    DEFAULT_MODE,
    agent_panel_html,
    bridge_markdown,
    connectors_status_markdown,
    mcp_stub_pretty,
    setup_prompt,
)
from film_lab.consistency import (
    DEFAULT_FACE_LOCK,
    DEFAULT_FACE_METHOD,
    FACE_METHODS,
    consistency_program_md,
    stack_markdown,
)
from film_lab.envlock import (
    DEFAULT_ENV_STRENGTH,
    DEFAULT_GEOMETRY,
    ENV_GEOMETRY,
    env_gallery_items,
    env_markdown,
    load_env_lock,
)
from film_lab.hub import (
    HUB_CARDS,
    craft_shelf_html,
    effect_labels,
    hub_chrome_html,
    hub_hero_html,
    hub_tile_html,
    local_lot_html,
    looks_shelf_html,
)
from film_lab.lighting import (
    PICKER_LABEL,
    SKIP_LABEL,
    catalog_markdown,
    expand_lighting,
    lighting_chips_html,
    mentor_markdown,
    preset_choices,
)
from film_lab.music import score_stack_markdown
from film_lab.video_tools import video_tools_markdown
from film_lab.voice import PACES, REGISTERS, VOICE_BACKENDS, voice_stack_markdown
from film_lab.animate_ux import default_ref_still, extra_allowed_paths
from film_lab.effects import (
    ASPECTS as FX_ASPECTS,
    RESOLUTIONS as FX_RESOLUTIONS,
    engine_markdown as effects_engine_markdown,
    preset_detail_md,
    preset_labels,
)
from film_lab.duration import DEFAULT_DURATION_PRESET, DURATION_PRESETS, parse_duration_preset
from film_lab.offline import boot_duration, boot_quality, offline_banner_html, repair_markdown
from film_lab.quality import DEFAULT_QUALITY, QUALITY_PRESETS, quality_debug_md
from film_lab.characters import character_choices
from film_lab.motion_scope import (
    DEFAULT_PRODUCT_BEATS,
    DEFAULT_SUBJECT,
    MOTION_SUBJECTS,
    motion_scope_help,
    product_beats_help,
)
from film_lab.product import DEFAULT_PLACE, PLACEMENTS, product_markdown
from film_lab.genetics import adult_parent_choices
from film_lab.performance import (
    BEHAVIORS,
    DEFAULT_BEHAVIOR,
    DEFAULT_MICRO,
    DEFAULT_PROP,
    MICRO_EXPRESSIONS,
    PERFORMANCE_HELP,
    PROP_ACTIONS,
)
from film_lab.dream import (
    DEFAULT_DREAM_TITLES,
    DEFAULT_PRESENTATION,
    DEFAULT_TEXT_STYLE,
    DEFAULT_VISION,
    DREAM_HELP,
    INNER_VISIONS,
    PRESENTATIONS,
    TEXT_STYLES,
    bible_actor_labels,
    dream_board_items,
    dream_markdown,
    load_dream,
)
from film_lab.ugc import UGC_ASPECT
from film_lab.variations import take_gallery_items
from film_lab.extend import BEAT_HEADERS, plan_note
from film_lab.imagine_feed import ref_chip_html, render_feed
from film_lab.filming import (
    CAST_ROLES,
    FILMING_MODES,
    MODE_EXPLICIT,
    ROLE_ADULT,
    filming_help,
)
from film_lab.director_notes import (
    DEFAULT_EARTH,
    DEFAULT_EMOTION,
    DEFAULT_OUTDOOR,
    DEFAULT_THUNDER,
    DEFAULT_WEATHER,
    DEFAULT_WARDROBE,
    DEFAULT_WIND,
    OUTDOOR_CHOICES,
    SAFETY_LINE,
    THUNDER_CHOICES,
    EARTH_CHOICES,
    WIND_CHOICES,
    cast_gallery_items,
    emotion_choices,
    load_notes,
    notes_markdown,
    wardrobe_choices,
    weather_choices,
)
from film_lab.pose import (
    DEFAULT_BODY,
    DEFAULT_FACE,
    DEFAULT_HANDS,
    body_labels,
    face_labels,
    hand_labels,
    motion_step_html,
    pose_markdown,
)
from film_lab.pipeline import (
    DEFAULT_STEP as PIPE_DEFAULT,
    STEPS as PIPE_STEPS,
    arm_shot as arm_pipeline_shot,
    step_visibilities as pipe_step_vis,
    stepper_html as pipe_stepper_html,
)
from film_lab.savelib import SHELVES as LIBRARY_SHELVES, library_help
from film_lab.setdesk import (
    DEFAULT_OUTDOOR as SET_DEFAULT_OUTDOOR,
    DEFAULT_SET_CAMERA,
    OUTDOOR_PLATES,
    SET_CAMERAS,
    set_markdown,
)
from film_lab.setbuild import (
    DEFAULT_ENV_CAMERA,
    ENV_CAMERAS,
    built_set_choices,
    storage_help,
)
from film_lab.pointer import destination_choices, pointer_markdown
from film_lab.mark import (
    DEFAULT_SHAPE,
    DEFAULT_TARGET,
    SHAPES,
    TARGETS,
    load_marks,
    marks_markdown,
)
from film_lab.voice_notes import NOTE_HELP, voice_note_markdown
from film_lab.playback import (
    DIRECT_BANNER,
    ENTER_LABEL,
    EXIT_LABEL,
    FIX_HELPER,
    MODE_PLAYBACK,
    PLAYBACK_HELP,
    play_fix_legend_html,
)
from film_lab.ui_handlers import (
    DIALOGUE_HEADERS,
    QUEUE_HEADERS,
    REEL_HEADERS,
    add_shot_to_reel,
    apply_char_living_preset_ui,
    apply_effect_shelf_ui,
    apply_pose_ui,
    apply_director_note_ui,
    apply_filming_mode_ui,
    apply_quality_ui,
    apply_aspect_ui,
    apply_mark_ui,
    apply_role_defaults_ui,
    apply_set_note_ui,
    build_locked_env_ui,
    load_locked_env_ui,
    delete_locked_env_ui,
    apply_world_note_ui,
    apply_env_lock_ui,
    apply_face_method_ui,
    family_sheet_ui,
    import_character_sheet_ui,
    export_character_sheet_ui,
    mark_shape_ui,
    pointer_go_to_ui,
    close_director_note_ui,
    transcribe_into_note_ui,
    apply_take_mark_ui,
    add_dream_step_ui,
    close_dream_about_ui,
    enter_dream_ui,
    fill_dream_sheet_ui,
    head_note_hint_ui,
    open_dream_about_ui,
    open_dream_sequence_ui,
    plan_dream_shots_ui,
    play_dream_seq_ui,
    stitch_dream_ui,
    enter_direct_ui,
    exit_direct_ui,
    freeze_direct_ui,
    open_take_loop_ui,
    play_take_ui,
    regenerate_direct_now,
    revise_current_take_ui,
    apply_lighting_ui,
    apply_still_lighting_ui,
    apply_finish_ui,
    apply_genre_preset_ui,
    apply_intensity_preset_ui,
    apply_living_preset_ui,
    apply_sense_preset_ui,
    assemble_reel_ui,
    build_takes_ui,
    build_writing_prompt_ui,
    char_dropdown,
    consistency_gallery,
    create_project,
    creator_acceptance_ui,
    draft_dropdown,
    enqueue_shot,
    ensure_default_project,
    examples_dropdown,
    export_scene_ui,
    export_writing_ui,
    filter_genre_examples_ui,
    insert_genre_example_ui,
    add_prompt_ui,
    auto_stitch_sequence_ui,
    apply_ugc_frame_ui,
    build_extend_plan_ui,
    enhance_motion_ui,
    enhance_writing_ui,
    continue_extend_now,
    generate_amd_now,
    generate_effect_now,
    generate_extend_reel_now,
    imagine_send,
    regenerate_motion_now,
    image_family_change_ui,
    generate_fallback_now,
    generate_now,
    generate_quick_now,
    request_cancel,
    generate_writing_ui,
    generate_kids_ui,
    fuse_writing_ui,
    import_writing_ui,
    fold_voice_micro_ui,
    inject_writing_performance_ui,
    import_examples,
    import_library_ui,
    import_music_ui,
    save_scene_room_tone_ui,
    import_vo_as_sample_ui,
    import_vo_ui,
    lighting_mentor_ui,
    inherit_living_ui,
    ingest_stills,
    link_shot_to_scene,
    load_character_ui,
    load_scene_ui,
    load_shot_ui,
    load_still_notes_ui,
    load_voice_direction_ui,
    load_writing_ui,
    lut_choices,
    new_scene_ui,
    new_shot_ui,
    new_writing_ui,
    on_project_change,
    open_director_note_ui,
    backup_library_ui,
    browse_library_ui,
    connect_drive_ui,
    library_status_ui,
    open_hub_tab,
    pin_refs_ui,
    preview_clip,
    pull_scene_into_writing,
    plan_writing_shots_ui,
    push_writing_to_scene_ui,
    rebuild_reel_ui,
    run_queue_ui,
    save_and_render_cue,
    save_active_cast_ui,
    save_character_ui,
    save_scene_ui,
    save_shot_ui,
    save_still_notes_ui,
    save_takes_voice_ui,
    save_voice_profile_ui,
    save_writing_ui,
    scene_dropdown,
    set_reel_status,
    shot_dropdown,
    speak_line_ui,
    speak_tagged_ui,
    still_cloud_ui,
    motion_engine_markdown,
    status_markdown,
    voice_takes_ui,
    still_dropdowns,
    stitch_selected,
    tag_choices,
    text_family_change_ui,
    ugc_brief_dropdown,
    ugc_ingest_product_ui,
    ugc_load_brief_ui,
    ugc_push_shots_ui,
    ugc_save_brief_ui,
    ugc_write_script_ui,
    apply_motion_subject_ui,
    apply_safe_mode_ui,
    compose_product_still_ui,
    enhance_product_ui,
    generate_product_now,
    open_product_direct_ui,
    push_product_beats_ui,
    resolve_product_avatar_ui,
    use_posed_still_ui,
    writing_api_markdown,
    writing_provider_models_ui,
    connect_bridge_ui,
    refresh_bridge_ui,
    select_bridge_ui,
    clear_finished,
    clear_queue,
    gallery_choices,
    production_take_select_ui,
    production_take_action_ui,
    production_audio_cut_ui,
    production_cinema_export_ui,
    director_home_plan_ui,
    director_home_apply_ui,
    director_timeline_refresh_ui,
    director_timeline_add_performance_ui,
    director_timeline_add_camera_ui,
    director_timeline_move_ui,
    director_timeline_visual_ui,
    director_timeline_drag_ui,
    director_timeline_playback_ui,
    director_timeline_scrub_ui,
    director_timeline_frame_ui,
    director_preview_regenerate_ui,
    director_preview_accept_ui,
    director_preview_reject_ui,
    continuity_localize_repair_ui,
    continuity_execute_repair_ui,
    continuity_reassemble_segment_ui,
    continuity_reassemble_audio_segment_ui,
    continuity_seam_blend_ui,
    continuity_motion_retime_ui,
    continuity_optical_flow_ui,
    take_quality_control_ui,
    take_quality_control_repair_ui,
    autonomous_multi_pass_repair_ui,
    shot_readiness_ui,
    scene_assembly_ui,
)
from film_lab.llm import (
    DEFAULT_DUAL_ROLES,
    DEFAULT_PROVIDER,
    DUAL_ROLES,
    PROVIDERS,
    UGC_PROVIDERS,
)
from film_lab.writing import ROLEPLAY_SPEAKERS, WRITING_MODES
from film_lab.providers import (
    IMAGE_FAMILIES,
    IMAGE_FAMILY_DEFAULT,
    VIDEO_FAMILIES,
    VIDEO_FAMILY_DEFAULT,
    TEXT_DUAL,
    TEXT_FAMILIES,
    TEXT_FAMILY_DEFAULT,
    VOICE_DEFAULT,
    VOICE_PROVIDERS,
    default_image_model,
    default_text_model,
    default_video_model,
    image_models_for,
    video_models_for,
    providers_markdown,
    text_models_for,
)

PORT = int(os.environ.get("FILM_LAB_PORT", "43123"))
HOST = os.environ.get("FILM_LAB_HOST", "127.0.0.1")
CSS = (Path(__file__).resolve().parent / "film_lab" / "studio.css").read_text(encoding="utf-8")


def _pointer_controls(project, *, visible: bool = False):
    labels = bible_actor_labels(project) or character_choices(project)
    dests = destination_choices(project)
    with gr.Column(visible=visible) as box:
        gr.Markdown(pointer_markdown())
        actor = gr.Dropdown(
            choices=labels,
            value=(labels[0] if labels else None),
            label="Actor A — click to go",
        )
        dest = gr.Dropdown(
            choices=dests,
            value=(dests[0] if dests else None),
            label="Destination — bathroom / locked set / room",
        )
        btn = gr.Button("Generate go-to take", variant="primary")
    return box, actor, dest, btn


def _note_mic(kind: str) -> gr.Audio:
    return gr.Audio(
        sources=["microphone", "upload"],
        type="filepath",
        format="wav",
        label=f"Mic — speak {kind} into the same note",
        buttons=[],
        elem_classes=["fl-note-mic"],
    )


def _gene_default(project, prefer: str) -> str | None:
    for label in adult_parent_choices(project):
        if label.startswith(prefer):
            return label
    picks = adult_parent_choices(project)
    return picks[0] if picks else None


def build_ui() -> gr.Blocks:
    boot_project = ensure_default_project()
    boot_notes = load_notes(boot_project)
    boot_faces = cast_gallery_items(boot_project)
    boot_note_md = notes_markdown(boot_notes)
    boot_takes = take_gallery_items(boot_project)
    boot_marks = load_marks(boot_project)
    boot_mark_md = marks_markdown(boot_marks)
    boot_dream_md = dream_markdown(load_dream(boot_project))
    boot_dream_seq = dream_board_items(boot_project)
    boot_actors = bible_actor_labels(boot_project)
    boot_env = load_env_lock(boot_project)
    boot_env_md = env_markdown(boot_env)
    boot_env_gal = env_gallery_items(boot_project, boot_env)
    boot_q = boot_quality()
    boot_d = boot_duration()
    ensure_stock_luts()
    theme = gr.themes.Base(
        primary_hue="violet",
        secondary_hue="teal",
        neutral_hue="zinc",
    ).set(
        body_background_fill="#0a0712",
        body_background_fill_dark="#0a0712",
        background_fill_primary="#16101f",
        background_fill_primary_dark="#16101f",
        background_fill_secondary="#100c18",
        background_fill_secondary_dark="#100c18",
        block_background_fill="#16101f",
        block_background_fill_dark="#16101f",
        border_color_primary="#2a2438",
        border_color_primary_dark="#2a2438",
        body_text_color="#f2eef8",
        body_text_color_dark="#f2eef8",
        block_label_text_color="#9a93a8",
        block_label_text_color_dark="#9a93a8",
        button_primary_background_fill="#7ee8e8",
        button_primary_background_fill_dark="#7ee8e8",
        button_primary_text_color="#0b0814",
        button_primary_text_color_dark="#0b0814",
    )
    generator_choices = generator_dropdown_choices()

    with gr.Blocks(title="Film Lab", theme=theme, css=CSS, elem_id="film-lab") as demo:
        project_name = gr.State(DEFAULT_PROJECT)
        queue_state = gr.State(GenerationQueue())

        gr.HTML(hub_chrome_html())
        gr.HTML(offline_banner_html())
        with gr.Row(elem_classes=["fl-nav"]):
            project_dd = gr.Dropdown(
                label="Lot",
                show_label=False,
                choices=Project.list_names(),
                value=DEFAULT_PROJECT,
                interactive=True,
            )
            new_name = gr.Textbox(label="New folder", show_label=False, placeholder="New folder")
            create_btn = gr.Button("New project", variant="secondary")
            import_btn = gr.Button("Import studio bundle")
            home_btn = gr.Button("Home", variant="primary")
            library_btn = gr.Button("Library")

        status = gr.Markdown(
            "Ready. Local folders only. No Film Lab credits.",
            elem_classes=["fl-status"],
        )

        with gr.Tabs(selected="home") as studio_tabs:
            with gr.Tab("Home", id="home"):
                gr.HTML(hub_hero_html())
                director_plan_id = gr.State("")
                with gr.Group(elem_classes=["director-command-hero"]):
                    gr.Markdown("""## Director Command
Describe the scene the way you would direct a film crew. Film Lab will build a reviewable production plan before changing the Shot.""")
                    director_command = gr.Textbox(
                        label="What do you want to happen?",
                        placeholder="Night warehouse. Sarah hears something, runs toward the exit, then hides as the camera follows and slowly pushes in.",
                        lines=4,
                    )
                    with gr.Row():
                        director_scene_id = gr.Textbox(label="Scene", value="scene-1")
                        director_shot_id = gr.Textbox(label="Shot", value="shot-1")
                    with gr.Row():
                        director_plan_btn = gr.Button("Build Production Plan", variant="primary")
                        director_apply_btn = gr.Button("Apply Plan")
                        director_create_btn = gr.Button("Create Scene / Prepare Generate", variant="primary")
                    director_plan_review = gr.Markdown("""### Production Plan

Enter a Director instruction, then build the plan.""")
                with gr.Row(elem_classes=["hero-cta"]):
                    hero_motion = gr.Button("Open Pipeline", variant="primary")
                    hero_effects = gr.Button("Open Effects Desk")
                    hero_ugc = gr.Button("Open Cinema Desk")
                hub_btns = []
                featured, rest = HUB_CARDS[:1], HUB_CARDS[1:3]
                with gr.Row(elem_classes=["hub-row"]):
                    for card, scale, klass in (
                        (featured[0], 3, "hub-col-feature"),
                        (rest[0], 1, "hub-col"),
                        (rest[1], 1, "hub-col"),
                    ):
                        with gr.Column(scale=scale, min_width=200, elem_classes=[klass]):
                            gr.HTML(hub_tile_html(card))
                            hub_btns.append(gr.Button(card.button, elem_classes=["hub-open"]))
                with gr.Row(elem_classes=["hub-row"]):
                    for card in HUB_CARDS[3:8]:
                        with gr.Column(scale=1, min_width=180, elem_classes=["hub-col"]):
                            gr.HTML(hub_tile_html(card))
                            hub_btns.append(gr.Button(card.button, elem_classes=["hub-open"]))
                gr.HTML(craft_shelf_html())
                with gr.Row(elem_classes=["hub-row"]):
                    for card in HUB_CARDS[8:]:
                        with gr.Column(scale=1, min_width=180, elem_classes=["hub-col"]):
                            gr.HTML(hub_tile_html(card))
                            hub_btns.append(gr.Button(card.button, elem_classes=["hub-open"]))
                with gr.Group(elem_classes=["looks-shelf"]):
                    gr.HTML(looks_shelf_html())
                    with gr.Row():
                        effect_pick = gr.Radio(choices=effect_labels(), value=effect_labels()[0], label="Apply a look")
                        apply_effect_btn = gr.Button("Open look on Finish")
                with gr.Group(elem_classes=["lot-strip"]):
                    lot_md = gr.HTML(local_lot_html())
                with gr.Accordion("Machine (local probes)", open=False):
                    machine = gr.Markdown(status_markdown())
                with gr.Accordion("Repair (desktop, works offline)", open=False):
                    gr.Markdown(repair_markdown())
                    safe_mode_btn = gr.Button("Safe mode (480p / short clip)")
                gr.Markdown(
                    f"{LOCAL_BANNER} Original Film Lab names only. "
                    "Works offline for local generation. "
                    "Online optional: Grok / Gemini / ChatGPT / Claude / ElevenLabs. "
                    "Desktop: START_FILM_LAB.bat · Install Film Lab: INSTALL_FILM_LAB.bat · "
                    "Uninstall: UNINSTALL_FILM_LAB.bat. Grok Bot can patch in place. Repair: REPAIR.bat. "
                    "**Save Library** (nav) browses stills / takes / sets / writing on this PC. "
                    "OneDrive / Google Drive folders are optional backup when online."
                )

            with gr.Tab("Save Library", id="library"):
                with gr.Row():
                    lib_home_btn = gr.Button("Back to Home", variant="secondary")
                gr.Markdown(library_help())
                lib_shelf = gr.Radio(
                    list(LIBRARY_SHELVES),
                    value="Stills",
                    label="Shelf — stills / takes / sets / writing / exports",
                )
                lib_refresh = gr.Button("Browse this PC", variant="primary")
                lib_table = gr.Dataframe(
                    headers=["name", "shelf", "path", "size", "updated"],
                    label="Local files",
                    wrap=True,
                    row_count=0,
                )
                lib_gallery = gr.Gallery(
                    label="Stills and takes on this PC",
                    columns=4,
                    height=220,
                    object_fit="contain",
                )
                lib_note = gr.Markdown("Pick a shelf. Browse this PC. Drive is optional.")
                gr.Markdown(
                    "### Optional Drive folders (online)\n"
                    "Paste the folder your **OneDrive** or **Google Drive** desktop app already "
                    "syncs. Film Lab does **not** log in. local-first: if Drive is offline or "
                    "the folder is missing, backup skips that target and the PC library stays."
                )
                lib_onedrive = gr.Textbox(
                    label="OneDrive folder (optional)",
                    placeholder=r"C:\Users\Liam\OneDrive\Film Lab",
                )
                lib_gdrive = gr.Textbox(
                    label="Google Drive folder (optional)",
                    placeholder=r"C:\Users\Liam\Google Drive\Film Lab",
                )
                with gr.Row():
                    lib_one_btn = gr.Button("Connect OneDrive folder")
                    lib_g_btn = gr.Button("Connect Google Drive folder")
                    lib_backup_btn = gr.Button("Backup to Drive folders", variant="primary")
                lib_sync_md = gr.Markdown("Local-first. Drive off until you connect a folder.")

            with gr.Tab("Still Desk", id="still"):
                gr.Markdown(
                    "Drop rehearsal stills into this project. "
                    "Adult nudes, sex stills, and explicit / pornographic stills are allowed. Adults 18+ only. Nothing is uploaded."
                )
                with gr.Row(elem_classes=["fl-quality"]):
                    still_quality = gr.Dropdown(
                        list(QUALITY_PRESETS),
                        value=boot_q,
                        filterable=True,
                        label="Resolution",
                    )
                    still_aspect = gr.Dropdown(
                        choices=aspect_dropdown_choices(),
                        value=DEFAULT_ASPECT,
                        filterable=True,
                        label="Aspect",
                        elem_classes=["fl-aspect-dd"],
                    )
                gr.Markdown(quality_debug_md())
                uploads = gr.File(label="Stills", file_count="multiple", file_types=["image"])
                ingest_btn = gr.Button("Ingest into project", variant="primary")
                stills_gallery = gr.Gallery(
                    label="Project stills",
                    columns=4,
                    height=320,
                    object_fit="contain",
                    preview=True,
                )
                still_notes = gr.Textbox(
                    label="Local generate notes (this folder only)",
                    lines=5,
                    placeholder="Lock the lamp, keep wedding bands readable, generate motion later on Motion Desk.",
                )
                still_light = gr.Dropdown(
                    choices=preset_choices(),
                    value=SKIP_LABEL,
                    label=PICKER_LABEL,
                )
                with gr.Row():
                    save_still_notes_btn = gr.Button("Save still notes")
                    still_light_btn = gr.Button("Fold lighting into still notes")
                gr.Markdown(providers_markdown())
                with gr.Row(elem_classes=["fl-provider-nest"]):
                    still_family = gr.Dropdown(
                        choices=list(IMAGE_FAMILIES),
                        value=IMAGE_FAMILY_DEFAULT,
                        label="Image family",
                    )
                    still_model = gr.Dropdown(
                        choices=image_models_for(IMAGE_FAMILY_DEFAULT),
                        value=default_image_model(IMAGE_FAMILY_DEFAULT),
                        label="Model",
                    )
                still_cloud_btn = gr.Button("Cloud still (key / coming soon)")
                still_cloud_status = gr.Markdown(
                    "Local / ComfyUI: ingest stills here. Cloud families fail soft — no fake still."
                )

            with gr.Tab("Character Consistency", id="characters"):
                gr.Markdown(
                    "Character bible for programmed likeness. "
                    "**Role tags:** Mom, Dad, Teen, Adult, Child, Infant. "
                    "Regular / story filming may include under-18 roles for **non-sexual** everyday scenes. "
                    "18+ Explicit (intimacy / nude / sex) stays **adult 18+ only** — "
                    "Teen / Child / Infant never unlock those tools. "
                    "Alison and Bradley are preloaded as Adult 28. "
                    "Profiles save to the project and to `data/characters/`. "
                    "The bible injects into Motion, Still notes, UGC, 3D Set, and Director Brain. "
                    "**Zero credits.** Primary lock on 6GB AMD: start still → img2vid. "
                    "Each bible entry has its own **Voice profile** (TTS id / imported sample / notes). "
                    "**Family Genetics:** Actor A + Actress B → **What would their kids look like?** "
                    "(infant / child / teen). Regular / story only — never 18+ intimacy. "
                    "**Import / Export** this bible as Word (.docx) or PDF — character sheets and bios. "
                    "Not Excel (awkward for bios; shot lists stay on Writing Studio). "
                    "See [docs/CHARACTER_CONSISTENCY.md](docs/CHARACTER_CONSISTENCY.md) "
                    "and [docs/GENETICS.md](docs/GENETICS.md)."
                )
                gr.Markdown(consistency_program_md())
                gr.Markdown(stack_markdown())
                with gr.Row():
                    active_cast = gr.CheckboxGroup(
                        choices=["alison", "bradley"],
                        value=["alison", "bradley"],
                        label="Active cast (this project)",
                    )
                    face_lock = gr.Slider(
                        0,
                        1,
                        value=DEFAULT_FACE_LOCK,
                        step=0.05,
                        label="Face lock strength (used when ComfyUI FaceID is present; else start-still)",
                    )
                    face_method = gr.Dropdown(
                        choices=list(FACE_METHODS),
                        value=DEFAULT_FACE_METHOD,
                        label="Face method (InstantID / FaceID stub until Comfy lists nodes)",
                    )
                    save_cast_btn = gr.Button("Save active cast", variant="primary")
                    save_face_btn = gr.Button("Save face method")
                    import_lib_btn = gr.Button("Import studio library")
                with gr.Row():
                    char_pick = gr.Dropdown(label="Characters", choices=[], interactive=True)
                    load_char_btn = gr.Button("Load")
                    save_char_btn = gr.Button("Save profile", variant="primary")
                with gr.Accordion("Character sheet — Word / PDF", open=True):
                    gr.Markdown(
                        "**Import** a bio or character sheet (`.docx` / `.pdf`) into these fields. "
                        "**Export** the typed bible as Word or PDF. "
                        "Excel stays on Writing Studio — not on Character Bible."
                    )
                    char_sheet_file = gr.File(
                        label="Upload Word / PDF character sheet",
                        file_count="multiple",
                        file_types=[".docx", ".pdf"],
                    )
                    with gr.Row():
                        import_sheet_btn = gr.Button("Import Word / PDF")
                        export_sheet_fmt = gr.Radio(
                            ["Word", "PDF"],
                            value="Word",
                            label="Export Word / PDF",
                        )
                        export_sheet_btn = gr.Button("Export Word / PDF")
                    char_sheet_export = gr.File(label="Exported character sheet")
                char_id = gr.Textbox(label="Character id")
                char_name = gr.Textbox(label="Name", value="Alison")
                with gr.Row():
                    char_role = gr.Dropdown(
                        choices=list(CAST_ROLES),
                        value=ROLE_ADULT,
                        label="Role tag (Mom / Dad / Teen / Adult / Child / Infant)",
                    )
                    char_age = gr.Textbox(label="Age band", value="late 20s (adult)")
                    char_age_years = gr.Number(
                        label="Age (years)",
                        value=28,
                        precision=0,
                        minimum=0,
                        maximum=120,
                    )
                gr.Markdown(
                    "Numeric **Age (years)** plus a role tag. "
                    "Adult / Mom / Dad are 18+. Teen 13–17, Child 3–12, Infant 0–2 "
                    "are Regular-story roles only. Intimate / frank / explicit modes "
                    "require Adult 18+ and filming mode **18+ Explicit**."
                )
                char_look = gr.Textbox(label="Look / appearance", lines=2)
                char_wardrobe = gr.Textbox(label="Wardrobe", lines=2)
                char_rings = gr.Textbox(label="Rings / props", value="Wedding band on the left hand. Story prop.")
                char_personality = gr.Textbox(label="Personality", lines=2)
                char_emotion = gr.Textbox(label="Emotion baseline", lines=2)
                with gr.Row():
                    char_micro = gr.Dropdown(
                        choices=list(MICRO_EXPRESSIONS),
                        value=DEFAULT_MICRO,
                        label="Micro-expression (bible default)",
                    )
                    char_behavior = gr.Dropdown(
                        choices=list(BEHAVIORS),
                        value=DEFAULT_BEHAVIOR,
                        label="Behavior (full body)",
                    )
                char_voice = gr.Textbox(label="Voice notes / performance", lines=2)
                with gr.Accordion("Voice profile (TTS / sample)", open=True):
                    gr.Markdown(
                        "This character's film-acting voice. Tagged dialogue routes here. "
                        "Alison defaults to `en+f3`, Bradley to `en+m3`. Local TTS or import first. "
                        "Zero credits."
                    )
                    with gr.Row():
                        char_voice_backend = gr.Dropdown(
                            choices=list(VOICE_BACKENDS),
                            value="auto",
                            label="TTS backend",
                        )
                        char_voice_id = gr.Textbox(
                            label="TTS voice id",
                            placeholder="en+f3 (Alison) / en+m3 (Bradley) / Piper model path",
                        )
                    char_voice_sample_path = gr.Textbox(label="Imported sample path", interactive=False)
                    char_voice_sample_file = gr.File(
                        label="Import voice sample (WAV / MP3)",
                        file_types=["audio"],
                    )
                char_lock = gr.Textbox(label="Locked descriptor (injected into local_prompt)", lines=2)
                _nest = living_preset_brief(DEFAULT_LIVING_PRESET)
                with gr.Accordion("Living style", open=True):
                    gr.Markdown(
                        "Lifestyle of the nest. Multi-select plus custom tags. "
                        "Campus / dorm is **adult students only**."
                    )
                    with gr.Row():
                        char_live_preset = gr.Dropdown(
                            choices=list(LIVING_PRESET_LABELS),
                            value=DEFAULT_LIVING_PRESET,
                            label="Living preset",
                        )
                        apply_char_live_btn = gr.Button("Apply living preset")
                    char_styles = gr.CheckboxGroup(
                        choices=list(LIVING_STYLES),
                        value=list(_nest.styles),
                        label="Living style",
                    )
                    char_style_custom = gr.Textbox(
                        label="Custom living-style tags",
                        placeholder="IKEA leftovers, plants on the sill",
                    )
                    char_norms = gr.Textbox(
                        label="Religious / cultural household norms (optional)",
                        placeholder="Two adults. No family in the next room unless the scene asks.",
                        lines=2,
                    )
                with gr.Accordion("Living conditions", open=True):
                    gr.Markdown(
                        "Material / situational reality. Story labels only — not real income or addresses."
                    )
                    with gr.Row():
                        char_income = gr.Dropdown(choices=list(INCOME_BANDS), value=_nest.income_band, allow_custom_value=True, label="Income / financial pressure")
                        char_housing = gr.Dropdown(choices=list(HOUSING_QUALITY), value=_nest.housing_quality, allow_custom_value=True, label="Housing quality")
                        char_privacy = gr.Dropdown(choices=list(PRIVACY_LEVELS), value=_nest.privacy, allow_custom_value=True, label="Privacy")
                    with gr.Row():
                        char_clean = gr.Dropdown(choices=list(CLEANLINESS), value=_nest.cleanliness, allow_custom_value=True, label="Cleanliness / clutter")
                        char_hood = gr.Dropdown(choices=list(NEIGHBORHOODS), value=_nest.neighborhood, allow_custom_value=True, label="Neighborhood vibe")
                        char_utils = gr.Dropdown(choices=list(UTILITIES), value=_nest.utilities, allow_custom_value=True, label="Utilities & comfort")
                    with gr.Row():
                        char_deps = gr.Dropdown(choices=list(DEPENDENTS), value=_nest.dependents, allow_custom_value=True, label="Dependents / caregiving")
                        char_work = gr.Dropdown(choices=list(WORK_PATTERNS), value=_nest.work_pattern, allow_custom_value=True, label="Work pattern")
                    char_health = gr.Textbox(label="Health / accessibility notes (optional, story)", lines=2)
                    char_as_project = gr.Checkbox(
                        value=True,
                        label="Also save as project nest default (project.json)",
                    )
                with gr.Row():
                    char_uploads = gr.File(label="Pin reference stills", file_count="multiple", file_types=["image"])
                    pin_still = gr.Dropdown(label="Or pin a project still", choices=[])
                    pin_btn = gr.Button("Pin to consistency pack")
                    sheet_btn = gr.Button("Show character sheet")
                char_refs = gr.Gallery(
                    label="Character sheet / consistency pack",
                    columns=5,
                    height=220,
                    object_fit="contain",
                )
                with gr.Accordion("Family Genetics", open=True):
                    gr.Markdown(
                        "Pick **Actor A** + **Actress B** (adult 18+ face-locked refs). "
                        "Age picker: **infant / child / teen**. "
                        "**What would their kids look like?** blends the refs locally "
                        "and saves a Character Bible card that **belongs to both parents**. "
                        "Stills land on Still Desk. Regular / story only — "
                        "never route through 18+ intimacy. Not InstantID. Zero credits."
                    )
                    with gr.Row():
                        gene_actor = gr.Dropdown(
                            label="Actor A (parent)",
                            choices=adult_parent_choices(boot_project),
                            value=_gene_default(boot_project, "bradley"),
                            interactive=True,
                        )
                        gene_actress = gr.Dropdown(
                            label="Actress B (parent)",
                            choices=adult_parent_choices(boot_project),
                            value=_gene_default(boot_project, "alison"),
                            interactive=True,
                        )
                        gene_age = gr.Radio(
                            ["infant", "child", "teen"],
                            value="child",
                            label="Kid age (Regular / story)",
                        )
                    gene_name = gr.Textbox(
                        label="Child name (optional)",
                        placeholder="Leave blank for Alison & Bradley — child",
                    )
                    gene_btn = gr.Button("What would their kids look like?", variant="primary")
                    gene_gallery = gr.Gallery(
                        label="Blended child stills (local)",
                        columns=2,
                        height=220,
                        object_fit="contain",
                    )

            with gr.Tab("Pose Desk", id="pose"):
                gr.Markdown(
                    "Pose / Hand–Face adjust on the **still** before Animate. "
                    "OpenPose / ControlNet-style guide. Face lock stays via Character Bible / FaceID. "
                    "**Not** frame-by-frame video puppeting. Then Motion Desk Animate (ComfyUI SVD). "
                    "Regenerate stays on after. Zero credits. Adults 18+."
                )
                gr.HTML(motion_step_html())
                gr.Markdown(pose_markdown())
                with gr.Column(elem_classes=["fl-pose"]):
                    with gr.Row(elem_classes=["fl-pose-compare"]):
                        pose_still = gr.Image(
                            type="filepath",
                            label="Upload still",
                            height=320,
                            value=str(default_ref_still()) if default_ref_still() else None,
                        )
                        pose_after = gr.Image(
                            type="filepath",
                            label="Posed still (face pixels kept)",
                            height=320,
                            interactive=False,
                        )
                    with gr.Row():
                        pose_body = gr.Dropdown(
                            choices=body_labels(),
                            value=DEFAULT_BODY,
                            label="Body",
                        )
                        pose_hands = gr.Dropdown(
                            choices=hand_labels(),
                            value=DEFAULT_HANDS,
                            label="Hands",
                        )
                        pose_face = gr.Dropdown(
                            choices=face_labels(),
                            value=DEFAULT_FACE,
                            label="Face (tick only — no feature paint)",
                        )
                    with gr.Row():
                        pose_micro = gr.Dropdown(
                            choices=list(MICRO_EXPRESSIONS),
                            value=DEFAULT_MICRO,
                            label="Micro-expression",
                        )
                        pose_behavior = gr.Dropdown(
                            choices=list(BEHAVIORS),
                            value=DEFAULT_BEHAVIOR,
                            label="Behavior",
                        )
                    pose_path = gr.State("")
                    with gr.Row():
                        pose_apply = gr.Button("Apply pose", variant="primary")
                        pose_to_motion = gr.Button("Use posed still on Motion Desk")
                    pose_status = gr.Markdown(
                        "Upload a still, pick body / hands / face + micro-expression / behavior, Apply pose. "
                        "Then Enhance → Animate. Not video puppeting."
                    )

            with gr.Tab("3D Set Desk", id="set"):
                gr.Markdown(
                    "Virtual **3D Set** — **LOCKED Environment from photo**, then notes. "
                    "Upload a photo → invent plausible missing areas → camera "
                    "**look-around / zoom / aerial**. Optional: place Character Bible "
                    "actors and look around with them. Not a realtime 3D mesh engine. "
                    "Regular / story may include Teen / Child / Infant. Intimate tools "
                    "stay locked unless **18+ Explicit** and every cast member is 18+."
                )
                gr.Markdown(set_markdown())
                with gr.Accordion("LOCKED Environment from photo", open=True):
                    gr.Markdown(
                        "**On this PC:** `data/projects/<name>/sets/` · `stills/` · `takes/` "
                        "(offline, deletable). Also `env_lock.json` + `env_refs/`."
                    )
                    gr.Markdown(storage_help(boot_project))
                    set_env_photo = gr.Image(
                        type="filepath",
                        label="Upload photo — build the locked set",
                        height=200,
                    )
                    with gr.Row():
                        set_env_cam = gr.Radio(
                            list(ENV_CAMERAS),
                            value=DEFAULT_ENV_CAMERA,
                            label="Camera — look-around / zoom / aerial",
                        )
                        set_env_place = gr.Checkbox(
                            value=False,
                            label="Place Character Bible actors in this set",
                        )
                    set_env_cast = gr.CheckboxGroup(
                        choices=character_choices(boot_project) or ["alison", "bradley"],
                        value=[],
                        label="Actors to place (optional)",
                    )
                    with gr.Row():
                        set_env_build = gr.Button(
                            "Build locked environment",
                            variant="primary",
                        )
                        set_env_pick = gr.Dropdown(
                            choices=built_set_choices(boot_project),
                            label="Built sets on this PC",
                            interactive=True,
                        )
                        set_env_delete = gr.Button("Delete this set")
                    set_env_views = gr.Gallery(
                        label="Locked set views (this PC)",
                        columns=3,
                        height=180,
                    )
                    set_env_take = gr.Video(
                        label="Look-around / zoom / aerial take",
                        height=180,
                    )
                    set_env_store = gr.Markdown(storage_help(boot_project))
                with gr.Accordion("Pointer / Go-to", open=True):
                    set_ptr_box, set_ptr_actor, set_ptr_dest, set_ptr_btn = _pointer_controls(
                        boot_project, visible=True
                    )
                set_filming = gr.Radio(
                    list(FILMING_MODES),
                    value=MODE_EXPLICIT,
                    label="Filming mode — Regular | 18+ Explicit",
                )
                with gr.Row():
                    set_camera = gr.Radio(
                        list(SET_CAMERAS),
                        value=DEFAULT_SET_CAMERA,
                        label="Set camera (orbit / push / aerial)",
                    )
                    set_outdoor = gr.Dropdown(
                        choices=list(OUTDOOR_PLATES),
                        value=SET_DEFAULT_OUTDOOR,
                        label="Outdoor plate (street, sky, bus, walk home, drone aerial)",
                    )
                set_description = gr.Textbox(
                    label="Set / environment",
                    lines=3,
                    placeholder="Wet street after the bus. Porch lamp. Kitchen doorway.",
                )
                with gr.Row():
                    set_mark_role = gr.Dropdown(
                        choices=list(CAST_ROLES),
                        value=ROLE_ADULT,
                        label="Place role",
                    )
                    set_mark_who = gr.Textbox(
                        label="Character (bible id or name)",
                        placeholder="alison — Alison",
                    )
                    set_mark_where = gr.Textbox(
                        label="Mark / placement",
                        placeholder="at the bus door",
                    )
                set_apply = gr.Button("Apply 3D Set", variant="primary")
                set_status = gr.Markdown(set_markdown())
                gr.Markdown(
                    "**Environment lock** on this set. World Note reuses the same plate. "
                    "Img2vid seeds from the locked still. Regenerate keeps it."
                )
                set_env_still = gr.Image(type="filepath", label="Locked set still", height=160)
                set_env_style = gr.Image(type="filepath", label="Style / scene ref (optional)", height=120)
                set_env_geo = gr.Radio(
                    list(ENV_GEOMETRY),
                    value=DEFAULT_GEOMETRY,
                    label="Geometry (ControlNet depth / canny / softedge)",
                )
                set_env_str = gr.Slider(
                    0, 1, value=DEFAULT_ENV_STRENGTH, step=0.05, label="Env lock strength"
                )
                set_env_note = gr.Textbox(
                    label="Set note",
                    lines=2,
                    placeholder="Porch lamp. Wet asphalt. Same room across aerial retakes.",
                )
                set_env_apply = gr.Button("Apply Environment lock", variant="secondary")
                set_env_md = gr.Markdown(boot_env_md)
                set_env_gal = gr.Gallery(
                    value=boot_env_gal,
                    label="Locked set refs",
                    columns=3,
                    height=120,
                )

            with gr.Tab("Mark & Direct", id="mark"):
                gr.Markdown(
                    "**Mark & Direct** — region edit on a still or a short-clip frame. "
                    "Draw **circle / square / lasso**, or pick **pointer** to send Actor A "
                    "to a locked room (bathroom / set) and record the go-to take on Take Board. "
                    "One region note at a time (stackable). "
                    "Apply = masked prompt / regional inpaint (local overlay; Comfy inpaint "
                    "is optional and never faked). Then Motion **Animate / Regenerate**. "
                    "Works with Pose + Director Note. Regular vs **18+ Explicit** still applies. "
                    "Type or speak the region note (actor / prop / object)."
                )
                gr.Markdown(voice_note_markdown())
                gr.HTML(motion_step_html())
                mk_mark_status = gr.Markdown(boot_mark_md)
                with gr.Row():
                    mk_mark_still = gr.Image(
                        type="filepath",
                        label="Still",
                        height=280,
                        value=str(default_ref_still()) if default_ref_still() else None,
                    )
                    mk_mark_clip = gr.File(
                        label="Or short clip (first frame)",
                        file_types=["video"],
                    )
                    mk_mark_preview = gr.Image(
                        type="filepath",
                        label="Marked still",
                        height=280,
                        interactive=False,
                    )
                mk_mark_shape = gr.Radio(list(SHAPES), value=DEFAULT_SHAPE, label="Shape — circle / square / lasso / pointer")
                mk_ptr_box, mk_ptr_actor, mk_ptr_dest, mk_ptr_btn = _pointer_controls(boot_project)
                with gr.Row(visible=True) as mk_mark_sliders:
                    mk_mark_cx = gr.Slider(0, 1, value=0.50, step=0.01, label="Center X")
                    mk_mark_cy = gr.Slider(0, 1, value=0.42, step=0.01, label="Center Y")
                    mk_mark_size = gr.Slider(0.04, 0.8, value=0.28, step=0.01, label="Size")
                mk_mark_editor = gr.ImageEditor(
                    type="pil",
                    label="Lasso — brush the region on the still",
                    height=280,
                    visible=False,
                )
                mk_mark_target = gr.Dropdown(choices=list(TARGETS), value=DEFAULT_TARGET, label="Region (clothing, body, face emotion, prop action…)")
                mk_mark_prop = gr.Dropdown(
                    choices=list(PROP_ACTIONS),
                    value=DEFAULT_PROP,
                    label="Prop action — pick up book from still or clip",
                )
                mk_mark_note = gr.Textbox(
                    label="Region note — typed or voice (actor / prop / object)",
                    lines=2,
                    placeholder="pick up book from this still. Jacket stays. Face holds the look.",
                )
                mk_mark_mic = _note_mic("prop / object / clothing")
                gr.Markdown(NOTE_HELP)
                with gr.Row():
                    mk_mark_apply = gr.Button("Apply mark", variant="primary")
                    mk_enter_dream = gr.Button("Enter dream")
                    mk_to_motion = gr.Button("Use marked still on Motion Desk")

            with gr.Tab("Script", id="script"):
                gr.Markdown(
                    "Fountain-ish desk: scene heading, action, character / parenthetical / dialogue, director notes. "
                    "Link shots already on the shot desk. Export `.fountain`, `.txt`, or `.pdf`."
                )
                with gr.Row():
                    scene_pick = gr.Dropdown(label="Scenes", choices=[], interactive=True)
                    load_scene_btn = gr.Button("Load scene")
                    new_scene_btn = gr.Button("New scene")
                    save_scene_btn = gr.Button("Save scene", variant="primary")
                scene_id = gr.Textbox(label="Scene id")
                scene_heading = gr.Textbox(label="Scene heading", value="INT. BEDROOM - NIGHT")
                scene_action = gr.Textbox(label="Action", lines=4)
                scene_lines = gr.Dataframe(
                    headers=DIALOGUE_HEADERS,
                    datatype=["str", "str", "str"],
                    row_count=3,
                    column_count=3,
                    label="Dialogue",
                    wrap=True,
                )
                scene_notes = gr.Textbox(label="Director notes", lines=3)
                with gr.Row():
                    scene_status = gr.Radio(list(REEL_STATUSES), value="idea", label="Scene status")
                    scene_shot_ids = gr.Textbox(label="Linked shot ids (comma-separated)")
                with gr.Row():
                    link_shot_pick = gr.Dropdown(label="Shot to link", choices=[])
                    link_btn = gr.Button("Link shot → scene")
                fountain_preview = gr.Textbox(label="Fountain preview", lines=10)
                with gr.Row():
                    export_fmt = gr.Radio(["fountain", "txt", "pdf"], value="fountain", label="Export format")
                    export_btn = gr.Button("Export scene")
                export_file = gr.File(label="Exported file")

            with gr.Tab("Director Brain", id="brain"):
                gr.Markdown(
                    "Writing Studio — screenplay, novel, book→pages, rehearsal, director rewrite. "
                    "**Import** PDF / Word / PowerPoint / Excel / text, or paste Grok online + Gemini "
                    "and **Fuse** into one script, novel, or **beat sheet**. "
                    "**Export** Word, PDF, PowerPoint, Excel, or plain text. "
                    "Edit, then **Plan shots** → Motion / Take Board. "
                    "Story **genre** plus **emotion, senses, and environment** compose one local director brief. "
                    "Pick a **primary genre** plus optional secondary tags; they inject into every prompt pack. "
                    "YA / New adult / coming-of-age / theatrical teen film are labeled "
                    "**18+ protagonists only** (college senior, newly adult — not high-school minors). "
                    "Prompts always build locally and inject the Alison/Bradley bible. "
                    "Live generation is optional (Grok / Gemini / ChatGPT / Claude / Dual) with **your** keys. "
                    "**No Film Lab credits.** **No NSFW filter.** "
                    "Adult explicit sex is allowed. Adults 18+ only. "
                    "Content intensity is a director dial, not a ratings board and not a refusal gate."
                )
                writing_api = gr.Markdown(writing_api_markdown())
                with gr.Row():
                    draft_pick = gr.Dropdown(label="Saved drafts", choices=[], interactive=True)
                    load_draft_btn = gr.Button("Load draft")
                    new_draft_btn = gr.Button("New draft")
                    save_draft_btn = gr.Button("Save draft")
                write_id = gr.Textbox(label="Draft id")
                write_title = gr.Textbox(label="Title", value="Bedroom study")
                write_mode = gr.Radio(list(WRITING_MODES), value="screenplay", label="Mode")
                with gr.Row(elem_classes=["fl-provider-nest"]):
                    write_provider = gr.Radio(
                        list(PROVIDERS),
                        value=DEFAULT_PROVIDER,
                        label="Writing family (your keys — no Film Lab credits)",
                    )
                    write_model = gr.Dropdown(
                        choices=text_models_for(TEXT_FAMILY_DEFAULT),
                        value=default_text_model(TEXT_FAMILY_DEFAULT),
                        label="Chat model",
                    )
                    write_dual_roles = gr.Dropdown(
                        choices=list(DUAL_ROLES),
                        value=DEFAULT_DUAL_ROLES,
                        label="Dual roles (used when Dual is selected)",
                    )
                gr.Markdown(
                    "Local templates always work. Grok needs `FILM_LAB_XAI_API_KEY`. "
                    "Gemini needs `FILM_LAB_GEMINI_API_KEY` (or `GEMINI_API_KEY` / `GOOGLE_API_KEY`). "
                    "ChatGPT needs `FILM_LAB_OPENAI_API_KEY` (or `OPENAI_API_KEY`). "
                    "Claude needs `FILM_LAB_ANTHROPIC_API_KEY` (or `ANTHROPIC_API_KEY`). "
                    "Default Dual: Gemini writes the story spine, Grok expands dialogue and roleplay. "
                    "ChatGPT can take the spine, a sequential pass, or a compare page. "
                    "Generate with a cloud provider **leaves this machine** to that API. "
                    "Film Lab never meters those calls."
                )
                with gr.Accordion("Genre — primary + tags", open=True):
                    gr.Markdown(
                        "Catalog covers literary through erotica and experimental. "
                        "Young adult / New adult / adult coming-of-age / theatrical teen film "
                        "require **18+ characters** (college senior, 18–19+, newly adult). "
                        "Intimate or nude study plus minor-coded text is blocked."
                    )
                    with gr.Row():
                        write_primary = gr.Dropdown(
                            choices=list(PRIMARY_CHOICES),
                            value=DEFAULT_PRIMARY,
                            label="Primary genre",
                        )
                        apply_genre_btn = gr.Button("Apply genre preset")
                    write_secondary = gr.CheckboxGroup(
                        choices=list(GENRE_LABELS),
                        value=[],
                        label="Secondary genres / subgenres",
                    )
                    write_custom = gr.Textbox(
                        label="Custom genre tags",
                        placeholder="chamber piece, marriage study, lamp-lit",
                    )
                    write_tropes = gr.Textbox(
                        label="Tropes checklist (editable)",
                        lines=4,
                        placeholder="Apply a preset, then edit.",
                    )
                    with gr.Row():
                        write_examples = gr.Dropdown(
                            choices=examples_for(DEFAULT_PRIMARY, []),
                            value=(examples_for(DEFAULT_PRIMARY, []) or [None])[0],
                            label="Example prompts (filtered by genre)",
                            allow_custom_value=True,
                        )
                        insert_example_btn = gr.Button("Insert example into source")
                _bedroom = preset_brief(DEFAULT_SENSE_PRESET)
                with gr.Accordion("Emotion & senses", open=True):
                    gr.Markdown(
                        "Direct actors who **feel the room**. Primary feeling plus a conflicting one. "
                        "Inner state vs outer behavior is the subtext. Enable only the senses this set needs."
                    )
                    with gr.Row():
                        write_sense_preset = gr.Dropdown(
                            choices=list(PRESET_LABELS),
                            value=DEFAULT_SENSE_PRESET,
                            label="Emotion / environment preset",
                        )
                        apply_sense_btn = gr.Button("Apply room preset")
                    write_sensory_pass = gr.Checkbox(
                        value=_bedroom.sensory_pass,
                        label="Sensory pass — mandatory multi-sense detail grounded in this environment",
                    )
                    with gr.Row():
                        write_emotion = gr.Dropdown(
                            choices=list(EMOTIONS),
                            value=_bedroom.primary_emotion,
                            allow_custom_value=True,
                            label="Primary emotion",
                        )
                        write_emotion2 = gr.Dropdown(
                            choices=list(EMOTIONS),
                            value=_bedroom.secondary_emotion,
                            allow_custom_value=True,
                            label="Secondary / conflicting emotion",
                        )
                        write_intensity = gr.Slider(
                            0,
                            1,
                            value=_bedroom.intensity,
                            step=0.05,
                            label="Intensity",
                        )
                    write_rel_temp = gr.Dropdown(
                        choices=list(RELATIONSHIP_TEMPS),
                        value=_bedroom.relationship_temp,
                        allow_custom_value=True,
                        label="Relationship temperature",
                    )
                    with gr.Row():
                        write_inner = gr.Textbox(
                            label="Inner state (what they feel)",
                            value=_bedroom.inner_state,
                            lines=2,
                        )
                        write_outer = gr.Textbox(
                            label="Outer behavior (what we see)",
                            value=_bedroom.outer_behavior,
                            lines=2,
                        )
                    write_senses = gr.CheckboxGroup(
                        choices=list(SENSE_CHOICES),
                        value=sense_labels_for(_bedroom.enabled_senses),
                        label="Senses to write (sight stays balanced so it does not dominate)",
                    )
                    with gr.Row():
                        write_touch = gr.Textbox(label="Touch notes", value=_bedroom.touch_notes, lines=2)
                        write_smell = gr.Textbox(label="Smell notes", value=_bedroom.smell_notes, lines=2)
                    with gr.Row():
                        write_taste = gr.Textbox(label="Taste notes", value=_bedroom.taste_notes, lines=2)
                        write_hearing = gr.Textbox(label="Hearing notes", value=_bedroom.hearing_notes, lines=2)
                    write_sight = gr.Textbox(label="Sight notes (keep secondary to other enabled senses)", value=_bedroom.sight_notes, lines=2)
                with gr.Accordion("Environment", open=True):
                    gr.Markdown(
                        "Couple every enabled sense to this set. Do not invent a different room."
                    )
                    write_location = gr.Textbox(
                        label="Location / set",
                        value=_bedroom.location,
                        placeholder="INT. BEDROOM - NIGHT",
                    )
                    with gr.Row():
                        write_tod = gr.Dropdown(
                            choices=list(TIMES_OF_DAY),
                            value=_bedroom.time_of_day,
                            allow_custom_value=True,
                            label="Time of day",
                        )
                        write_weather = gr.Dropdown(
                            choices=list(WEATHERS),
                            value=_bedroom.weather,
                            allow_custom_value=True,
                            label="Weather",
                        )
                        write_light = gr.Dropdown(
                            choices=list(LIGHTS),
                            value=_bedroom.light,
                            allow_custom_value=True,
                            label="Light quality",
                        )
                    write_ambient = gr.Textbox(label="Ambient sound", value=_bedroom.ambient_sound)
                    write_blocking = gr.Textbox(label="Spatial blocking", value=_bedroom.blocking, lines=2)
                    write_props = gr.Textbox(
                        label="Props that trigger senses",
                        value=_bedroom.props,
                        placeholder="sheets, coffee, wet asphalt",
                    )
                with gr.Accordion("Living style & conditions", open=True):
                    gr.Markdown(
                        "The nest. Inherit from selected character bible + project defaults, "
                        "or override for this scene. Couples to sensory pass "
                        "(thin walls → hearing; cramped → touch)."
                    )
                    with gr.Row():
                        write_live_preset = gr.Dropdown(
                            choices=list(LIVING_PRESET_LABELS),
                            value=DEFAULT_LIVING_PRESET,
                            label="Living preset",
                        )
                        apply_write_live_btn = gr.Button("Apply living preset")
                        inherit_live_btn = gr.Button("Inherit from bible / scene")
                    write_live_override = gr.Checkbox(
                        value=False,
                        label="Override nest for this draft (else inherit from characters → scene → project.json)",
                    )
                    write_live_styles = gr.CheckboxGroup(
                        choices=list(LIVING_STYLES),
                        value=[],
                        label="Living style",
                    )
                    write_live_custom = gr.Textbox(label="Custom living-style tags")
                    write_live_norms = gr.Textbox(label="Household / cultural norms (optional)", lines=2)
                    with gr.Row():
                        write_live_income = gr.Dropdown(choices=list(INCOME_BANDS), value="unspecified", allow_custom_value=True, label="Income / pressure")
                        write_live_housing = gr.Dropdown(choices=list(HOUSING_QUALITY), value="unspecified", allow_custom_value=True, label="Housing")
                        write_live_privacy = gr.Dropdown(choices=list(PRIVACY_LEVELS), value="unspecified", allow_custom_value=True, label="Privacy")
                    with gr.Row():
                        write_live_clean = gr.Dropdown(choices=list(CLEANLINESS), value="unspecified", allow_custom_value=True, label="Cleanliness")
                        write_live_hood = gr.Dropdown(choices=list(NEIGHBORHOODS), value="unspecified", allow_custom_value=True, label="Neighborhood")
                        write_live_utils = gr.Dropdown(choices=list(UTILITIES), value="unspecified", allow_custom_value=True, label="Utilities")
                    with gr.Row():
                        write_live_deps = gr.Dropdown(choices=list(DEPENDENTS), value="unspecified", allow_custom_value=True, label="Dependents")
                        write_live_work = gr.Dropdown(choices=list(WORK_PATTERNS), value="unspecified", allow_custom_value=True, label="Work pattern")
                    write_live_health = gr.Textbox(label="Health / accessibility (story, optional)", lines=2)
                with gr.Row():
                    write_scene = gr.Dropdown(
                        label="Linked scene",
                        choices=[""],
                        value="",
                        allow_custom_value=True,
                    )
                    pull_scene_btn = gr.Button("Pull scene into source")
                    write_chars = gr.CheckboxGroup(
                        choices=["alison", "bradley"],
                        value=["alison", "bradley"],
                        label="Bible ids to inject",
                    )
                write_filming = gr.Radio(
                    list(FILMING_MODES),
                    value=MODE_EXPLICIT,
                    label="Filming mode — Regular | 18+ Explicit",
                )
                gr.Markdown(filming_help())
                with gr.Column(visible=True) as write_explicit_tools:
                    write_intimacy = gr.Radio(
                        list(INTIMACY_MODES),
                        value="covered sheets",
                        label="Intimacy / sex mode (what's available on camera)",
                    )
                with gr.Group(elem_classes=["fl-enhance"]):
                    write_idea = gr.Textbox(
                        label="Short idea to enhance",
                        lines=2,
                        placeholder="Two adults in the lamp. She tells him not to move.",
                    )
                    enhance_brain_btn = gr.Button("Enhance prompt", variant="primary")
                    write_before = gr.Textbox(label="Before", lines=2, interactive=False)
                    gr.Markdown(
                        "Enhance expands the idea with bible tags (Alison / Bradley), "
                        "camera, lighting, emotion. Edit the User prompt, then Generate pages. "
                        "Adult 18+ intimate is allowed. No Film Lab NSFW filter. Zero credits."
                    )
                    gr.Markdown(intensity_ui_help())
                    write_intensity_preset = gr.Radio(
                        list(INTENSITY_PRESETS),
                        value=DEFAULT_PRESET,
                        label="Content intensity preset (creative guide — not MPAA)",
                    )
                    write_content_intensity = gr.Slider(
                        0,
                        1,
                        value=DEFAULT_INTENSITY,
                        step=0.01,
                        label="Content intensity — intimate / explicit: adult 18+ ONLY",
                    )
                with gr.Row():
                    write_tone = gr.Textbox(label="Tone (from genre preset or rewrite)", placeholder="held, warm, unhurried")
                    write_pacing = gr.Textbox(label="Pacing", placeholder="let the lamp work")
                    write_speaker = gr.Radio(list(ROLEPLAY_SPEAKERS), value="Director", label="Roleplay speaker")
                write_source = gr.Textbox(
                    label="Source / excerpt / scene pages",
                    lines=8,
                    placeholder="Paste a book excerpt, or pull the Script desk scene.",
                )
                write_notes = gr.Textbox(label="Director / chapter notes", lines=3)
                with gr.Accordion("Micro-expression & behavior", open=False):
                    gr.Markdown(PERFORMANCE_HELP)
                    with gr.Row():
                        write_micro = gr.Dropdown(
                            choices=list(MICRO_EXPRESSIONS),
                            value=DEFAULT_MICRO,
                            label="Micro-expression",
                        )
                        write_behavior = gr.Dropdown(
                            choices=list(BEHAVIORS),
                            value=DEFAULT_BEHAVIOR,
                            label="Behavior",
                        )
                        write_prop = gr.Dropdown(
                            choices=list(PROP_ACTIONS),
                            value=DEFAULT_PROP,
                            label="Prop action",
                        )
                    write_perf_btn = gr.Button("Inject into notes")
                with gr.Accordion("Dream beat sheet", open=False):
                    gr.Markdown(DREAM_HELP)
                    write_dream_titles = gr.Textbox(
                        label="Dream scenes (comma list)",
                        value=", ".join(DEFAULT_DREAM_TITLES),
                        placeholder="island, meet crush, talk",
                    )
                    write_dream_sleeper = gr.Dropdown(
                        choices=character_choices(boot_project),
                        value=_gene_default(boot_project, "alison")
                        or (character_choices(boot_project)[0] if character_choices(boot_project) else None),
                        label="Sleeper (parent take)",
                        allow_custom_value=True,
                    )
                    with gr.Row():
                        fill_dream_btn = gr.Button("Fill dream beat sheet")
                        plan_dream_btn = gr.Button("Plan dream shots → Take Board", variant="primary")
                with gr.Row():
                    build_prompt_btn = gr.Button("Build prompt pack")
                    generate_write_btn = gr.Button(
                        "Generate pages (local templates, or API if Ready)",
                        variant="primary",
                    )
                write_system = gr.Textbox(label="System prompt (local until Generate)", lines=5)
                write_user = gr.Textbox(label="User prompt (local until Generate)", lines=8)
                with gr.Accordion("Import & Fuse", open=True):
                    gr.Markdown(
                        "Paste **Grok online** + **Gemini** (or any chat) and **Fuse** into one draft. "
                        "**Import** PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx), or text. "
                        "RTF later. Local merge — no API, works offline. Then edit, "
                        "**Plan shots → Motion Desk**, or Open Take Board. "
                        "Intimate / explicit: adult 18+ ONLY."
                    )
                    fuse_a = gr.Textbox(
                        label="Draft A (e.g. Grok online)",
                        lines=8,
                        placeholder="Paste pages from Grok online…",
                    )
                    fuse_b = gr.Textbox(
                        label="Draft B (e.g. Gemini)",
                        lines=8,
                        placeholder="Paste pages from Gemini…",
                    )
                    fuse_c = gr.Textbox(
                        label="Draft C (optional)",
                        lines=5,
                        placeholder="Third draft or a rewrite",
                    )
                    fuse_files = gr.File(
                        label="Upload PDF / Word / PowerPoint / Excel / text",
                        file_count="multiple",
                        file_types=[
                            ".pdf",
                            ".docx",
                            ".pptx",
                            ".xlsx",
                            ".txt",
                            ".md",
                            ".markdown",
                        ],
                    )
                    fuse_target = gr.Radio(
                        ["screenplay", "novel", "beat sheet"],
                        value="screenplay",
                        label="Fuse target",
                    )
                    with gr.Row():
                        import_write_btn = gr.Button("Import")
                        fuse_btn = gr.Button("Fuse into one draft", variant="primary")
                write_body = gr.Textbox(label="Draft body (generate, fuse, or paste from chat)", lines=16)
                rp_line = gr.Textbox(label="Roleplay line to send", placeholder="Stay like that.")
                rp_chat = gr.Chatbot(label="Rehearsal takes", height=240)
                rp_state = gr.State([])
                with gr.Row():
                    export_write_fmt = gr.Radio(
                        [
                            "Word",
                            "PDF",
                            "PowerPoint",
                            "Excel",
                            "plain text",
                            "fountain",
                            "md",
                        ],
                        value="Word",
                        label="Export",
                    )
                    export_write_btn = gr.Button("Export draft")
                    push_scene_btn = gr.Button("Push body → Script scene")
                    plan_shots_btn = gr.Button("Plan shots → Motion Desk", variant="primary")
                    write_to_takes = gr.Button("Open Take Board")
                    takes_voice_btn = gr.Button("Save takes → Voice")
                write_export = gr.File(label="Exported draft")

            with gr.Tab("AI Production Pipeline", id="pipeline", elem_id="tab-pipeline"):
                with gr.Row(elem_classes=["fl-pipe-nav"]):
                    pipe_home_btn = gr.Button("Back to Home", variant="secondary")
                    pipe_to_motion = gr.Button("Full Motion Desk")
                gr.Markdown(
                    "One Pipeline desk. **Enhance | Pose | Animate** on the **same shot** — "
                    "no re-upload when you change steps. Upload the still once. "
                    "Back to Home when you are done. Local SVD-XT. Zero credits. "
                    "Intimate / explicit: adult 18+ ONLY. "
                    "Sidecar Off → honest toast, no Ken Burns auto-fallback. "
                    "Quality, duration, Director Note, and Mark live on Full Motion Desk."
                )
                pipe_step_html = gr.HTML(pipe_stepper_html(PIPE_DEFAULT))
                pipe_still = gr.Image(
                    type="filepath",
                    label="This shot — upload once",
                    height=380,
                    value=str(default_ref_still()) if default_ref_still() else None,
                    elem_classes=["fl-pipe-still"],
                )
                pipe_step = gr.Radio(
                    list(PIPE_STEPS),
                    value=PIPE_DEFAULT,
                    label="Enhance | Pose | Animate",
                    elem_classes=["fl-pipe-stepper"],
                )
                with gr.Group(visible=True, elem_classes=["fl-pipe-panel"]) as pipe_enhance_box:
                    gr.Markdown(
                        "Write the motion for **this still**. Enhance expands it for SVD-XT. "
                        "The frame stays. Next step is Pose or Animate — same shot."
                    )
                    pipe_prompt = gr.Textbox(
                        label="Prompt",
                        lines=4,
                        placeholder="Slow kiss. Don't cut. Keep her hand on his chest.",
                    )
                    pipe_enhanced = gr.Textbox(
                        label="Enhanced prompt (same shot — edit, then Animate)",
                        lines=5,
                        placeholder=(
                            "Enhance writes the dense img2vid line here. "
                            "Same still. No second upload."
                        ),
                    )
                    gr.Markdown(
                        "Three dropdowns — no button grids. pick one or skip lighting. "
                        "Aspect options show a small frame icon (square, tall, landscape, ultrawide). "
                        "Aspect: 16:9, 9:16, 1:1, 4:5, 3:2, 2:3, 4:3, 3:4, 21:9, "
                        "2.39:1 cinema scope, 1.85:1. "
                        "Resolution: 480p, 720p, 1080p, 1440p, 4K. "
                        "Lighting: one searchable dropdown — None — skip, Rembrandt, "
                        "overcast, neon noir, prestige-TV night, space-opera rim, "
                        "and the full studio / natural + cinematic pack."
                    )
                    with gr.Row(elem_classes=["fl-pipe-locks"]):
                        pipe_aspect = gr.Dropdown(
                            choices=aspect_dropdown_choices(),
                            value=DEFAULT_ASPECT,
                            filterable=True,
                            label="Aspect",
                            elem_classes=["fl-aspect-dd"],
                        )
                        pipe_quality = gr.Dropdown(
                            choices=list(QUALITY_PRESETS),
                            value=boot_q,
                            filterable=True,
                            label="Resolution",
                        )
                        pipe_lighting = gr.Dropdown(
                            choices=preset_choices(),
                            value=SKIP_LABEL,
                            filterable=True,
                            label=PICKER_LABEL,
                        )
                    pipe_enhance_btn = gr.Button("Enhance", variant="primary")
                with gr.Group(visible=False, elem_classes=["fl-pipe-panel"]) as pipe_pose_box:
                    gr.Markdown(
                        "Pose the **same still**. No re-upload. Face lock stays. "
                        "Skip on a can, poster, or product-only frame. Not video puppeting."
                    )
                    with gr.Row():
                        pipe_pose_body = gr.Dropdown(
                            choices=body_labels(),
                            value=DEFAULT_BODY,
                            label="Body",
                        )
                        pipe_pose_hands = gr.Dropdown(
                            choices=hand_labels(),
                            value=DEFAULT_HANDS,
                            label="Hands",
                        )
                        pipe_pose_face = gr.Dropdown(
                            choices=face_labels(),
                            value=DEFAULT_FACE,
                            label="Face",
                        )
                    with gr.Row():
                        pipe_pose_micro = gr.Dropdown(
                            choices=list(MICRO_EXPRESSIONS),
                            value=DEFAULT_MICRO,
                            label="Micro-expression",
                        )
                        pipe_pose_behavior = gr.Dropdown(
                            choices=list(BEHAVIORS),
                            value=DEFAULT_BEHAVIOR,
                            label="Behavior",
                        )
                    pipe_apply_pose = gr.Button("Apply pose", variant="primary")
                    pipe_pose_preview = gr.Image(
                        type="filepath",
                        label="Posed still (this shot)",
                        height=180,
                        interactive=False,
                    )
                    pipe_pose_status = gr.Markdown(
                        "Apply pose writes over this shot. Then Enhance or Animate. "
                        "No re-upload."
                    )
                with gr.Group(visible=False, elem_classes=["fl-pipe-panel"]) as pipe_animate_box:
                    gr.Markdown(
                        "Animate **this same shot**. ComfyUI SVD-XT. "
                        "Sidecar Off → honest toast, no Ken Burns auto-fallback."
                    )
                    pipe_animate_btn = gr.Button("Animate", variant="primary")
                    pipe_video = gr.Video(
                        label="Take",
                        buttons=["download"],
                        autoplay=True,
                        loop=True,
                    )
                    pipe_download = gr.File(label="Download MP4 (DaVinci / After Effects)")

            with gr.Tab("Motion Desk", id="motion"):
                gr.Markdown(
                    "Any still → **Animate**: people, products, cans, posters. "
                    "Upload → **Pose adjust** (people) → Enhance → Animate. "
                    "Still-first OpenPose-style guide, then **Add Prompt** / **Generate**. "
                    "Duration lock: 5s / 10s / 15s / 20s / 30s one pass; "
                    "**1 min** (60s reel) / **2 min** (120s reel) = last-frame chain + stitch. "
                    "**Regenerate** is always on (new seed, same still + prompt). "
                    "Filming mode **Regular | 18+ Explicit** sits before the intensity dial. "
                    "**Director Note** can undress through motion into explicit sex "
                    "(18+ Explicit + Explicit dial + adult cast). **World Note** is mise-en-scène "
                    "including aerial / outdoor plates. "
                    "Loop: Upload still → Director/World Note → **Mark & Direct** → Pose → Enhance → Animate. "
                    "Then click the take on **Take Board** to play. Pause freezes — it does not edit. "
                    "**Mark & Direct** · Fix this frame. **Revise this take** opens Director Note on Motion. "
                    "Product + person ads: **UGC Ads Desk**. No marketplace. "
                    "Not video puppeting. Local ComfyUI SVD-XT. Zero credits."
                )
                gr.Markdown(motion_scope_help())
                motion_subject = gr.Radio(
                    list(MOTION_SUBJECTS),
                    value=DEFAULT_SUBJECT,
                    label="Still kind — any still → Animate",
                )
                gr.HTML(motion_step_html())
                motion_filming = gr.Radio(
                    list(FILMING_MODES),
                    value=MODE_EXPLICIT,
                    label="Filming mode — Regular | 18+ Explicit",
                )
                gr.Markdown(filming_help())
                gr.Markdown(SAFETY_LINE)
                motion_cast_faces = gr.Gallery(
                    value=boot_faces,
                    label="Cast faces — click for Director Note",
                    columns=4,
                    height=140,
                    object_fit="cover",
                    allow_preview=False,
                    elem_classes=["fl-cast-faces"],
                )
                motion_notes_md = gr.Markdown(boot_note_md)
                with gr.Accordion("World Note (Background)", open=False, elem_classes=["fl-world-note"]):
                    gr.Markdown(
                        "Mise-en-scène / environment direction: weather, thunder, earth, "
                        "wind, setting, placement. Same Apply path as Director Note."
                    )
                    with gr.Row():
                        md_world_weather = gr.Dropdown(
                            choices=weather_choices(),
                            value=boot_notes.world.weather or DEFAULT_WEATHER,
                            label="Weather",
                        )
                        md_world_thunder = gr.Dropdown(
                            choices=list(THUNDER_CHOICES),
                            value=boot_notes.world.thunder or DEFAULT_THUNDER,
                            label="Thunder",
                        )
                    with gr.Row():
                        md_world_earth = gr.Dropdown(
                            choices=list(EARTH_CHOICES),
                            value=boot_notes.world.earth or DEFAULT_EARTH,
                            label="Earth",
                        )
                        md_world_wind = gr.Dropdown(
                            choices=list(WIND_CHOICES),
                            value=boot_notes.world.wind or DEFAULT_WIND,
                            label="Wind",
                        )
                    md_world_setting = gr.Textbox(
                        label="Setting",
                        value=boot_notes.world.setting,
                        placeholder="Thin-wall bedroom, lamp, rain on the sash",
                    )
                    md_world_placement = gr.Textbox(
                        label="Placement",
                        value=boot_notes.world.placement,
                        placeholder="She at the window. He on the bed.",
                    )
                    md_world_outdoor = gr.Dropdown(
                        choices=list(OUTDOOR_CHOICES),
                        value=boot_notes.world.outdoor or DEFAULT_OUTDOOR,
                        label="Outdoor / aerial plate (street, sky, bus, walk home, drone)",
                    )
                    md_world_prop = gr.Dropdown(
                        choices=list(PROP_ACTIONS),
                        value=boot_notes.world.prop_action or DEFAULT_PROP,
                        label="Prop action (pick up book / glass / door)",
                    )
                    md_world_apply = gr.Button("Apply World Note", variant="secondary")
                    gr.Markdown("**Environment lock** — same plate for World Note + 3D Set. RX 5600 XT.")
                    md_env_still = gr.Image(type="filepath", label="Locked set still", height=140)
                    md_env_style = gr.Image(type="filepath", label="Style / scene ref (optional)", height=120)
                    md_env_geo = gr.Radio(
                        list(ENV_GEOMETRY),
                        value=DEFAULT_GEOMETRY,
                        label="Geometry (ControlNet depth / canny / softedge)",
                    )
                    md_env_str = gr.Slider(
                        0, 1, value=DEFAULT_ENV_STRENGTH, step=0.05, label="Env lock strength"
                    )
                    md_env_note = gr.Textbox(
                        label="Set note",
                        lines=2,
                        placeholder="Same lamp, same street. Hold the room across takes.",
                    )
                    md_env_apply = gr.Button("Apply Environment lock", variant="secondary")
                    md_env_md = gr.Markdown(boot_env_md)
                    md_env_gal = gr.Gallery(
                        value=boot_env_gal,
                        label="Locked set refs",
                        columns=3,
                        height=120,
                    )
                with gr.Row(elem_classes=["fl-motion-desk"]):
                    with gr.Column(scale=3, min_width=280, elem_classes=["fl-motion-rail"]):
                        idea = gr.Textbox(
                            label="Prompt",
                            lines=4,
                            placeholder="Slow kiss. Don't cut. Keep her hand on his chest.",
                        )
                        with gr.Group(elem_classes=["fl-quality"]):
                            motion_quality = gr.Dropdown(
                                list(QUALITY_PRESETS),
                                value=boot_q,
                                filterable=True,
                                label="Resolution",
                            )
                            aspect = gr.Dropdown(
                                choices=aspect_dropdown_choices(),
                                value=DEFAULT_ASPECT,
                                filterable=True,
                                label="Aspect",
                                elem_classes=["fl-aspect-dd"],
                            )
                            gr.Markdown(
                                "RX 5600 XT — AMD, not NVIDIA. Prefer native **480p / 720p**. "
                                "**4K** is export upscale, never native SVD. "
                                "Aspect sticks on the shot card — Regenerate keeps it unless you change it."
                            )
                            with gr.Accordion("Quality program / DEBUG CHECKLIST", open=False):
                                quality_help_md = gr.Markdown(quality_debug_md())
                        with gr.Column(elem_classes=["fl-provider-nest"]):
                            video_family = gr.Dropdown(
                                choices=list(VIDEO_FAMILIES),
                                value=VIDEO_FAMILY_DEFAULT,
                                label="Video family",
                            )
                            video_model = gr.Dropdown(
                                choices=video_models_for(VIDEO_FAMILY_DEFAULT),
                                value=default_video_model(VIDEO_FAMILY_DEFAULT),
                                label="Video model",
                            )
                        multi_shot = gr.Checkbox(
                            label="Multi-shot (local reel / Take Board — not a hosted pack)",
                            value=False,
                        )
                        duration_preset = gr.Radio(
                            list(DURATION_PRESETS),
                            value=boot_d,
                            label="Duration (1 min / 2 min = chain + stitch)",
                        )
                        send_btn = gr.Button("Generate", variant="primary", elem_classes=["fl-send"])
                        regen_btn = gr.Button(
                            "Regenerate",
                            elem_classes=["fl-regen"],
                        )
                        with gr.Accordion("Prompt Enhancement", open=False):
                            with gr.Row(elem_classes=["fl-provider-nest"]):
                                enhance_family = gr.Dropdown(
                                    choices=[f for f in TEXT_FAMILIES if f != TEXT_DUAL],
                                    value=TEXT_FAMILY_DEFAULT,
                                    label="Enhance family (Local default · online optional)",
                                )
                                enhance_model = gr.Dropdown(
                                    choices=text_models_for(TEXT_FAMILY_DEFAULT),
                                    value=default_text_model(TEXT_FAMILY_DEFAULT),
                                    label="Enhance model",
                                )
                            lighting_enhance = gr.Dropdown(
                                choices=preset_choices(),
                                value=SKIP_LABEL,
                                label=PICKER_LABEL,
                            )
                        with gr.Accordion("Image family", open=False):
                            image_family = gr.Dropdown(
                                choices=list(IMAGE_FAMILIES),
                                value=IMAGE_FAMILY_DEFAULT,
                                label="Image / generation family",
                            )
                            image_model = gr.Dropdown(
                                choices=image_models_for(IMAGE_FAMILY_DEFAULT),
                                value=default_image_model(IMAGE_FAMILY_DEFAULT),
                                label="Image / generation model",
                            )
                        with gr.Row(elem_classes=["fl-stage-dock"]):
                            generate_btn = gr.Button("Animate", elem_classes=["fl-animate"])
                            quick_btn = gr.Button("Quick Animate", elem_classes=["fl-quick"])
                    with gr.Column(scale=7, min_width=420, elem_classes=["fl-imagine"]):
                        with gr.Column(elem_classes=["fl-imagine-still"]):
                            motion_image = gr.Image(
                                type="filepath",
                                label="Reference still",
                                show_label=False,
                                height=420,
                                value=str(default_ref_still()) if default_ref_still() else None,
                                elem_classes=["fl-stage-still"],
                            )
                            add_prompt_btn = gr.Button(
                                "Add Prompt",
                                elem_classes=["fl-add-prompt"],
                            )
                        with gr.Accordion("Pose / Hand–Face adjust", open=True, elem_classes=["fl-pose-acc"]):
                            gr.Markdown(
                                "Pose adjust on a **person** still **before** Enhance / Animate. "
                                "Skip on a can, poster, or product-only still. "
                                "OpenPose-style skeleton. Face lock stays on people. Not video puppeting."
                            )
                            with gr.Row():
                                md_pose_body = gr.Dropdown(
                                    choices=body_labels(),
                                    value=DEFAULT_BODY,
                                    label="Body",
                                )
                                md_pose_hands = gr.Dropdown(
                                    choices=hand_labels(),
                                    value=DEFAULT_HANDS,
                                    label="Hands",
                                )
                                md_pose_face = gr.Dropdown(
                                    choices=face_labels(),
                                    value=DEFAULT_FACE,
                                    label="Face",
                                )
                            with gr.Row():
                                md_pose_micro = gr.Dropdown(
                                    choices=list(MICRO_EXPRESSIONS),
                                    value=DEFAULT_MICRO,
                                    label="Micro-expression",
                                )
                                md_pose_behavior = gr.Dropdown(
                                    choices=list(BEHAVIORS),
                                    value=DEFAULT_BEHAVIOR,
                                    label="Behavior",
                                )
                            md_apply_pose = gr.Button("Apply pose", variant="secondary")
                            md_pose_preview = gr.Image(
                                type="filepath",
                                label="Posed still",
                                height=180,
                                interactive=False,
                            )
                            md_pose_status = gr.Markdown(
                                "Apply pose, then Enhance, then Animate. Regenerate stays on."
                            )
                        with gr.Accordion("Mark & Direct", open=False, elem_classes=["fl-mark-acc"]):
                            gr.Markdown(
                                "Region edit on this still or a short-clip frame. "
                                "Circle / square / lasso. One note at a time — stackable. "
                                "Apply, then Animate / Regenerate. Regular vs 18+ Explicit."
                            )
                            md_mark_clip = gr.File(label="Or pull first frame from a short clip", file_types=["video"])
                            md_mark_shape = gr.Radio(list(SHAPES), value=DEFAULT_SHAPE, label="Shape — circle / square / lasso / pointer")
                            md_ptr_box, md_ptr_actor, md_ptr_dest, md_ptr_btn = _pointer_controls(boot_project)
                            with gr.Row(visible=True) as md_mark_sliders:
                                md_mark_cx = gr.Slider(0, 1, value=0.50, step=0.01, label="Center X")
                                md_mark_cy = gr.Slider(0, 1, value=0.42, step=0.01, label="Center Y")
                                md_mark_size = gr.Slider(0.04, 0.8, value=0.28, step=0.01, label="Size")
                            md_mark_editor = gr.ImageEditor(
                                type="pil",
                                label="Lasso — brush the region",
                                height=220,
                                visible=False,
                            )
                            md_mark_target = gr.Dropdown(choices=list(TARGETS), value=DEFAULT_TARGET, label="Region")
                            md_mark_prop = gr.Dropdown(
                                choices=list(PROP_ACTIONS),
                                value=DEFAULT_PROP,
                                label="Prop action — pick up book",
                            )
                            md_mark_note = gr.Textbox(
                                label="Region note — typed or voice (actor / prop / object)",
                                lines=2,
                                placeholder="pick up book from this still. Clothing stays. Hold the look.",
                            )
                            md_mark_mic = _note_mic("prop / object / clothing")
                            md_mark_apply = gr.Button("Apply mark", variant="secondary")
                            md_mark_preview = gr.Image(
                                type="filepath",
                                label="Marked still",
                                height=160,
                                interactive=False,
                            )
                            md_mark_status = gr.Markdown(boot_mark_md)
                        feed_html = gr.HTML(render_feed([]), elem_classes=["fl-feed-host"])
                        feed_state = gr.State([])
                        attached_ref = gr.State("")
                        with gr.Column(elem_id="fl-stage", elem_classes=["fl-imagine-stage"]):
                            result_video = gr.Video(
                                label="Take",
                                show_label=False,
                                buttons=["download"],
                                autoplay=True,
                                loop=True,
                                visible=False,
                                elem_classes=["fl-stage-clip"],
                            )
                            revise_take_btn = gr.Button(
                                "Revise this take",
                                elem_classes=["fl-revise-take"],
                            )
                            gr.Markdown(
                                "**Revise this take** opens Director Note + Pose on Motion. "
                                "It is not Fix this frame. Pause on the player never edits. "
                                "Fix this frame lives on **Take Board → Mark & Direct**."
                            )
                            motion_takes = gr.Gallery(
                                value=boot_takes,
                                label="Takes — click for Director Note (not Fix this frame)",
                                columns=3,
                                height=140,
                                object_fit="cover",
                                allow_preview=False,
                                elem_classes=["fl-takes"],
                            )
                            with gr.Column(visible=False, elem_classes=["fl-overlay"]) as overlay:
                                with gr.Row(elem_classes=["fl-gen-pill"]):
                                    progress_md = gr.Markdown("Generating… 0%")
                                    cancel_btn = gr.Button("Cancel", elem_classes=["fl-cancel"])
                        ref_chip = gr.HTML(ref_chip_html(""))
                    motion_download = gr.File(
                        label="Download MP4 (DaVinci / After Effects)",
                        visible=True,
                    )
                    with gr.Accordion("Extended reel · 60s / 120s", open=False, elem_classes=["fl-extend"]):
                        gr.Markdown(
                            "One SVD pass is seconds. Pick **1 min** (60s reel) or **2 min** "
                            "(120s reel) on the rail — Generate builds the chain. "
                            "Or build the shot list here, continue from the last frame, stitch. "
                            "Not Ken Burns. Crash notes: docs/CRASH_RECOVERY.md."
                        )
                        plan_md = gr.Markdown(plan_note(60))
                        beat_table = gr.Dataframe(
                            headers=list(BEAT_HEADERS),
                            label="Shot list (beat sheet → N clips)",
                            wrap=True,
                            row_count=0,
                        )
                        with gr.Row():
                            build_plan_btn = gr.Button("Build shot list", variant="primary")
                            continue_btn = gr.Button("Continue from last frame")
                            generate_reel_btn = gr.Button("Generate remaining + stitch")
                    with gr.Accordion("Prompt Enhancement (edit after Send)", open=False):
                        enhance_btn = gr.Button("Enhance only (no clip)")
                        enhance_before = gr.Textbox(
                            label="Before",
                            lines=2,
                            interactive=False,
                        )
                        intent = gr.Textbox(
                            label="Enhanced prompt (img2vid line — edit, then Animate)",
                            lines=6,
                            placeholder=(
                                "Send writes the cinematic paragraph into the feed, "
                                "then this dense line for SVD-XT. Edit and Animate if you want another take."
                            ),
                        )
                with gr.Row():
                    ugc_frame_btn = gr.Button("Use 9:16 UGC")
                    duration = gr.Slider(
                        MIN_DURATION,
                        MAX_DURATION,
                        value=DEFAULT_DURATION,
                        step=0.5,
                        label="Per-clip SVD for 1 min / 2 min chains (2–4s recommended on 6GB)",
                    )
                with gr.Accordion("Motion engine", open=False):
                    gr.Markdown(motion_engine_markdown())
                with gr.Accordion("Shot card", open=False):
                    with gr.Row():
                        saved_shots = gr.Dropdown(label="Saved shots", choices=[], interactive=True)
                        load_shot_btn = gr.Button("Load shot")
                        new_shot_btn = gr.Button("New shot")
                    shot_id = gr.Textbox(label="Shot id", interactive=False)
                    name = gr.Textbox(label="Shot name", value="Untitled shot")
                    shot_scene = gr.Dropdown(label="Linked scene", choices=[""], value="")
                    with gr.Row():
                        start_frame = gr.Dropdown(label="Project still (or drop a reference above)", choices=[])
                        end_frame = gr.Dropdown(label="End frame (optional)", choices=[""], value="")
                    with gr.Row():
                        start_hint = gr.Textbox(label="Start-frame hint", placeholder="Wide of the bed, lamp, both under the duvet")
                        end_hint = gr.Textbox(label="End-frame hint", placeholder="Optional landing still")
                    camera = gr.Radio(list(CAMERA_MOVES), value="slow push-in", label="Camera move")
                    strength = gr.Slider(0, 1, value=0.55, step=0.05, label="Subject motion strength")
                    body = gr.Textbox(
                        label="Body motion notes",
                        placeholder="breathing, kiss, weight shift, hips, hands, penetration",
                        lines=3,
                    )
                    with gr.Column(visible=True) as motion_explicit_tools:
                        intimacy = gr.Radio(
                            list(INTIMACY_MODES),
                            value="covered sheets",
                            label="Intimacy / sex mode — nude / sex / explicit: adult 18+ ONLY",
                        )
                        shot_intensity_preset = gr.Radio(
                            list(INTENSITY_PRESETS),
                            value=DEFAULT_PRESET,
                            label="Content intensity — intimate / explicit: adult 18+ ONLY",
                        )
                        shot_content_intensity = gr.Slider(
                            0,
                            1,
                            value=DEFAULT_INTENSITY,
                            step=0.01,
                            label="Content intensity slider (0–1) — porn intensity is adult 18+ ONLY",
                        )
                    tags = gr.CheckboxGroup(choices=list(CHARACTER_TAGS), value=list(CHARACTER_TAGS), label="Character tags")
                    char_ids = gr.CheckboxGroup(choices=["alison", "bradley"], value=["alison", "bradley"], label="Character bible ids")
                    shot_face_lock = gr.Slider(
                        0,
                        1,
                        value=DEFAULT_FACE_LOCK,
                        step=0.05,
                        label="Face lock strength (start-still primary; FaceID stub when sidecar has nodes)",
                    )
                    lighting_pick = gr.Dropdown(
                        choices=preset_choices(),
                        value=SKIP_LABEL,
                        label=PICKER_LABEL,
                    )
                    lighting = gr.Textbox(label="Lighting (injected chip, empty = skip)", value="")
                    with gr.Row():
                        negative = gr.Textbox(
                            label="Negative (optional — quality / age only, not an NSFW gate)",
                            lines=2,
                        )
                        seed = gr.Number(label="Seed (optional)", precision=0, value=None)
                    with gr.Row():
                        dialogue_cue = gr.Textbox(label="Dialogue cue (timeline note)")
                        dialogue_start = gr.Number(label="Dialogue start (s)", value=0)
                        dialogue_wav = gr.Textbox(label="Attached dialogue WAV")
                    local_prompt = gr.Textbox(label="Composed local prompt (bible + desk, never uploaded)", lines=4, interactive=False)
                    refresh_refs_btn = gr.Button("Show consistency refs for this shot")
                    shot_refs = gr.Gallery(label="Pinned character refs", columns=5, height=160, object_fit="contain")
                    generator = gr.Dropdown(
                        label="Engine (queue — local SVD-XT default)",
                        choices=generator_choices,
                        value=DEFAULT_GENERATOR_ID,
                    )
                    with gr.Row():
                        save_btn = gr.Button("Save shot card")
                        queue_btn = gr.Button("Add to queue")
                with gr.Accordion("Local video tools (6GB AMD)", open=False):
                    gr.Markdown(video_tools_markdown())
                with gr.Accordion("Advanced · Ken Burns (timing only)", open=False):
                    gr.Markdown(
                        "Not actor motion. **Not the product.** "
                        "ffmpeg zoompan on the still or prompt card when you only need timing. "
                        "Primary Generate never uses this."
                    )
                    fallback_btn = gr.Button("Generate timing MP4 (Ken Burns CPU)")

            with gr.Tab("Take Board", id="takes"):
                gr.Markdown(
                    "One locked still, many takes. **Playback is the default.** "
                    "Click a take to play. Pause and scrub freeze the player — they do **not** edit. "
                    "**Pointer / Go-to:** Actor A walks to a locked room (bathroom / set) "
                    "and the take lands here. "
                    "Enter Direct only with **Mark & Direct** · Fix this frame. "
                    "Directing — changes will make a new take. Exit Direct returns to Playback; "
                    "the old take stays on this board. "
                    "Director Note (performance) is on Motion Desk — click a cast face there. "
                    "**World Note** is mise-en-scène. "
                    "**Dream about…:** pause the sleeping take, click the person. "
                    "Actor A / B / C + free text + look-refs. Linked child scenes under that sleeper. "
                    "Mark the **head** still opens a dream. "
                    "Intimate / explicit: adult 18+ ONLY. "
                    "Filming mode Regular | 18+ Explicit. Local only. Zero credits."
                )
                gr.HTML(play_fix_legend_html())
                take_filming = gr.Radio(
                    list(FILMING_MODES),
                    value=MODE_EXPLICIT,
                    label="Filming mode — Regular | 18+ Explicit",
                )
                gr.Markdown(SAFETY_LINE)
                take_mode = gr.State(MODE_PLAYBACK)
                take_player = gr.Video(
                    label="Playback — pause, then click the person to Dream about… Pause does not edit.",
                    buttons=["download"],
                    autoplay=True,
                    loop=True,
                    elem_classes=["fl-take-player"],
                )
                with gr.Row(elem_classes=["fl-play-fix-actions"]):
                    enter_direct_btn = gr.Button(ENTER_LABEL, variant="primary")
                    exit_direct_btn = gr.Button(EXIT_LABEL, visible=False)
                gr.Markdown(f"**{FIX_HELPER}** — only **{ENTER_LABEL}** enters Direct. Pause never edits.")
                take_direct_banner = gr.HTML("", elem_classes=["fl-direct-banner-host"])
                take_mode_help = gr.Markdown(PLAYBACK_HELP)
                with gr.Column(visible=False, elem_classes=["fl-direct-panel"]) as direct_panel:
                    gr.Markdown(
                        f"**{DIRECT_BANNER}.** Pause or scrub on the player, set the second, "
                        "circle / square / lasso, write the note, then Apply or Regenerate. "
                        "Exit Direct returns to Playback. The old take stays on the board."
                    )
                    with gr.Row():
                        tk_direct_time = gr.Slider(
                            0, 30, value=0, step=0.1, label="Mark at (seconds)"
                        )
                        tk_freeze_btn = gr.Button("Use this second")
                    tk_mark_frame = gr.Image(
                        type="filepath",
                        label="Frozen frame — mark this, not the paused player",
                        height=200,
                    )
                    tk_mark_shape = gr.Radio(list(SHAPES), value=DEFAULT_SHAPE, label="Shape — circle / square / lasso / pointer")
                    tk_ptr_box, tk_ptr_actor, tk_ptr_dest, tk_ptr_btn = _pointer_controls(boot_project)
                    with gr.Row(visible=True) as tk_mark_sliders:
                        tk_mark_cx = gr.Slider(0, 1, value=0.50, step=0.01, label="Center X")
                        tk_mark_cy = gr.Slider(0, 1, value=0.42, step=0.01, label="Center Y")
                        tk_mark_size = gr.Slider(0.04, 0.8, value=0.28, step=0.01, label="Size")
                    tk_mark_editor = gr.ImageEditor(
                        type="pil",
                        label="Lasso — brush the region",
                        height=200,
                        visible=False,
                    )
                    tk_mark_target = gr.Dropdown(choices=list(TARGETS), value=DEFAULT_TARGET, label="Region")
                    tk_mark_prop = gr.Dropdown(
                        choices=list(PROP_ACTIONS),
                        value=DEFAULT_PROP,
                        label="Prop action — pick up book from this frame",
                    )
                    tk_mark_note = gr.Textbox(
                        label="Region note — typed or voice (actor / prop / object)",
                        lines=2,
                        placeholder="pick up book. Jacket. Walk. Don't rush the face.",
                    )
                    tk_mark_mic = _note_mic("prop / object / clothing")
                    with gr.Row():
                        tk_mark_apply = gr.Button("Apply mark", variant="secondary")
                        tk_enter_dream = gr.Button("Enter dream", variant="primary")
                        tk_mark_regen = gr.Button("Regenerate", variant="primary")
                    tk_mark_preview = gr.Image(type="filepath", label="Marked still", height=140, interactive=False)
                    tk_mark_status = gr.Markdown(boot_mark_md)
                take_clips = gr.Gallery(
                    value=boot_takes,
                    label="Takes — click to play. Pause never edits. Fix this frame = Mark & Direct.",
                    columns=3,
                    height=160,
                    object_fit="cover",
                    allow_preview=False,
                    elem_classes=["fl-takes"],
                )
                take_cast_faces = gr.Gallery(
                    value=boot_faces,
                    label="Click person — Dream about… (pause the take first)",
                    columns=4,
                    height=140,
                    object_fit="cover",
                    allow_preview=False,
                    elem_classes=["fl-cast-faces"],
                )
                take_notes_md = gr.Markdown(boot_note_md)
                # Authoritative persistent production controls. Legacy gallery remains the visual source,
                # while these actions operate only on real registered Take records.
                production_take_id = gr.State("")
                production_take_detail = gr.Markdown("**Persistent Take:** choose a registered take")
                with gr.Row():
                    production_keep = gr.Button("Keep / Select Take", variant="primary")
                    production_review = gr.Button("Return to Review")
                    production_reject = gr.Button("Reject Take")
                production_notes = gr.Textbox(label="Director Notes (persistent)", lines=2)
                production_tags = gr.Textbox(label="Tags (comma separated)")
                production_save_notes = gr.Button("Save Notes & Tags")
                with gr.Accordion("Audio cut into this Take", open=False):
                    gr.Markdown("Explicit Director timing only. J-cut starts this Take's audio before its picture; L-cut keeps the prior Take's audio under this picture. Timing is bounded to available source handles and 2 seconds.")
                    production_cut_style = gr.Dropdown(
                        ["HARD_CUT", "J_CUT", "L_CUT", "J_L_CUT"], value="HARD_CUT", label="Cut style"
                    )
                    with gr.Row():
                        production_j_lead = gr.Slider(0.0, 2.0, value=0.0, step=0.05, label="J-cut lead (seconds)")
                        production_l_tail = gr.Slider(0.0, 2.0, value=0.0, step=0.05, label="L-cut tail (seconds)")
                    with gr.Row():
                        production_picture_in = gr.Number(value=0.0, minimum=0.0, label="Incoming picture in-point (source seconds)")
                        production_picture_out = gr.Number(value=0.0, minimum=0.0, label="Outgoing picture out-point (0 = source end)")
                    production_save_cut = gr.Button("Save Audio Cut Direction")
                production_cinema = gr.Button("Send Selected Takes to Cinema", variant="primary")
                production_cinema_file = gr.Video(label="Cinema export", interactive=False)
                with gr.Accordion("World Note (Background)", open=False, elem_classes=["fl-world-note"]):
                    gr.Markdown(
                        "Environment direction for every take from this board. "
                        "Same Apply path as Motion Desk."
                    )
                    with gr.Row():
                        tk_world_weather = gr.Dropdown(
                            choices=weather_choices(),
                            value=boot_notes.world.weather or DEFAULT_WEATHER,
                            label="Weather",
                        )
                        tk_world_thunder = gr.Dropdown(
                            choices=list(THUNDER_CHOICES),
                            value=boot_notes.world.thunder or DEFAULT_THUNDER,
                            label="Thunder",
                        )
                    with gr.Row():
                        tk_world_earth = gr.Dropdown(
                            choices=list(EARTH_CHOICES),
                            value=boot_notes.world.earth or DEFAULT_EARTH,
                            label="Earth",
                        )
                        tk_world_wind = gr.Dropdown(
                            choices=list(WIND_CHOICES),
                            value=boot_notes.world.wind or DEFAULT_WIND,
                            label="Wind",
                        )
                    tk_world_setting = gr.Textbox(
                        label="Setting",
                        value=boot_notes.world.setting,
                        placeholder="Kitchen, wet street, porch lamp",
                    )
                    tk_world_placement = gr.Textbox(
                        label="Placement",
                        value=boot_notes.world.placement,
                        placeholder="Both at the table. He stands in the door.",
                    )
                    tk_world_outdoor = gr.Dropdown(
                        choices=list(OUTDOOR_CHOICES),
                        value=boot_notes.world.outdoor or DEFAULT_OUTDOOR,
                        label="Outdoor / aerial plate",
                    )
                    tk_world_prop = gr.Dropdown(
                        choices=list(PROP_ACTIONS),
                        value=boot_notes.world.prop_action or DEFAULT_PROP,
                        label="Prop action (pick up book / glass / door)",
                    )
                    tk_world_apply = gr.Button("Apply World Note", variant="secondary")
                    gr.Markdown("**Environment lock** — reuse the locked World / 3D Set plate.")
                    tk_env_still = gr.Image(type="filepath", label="Locked set still", height=140)
                    tk_env_style = gr.Image(type="filepath", label="Style / scene ref (optional)", height=120)
                    tk_env_geo = gr.Radio(
                        list(ENV_GEOMETRY),
                        value=DEFAULT_GEOMETRY,
                        label="Geometry (ControlNet depth / canny / softedge)",
                    )
                    tk_env_str = gr.Slider(
                        0, 1, value=DEFAULT_ENV_STRENGTH, step=0.05, label="Env lock strength"
                    )
                    tk_env_note = gr.Textbox(
                        label="Set note",
                        lines=2,
                        placeholder="Hold the kitchen lamp. Same wet street.",
                    )
                    tk_env_apply = gr.Button("Apply Environment lock", variant="secondary")
                    tk_env_md = gr.Markdown(boot_env_md)
                    tk_env_gal = gr.Gallery(
                        value=boot_env_gal,
                        label="Locked set refs",
                        columns=3,
                        height=120,
                    )
                with gr.Accordion("Dream / Lucid Layer", open=True, elem_classes=["fl-dream-layer"]):
                    gr.Markdown(DREAM_HELP)
                    dream_md = gr.Markdown(boot_dream_md)
                    dream_seq = gr.Gallery(
                        value=boot_dream_seq,
                        label="Dream sequence — SLEEP → layers → WAKE. Click a layer to play or Animate.",
                        columns=4,
                        height=160,
                        object_fit="cover",
                        allow_preview=False,
                        elem_classes=["fl-dream-seq"],
                    )
                    with gr.Row():
                        dream_sleeper = gr.Dropdown(
                            choices=character_choices(boot_project),
                            value=_gene_default(boot_project, "alison")
                            or (character_choices(boot_project)[0] if character_choices(boot_project) else None),
                            label="Sleeper",
                            allow_custom_value=True,
                        )
                    dream_presentation = gr.Radio(
                        list(PRESENTATIONS),
                        value=DEFAULT_PRESENTATION,
                        label="Dream style — Enter dream / Thought bubble",
                    )
                    dream_vision = gr.Radio(
                        list(INNER_VISIONS),
                        value=DEFAULT_VISION,
                        label="Inner vision — dream / daydream / thinking / lucid",
                    )
                    dream_text_style = gr.Radio(
                        list(TEXT_STYLES),
                        value=DEFAULT_TEXT_STYLE,
                        label="Text stylize — comic bubble / soft subtitle / diary caption / none",
                    )
                    dream_titles = gr.Textbox(
                        label="Dream scenes (comma list)",
                        value=", ".join(DEFAULT_DREAM_TITLES),
                        placeholder="island, meet crush, talk",
                    )
                    dream_cast = gr.CheckboxGroup(
                        choices=["alison", "bradley"],
                        value=["alison", "bradley"],
                        label="Dream cast — any Character Bible id",
                    )
                    dream_bubble = gr.Image(
                        type="filepath",
                        label="Thought-bubble plate (presentation)",
                        height=140,
                        interactive=False,
                    )
                    with gr.Row():
                        enter_dream_btn = gr.Button("Enter dream", variant="primary")
                        stitch_dream_btn = gr.Button("Stitch sleep → dream → wake")
                take_source = gr.Dropdown(label="Source shot", choices=[])
                with gr.Row():
                    take_count = gr.Slider(2, 8, value=3, step=1, label="Number of takes")
                    take_seed = gr.Checkbox(value=True, label="Vary seed")
                    take_cam = gr.Checkbox(value=True, label="Vary camera move")
                    take_motion = gr.Checkbox(value=False, label="Vary motion strength")
                build_takes_btn = gr.Button("Build takes", variant="primary")
                take_table = gr.Dataframe(
                    headers=["id", "name", "camera", "seed", "motion"],
                    label="New takes this pass",
                    wrap=True,
                )

            with gr.Tab("Director Timeline", id="timeline"):
                gr.Markdown("""## Director Timeline
One persistent shot timeline for dialogue, voice acting, actor performance, reactions, and camera direction. Creator edits write to project state; renderer enforcement remains separately certified.""")
                with gr.Row():
                    timeline_scene = gr.Textbox(label="Scene", value="scene-1")
                    timeline_shot = gr.Textbox(label="Shot", value="shot-1")
                    timeline_refresh = gr.Button("Load / Refresh Timeline", variant="primary")
                timeline_status = gr.Markdown("Load a Scene and Shot. No demo events are inserted.")
                with gr.Row():
                    timeline_preview = gr.Video(label="Selected Take Playback", interactive=False)
                    timeline_frame = gr.Image(label="Paused frame for Mark & Direct", interactive=False)
                timeline_playhead = gr.Slider(0, 1, value=0, step=0.01, label="Playhead / Scrub (seconds)")
                with gr.Row():
                    timeline_load_take = gr.Button("Load Selected Take", variant="secondary")
                    timeline_prepare_frame = gr.Button("Pause Here → Prepare Mark & Direct Frame", variant="primary")
                with gr.Accordion("Director Preview & Regeneration", open=True):
                    gr.Markdown("Pause on the exact moment, give direction, generate a candidate Take, then A/B it against the untouched source before choosing.")
                    timeline_regen_instruction = gr.Textbox(label="Director instruction at playhead", placeholder="Sarah realizes he is lying; fear shifts into suspicion.")
                    with gr.Row():
                        timeline_regen_character = gr.Textbox(label="Character ID (optional actor-isolated mark)")
                        timeline_regen_region = gr.Textbox(label="Region ID (optional saved Mark & Direct region)")
                        timeline_regenerate = gr.Button("Regenerate From This Moment", variant="primary")
                    timeline_ab_status = gr.Markdown("No candidate generated yet.")
                    with gr.Row():
                        timeline_ab_source = gr.Video(label="A · Source Take", interactive=False)
                        timeline_ab_candidate = gr.Video(label="B · New Directed Take", interactive=False)
                    with gr.Row():
                        timeline_accept_candidate = gr.Button("Keep Candidate as Selected Take", variant="primary")
                        timeline_reject_candidate = gr.Button("Keep Source / Reject Candidate", variant="secondary")
                    with gr.Accordion("Director Quality Control", open=True):
                        gr.Markdown("Diagnose the current A/B candidate, classify the failure, and recommend the safest repair path. Film Lab never selects a repaired Take automatically.")
                        with gr.Row():
                            timeline_qc_scan = gr.Button("Analyze Take & Recommend Repair", variant="primary")
                            timeline_qc_repair = gr.Button("Repair Automatically", variant="secondary")
                        timeline_qc_status = gr.Markdown("No Quality Control decision yet.")
                        with gr.Accordion("Autonomous Repair Planning", open=False):
                            gr.Markdown("Run a bounded technical repair loop. Each pass must improve QC without a new severe regression. Film Lab never selects the final Take automatically.")
                            with gr.Row():
                                timeline_auto_max_passes = gr.Slider(1, 5, value=3, step=1, label="Maximum Repair Passes")
                                timeline_auto_min_improvement = gr.Slider(0, 5, value=0.5, step=0.5, label="Minimum QC Improvement")
                            timeline_auto_repair = gr.Button("Run Bounded Multi-Pass Repair", variant="primary")
                            timeline_auto_status = gr.Markdown("No autonomous repair plan has run yet.")
                        with gr.Accordion("Shot Readiness & Take Ranking", open=False):
                            gr.Markdown("Rank Takes from persisted QC evidence and check whether the Selected Take is technically ready for Director acceptance. Recommendations never change selection.")
                            timeline_readiness = gr.Button("Evaluate Shot Readiness", variant="primary")
                            timeline_readiness_status = gr.Markdown("Shot readiness has not been evaluated yet.")
                        with gr.Accordion("Scene Assembly Intelligence", open=False):
                            gr.Markdown("Check whether consecutive Selected Takes in this Scene are structurally ready to cut together. Film Lab samples cut boundaries and surfaces unresolved visual, semantic, continuity, and audio review without changing Take selection or exporting Cinema.")
                            timeline_scene_assembly = gr.Button("Evaluate Scene Assembly", variant="primary")
                            timeline_scene_assembly_status = gr.Markdown("Scene assembly has not been evaluated yet.")
                    with gr.Accordion("Continuity Problem → Targeted Repair", open=False):
                        gr.Markdown("Use a time-localized Full-Take continuity event to prepare a repair candidate. Film Lab preserves the existing Takes and does not claim temporal-only splicing unless the renderer proves it.")
                        with gr.Row():
                            timeline_repair_event = gr.Number(value=0, precision=0, label="Timed continuity event #")
                            timeline_repair_localize = gr.Button("Localize Problem", variant="secondary")
                        timeline_repair_instruction = gr.Textbox(label="Repair direction (optional)", placeholder="Restore the red handbag while preserving Sarah, camera, lighting, and everything else.")
                        timeline_repair_status = gr.Markdown("No repair localized yet.")
                        timeline_repair_execute = gr.Button("Generate Repair Candidate", variant="primary")
                        timeline_repair_reassemble = gr.Button("Reassemble Only Localized Segment", variant="secondary")
                        timeline_repair_reassemble_audio = gr.Button("Reassemble Segment + Repair Audio", variant="secondary")
                        timeline_seam_blend_duration = gr.Slider(0.05, 0.5, value=0.12, step=0.01, label="Seam Blend (seconds)")
                        timeline_repair_seam_blend = gr.Button("Blend & Certify Repair Seams", variant="primary")
                        timeline_repair_motion_retime = gr.Button("Align Motion Timing & Blend", variant="primary")
                        timeline_optical_flow_fps = gr.Slider(24, 120, value=60, step=1, label="Optical-Flow Interpolation FPS")
                        timeline_repair_optical_flow = gr.Button("Optical-Flow Align & Blend", variant="primary")
                from film_lab.director_timeline_editor import DRAG_TIMELINE_JS
                timeline_visual = gr.HTML("<div class=\"fl-dt-shell\"><div class=\"fl-dt-help\">Load a Scene and Shot to edit the timeline.</div></div>", elem_id="fl-director-timeline-visual", js_on_load=DRAG_TIMELINE_JS)
                timeline_drag_payload = gr.Textbox(value="", visible="hidden", elem_id="fl-timeline-drag-payload")
                timeline_drag_save = gr.Button("Save timeline drag", visible="hidden", elem_id="fl-timeline-drag-save")
                timeline_table = gr.Dataframe(headers=["Lane","Character ID","Event ID","Start s","End s","Direction"],datatype=["str","str","str","number","str","str"],interactive=False,row_count=0,label="Persistent shot timeline")
                with gr.Accordion("Add Actor Performance Beat", open=True):
                    with gr.Row():
                        tl_char_id=gr.Textbox(label="Character ID")
                        tl_char_name=gr.Textbox(label="Character Name")
                        tl_perf_time=gr.Number(label="Time (seconds)",value=0)
                    with gr.Row():
                        tl_emotion=gr.Textbox(label="Emotion")
                        tl_expression=gr.Textbox(label="Expression")
                        tl_gaze=gr.Textbox(label="Gaze")
                        tl_posture=gr.Textbox(label="Posture")
                    with gr.Row():
                        tl_gesture=gr.Textbox(label="Gesture")
                        tl_action=gr.Textbox(label="Action")
                        tl_intensity=gr.Number(label="Intensity 0–1",value=None)
                        tl_add_perf=gr.Button("Add Performance Beat",variant="primary")
                with gr.Accordion("Add Camera Direction Beat", open=True):
                    with gr.Row():
                        tl_cam_time=gr.Number(label="Time (seconds)",value=0)
                        tl_cam_move=gr.Textbox(label="Move",placeholder="push in / orbit / pan")
                        tl_cam_framing=gr.Textbox(label="Framing",placeholder="wide / medium / close")
                        tl_cam_lens=gr.Textbox(label="Lens intention",placeholder="35mm / compressed / intimate")
                    with gr.Row():
                        tl_cam_focus=gr.Textbox(label="Focus target")
                        tl_cam_follow=gr.Textbox(label="Follow Character ID")
                        tl_cam_speed=gr.Number(label="Speed 0–1",value=None)
                        tl_cam_note=gr.Textbox(label="Director note")
                        tl_add_cam=gr.Button("Add Camera Beat",variant="primary")
                with gr.Accordion("Move Existing Beat", open=False):
                    gr.Markdown("Use the lane's persistent index (0 = first saved beat in that lane/Character). This remains the accessible precision editor alongside graphical drag-and-drop.")
                    with gr.Row():
                        tl_move_lane=gr.Dropdown(choices=["dialogue","voice_acting","performance","reaction","camera"],value="dialogue",label="Lane")
                        tl_move_char=gr.Textbox(label="Character ID (required for performance)")
                        tl_move_index=gr.Number(label="Beat index",value=0,precision=0)
                        tl_move_time=gr.Number(label="New time (seconds)",value=0)
                        tl_move_btn=gr.Button("Move & Save",variant="primary")
                with gr.Row():
                    tl_to_takes=gr.Button("Open Take Board")
                    tl_to_mark=gr.Button("Open Mark & Direct")
                    tl_to_motion=gr.Button("Open Motion Desk")

            with gr.Tab("Certification", id="certification"):
                gr.Markdown(
                    "# Creator Acceptance\n"
                    "One truthful result for the real production slice. Generate normally on Motion Desk; "
                    "Film Lab automatically runs Preflight and certification. This page only reads saved evidence "
                    "and never manufactures a PASS."
                )
                acceptance_report = gr.Markdown(
                    "No certification loaded yet. Click **Refresh certification**.",
                    elem_classes=["fl-status"],
                )
                with gr.Row():
                    acceptance_refresh = gr.Button("Refresh certification", variant="primary")
                    acceptance_motion = gr.Button("Open Motion Desk")
                    acceptance_takes = gr.Button("Open Take Board")
                    acceptance_cinema = gr.Button("Open Cinema Desk")
                gr.Markdown(
                    "**PASS** requires a real validated generative render, persistent Take, selected Take, "
                    "real Cinema output, and persistence reload. Mock/import/fallback output cannot earn PASS."
                )

            with gr.Tab("Effects Desk", id="effects"):
                gr.Markdown(
                    "Character still required. Location and product optional. "
                    "Pick a preset, **Generate**. Local SVD-XT. "
                    "Download the MP4 for DaVinci or After Effects. Zero credits."
                )
                with gr.Column(elem_classes=["fl-fx"]):
                    with gr.Row():
                        fx_character = gr.Image(
                            type="filepath",
                            label="Character still (required)",
                            height=280,
                            value=str(default_ref_still()) if default_ref_still() else None,
                        )
                        fx_location = gr.Image(
                            type="filepath",
                            label="Location (optional)",
                            height=280,
                        )
                        fx_product = gr.Image(
                            type="filepath",
                            label="Product (optional)",
                            height=280,
                        )
                    fx_preset = gr.Radio(
                        preset_labels(),
                        value=preset_labels()[0],
                        label="Preset",
                        elem_classes=["fl-fx-presets"],
                    )
                    fx_preset_md = gr.Markdown(preset_detail_md(preset_labels()[0]))
                    fx_use_extra = gr.Checkbox(label="Add extra prompt", value=False)
                    fx_extra = gr.Textbox(
                        label="Extra prompt",
                        lines=2,
                        placeholder="Keep her hand on the bottle. Don't cut the face.",
                        visible=False,
                    )
                    with gr.Row():
                        fx_aspect = gr.Radio(list(FX_ASPECTS), value="9:16", label="Aspect")
                        fx_resolution = gr.Radio(
                            list(FX_RESOLUTIONS),
                            value="720",
                            label="Effects size (720 / 1080 — not the Quality lock)",
                        )
                    fx_chars = gr.CheckboxGroup(
                        choices=["alison", "bradley"],
                        value=["alison", "bradley"],
                        label="Character bible ids",
                    )
                    fx_light = gr.Dropdown(
                        choices=preset_choices(),
                        value=SKIP_LABEL,
                        label=PICKER_LABEL,
                    )
                    with gr.Row(elem_classes=["fl-provider-nest"]):
                        fx_family = gr.Dropdown(
                            choices=list(IMAGE_FAMILIES),
                            value=IMAGE_FAMILY_DEFAULT,
                            label="Image / generation family",
                        )
                        fx_model = gr.Dropdown(
                            choices=image_models_for(IMAGE_FAMILY_DEFAULT),
                            value=default_image_model(IMAGE_FAMILY_DEFAULT),
                            label="Model",
                        )
                    fx_generate = gr.Button("Generate", variant="primary", elem_classes=["fl-fx-go"])
                    with gr.Column(elem_classes=["fl-imagine-stage"]):
                        fx_video = gr.Video(
                            label="Effect take",
                            buttons=["download"],
                            autoplay=True,
                            loop=True,
                            visible=False,
                        )
                        with gr.Column(visible=False, elem_classes=["fl-overlay"]) as fx_overlay:
                            with gr.Row(elem_classes=["fl-gen-pill"]):
                                fx_progress = gr.Markdown("Generating… 0%")
                                fx_cancel = gr.Button("Cancel", elem_classes=["fl-cancel"])
                    fx_download = gr.File(label="Download MP4 (DaVinci / After Effects)")
                    with gr.Accordion("Effects engine", open=False):
                        gr.Markdown(effects_engine_markdown())

            with gr.Tab("UGC Ads Desk", id="ugc"):
                gr.Markdown(
                    "**UGC Ads / Product desk.** Product ref + avatar + prompt → "
                    "Enhance → Animate. Local composite still, then SVD-XT. "
                    "Edit the finished take with **Mark & Direct** → Regenerate. "
                    "**Zero Film Lab credits.** Adults 18+ only. **No marketplace.** "
                    "Plain image→video stays on **Motion Desk**."
                )
                gr.Markdown(product_markdown())
                gr.Markdown("### 1 · Product image")
                ugc_prod_image = gr.Image(
                    type="filepath",
                    label="Product still",
                    height=220,
                )
                gr.Markdown("### 2 · Avatar — Character Bible or upload")
                with gr.Row():
                    ugc_prod_bible = gr.Dropdown(
                        label="Avatar from Character Bible",
                        choices=character_choices(boot_project),
                        value=(character_choices(boot_project) or [None])[0],
                    )
                    ugc_prod_avatar = gr.Image(
                        type="filepath",
                        label="Or upload a picture",
                        height=180,
                    )
                    ugc_prod_avatar_view = gr.Image(
                        type="filepath",
                        label="Resolved avatar",
                        height=180,
                        interactive=False,
                    )
                ugc_prod_age = gr.Number(label="Age (years) — adults 18+", value=28, minimum=18, precision=0)
                gr.Markdown("### 3 · How product + person appear")
                ugc_prod_direction = gr.Textbox(
                    label="Prompt — typed or edit after Enhance",
                    lines=3,
                    placeholder="She holds the serum at the lamp. Don't hide the label. Soft look to camera.",
                )
                ugc_prod_name = gr.Textbox(label="Product name", placeholder="Serum / lamp oil / can")
                ugc_prod_notes = gr.Textbox(label="Product notes", lines=2, placeholder="What it does in one room.")
                ugc_prod_place = gr.Radio(list(PLACEMENTS), value=DEFAULT_PLACE, label="Product placement on the still")
                with gr.Row():
                    ugc_prod_aspect = gr.Dropdown(
                        list(ASPECT_RATIOS),
                        value=UGC_ASPECT,
                        filterable=True,
                        label="Aspect",
                    )
                    ugc_prod_quality = gr.Dropdown(
                        list(QUALITY_PRESETS),
                        value=boot_q,
                        filterable=True,
                        label="Resolution",
                    )
                with gr.Row():
                    ugc_prod_still_btn = gr.Button("Generate still", variant="secondary")
                    ugc_prod_enhance_btn = gr.Button("Enhance")
                    ugc_prod_anim_btn = gr.Button("Animate", variant="primary")
                ugc_prod_comp = gr.Image(type="filepath", label="Product still (local composite)", height=240)
                ugc_prod_video = gr.Video(label="Product take", height=240)
                with gr.Row():
                    ugc_prod_direct_btn = gr.Button("Mark & Direct this take")
                    ugc_to_motion = gr.Button("Open Motion Desk")
                    ugc_to_takes = gr.Button("Open Take Board")
                    ugc_to_cinema = gr.Button("Open Cinema Desk")
                gr.Markdown(
                    "Finished video: Take Board **Playback**, then **Mark & Direct** · Fix this frame, "
                    "then **Regenerate**. The old take stays."
                )
                gr.Markdown(product_beats_help())
                with gr.Row():
                    ugc_beat1 = gr.Image(
                        type="filepath",
                        label="Beat 1 still — can / bottle opens alone",
                        height=160,
                    )
                    ugc_beat2 = gr.Image(
                        type="filepath",
                        label="Beat 2 still — person picks up and pours",
                        height=160,
                    )
                ugc_beat1_prompt = gr.Textbox(
                    label="Beat 1 — Opens alone",
                    lines=2,
                    value=DEFAULT_PRODUCT_BEATS[0].prompt,
                )
                ugc_beat2_prompt = gr.Textbox(
                    label="Beat 2 — Pick up and pour",
                    lines=2,
                    value=DEFAULT_PRODUCT_BEATS[1].prompt,
                )
                ugc_beats_btn = gr.Button("Push two beats → Motion Desk", variant="secondary")
                with gr.Accordion("Spoken ad plan (hook → CTA)", open=False):
                    gr.Markdown(
                        "Optional five-beat script. Local templates always work. "
                        "Optional Grok / Gemini / ChatGPT / Claude use keys you own. "
                        "9:16, about 8–15 seconds after Cinema stitch."
                    )
                    with gr.Row():
                        ugc_pick = gr.Dropdown(label="Saved UGC briefs", choices=[])
                        ugc_load_btn = gr.Button("Load brief")
                        ugc_save_btn = gr.Button("Save brief")
                    ugc_id = gr.Textbox(label="Brief id", interactive=False)
                    gr.Markdown("### Plan · Product")
                    ugc_product = gr.Textbox(label="Product name", placeholder="Lamp oil / serum / app")
                    ugc_notes = gr.Textbox(label="Product notes", lines=3, placeholder="What it does in one room, one night.")
                    with gr.Row():
                        ugc_product_file = gr.File(label="Product / creator still", file_types=["image"])
                        ugc_ingest_btn = gr.Button("Ingest product still")
                        ugc_still = gr.Dropdown(label="Product still in project", choices=[], allow_custom_value=True)
                    gr.Markdown("### Plan · Creator (adults 18+ only)")
                    with gr.Row():
                        ugc_creator = gr.Textbox(label="Creator name", placeholder="Alison")
                        ugc_age = gr.Number(label="Age (years)", value=28, minimum=18, precision=0)
                    ugc_look = gr.Textbox(label="Look / wardrobe", lines=2, placeholder="late-20s adult, phone-light, lived-in kitchen")
                    gr.Markdown("### Plan · Script (spoken beats)")
                    with gr.Row(elem_classes=["fl-provider-nest"]):
                        ugc_family = gr.Dropdown(
                            choices=[f for f in TEXT_FAMILIES if f != TEXT_DUAL],
                            value=TEXT_FAMILY_DEFAULT,
                            label="Script family",
                        )
                        ugc_model = gr.Dropdown(
                            choices=text_models_for(TEXT_FAMILY_DEFAULT),
                            value=default_text_model(TEXT_FAMILY_DEFAULT),
                            label="Script model",
                        )
                        ugc_provider = gr.Textbox(
                            value=DEFAULT_PROVIDER,
                            visible=False,
                            label="Script backend",
                        )
                    ugc_write_btn = gr.Button("Write hook → CTA", variant="primary")
                    ugc_hook = gr.Textbox(label="HOOK", lines=2)
                    ugc_problem = gr.Textbox(label="PROBLEM", lines=2)
                    ugc_product_line = gr.Textbox(label="PRODUCT", lines=2)
                    ugc_proof = gr.Textbox(label="PROOF", lines=2)
                    ugc_cta = gr.Textbox(label="CTA", lines=2)
                    gr.Markdown("### Plan · Shot plan (9:16, stitch to 8–15s)")
                    ugc_plan = gr.Dataframe(
                        headers=["beat", "seconds", "aspect", "camera", "line"],
                        label="Vertical plan",
                        wrap=True,
                    )
                    ugc_push_btn = gr.Button("Push plan → Motion Desk shots", variant="primary")
                    gr.Markdown(
                        "Then generate each beat on Motion Desk with Local img2vid / AMD, "
                        "variant on Take Board, stitch on Cinema Desk."
                    )

            with gr.Tab("Lighting Desk", id="lighting"):
                gr.Markdown(
                    "Optional lighting presets. Pick one or skip. **None — skip** or pick **one** — never forced. "
                    "Full studio / natural list (Rembrandt, hard noon sun, practical bedside lamp, golden hour, neon noir) plus a cinematic pack "
                    "(anamorphic night, teal & orange, volumetric god-rays, fog / haze, "
                    "rain on glass, handheld documentary, clean studio beauty, noir venetian, "
                    "warm tungsten interior, cool moonlight exterior, prestige-TV night, "
                    "space-opera rim). Original Film Lab labels — not a show or franchise kit. "
                    "Same picker on Pipeline Enhance, Still / Motion Enhance, Effects, and Cinema. "
                    "**Adults 18+.** Zero credits. See [docs/LIGHTING.md](docs/LIGHTING.md)."
                )
                gr.HTML(lighting_chips_html())
                gr.Markdown(catalog_markdown())
                light_preset = gr.Radio(
                    choices=preset_choices(),
                    value=SKIP_LABEL,
                    label=PICKER_LABEL,
                )
                light_mentor = gr.Markdown(mentor_markdown(SKIP_LABEL))
                light_chip = gr.Textbox(
                    label="Injected chip (empty = skipped)",
                    value="",
                    interactive=False,
                )
                with gr.Row():
                    apply_light_btn = gr.Button("Lock lighting on project + shot", variant="primary")
                    light_to_motion = gr.Button("Open Motion Desk")

            with gr.Tab("Voice Desk", id="voice"):
                gr.Markdown(
                    "Per-character film acting — each bible Voice profile owns a TTS id, sample, and notes. "
                    "Tagged lines (`ALISON:` / `BRADLEY:`) route to that voice. "
                    "Local TTS if installed; **import recorded VO** is the 6GB-safe path. "
                    "Pause markup: `[2s]`, `...`, `/` for a breath. "
                    "Cinema Desk muxes every cue. See [docs/VOICE.md](docs/VOICE.md). Zero credits."
                )
                gr.Markdown(voice_stack_markdown())
                voice_provider = gr.Radio(
                    list(VOICE_PROVIDERS),
                    value=VOICE_DEFAULT,
                    label="Voice provider (Local TTS default — online optional: ElevenLabs)",
                )
                voice_character = gr.Dropdown(label="Speak as (Alison / Bradley)", choices=[])
                load_voice_dir_btn = gr.Button("Load character Voice profile")
                with gr.Accordion("Character Voice profile", open=True):
                    with gr.Row():
                        voice_backend = gr.Dropdown(
                            choices=list(VOICE_BACKENDS),
                            value="auto",
                            label="TTS backend",
                        )
                        voice_id = gr.Textbox(
                            label="TTS voice id",
                            placeholder="en+f3 / en+m3 / Piper model path",
                        )
                    voice_sample_path = gr.Textbox(label="Imported sample path", interactive=False)
                    voice_sample_file = gr.File(
                        label="Set this character's sample",
                        file_types=["audio"],
                    )
                    save_voice_profile_btn = gr.Button("Save voice profile to bible")
                voice_text = gr.Textbox(
                    label="Dialogue line",
                    lines=3,
                    placeholder="Stay like that. [1s] Don't move.",
                )
                voice_tagged = gr.Textbox(
                    label="Tagged scene lines",
                    lines=5,
                    placeholder="ALISON: Stay like that.\nBRADLEY: I'm not going anywhere.",
                )
                with gr.Row():
                    voice_intention = gr.Textbox(label="Intention", value="held want")
                    voice_breath = gr.Textbox(label="Breath", value="close-mic, audible inhale")
                    voice_micro = gr.Dropdown(
                        choices=list(MICRO_EXPRESSIONS),
                        value=DEFAULT_MICRO,
                        label="Micro-expression (folds into breath)",
                    )
                with gr.Row():
                    voice_pace = gr.Radio(list(PACES), value="unhurried", label="Pace")
                    voice_register = gr.Radio(list(REGISTERS), value="intimate", label="Register")
                    voice_intensity = gr.Slider(0, 1, value=0.45, step=0.05, label="Acting intensity")
                with gr.Row():
                    voice_start = gr.Number(label="Cue start (s)", value=0)
                    voice_shot = gr.Dropdown(label="Attach to shot", choices=[])
                    voice_scene = gr.Dropdown(label="Attach to scene", choices=[])
                    voice_takes = gr.Slider(1, 5, value=3, step=1, label="Take variants")
                with gr.Row():
                    speak_btn = gr.Button("Generate one take", variant="primary")
                    voice_takes_btn = gr.Button("Generate take variants")
                    speak_tagged_btn = gr.Button("Speak tagged scene lines")
                voice_audio = gr.Audio(label="Last take", type="filepath")
                voice_files = gr.Dropdown(label="Project dialogue files", choices=[])
                voice_import = gr.File(label="Import recorded VO", file_count="multiple", file_types=["audio"])
                with gr.Row():
                    import_vo_btn = gr.Button("Import VO into audio/dialogue")
                    import_sample_btn = gr.Button("Import VO as this character's sample")

            with gr.Tab("Score Desk", id="score"):
                gr.Markdown(
                    "Cue list: **mood, duration, intensity**. "
                    "**Import your music first** — this 6GB AMD card may struggle with MusicGen. "
                    "Local synth beds always work. Cinema Desk muxes the pick. "
                    "No hosted music subscription. See [docs/SCORE.md](docs/SCORE.md)."
                )
                gr.Markdown(score_stack_markdown())
                with gr.Row():
                    cue_name = gr.Textbox(label="Cue name", value="lamp bed")
                    cue_mood = gr.Dropdown(choices=list(MOODS), value=MOODS[0], label="Mood")
                with gr.Row():
                    cue_in = gr.Number(label="In (s)", value=0)
                    cue_out = gr.Number(label="Out (s)", value=8)
                    cue_bpm = gr.Number(label="Temp BPM", value=62)
                    cue_intensity = gr.Slider(0, 1, value=0.35, step=0.05, label="Intensity")
                cue_notes = gr.Textbox(label="Notes", placeholder="Under the establishing, diegetic-adjacent")
                music_import = gr.File(label="Import music (primary on 6GB)", file_count="multiple", file_types=["audio"])
                import_music_btn = gr.Button("Import into audio/music", variant="primary")
                render_cue_btn = gr.Button("Render local synth bed")
                music_preview = gr.Audio(label="Last bed", type="filepath")
                cue_table = gr.Dataframe(
                    headers=["id", "name", "mood", "in", "out", "bpm", "intensity", "file"],
                    label="Cue list",
                    wrap=True,
                )
                music_pick = gr.Dropdown(label="Project audio (mux / reel)", choices=[])
                with gr.Accordion("Scene Room Tone", open=True):
                    gr.Markdown("Assign a real ambient recording to one Scene. Film Lab loops it continuously under that Scene during Cinema export; it does not guess room acoustics.")
                    room_tone_scene = gr.Textbox(label="Scene ID", value="scene_001")
                    room_tone_upload = gr.File(label="Room-tone / ambient recording", file_count="single", file_types=["audio"])
                    with gr.Row():
                        room_tone_enabled = gr.Checkbox(label="Use in Cinema", value=True)
                        room_tone_gain = gr.Slider(-60, 12, value=-24, step=1, label="Bed gain (dB)")
                    with gr.Row():
                        room_tone_fade_in = gr.Slider(0, 10, value=.25, step=.05, label="Fade in (seconds)")
                        room_tone_fade_out = gr.Slider(0, 10, value=.25, step=.05, label="Fade out (seconds)")
                    room_tone_note = gr.Textbox(label="Director room-tone note", placeholder="Bedroom night recording; keep low under dialogue")
                    room_tone_save = gr.Button("Assign Room Tone to Scene", variant="primary")
                    room_tone_preview = gr.Audio(label="Assigned Scene room tone", type="filepath")
                    room_tone_status = gr.Markdown("No room tone assigned in this control yet.")

            with gr.Tab("Finish", id="finish"):
                gr.Markdown(
                    "Original stock LUTs in `data/luts/` (warm lamp, soft print, cool shadow) — not commercial packs. "
                    "Drop more `.cube` files there. VFX is ffmpeg: fade, grain, bloom, letterbox, speed."
                )
                lut_dd = gr.Dropdown(label="LUT", choices=[])
                with gr.Row():
                    vfx_op = gr.Radio(["fade", "grain", "bloom", "letterbox", "speed"], value="grain", label="VFX")
                    vfx_strength = gr.Slider(0, 1, value=0.4, label="VFX strength")
                    vfx_speed = gr.Slider(0.25, 2.5, value=1.0, label="Speed factor")
                with gr.Row():
                    do_lut = gr.Checkbox(label="Apply LUT", value=True)
                    do_vfx = gr.Checkbox(label="Apply VFX", value=False)
                finish_btn = gr.Button("Run finish on first selected gallery clip", variant="primary")
                finish_video = gr.Video(label="Finished clip", buttons=["download"])

            with gr.Tab("Queue", id="queue"):
                gr.Markdown(
                    "Generate queued shots **one after another** on this box. "
                    "Uses the Motion Desk engine (default: local SVD-XT img2vid). "
                    "No Film Lab credits."
                )
                queue_table = gr.Dataframe(
                    headers=QUEUE_HEADERS,
                    datatype=["str"] * len(QUEUE_HEADERS),
                    row_count=0,
                    wrap=True,
                    label="Generation queue",
                )
                with gr.Row():
                    run_btn = gr.Button("Run queue", variant="primary")
                    clear_done_btn = gr.Button("Clear finished")
                    clear_all_btn = gr.Button("Clear queue")

            with gr.Tab("Cinema Desk", id="cinema"):
                gr.Markdown(
                    "Gallery is every output. The **reel** is story order: scenes → shots → clips → audio. "
                    "Assemble uses stitch plus optional **Score Desk** bed and **per-character** Voice Desk mux — "
                    "Alison and Bradley never share a take. Cues land at their start times. "
                    "**Auto-stitch sequence** crossfades the Motion Desk 60s / 120s chain into one MP4. "
                    "Zero credits."
                )
                cinema_quality = gr.Dropdown(
                    list(QUALITY_PRESETS),
                    value=boot_q,
                    filterable=True,
                    label="Export resolution",
                )
                cinema_light = gr.Dropdown(
                    choices=preset_choices(),
                    value=SKIP_LABEL,
                    label="Lighting note (optional — Cinema does not re-light; skip anytime)",
                )
                gr.Markdown(
                    "RX 5600 XT Quality program — AMD, not NVIDIA. "
                    "Download / stitch / assemble scale to this Quality. "
                    "4K is an export upscale — never a native SVD pass."
                )
                gr.Markdown(quality_debug_md())
                gallery_picks = gr.CheckboxGroup(label="Outputs", choices=[])
                with gr.Row():
                    preview_btn = gr.Button("Preview first selected")
                    stitch_btn = gr.Button("Stitch selected")
                    auto_stitch_btn = gr.Button("Auto-stitch sequence", variant="primary")
                gallery_video = gr.Video(label="Preview / stitch / reel", buttons=["download"])
                download = gr.File(label="Download MP4 (DaVinci / After Effects)")
                reel_table = gr.Dataframe(headers=REEL_HEADERS, label="Reel board", wrap=True)
                with gr.Row():
                    rebuild_btn = gr.Button("Rebuild reel from scenes")
                    add_reel_btn = gr.Button("Add current saved shot to reel")
                    reel_status = gr.Radio(list(REEL_STATUSES), value="idea", label="Status for add / set")
                    reel_entry_id = gr.Textbox(label="Reel row id (from table)")
                    set_status_btn = gr.Button("Set row status")
                with gr.Row():
                    include_dialogue = gr.Checkbox(label="Mux per-character dialogue cues", value=True)
                    assemble_btn = gr.Button("Assemble reel", variant="primary")

            with gr.Tab("Director Bridge", id="bridge"):
                gr.Markdown(bridge_markdown())
                with gr.Row(elem_classes=["fl-bridge-controls"]):
                    bridge_agent = gr.Radio(
                        list(AGENT_TAB_LABELS),
                        value=DEFAULT_AGENT,
                        label="Agent",
                        elem_classes=["fl-bridge-agents"],
                    )
                    bridge_mode = gr.Radio(
                        list(BRIDGE_MODES),
                        value=DEFAULT_MODE,
                        label="MCP / CLI",
                        elem_classes=["fl-bridge-mode"],
                    )
                bridge_panel = gr.HTML(
                    agent_panel_html(DEFAULT_AGENT, DEFAULT_MODE),
                    elem_classes=["fl-bridge-host"],
                )
                bridge_prompt = gr.Textbox(
                    value=setup_prompt(DEFAULT_AGENT, DEFAULT_MODE),
                    lines=12,
                    label="Setup prompt (copy into the agent)",
                    buttons=["copy"],
                )
                with gr.Row():
                    bridge_connect = gr.Button(
                        "Connect and start creating",
                        variant="primary",
                    )
                    bridge_refresh = gr.Button("Refresh status")
                bridge_status = gr.Markdown(connectors_status_markdown())
                with gr.Accordion("Local Film Lab MCP stub (personal use)", open=False):
                    gr.Markdown(
                        "Print the same JSON with `python -m film_lab.mcp_stub`. "
                        "CLI stub: `python -m film_lab.cli init`. "
                        "Point Claude Code, OpenClaw, Hermes, or Cursor at this box. "
                        "Not a hosted plugin. Zero Film Lab credits."
                    )
                    gr.Code(mcp_stub_pretty(), language="json", label="film-lab MCP stub")

        with gr.Column(visible=False, elem_classes=["fl-note-pop"]) as director_pop:
            note_char_id = gr.State("")
            note_char_title = gr.Markdown("### Director Note")
            note_emotion = gr.Dropdown(
                choices=emotion_choices(),
                value=DEFAULT_EMOTION,
                label="Emotion",
            )
            note_beats = gr.Textbox(
                label="Acting beats — typed or voice",
                lines=4,
                placeholder="Hold the look. Don't rush the line. Weight in the hands.",
            )
            note_mic = _note_mic("actor beats")
            gr.Markdown(NOTE_HELP)
            note_wardrobe = gr.Dropdown(
                choices=wardrobe_choices(),
                value=DEFAULT_WARDROBE,
                label="Wardrobe through motion (undress / explicit sex: adult 18+ + Explicit dial)",
            )
            with gr.Row():
                note_micro = gr.Dropdown(
                    choices=list(MICRO_EXPRESSIONS),
                    value=DEFAULT_MICRO,
                    label="Micro-expression",
                )
                note_behavior = gr.Dropdown(
                    choices=list(BEHAVIORS),
                    value=DEFAULT_BEHAVIOR,
                    label="Behavior (full human)",
                )
            gr.Markdown(PERFORMANCE_HELP)
            gr.Markdown(SAFETY_LINE)
            with gr.Row():
                note_apply = gr.Button("Apply", variant="primary")
                note_close = gr.Button("Close")
        with gr.Column(visible=False, elem_classes=["fl-note-pop", "fl-dream-pop"]) as dream_pop:
            dream_pop_sleeper = gr.State("")
            dream_pop_steps = gr.State([])
            dream_pop_title = gr.Markdown("### Dream about…")
            dream_pop_style = gr.Radio(
                list(PRESENTATIONS),
                value=DEFAULT_PRESENTATION,
                label="Dream style — Enter dream / Thought bubble",
            )
            dream_pop_vision = gr.Radio(
                list(INNER_VISIONS),
                value=DEFAULT_VISION,
                label="Inner vision — dream / daydream / thinking / lucid",
            )
            dream_pop_text = gr.Radio(
                list(TEXT_STYLES),
                value=DEFAULT_TEXT_STYLE,
                label="Text stylize — comic bubble / soft subtitle / diary caption / none",
            )
            dream_pop_about = gr.Textbox(
                label="Dream about… (free text)",
                lines=3,
                placeholder="Island. Meet a crush. They talk at a lamp. Original characters only.",
            )
            dream_pop_cast = gr.CheckboxGroup(
                choices=boot_actors,
                value=boot_actors,
                label="Dream cast — Actor A / B / C (Character Bible)",
            )
            dream_pop_refs = gr.File(
                label="Look-refs — image + video (guide the dream look)",
                file_count="multiple",
                file_types=["image", "video"],
            )
            dream_pop_step = gr.Markdown("Beat 1 — first dream layer")
            with gr.Row():
                dream_pop_beat_title = gr.Textbox(
                    label="This layer title",
                    placeholder="island",
                    scale=1,
                )
                dream_pop_beat_prompt = gr.Textbox(
                    label="This layer prompt",
                    placeholder="Warm water. Original shoreline. Held look.",
                    lines=2,
                    scale=2,
                )
            dream_pop_beats_md = gr.Markdown("No dream layers yet.")
            with gr.Row():
                dream_add_beat = gr.Button("Add this beat")
                dream_open_seq = gr.Button("Open dream sequence", variant="primary")
                dream_pop_close = gr.Button("Close")
            gr.Markdown(
                "Dream style picker: **Enter dream** (they are inside the sequence) "
                "or **Thought bubble** (overlay on the sleeping shot — still, mini-clip, or styled text). "
                "Layer by layer. Inspired-only original characters. Intimate / explicit: adult 18+ ONLY."
            )
        toast = gr.HTML("", elem_classes=["fl-toast-host"])

        form_fields = [
            shot_id,
            name,
            start_frame,
            end_frame,
            duration,
            aspect,
            camera,
            strength,
            body,
            intimacy,
            shot_intensity_preset,
            shot_content_intensity,
            tags,
            lighting,
            negative,
            seed,
            intent,
            start_hint,
            end_hint,
            shot_scene,
            char_ids,
            dialogue_cue,
            dialogue_start,
            dialogue_wav,
            shot_face_lock,
        ]
        shot_intensity_preset.change(
            apply_intensity_preset_ui,
            inputs=[shot_intensity_preset, project_name, intimacy, char_ids],
            outputs=[shot_content_intensity],
        )

        acceptance_refresh.click(creator_acceptance_ui, inputs=[project_name], outputs=[acceptance_report])
        acceptance_motion.click(lambda: gr.Tabs(selected="motion"), outputs=[studio_tabs])
        acceptance_takes.click(lambda: gr.Tabs(selected="takes"), outputs=[studio_tabs])
        acceptance_cinema.click(lambda: gr.Tabs(selected="cinema"), outputs=[studio_tabs])

        core_out = [
            stills_gallery,
            start_frame,
            end_frame,
            saved_shots,
            gallery_picks,
            scene_pick,
            char_pick,
            reel_table,
            draft_pick,
            write_scene,
            take_source,
        ]

        quality_outs = [motion_quality, still_quality, cinema_quality, quality_help_md, status]
        create_btn.click(
            create_project,
            inputs=[new_name, project_name],
            outputs=[
                project_dd,
                project_name,
                *core_out,
                status,
                lot_md,
                still_notes,
                ugc_pick,
                ugc_still,
                motion_quality,
                still_quality,
                cinema_quality,
                quality_help_md,
                aspect,
                still_aspect,
            ],
        )
        project_dd.change(
            on_project_change,
            inputs=[project_dd],
            outputs=[
                project_name,
                *core_out,
                status,
                lot_md,
                still_notes,
                ugc_pick,
                ugc_still,
                motion_quality,
                still_quality,
                cinema_quality,
                quality_help_md,
                aspect,
                still_aspect,
            ],
        )
        for _quality in (motion_quality, still_quality, cinema_quality):
            _quality.change(
                apply_quality_ui,
                inputs=[project_name, _quality],
                outputs=quality_outs,
            )
        aspect_outs = [aspect, still_aspect, pipe_aspect, status]
        for _aspect in (aspect, still_aspect, pipe_aspect):
            _aspect.change(
                apply_aspect_ui,
                inputs=[project_name, _aspect],
                outputs=aspect_outs,
            )
        home_btn.click(lambda: open_hub_tab("home"), outputs=[studio_tabs])
        library_btn.click(lambda: open_hub_tab("library"), outputs=[studio_tabs]).then(
            browse_library_ui,
            inputs=[project_name, lib_shelf],
            outputs=[lib_table, lib_gallery, lib_note],
        ).then(
            library_status_ui,
            outputs=[lib_onedrive, lib_gdrive, lib_sync_md],
        )
        lib_home_btn.click(lambda: open_hub_tab("home"), outputs=[studio_tabs])
        lib_refresh.click(
            browse_library_ui,
            inputs=[project_name, lib_shelf],
            outputs=[lib_table, lib_gallery, lib_note],
        )
        lib_shelf.change(
            browse_library_ui,
            inputs=[project_name, lib_shelf],
            outputs=[lib_table, lib_gallery, lib_note],
        )
        lib_one_btn.click(
            lambda path: connect_drive_ui("onedrive", path),
            inputs=[lib_onedrive],
            outputs=[lib_onedrive, lib_sync_md, status],
        )
        lib_g_btn.click(
            lambda path: connect_drive_ui("gdrive", path),
            inputs=[lib_gdrive],
            outputs=[lib_gdrive, lib_sync_md, status],
        )
        lib_backup_btn.click(
            backup_library_ui,
            inputs=[project_name, lib_onedrive, lib_gdrive],
            outputs=[lib_sync_md, status],
        )
        safe_mode_btn.click(
            apply_safe_mode_ui,
            outputs=[
                motion_quality,
                still_quality,
                cinema_quality,
                duration_preset,
                quality_help_md,
                status,
            ],
        )
        director_plan_btn.click(
            director_home_plan_ui,
            inputs=[project_name, director_command, director_scene_id, director_shot_id],
            outputs=[director_plan_id, director_plan_review, status],
        )
        director_apply_btn.click(
            director_home_apply_ui,
            inputs=[project_name, director_plan_id],
            outputs=[director_plan_review, status],
        )
        director_create_btn.click(
            director_home_apply_ui,
            inputs=[project_name, director_plan_id],
            outputs=[director_plan_review, status],
        ).then(lambda: open_hub_tab("motion"), outputs=[studio_tabs])
        hero_motion.click(lambda: open_hub_tab("pipeline"), outputs=[studio_tabs])
        pipe_home_btn.click(lambda: open_hub_tab("home"), outputs=[studio_tabs])
        pipe_to_motion.click(lambda: open_hub_tab("motion"), outputs=[studio_tabs])
        def _pipe_step_ui(step: str):
            enh, pose, anim = pipe_step_vis(step)
            return (
                gr.update(visible=enh),
                gr.update(visible=pose),
                gr.update(visible=anim),
                pipe_stepper_html(step),
            )

        pipe_step.change(
            _pipe_step_ui,
            inputs=[pipe_step],
            outputs=[pipe_enhance_box, pipe_pose_box, pipe_animate_box, pipe_step_html],
        )
        pipe_still.change(lambda still: still, inputs=[pipe_still], outputs=[motion_image])
        pipe_prompt.change(lambda text: text, inputs=[pipe_prompt], outputs=[idea])
        pipe_quality.change(lambda value: value, inputs=[pipe_quality], outputs=[motion_quality])
        pipe_enhance_btn.click(
            lambda prompt, enhanced, look, frame, res: (
                prompt,
                enhanced or "",
                look,
                expand_lighting(look),
                frame,
                res,
            ),
            inputs=[pipe_prompt, pipe_enhanced, pipe_lighting, pipe_aspect, pipe_quality],
            outputs=[idea, intent, lighting_enhance, lighting, aspect, motion_quality],
        ).then(
            enhance_motion_ui,
            inputs=[
                project_name,
                idea,
                intent,
                enhance_family,
                enhance_model,
                aspect,
                camera,
                lighting,
                intimacy,
                char_ids,
                negative,
                feed_state,
                attached_ref,
                shot_content_intensity,
            ],
            outputs=[
                enhance_before,
                intent,
                toast,
                status,
                negative,
                feed_html,
                feed_state,
                ref_chip,
            ],
        ).then(
            lambda line: line,
            inputs=[intent],
            outputs=[pipe_enhanced],
        )
        pipe_apply_pose.click(
            apply_pose_ui,
            inputs=[
                project_name,
                pipe_still,
                pipe_pose_body,
                pipe_pose_hands,
                pipe_pose_face,
                pipe_pose_micro,
                pipe_pose_behavior,
            ],
            outputs=[
                pose_path,
                pipe_pose_preview,
                pipe_pose_status,
                motion_image,
                attached_ref,
                ref_chip,
                toast,
                status,
                start_frame,
            ],
        ).then(
            lambda posed: posed,
            inputs=[motion_image],
            outputs=[pipe_still],
        )
        hero_effects.click(lambda: open_hub_tab("effects"), outputs=[studio_tabs])
        hero_ugc.click(lambda: open_hub_tab("cinema"), outputs=[studio_tabs])
        for _card, _btn in zip(HUB_CARDS, hub_btns):
            _btn.click(lambda tid=_card.tab_id: open_hub_tab(tid), outputs=[studio_tabs])
        apply_effect_btn.click(
            apply_effect_shelf_ui,
            inputs=[effect_pick],
            outputs=[studio_tabs, lut_dd, vfx_op, vfx_strength, do_lut, do_vfx, status],
        )
        still_light_btn.click(
            apply_still_lighting_ui,
            inputs=[project_name, still_notes, still_light],
            outputs=[still_notes, status],
        )
        save_still_notes_btn.click(
            save_still_notes_ui,
            inputs=[project_name, still_notes],
            outputs=[status],
        )
        still_family.change(image_family_change_ui, inputs=[still_family], outputs=[still_model])
        still_cloud_btn.click(
            still_cloud_ui,
            inputs=[still_family, still_model],
            outputs=[still_cloud_status],
        )
        build_takes_btn.click(
            build_takes_ui,
            inputs=[project_name, take_source, take_count, take_seed, take_cam, take_motion],
            outputs=[take_source, saved_shots, take_table, status],
        )
        ugc_form = [
            ugc_id,
            ugc_product,
            ugc_notes,
            ugc_still,
            ugc_creator,
            ugc_look,
            ugc_age,
            ugc_hook,
            ugc_problem,
            ugc_product_line,
            ugc_proof,
            ugc_cta,
            ugc_provider,
        ]
        ugc_write_btn.click(
            ugc_write_script_ui,
            inputs=[project_name, *ugc_form],
            outputs=[*ugc_form, ugc_plan, ugc_pick, status],
        )
        ugc_save_btn.click(
            ugc_save_brief_ui,
            inputs=[project_name, *ugc_form],
            outputs=[ugc_id, ugc_pick, status],
        )
        ugc_load_btn.click(
            ugc_load_brief_ui,
            inputs=[project_name, ugc_pick],
            outputs=[*ugc_form, ugc_plan, status],
        )
        ugc_push_btn.click(
            ugc_push_shots_ui,
            inputs=[project_name, *ugc_form],
            outputs=[ugc_id, ugc_plan, saved_shots, take_source, ugc_pick, status],
        )
        ugc_ingest_btn.click(
            ugc_ingest_product_ui,
            inputs=[project_name, ugc_product_file],
            outputs=[ugc_still, start_frame, stills_gallery, status],
        )
        ugc_to_motion.click(lambda: open_hub_tab("motion"), outputs=[studio_tabs])
        ugc_to_takes.click(lambda: open_hub_tab("takes"), outputs=[studio_tabs])
        ugc_to_cinema.click(lambda: open_hub_tab("cinema"), outputs=[studio_tabs])
        ugc_prod_bible.change(
            resolve_product_avatar_ui,
            inputs=[project_name, ugc_prod_bible, ugc_prod_avatar],
            outputs=[ugc_prod_avatar_view, toast, status],
        )
        ugc_prod_avatar.change(
            resolve_product_avatar_ui,
            inputs=[project_name, ugc_prod_bible, ugc_prod_avatar],
            outputs=[ugc_prod_avatar_view, toast, status],
        )
        ugc_prod_still_btn.click(
            compose_product_still_ui,
            inputs=[
                project_name,
                ugc_prod_image,
                ugc_prod_bible,
                ugc_prod_avatar,
                ugc_prod_direction,
                ugc_prod_name,
                ugc_prod_notes,
                ugc_prod_place,
                ugc_prod_aspect,
                ugc_prod_quality,
                ugc_prod_age,
            ],
            outputs=[ugc_prod_comp, motion_image, start_frame, ugc_prod_direction, toast, status],
        )
        ugc_prod_enhance_btn.click(
            enhance_product_ui,
            inputs=[
                project_name,
                ugc_prod_direction,
                ugc_prod_name,
                ugc_prod_notes,
                ugc_prod_bible,
                ugc_prod_place,
                ugc_prod_aspect,
                enhance_family,
                enhance_model,
            ],
            outputs=[ugc_prod_direction, idea, toast, status],
        )
        prod_evt = ugc_prod_anim_btn.click(
            generate_product_now,
            inputs=[
                project_name,
                ugc_prod_image,
                ugc_prod_bible,
                ugc_prod_avatar,
                ugc_prod_direction,
                ugc_prod_name,
                ugc_prod_notes,
                ugc_prod_place,
                ugc_prod_aspect,
                ugc_prod_quality,
                ugc_prod_age,
                video_family,
                video_model,
            ],
            outputs=[
                ugc_prod_comp,
                motion_image,
                ugc_prod_video,
                start_frame,
                ugc_prod_direction,
                toast,
                status,
                motion_takes,
                take_clips,
            ],
            show_progress="hidden",
        )
        ugc_prod_direct_btn.click(
            open_product_direct_ui,
            inputs=[project_name, ugc_prod_video],
            outputs=[studio_tabs, take_player, toast, status],
        )
        ugc_beats_btn.click(
            push_product_beats_ui,
            inputs=[
                project_name,
                ugc_beat1,
                ugc_beat2,
                ugc_beat1_prompt,
                ugc_beat2_prompt,
                ugc_prod_name,
                ugc_prod_aspect,
                ugc_prod_quality,
                ugc_prod_image,
                ugc_prod_comp,
                ugc_prod_age,
            ],
            outputs=[saved_shots, take_source, start_frame, studio_tabs, toast, status],
        )
        ingest_btn.click(
            ingest_stills,
            inputs=[project_name, uploads, still_quality, still_aspect],
            outputs=[stills_gallery, start_frame, end_frame, status],
        )
        import_btn.click(
            import_examples,
            inputs=[project_name],
            outputs=[saved_shots, scene_pick, char_pick, write_scene, draft_pick, status],
        )

        load_char_btn.click(
            load_character_ui,
            inputs=[project_name, char_pick],
            outputs=[
                char_id,
                char_name,
                char_role,
                char_age,
                char_age_years,
                char_look,
                char_wardrobe,
                char_rings,
                char_personality,
                char_emotion,
                char_micro,
                char_behavior,
                char_voice,
                char_voice_backend,
                char_voice_id,
                char_voice_sample_path,
                char_lock,
                char_styles,
                char_style_custom,
                char_norms,
                char_income,
                char_housing,
                char_privacy,
                char_clean,
                char_hood,
                char_utils,
                char_deps,
                char_work,
                char_health,
                char_refs,
                status,
            ],
        )
        save_char_btn.click(
            save_character_ui,
            inputs=[
                project_name,
                char_id,
                char_name,
                char_role,
                char_age,
                char_age_years,
                char_look,
                char_wardrobe,
                char_rings,
                char_personality,
                char_emotion,
                char_micro,
                char_behavior,
                char_voice,
                char_voice_backend,
                char_voice_id,
                char_voice_sample_file,
                char_lock,
                char_styles,
                char_style_custom,
                char_norms,
                char_income,
                char_housing,
                char_privacy,
                char_clean,
                char_hood,
                char_utils,
                char_deps,
                char_work,
                char_health,
                char_as_project,
            ],
            outputs=[char_id, char_pick, status, gene_actor, gene_actress],
        )
        import_sheet_btn.click(
            import_character_sheet_ui,
            inputs=[
                char_sheet_file,
                char_id,
                char_name,
                char_role,
                char_age,
                char_age_years,
                char_look,
                char_wardrobe,
                char_rings,
                char_personality,
                char_emotion,
                char_micro,
                char_behavior,
                char_voice,
                char_lock,
            ],
            outputs=[
                char_id,
                char_name,
                char_role,
                char_age,
                char_age_years,
                char_look,
                char_wardrobe,
                char_rings,
                char_personality,
                char_emotion,
                char_micro,
                char_behavior,
                char_voice,
                char_lock,
                status,
            ],
        )
        export_sheet_btn.click(
            export_character_sheet_ui,
            inputs=[
                project_name,
                char_id,
                char_name,
                char_role,
                char_age,
                char_age_years,
                char_look,
                char_wardrobe,
                char_rings,
                char_personality,
                char_emotion,
                char_micro,
                char_behavior,
                char_voice,
                char_lock,
                export_sheet_fmt,
            ],
            outputs=[char_sheet_export, status],
        )
        gene_btn.click(
            generate_kids_ui,
            inputs=[project_name, gene_actor, gene_actress, gene_age, gene_name],
            outputs=[
                gene_gallery,
                char_pick,
                char_id,
                char_name,
                char_role,
                char_age,
                char_age_years,
                char_look,
                char_wardrobe,
                char_lock,
                char_refs,
                start_frame,
                stills_gallery,
                status,
                gene_actor,
                gene_actress,
            ],
        )
        char_role.change(
            apply_role_defaults_ui,
            inputs=[char_role],
            outputs=[char_role, char_age, char_age_years],
        )
        filming_outs = [
            motion_filming,
            write_filming,
            set_filming,
            take_filming,
            motion_explicit_tools,
            write_explicit_tools,
            intimacy,
            write_intimacy,
            shot_intensity_preset,
            shot_content_intensity,
            write_intensity_preset,
            write_content_intensity,
            status,
        ]
        for _filming in (motion_filming, write_filming, set_filming, take_filming):
            _filming.change(
                apply_filming_mode_ui,
                inputs=[project_name, _filming, char_ids],
                outputs=filming_outs,
            )
        mark_outs = [
            motion_image,
            md_mark_preview,
            tk_mark_preview,
            mk_mark_preview,
            idea,
            mk_mark_status,
            md_mark_status,
            tk_mark_status,
            toast,
            status,
        ]
        mk_mark_apply.click(
            apply_mark_ui,
            inputs=[
                project_name,
                mk_mark_still,
                mk_mark_clip,
                mk_mark_editor,
                mk_mark_shape,
                mk_mark_cx,
                mk_mark_cy,
                mk_mark_size,
                mk_mark_target,
                mk_mark_note,
                mk_mark_prop,
                idea,
                intimacy,
                shot_content_intensity,
            ],
            outputs=mark_outs,
        )
        md_mark_apply.click(
            apply_mark_ui,
            inputs=[
                project_name,
                motion_image,
                md_mark_clip,
                md_mark_editor,
                md_mark_shape,
                md_mark_cx,
                md_mark_cy,
                md_mark_size,
                md_mark_target,
                md_mark_note,
                md_mark_prop,
                idea,
                intimacy,
                shot_content_intensity,
            ],
            outputs=mark_outs,
        )
        tk_mark_apply.click(
            apply_take_mark_ui,
            inputs=[
                project_name,
                tk_mark_frame,
                take_player,
                tk_mark_editor,
                tk_mark_shape,
                tk_mark_cx,
                tk_mark_cy,
                tk_mark_size,
                tk_mark_target,
                tk_mark_note,
                tk_mark_prop,
                idea,
                intimacy,
                shot_content_intensity,
            ],
            outputs=[
                tk_mark_frame,
                tk_mark_preview,
                idea,
                tk_mark_status,
                toast,
                status,
                dream_md,
            ],
        )
        _dream_enter_inputs = [
            project_name,
            tk_mark_frame,
            take_player,
            dream_sleeper,
            dream_titles,
            dream_cast,
            dream_presentation,
            dream_vision,
            dream_text_style,
            intimacy,
            shot_content_intensity,
        ]
        _dream_enter_outputs = [
            dream_md,
            dream_bubble,
            take_clips,
            dream_seq,
            toast,
            status,
            studio_tabs,
        ]
        enter_dream_btn.click(
            enter_dream_ui,
            inputs=_dream_enter_inputs,
            outputs=_dream_enter_outputs,
        )
        tk_enter_dream.click(
            enter_dream_ui,
            inputs=_dream_enter_inputs,
            outputs=_dream_enter_outputs,
        )
        mk_enter_dream.click(
            enter_dream_ui,
            inputs=[
                project_name,
                mk_mark_still,
                mk_mark_clip,
                dream_sleeper,
                dream_titles,
                dream_cast,
                dream_presentation,
                dream_vision,
                dream_text_style,
                intimacy,
                shot_content_intensity,
            ],
            outputs=_dream_enter_outputs,
        )
        stitch_dream_btn.click(
            stitch_dream_ui,
            inputs=[project_name],
            outputs=[take_player, take_clips, dream_seq, dream_md, toast, status],
        )
        for _mic, _box in (
            (mk_mark_mic, mk_mark_note),
            (md_mark_mic, md_mark_note),
            (tk_mark_mic, tk_mark_note),
        ):
            _mic.change(
                transcribe_into_note_ui,
                inputs=[_mic, _box],
                outputs=[_box, toast, status],
            )
        mk_mark_shape.change(
            mark_shape_ui,
            inputs=[mk_mark_shape],
            outputs=[mk_mark_editor, mk_mark_sliders, mk_ptr_box],
        )
        md_mark_shape.change(
            mark_shape_ui,
            inputs=[md_mark_shape],
            outputs=[md_mark_editor, md_mark_sliders, md_ptr_box],
        )
        tk_mark_shape.change(
            mark_shape_ui,
            inputs=[tk_mark_shape],
            outputs=[tk_mark_editor, tk_mark_sliders, tk_ptr_box],
        )
        for _actor, _dest, _btn, _mode in (
            (set_ptr_actor, set_ptr_dest, set_ptr_btn, set_filming),
            (mk_ptr_actor, mk_ptr_dest, mk_ptr_btn, set_filming),
            (md_ptr_actor, md_ptr_dest, md_ptr_btn, motion_filming),
            (tk_ptr_actor, tk_ptr_dest, tk_ptr_btn, take_filming),
        ):
            _btn.click(
                pointer_go_to_ui,
                inputs=[project_name, _actor, _dest, _mode],
                outputs=[take_player, take_clips, motion_takes, studio_tabs, status],
            )
        for _tgt, _note in (
            (mk_mark_target, mk_mark_note),
            (md_mark_target, md_mark_note),
            (tk_mark_target, tk_mark_note),
        ):
            _tgt.change(head_note_hint_ui, inputs=[_tgt, _note], outputs=[_note])
        mk_to_motion.click(
            use_posed_still_ui,
            inputs=[mk_mark_preview],
            outputs=[studio_tabs, motion_image, attached_ref, ref_chip, toast, status],
        )
        set_env_build.click(
            build_locked_env_ui,
            inputs=[
                project_name,
                set_env_photo,
                set_env_cam,
                set_env_place,
                set_env_cast,
                set_filming,
                idea,
            ],
            outputs=[
                idea,
                set_env_store,
                set_env_views,
                set_env_take,
                set_env_pick,
                md_env_md,
                tk_env_md,
                set_env_md,
                md_env_gal,
                tk_env_gal,
                set_env_gal,
                motion_image,
                start_frame,
                status,
            ],
        )
        set_env_pick.change(
            load_locked_env_ui,
            inputs=[project_name, set_env_pick],
            outputs=[set_env_store, set_env_views, set_env_take, status],
        )
        set_env_delete.click(
            delete_locked_env_ui,
            inputs=[project_name, set_env_pick, idea],
            outputs=[
                idea,
                set_env_store,
                set_env_views,
                set_env_take,
                set_env_pick,
                md_env_md,
                tk_env_md,
                set_env_md,
                md_env_gal,
                tk_env_gal,
                set_env_gal,
                motion_image,
                start_frame,
                status,
            ],
        )
        set_apply.click(
            apply_set_note_ui,
            inputs=[
                project_name,
                set_camera,
                set_outdoor,
                set_description,
                set_mark_role,
                set_mark_who,
                set_mark_where,
                idea,
                md_world_outdoor,
            ],
            outputs=[idea, set_status, md_world_outdoor, camera, status],
        )
        save_cast_btn.click(
            save_active_cast_ui,
            inputs=[project_name, active_cast, face_lock],
            outputs=[active_cast, face_lock, status],
        )
        import_lib_btn.click(
            import_library_ui,
            inputs=[project_name],
            outputs=[char_pick, active_cast, status],
        )
        apply_char_live_btn.click(
            apply_char_living_preset_ui,
            inputs=[char_live_preset],
            outputs=[
                char_styles,
                char_style_custom,
                char_norms,
                char_income,
                char_housing,
                char_privacy,
                char_clean,
                char_hood,
                char_utils,
                char_deps,
                char_work,
                char_health,
                status,
            ],
        )
        pin_btn.click(
            pin_refs_ui,
            inputs=[project_name, char_pick, char_uploads, pin_still],
            outputs=[char_refs, status],
        )
        sheet_btn.click(
            family_sheet_ui,
            inputs=[project_name],
            outputs=[char_refs, status],
        )
        save_face_btn.click(
            apply_face_method_ui,
            inputs=[project_name, face_method, face_lock],
            outputs=[face_method, face_lock, status],
        )

        load_scene_btn.click(
            load_scene_ui,
            inputs=[project_name, scene_pick],
            outputs=[
                scene_id,
                scene_heading,
                scene_action,
                scene_lines,
                scene_notes,
                scene_status,
                scene_shot_ids,
                fountain_preview,
                status,
            ],
        )
        new_scene_btn.click(
            new_scene_ui,
            outputs=[
                scene_id,
                scene_heading,
                scene_action,
                scene_lines,
                scene_notes,
                scene_status,
                scene_shot_ids,
                fountain_preview,
                status,
            ],
        )
        save_scene_btn.click(
            save_scene_ui,
            inputs=[project_name, scene_id, scene_heading, scene_action, scene_lines, scene_notes, scene_status, scene_shot_ids],
            outputs=[scene_id, scene_pick, fountain_preview, status],
        )
        export_btn.click(
            export_scene_ui,
            inputs=[
                project_name,
                scene_id,
                scene_heading,
                scene_action,
                scene_lines,
                scene_notes,
                scene_status,
                scene_shot_ids,
                export_fmt,
            ],
            outputs=[export_file, status],
        )
        link_btn.click(
            link_shot_to_scene,
            inputs=[project_name, scene_pick, link_shot_pick],
            outputs=[scene_shot_ids, status],
        )

        write_form = [
            write_id,
            write_title,
            write_mode,
            write_provider,
            write_dual_roles,
            write_primary,
            write_secondary,
            write_custom,
            write_tropes,
            write_emotion,
            write_emotion2,
            write_intensity,
            write_inner,
            write_outer,
            write_rel_temp,
            write_senses,
            write_touch,
            write_smell,
            write_taste,
            write_hearing,
            write_sight,
            write_sensory_pass,
            write_location,
            write_tod,
            write_weather,
            write_light,
            write_ambient,
            write_blocking,
            write_props,
            write_live_override,
            write_live_styles,
            write_live_custom,
            write_live_norms,
            write_live_income,
            write_live_housing,
            write_live_privacy,
            write_live_clean,
            write_live_hood,
            write_live_utils,
            write_live_deps,
            write_live_work,
            write_live_health,
            write_scene,
            write_chars,
            write_source,
            write_notes,
            write_tone,
            write_pacing,
            write_intimacy,
            write_intensity_preset,
            write_content_intensity,
            write_speaker,
            write_body,
        ]
        write_intensity_preset.change(
            apply_intensity_preset_ui,
            inputs=[write_intensity_preset],
            outputs=[write_content_intensity],
        )
        apply_write_live_btn.click(
            apply_living_preset_ui,
            inputs=[write_live_preset],
            outputs=[
                write_live_override,
                write_live_styles,
                write_live_custom,
                write_live_norms,
                write_live_income,
                write_live_housing,
                write_live_privacy,
                write_live_clean,
                write_live_hood,
                write_live_utils,
                write_live_deps,
                write_live_work,
                write_live_health,
                write_location,
                write_light,
                write_ambient,
                write_blocking,
                write_props,
                status,
            ],
        )
        inherit_live_btn.click(
            inherit_living_ui,
            inputs=[project_name, write_chars, write_scene],
            outputs=[
                write_live_override,
                write_live_styles,
                write_live_custom,
                write_live_norms,
                write_live_income,
                write_live_housing,
                write_live_privacy,
                write_live_clean,
                write_live_hood,
                write_live_utils,
                write_live_deps,
                write_live_work,
                write_live_health,
                status,
            ],
        )
        apply_sense_btn.click(
            apply_sense_preset_ui,
            inputs=[write_sense_preset],
            outputs=[
                write_emotion,
                write_emotion2,
                write_intensity,
                write_inner,
                write_outer,
                write_rel_temp,
                write_senses,
                write_touch,
                write_smell,
                write_taste,
                write_hearing,
                write_sight,
                write_sensory_pass,
                write_location,
                write_tod,
                write_weather,
                write_light,
                write_ambient,
                write_blocking,
                write_props,
                status,
            ],
        )
        apply_genre_btn.click(
            apply_genre_preset_ui,
            inputs=[write_primary, write_secondary],
            outputs=[write_tone, write_pacing, write_tropes, write_examples, status],
        )
        write_primary.change(
            filter_genre_examples_ui,
            inputs=[write_primary, write_secondary],
            outputs=[write_examples],
        )
        write_secondary.change(
            filter_genre_examples_ui,
            inputs=[write_primary, write_secondary],
            outputs=[write_examples],
        )
        insert_example_btn.click(
            insert_genre_example_ui,
            inputs=[write_examples, write_source],
            outputs=[write_source],
        )
        pull_scene_btn.click(
            pull_scene_into_writing,
            inputs=[project_name, write_scene],
            outputs=[
                write_source,
                write_notes,
                write_primary,
                write_secondary,
                write_custom,
                write_tropes,
                write_examples,
                status,
            ],
        )
        build_prompt_btn.click(
            build_writing_prompt_ui,
            inputs=[project_name, *write_form, rp_state],
            outputs=[write_id, write_system, write_user, draft_pick, status],
        )
        generate_write_btn.click(
            generate_writing_ui,
            inputs=[project_name, *write_form, rp_state, rp_line, write_model],
            outputs=[write_id, write_body, write_system, write_user, rp_chat, rp_state, draft_pick, status],
        )
        save_draft_btn.click(
            save_writing_ui,
            inputs=[project_name, *write_form, write_system, write_user, rp_state],
            outputs=[write_id, draft_pick, status],
        )
        load_draft_btn.click(
            load_writing_ui,
            inputs=[project_name, draft_pick],
            outputs=[
                write_id,
                write_title,
                write_mode,
                write_provider,
                write_dual_roles,
                write_primary,
                write_secondary,
                write_custom,
                write_tropes,
                write_emotion,
                write_emotion2,
                write_intensity,
                write_inner,
                write_outer,
                write_rel_temp,
                write_senses,
                write_touch,
                write_smell,
                write_taste,
                write_hearing,
                write_sight,
                write_sensory_pass,
                write_location,
                write_tod,
                write_weather,
                write_light,
                write_ambient,
                write_blocking,
                write_props,
                write_live_override,
                write_live_styles,
                write_live_custom,
                write_live_norms,
                write_live_income,
                write_live_housing,
                write_live_privacy,
                write_live_clean,
                write_live_hood,
                write_live_utils,
                write_live_deps,
                write_live_work,
                write_live_health,
                write_scene,
                write_chars,
                write_source,
                write_notes,
                write_tone,
                write_pacing,
                write_intimacy,
                write_intensity_preset,
                write_content_intensity,
                write_speaker,
                write_body,
                write_system,
                write_user,
                rp_chat,
                rp_state,
                write_examples,
                status,
            ],
        )
        new_draft_btn.click(
            new_writing_ui,
            outputs=[
                write_id,
                write_title,
                write_mode,
                write_provider,
                write_dual_roles,
                write_primary,
                write_secondary,
                write_custom,
                write_tropes,
                write_emotion,
                write_emotion2,
                write_intensity,
                write_inner,
                write_outer,
                write_rel_temp,
                write_senses,
                write_touch,
                write_smell,
                write_taste,
                write_hearing,
                write_sight,
                write_sensory_pass,
                write_location,
                write_tod,
                write_weather,
                write_light,
                write_ambient,
                write_blocking,
                write_props,
                write_live_override,
                write_live_styles,
                write_live_custom,
                write_live_norms,
                write_live_income,
                write_live_housing,
                write_live_privacy,
                write_live_clean,
                write_live_hood,
                write_live_utils,
                write_live_deps,
                write_live_work,
                write_live_health,
                write_scene,
                write_chars,
                write_source,
                write_notes,
                write_tone,
                write_pacing,
                write_intimacy,
                write_intensity_preset,
                write_content_intensity,
                write_speaker,
                write_body,
                write_system,
                write_user,
                rp_chat,
                rp_state,
                write_examples,
                status,
            ],
        )
        export_write_btn.click(
            export_writing_ui,
            inputs=[project_name, *write_form, write_system, write_user, rp_state, export_write_fmt],
            outputs=[write_export, status],
        )
        push_scene_btn.click(
            push_writing_to_scene_ui,
            inputs=[project_name, *write_form, write_system, write_user, rp_state],
            outputs=[write_id, scene_pick, status],
        )
        import_write_btn.click(
            import_writing_ui,
            inputs=[fuse_files],
            outputs=[write_body, status],
        )
        fuse_btn.click(
            fuse_writing_ui,
            inputs=[fuse_a, fuse_b, fuse_c, fuse_files, fuse_target, write_title],
            outputs=[write_body, write_mode, status],
        )
        plan_shots_btn.click(
            plan_writing_shots_ui,
            inputs=[
                project_name,
                write_title,
                write_body,
                write_chars,
                write_intimacy,
                write_content_intensity,
            ],
            outputs=[saved_shots, take_source, studio_tabs, status],
        )
        write_perf_btn.click(
            inject_writing_performance_ui,
            inputs=[write_notes, write_micro, write_behavior, write_prop],
            outputs=[write_notes, status],
        )
        fill_dream_btn.click(
            fill_dream_sheet_ui,
            inputs=[project_name, write_dream_sleeper, write_dream_titles, write_chars, write_notes],
            outputs=[write_body, write_mode, write_notes, status],
        )
        plan_dream_btn.click(
            plan_dream_shots_ui,
            inputs=[
                project_name,
                write_title,
                write_body,
                write_dream_sleeper,
                write_dream_titles,
                write_chars,
                write_intimacy,
                write_content_intensity,
            ],
            outputs=[
                saved_shots,
                take_source,
                take_clips,
                dream_seq,
                dream_md,
                write_body,
                write_mode,
                studio_tabs,
                status,
            ],
        )
        write_to_takes.click(lambda: open_hub_tab("takes"), outputs=[studio_tabs])
        takes_voice_btn.click(
            save_takes_voice_ui,
            inputs=[project_name, write_body, write_scene, write_chars],
            outputs=[voice_audio, voice_text, voice_files, status],
        )

        save_btn.click(
            save_shot_ui,
            inputs=[project_name, *form_fields],
            outputs=[shot_id, saved_shots, local_prompt, status],
        )
        new_shot_btn.click(new_shot_ui, outputs=[*form_fields, local_prompt, status])
        load_shot_btn.click(
            load_shot_ui,
            inputs=[project_name, saved_shots],
            outputs=[
                *form_fields,
                local_prompt,
                motion_quality,
                still_quality,
                cinema_quality,
                quality_help_md,
                aspect,
                still_aspect,
                status,
            ],
        )
        refresh_refs_btn.click(
            consistency_gallery,
            inputs=[project_name, tags, char_ids],
            outputs=[shot_refs, status],
        )
        ugc_frame_btn.click(
            apply_ugc_frame_ui,
            outputs=[aspect, duration, status],
        )
        enhance_btn.click(
            enhance_motion_ui,
            inputs=[
                project_name,
                idea,
                intent,
                enhance_family,
                enhance_model,
                aspect,
                camera,
                lighting,
                intimacy,
                char_ids,
                negative,
                feed_state,
                attached_ref,
                shot_content_intensity,
            ],
            outputs=[
                enhance_before,
                intent,
                toast,
                status,
                negative,
                feed_html,
                feed_state,
                ref_chip,
            ],
        )
        enhance_brain_btn.click(
            enhance_writing_ui,
            inputs=[
                project_name,
                write_idea,
                write_user,
                write_provider,
                write_chars,
                write_emotion,
                write_intimacy,
            ],
            outputs=[write_before, write_user, status],
        )
        motion_outs = [
            shot_id,
            result_video,
            saved_shots,
            gallery_picks,
            motion_download,
            status,
            local_prompt,
            reel_table,
            start_frame,
            overlay,
            progress_md,
            toast,
            feed_html,
            feed_state,
            intent,
            enhance_before,
            ref_chip,
            seed,
            take_source,
            motion_takes,
            take_clips,
        ]
        motion_ins = [
            project_name,
            video_family,
            video_model,
            image_family,
            image_model,
            duration_preset,
            motion_quality,
            *form_fields,
            motion_image,
            feed_state,
            attached_ref,
        ]
        motion_subject.change(
            apply_motion_subject_ui,
            inputs=[motion_subject],
            outputs=[
                char_ids,
                tags,
                intimacy,
                shot_intensity_preset,
                shot_content_intensity,
                shot_face_lock,
                status,
            ],
        )
        def _text_models(fam):
            models = text_models_for(fam)
            return gr.Dropdown(choices=models, value=models[0] if models else None)

        def _image_models(fam):
            models = image_models_for(fam)
            return gr.Dropdown(choices=models, value=models[0] if models else None)

        enhance_family.change(_text_models, inputs=[enhance_family], outputs=[enhance_model])
        def _video_models(fam):
            models = video_models_for(fam)
            return gr.Dropdown(choices=models, value=models[0] if models else None)

        video_family.change(_video_models, inputs=[video_family], outputs=[video_model])
        image_family.change(_image_models, inputs=[image_family], outputs=[image_model])
        fx_family.change(_image_models, inputs=[fx_family], outputs=[fx_model])
        ugc_family.change(text_family_change_ui, inputs=[ugc_family], outputs=[ugc_model, ugc_provider])
        write_provider.change(
            writing_provider_models_ui,
            inputs=[write_provider],
            outputs=[write_model],
        )
        bridge_agent.change(
            select_bridge_ui,
            inputs=[bridge_agent, bridge_mode],
            outputs=[bridge_panel, bridge_prompt],
        )
        bridge_mode.change(
            select_bridge_ui,
            inputs=[bridge_agent, bridge_mode],
            outputs=[bridge_panel, bridge_prompt],
        )
        bridge_connect.click(
            connect_bridge_ui,
            inputs=[bridge_agent, bridge_mode],
            outputs=[bridge_panel, bridge_prompt, bridge_status],
        )
        bridge_refresh.click(
            refresh_bridge_ui,
            inputs=[bridge_agent, bridge_mode],
            outputs=[bridge_panel, bridge_prompt, bridge_status],
        )
        add_prompt_btn.click(
            add_prompt_ui,
            inputs=[motion_image],
            outputs=[attached_ref, ref_chip, toast, status],
        )
        motion_cast_faces.select(
            open_director_note_ui,
            inputs=[project_name],
            outputs=[
                director_pop,
                note_char_id,
                note_char_title,
                note_emotion,
                note_beats,
                note_wardrobe,
                note_micro,
                note_behavior,
                status,
            ],
        )
        take_cast_faces.select(
            open_dream_about_ui,
            inputs=[
                project_name,
                take_player,
                dream_presentation,
                dream_vision,
                dream_text_style,
            ],
            outputs=[
                dream_pop,
                dream_pop_sleeper,
                dream_pop_title,
                dream_pop_about,
                dream_pop_cast,
                dream_pop_steps,
                dream_pop_beats_md,
                dream_pop_step,
                dream_pop_beat_title,
                dream_pop_beat_prompt,
                dream_pop_style,
                dream_pop_vision,
                dream_pop_text,
                status,
            ],
        )
        dream_pop_close.click(close_dream_about_ui, outputs=[dream_pop])
        dream_add_beat.click(
            add_dream_step_ui,
            inputs=[dream_pop_steps, dream_pop_beat_title, dream_pop_beat_prompt, dream_pop_about],
            outputs=[
                dream_pop_steps,
                dream_pop_beats_md,
                dream_pop_step,
                dream_pop_beat_title,
                dream_pop_beat_prompt,
                status,
            ],
        )
        dream_pop_style.change(
            lambda v: v, inputs=[dream_pop_style], outputs=[dream_presentation]
        )
        dream_pop_vision.change(
            lambda v: v, inputs=[dream_pop_vision], outputs=[dream_vision]
        )
        dream_pop_text.change(
            lambda v: v, inputs=[dream_pop_text], outputs=[dream_text_style]
        )
        dream_presentation.change(
            lambda v: v, inputs=[dream_presentation], outputs=[dream_pop_style]
        )
        dream_vision.change(
            lambda v: v, inputs=[dream_vision], outputs=[dream_pop_vision]
        )
        dream_text_style.change(
            lambda v: v, inputs=[dream_text_style], outputs=[dream_pop_text]
        )
        dream_open_seq.click(
            open_dream_sequence_ui,
            inputs=[
                project_name,
                tk_mark_frame,
                take_player,
                dream_pop_sleeper,
                dream_pop_about,
                dream_pop_cast,
                dream_pop_refs,
                dream_pop_steps,
                dream_pop_style,
                dream_pop_vision,
                dream_pop_text,
                intimacy,
                shot_content_intensity,
            ],
            outputs=[
                dream_pop,
                dream_md,
                dream_seq,
                take_clips,
                dream_bubble,
                toast,
                status,
                studio_tabs,
            ],
        )
        dream_seq.select(
            play_dream_seq_ui,
            inputs=[project_name],
            outputs=[
                take_player,
                motion_image,
                attached_ref,
                ref_chip,
                studio_tabs,
                toast,
                status,
            ],
        )
        note_mic.change(
            transcribe_into_note_ui,
            inputs=[note_mic, note_beats],
            outputs=[note_beats, toast, status],
        )
        note_close.click(close_director_note_ui, outputs=[director_pop])
        note_apply.click(
            apply_director_note_ui,
            inputs=[
                project_name,
                note_char_id,
                note_char_title,
                note_emotion,
                note_beats,
                note_wardrobe,
                note_micro,
                note_behavior,
                idea,
                intimacy,
                shot_content_intensity,
            ],
            outputs=[
                director_pop,
                idea,
                motion_notes_md,
                take_notes_md,
                toast,
                status,
            ],
        )
        motion_takes.select(
            open_take_loop_ui,
            inputs=[project_name],
            outputs=[
                studio_tabs,
                result_video,
                motion_image,
                attached_ref,
                ref_chip,
                director_pop,
                note_char_id,
                note_char_title,
                note_emotion,
                note_beats,
                note_wardrobe,
                note_micro,
                note_behavior,
                toast,
                status,
                take_source,
            ],
        )
        timeline_refresh.click(director_timeline_refresh_ui, inputs=[project_name,timeline_scene,timeline_shot], outputs=[timeline_table,timeline_status])
        timeline_refresh.click(director_timeline_playback_ui, inputs=[project_name,timeline_scene,timeline_shot], outputs=[timeline_preview,timeline_playhead,timeline_visual,timeline_status])
        timeline_load_take.click(director_timeline_playback_ui, inputs=[project_name,timeline_scene,timeline_shot], outputs=[timeline_preview,timeline_playhead,timeline_visual,timeline_status])
        timeline_playhead.change(director_timeline_scrub_ui, inputs=[project_name,timeline_scene,timeline_shot,timeline_playhead], outputs=[timeline_visual,timeline_status])
        timeline_prepare_frame.click(director_timeline_frame_ui, inputs=[project_name,timeline_scene,timeline_shot,timeline_playhead], outputs=[timeline_frame,timeline_status,toast])
        timeline_regenerate.click(director_preview_regenerate_ui, inputs=[project_name,timeline_scene,timeline_shot,timeline_playhead,timeline_regen_instruction,timeline_regen_character,timeline_regen_region,generator], outputs=[timeline_ab_source,timeline_ab_candidate,timeline_ab_status,timeline_status,toast])
        timeline_accept_candidate.click(director_preview_accept_ui, inputs=[project_name], outputs=[timeline_ab_status,timeline_status,toast])
        timeline_reject_candidate.click(director_preview_reject_ui, inputs=[project_name], outputs=[timeline_ab_status,timeline_status,toast])
        timeline_qc_scan.click(take_quality_control_ui, inputs=[project_name], outputs=[timeline_qc_status,timeline_status,toast])
        timeline_qc_repair.click(take_quality_control_repair_ui, inputs=[project_name,generator], outputs=[timeline_ab_source,timeline_ab_candidate,timeline_qc_status,timeline_status,toast])
        timeline_auto_repair.click(autonomous_multi_pass_repair_ui, inputs=[project_name,generator,timeline_auto_max_passes,timeline_auto_min_improvement], outputs=[timeline_auto_status,timeline_status,toast])
        timeline_readiness.click(shot_readiness_ui, inputs=[project_name,timeline_scene,timeline_shot], outputs=[timeline_readiness_status,timeline_status,toast])
        timeline_scene_assembly.click(scene_assembly_ui, inputs=[project_name,timeline_scene], outputs=[timeline_scene_assembly_status,timeline_status,toast])
        timeline_repair_localize.click(continuity_localize_repair_ui, inputs=[project_name,timeline_repair_event,timeline_repair_instruction], outputs=[timeline_playhead,timeline_repair_status,timeline_status,toast])
        timeline_repair_execute.click(continuity_execute_repair_ui, inputs=[project_name,generator], outputs=[timeline_ab_source,timeline_ab_candidate,timeline_repair_status,timeline_status,toast])
        timeline_repair_reassemble.click(continuity_reassemble_segment_ui, inputs=[project_name], outputs=[timeline_ab_source,timeline_ab_candidate,timeline_repair_status,timeline_status,toast])
        timeline_repair_reassemble_audio.click(continuity_reassemble_audio_segment_ui, inputs=[project_name], outputs=[timeline_ab_source,timeline_ab_candidate,timeline_repair_status,timeline_status,toast])
        timeline_repair_seam_blend.click(continuity_seam_blend_ui, inputs=[project_name,timeline_seam_blend_duration], outputs=[timeline_ab_source,timeline_ab_candidate,timeline_repair_status,timeline_status,toast])
        timeline_repair_motion_retime.click(continuity_motion_retime_ui, inputs=[project_name,timeline_seam_blend_duration], outputs=[timeline_ab_source,timeline_ab_candidate,timeline_repair_status,timeline_status,toast])
        timeline_repair_optical_flow.click(continuity_optical_flow_ui, inputs=[project_name,timeline_seam_blend_duration,timeline_optical_flow_fps], outputs=[timeline_ab_source,timeline_ab_candidate,timeline_repair_status,timeline_status,toast])
        tl_add_perf.click(director_timeline_add_performance_ui, inputs=[project_name,timeline_scene,timeline_shot,tl_char_id,tl_char_name,tl_perf_time,tl_emotion,tl_expression,tl_gaze,tl_posture,tl_gesture,tl_action,tl_intensity], outputs=[timeline_table,timeline_status,toast])
        tl_add_cam.click(director_timeline_add_camera_ui, inputs=[project_name,timeline_scene,timeline_shot,tl_cam_time,tl_cam_move,tl_cam_framing,tl_cam_lens,tl_cam_focus,tl_cam_follow,tl_cam_speed,tl_cam_note], outputs=[timeline_table,timeline_status,toast])
        tl_move_btn.click(director_timeline_move_ui, inputs=[project_name,timeline_scene,timeline_shot,tl_move_lane,tl_move_char,tl_move_index,tl_move_time], outputs=[timeline_table,timeline_status,toast])
        timeline_refresh.click(director_timeline_visual_ui, inputs=[project_name,timeline_scene,timeline_shot], outputs=[timeline_visual])
        tl_add_perf.click(director_timeline_visual_ui, inputs=[project_name,timeline_scene,timeline_shot], outputs=[timeline_visual])
        tl_add_cam.click(director_timeline_visual_ui, inputs=[project_name,timeline_scene,timeline_shot], outputs=[timeline_visual])
        tl_move_btn.click(director_timeline_visual_ui, inputs=[project_name,timeline_scene,timeline_shot], outputs=[timeline_visual])
        timeline_drag_save.click(director_timeline_drag_ui, inputs=[project_name,timeline_scene,timeline_shot,timeline_drag_payload], outputs=[timeline_table,timeline_visual,timeline_status,toast])
        tl_to_takes.click(lambda: gr.Tabs(selected="takes"), outputs=[studio_tabs])
        tl_to_mark.click(lambda: gr.Tabs(selected="mark"), outputs=[studio_tabs])
        tl_to_motion.click(lambda: gr.Tabs(selected="motion"), outputs=[studio_tabs])

        # Playback remains the primary take click behavior via play_take_ui; persistent metadata is a parallel selection event.
        take_clips.select(
            # play_take_ui remains the parallel primary playback handler below.
            production_take_select_ui,
            inputs=[project_name],
            outputs=[production_take_id, production_take_detail, production_notes, production_tags, production_cut_style, production_j_lead, production_l_tail, production_picture_in, production_picture_out],
        )
        production_keep.click(
            lambda p, t, n, g: production_take_action_ui(p, t, "selected", n, g),
            inputs=[project_name, production_take_id, production_notes, production_tags],
            outputs=[production_take_detail, toast, status],
        )
        production_review.click(
            lambda p, t, n, g: production_take_action_ui(p, t, "review", n, g),
            inputs=[project_name, production_take_id, production_notes, production_tags],
            outputs=[production_take_detail, toast, status],
        )
        production_reject.click(
            lambda p, t, n, g: production_take_action_ui(p, t, "rejected", n, g),
            inputs=[project_name, production_take_id, production_notes, production_tags],
            outputs=[production_take_detail, toast, status],
        )
        production_save_notes.click(
            lambda p, t, n, g: production_take_action_ui(p, t, "save", n, g),
            inputs=[project_name, production_take_id, production_notes, production_tags],
            outputs=[production_take_detail, toast, status],
        )
        production_save_cut.click(
            production_audio_cut_ui,
            inputs=[project_name, production_take_id, production_cut_style, production_j_lead, production_l_tail, production_picture_in, production_picture_out],
            outputs=[production_take_detail, toast, status],
        )
        production_cinema.click(
            production_cinema_export_ui,
            inputs=[project_name],
            outputs=[production_cinema_file, toast, status],
        )
        take_clips.select(
            play_take_ui,
            inputs=[project_name],
            outputs=[
                studio_tabs,
                take_player,
                take_mode,
                take_direct_banner,
                take_mode_help,
                direct_panel,
                enter_direct_btn,
                exit_direct_btn,
                tk_mark_frame,
                toast,
                status,
                take_source,
            ],
        )
        enter_direct_btn.click(
            enter_direct_ui,
            inputs=[project_name, take_player, tk_direct_time],
            outputs=[
                studio_tabs,
                take_player,
                take_mode,
                take_direct_banner,
                take_mode_help,
                direct_panel,
                enter_direct_btn,
                exit_direct_btn,
                tk_mark_frame,
                toast,
                status,
                take_source,
            ],
        )
        exit_direct_btn.click(
            exit_direct_ui,
            inputs=[project_name, take_player],
            outputs=[
                studio_tabs,
                take_player,
                take_mode,
                take_direct_banner,
                take_mode_help,
                direct_panel,
                enter_direct_btn,
                exit_direct_btn,
                tk_mark_frame,
                toast,
                status,
                take_source,
            ],
        )
        tk_freeze_btn.click(
            freeze_direct_ui,
            inputs=[project_name, take_player, tk_direct_time],
            outputs=[tk_mark_frame, toast, status],
        )
        revise_take_btn.click(
            revise_current_take_ui,
            inputs=[project_name, result_video, shot_id],
            outputs=[
                studio_tabs,
                result_video,
                motion_image,
                attached_ref,
                ref_chip,
                director_pop,
                note_char_id,
                note_char_title,
                note_emotion,
                note_beats,
                note_wardrobe,
                note_micro,
                note_behavior,
                toast,
                status,
                take_source,
            ],
        )
        md_world_apply.click(
            apply_world_note_ui,
            inputs=[
                project_name,
                md_world_weather,
                md_world_thunder,
                md_world_earth,
                md_world_wind,
                md_world_setting,
                md_world_placement,
                md_world_outdoor,
                md_world_prop,
                idea,
                intimacy,
                shot_content_intensity,
            ],
            outputs=[idea, motion_notes_md, take_notes_md, toast, status],
        )
        tk_world_apply.click(
            apply_world_note_ui,
            inputs=[
                project_name,
                tk_world_weather,
                tk_world_thunder,
                tk_world_earth,
                tk_world_wind,
                tk_world_setting,
                tk_world_placement,
                tk_world_outdoor,
                tk_world_prop,
                idea,
                intimacy,
                shot_content_intensity,
            ],
            outputs=[idea, motion_notes_md, take_notes_md, toast, status],
        )
        env_lock_outs = [
            idea,
            md_env_md,
            tk_env_md,
            set_env_md,
            md_env_gal,
            tk_env_gal,
            set_env_gal,
            motion_image,
            start_frame,
            toast,
            status,
        ]
        md_env_apply.click(
            apply_env_lock_ui,
            inputs=[
                project_name,
                md_env_still,
                md_env_style,
                md_env_geo,
                md_env_str,
                md_env_note,
                idea,
            ],
            outputs=env_lock_outs,
        )
        tk_env_apply.click(
            apply_env_lock_ui,
            inputs=[
                project_name,
                tk_env_still,
                tk_env_style,
                tk_env_geo,
                tk_env_str,
                tk_env_note,
                idea,
            ],
            outputs=env_lock_outs,
        )
        set_env_apply.click(
            apply_env_lock_ui,
            inputs=[
                project_name,
                set_env_still,
                set_env_style,
                set_env_geo,
                set_env_str,
                set_env_note,
                idea,
            ],
            outputs=env_lock_outs,
        )
        md_apply_pose.click(
            apply_pose_ui,
            inputs=[project_name, motion_image, md_pose_body, md_pose_hands, md_pose_face, md_pose_micro, md_pose_behavior],
            outputs=[
                pose_path,
                md_pose_preview,
                md_pose_status,
                motion_image,
                attached_ref,
                ref_chip,
                toast,
                status,
                start_frame,
            ],
        )
        pose_apply.click(
            apply_pose_ui,
            inputs=[project_name, pose_still, pose_body, pose_hands, pose_face, pose_micro, pose_behavior],
            outputs=[
                pose_path,
                pose_after,
                pose_status,
                motion_image,
                attached_ref,
                ref_chip,
                toast,
                status,
                start_frame,
            ],
        )
        pose_to_motion.click(
            use_posed_still_ui,
            inputs=[pose_path],
            outputs=[studio_tabs, motion_image, attached_ref, ref_chip, toast, status],
        )
        duration_preset.change(
            lambda label: plan_note(parse_duration_preset(label).seconds),
            inputs=[duration_preset],
            outputs=[plan_md],
        )
        build_plan_btn.click(
            build_extend_plan_ui,
            inputs=[
                project_name,
                idea,
                intent,
                enhance_family,
                enhance_model,
                duration_preset,
                duration,
                aspect,
                camera,
                lighting,
                intimacy,
                char_ids,
                motion_image,
                feed_state,
                attached_ref,
            ],
            outputs=[
                beat_table,
                plan_md,
                saved_shots,
                toast,
                status,
                feed_html,
                feed_state,
                intent,
            ],
        )
        extend_outs = [*motion_outs, beat_table, plan_md]
        continue_evt = continue_btn.click(
            continue_extend_now,
            inputs=[
                project_name,
                idea,
                intent,
                duration_preset,
                feed_state,
                attached_ref,
                *form_fields,
                motion_image,
            ],
            outputs=extend_outs,
            show_progress="hidden",
        )
        reel_evt = generate_reel_btn.click(
            generate_extend_reel_now,
            inputs=[
                project_name,
                idea,
                intent,
                duration_preset,
                feed_state,
                attached_ref,
                *form_fields,
                motion_image,
            ],
            outputs=extend_outs,
            show_progress="hidden",
        )
        send_evt = send_btn.click(
            imagine_send,
            inputs=[
                project_name,
                idea,
                enhance_family,
                enhance_model,
                video_family,
                video_model,
                image_family,
                image_model,
                duration_preset,
                motion_quality,
                attached_ref,
                feed_state,
                *form_fields,
                motion_image,
            ],
            outputs=extend_outs,
            show_progress="hidden",
        )
        direct_regen_evt = tk_mark_regen.click(
            regenerate_direct_now,
            inputs=[
                project_name,
                idea,
                enhance_family,
                enhance_model,
                video_family,
                video_model,
                image_family,
                image_model,
                duration_preset,
                motion_quality,
                attached_ref,
                feed_state,
                take_player,
                tk_mark_frame,
                *form_fields,
                motion_image,
            ],
            outputs=[*extend_outs, take_player, studio_tabs],
            show_progress="hidden",
        )
        regen_evt = regen_btn.click(
            regenerate_motion_now,
            inputs=[
                project_name,
                idea,
                enhance_family,
                enhance_model,
                video_family,
                video_model,
                image_family,
                image_model,
                duration_preset,
                motion_quality,
                attached_ref,
                feed_state,
                *form_fields,
                motion_image,
            ],
            outputs=extend_outs,
            show_progress="hidden",
        )
        animate_evt = generate_btn.click(
            generate_amd_now,
            inputs=motion_ins,
            outputs=motion_outs,
            show_progress="hidden",
        )
        pipe_animate_evt = pipe_animate_btn.click(
            lambda still, prompt, enhanced, frame, res: (
                *arm_pipeline_shot(still, prompt, enhanced),
                frame,
                res,
            ),
            inputs=[pipe_still, pipe_prompt, pipe_enhanced, pipe_aspect, pipe_quality],
            outputs=[motion_image, attached_ref, idea, intent, aspect, motion_quality],
        ).then(
            generate_amd_now,
            inputs=motion_ins,
            outputs=motion_outs,
            show_progress="hidden",
        ).then(
            lambda clip, download: (clip, download),
            inputs=[result_video, motion_download],
            outputs=[pipe_video, pipe_download],
        )
        quick_evt = quick_btn.click(
            generate_quick_now,
            inputs=motion_ins,
            outputs=motion_outs,
            show_progress="hidden",
        )
        cancel_btn.click(
            request_cancel,
            outputs=[status, progress_md],
            cancels=[send_evt, regen_evt, direct_regen_evt, animate_evt, pipe_animate_evt, quick_evt, continue_evt, reel_evt, prod_evt],
        )
        fx_use_extra.change(
            lambda on: gr.update(visible=bool(on)),
            inputs=[fx_use_extra],
            outputs=[fx_extra],
        )
        fx_preset.change(preset_detail_md, inputs=[fx_preset], outputs=[fx_preset_md])
        fx_evt = fx_generate.click(
            generate_effect_now,
            inputs=[
                project_name,
                fx_character,
                fx_location,
                fx_product,
                fx_preset,
                fx_aspect,
                fx_resolution,
                fx_use_extra,
                fx_extra,
                fx_chars,
                fx_family,
                fx_model,
                fx_light,
            ],
            outputs=[fx_video, fx_overlay, fx_progress, toast, status, gallery_picks, fx_download],
            show_progress="hidden",
        )
        fx_cancel.click(
            request_cancel,
            outputs=[status, fx_progress],
            cancels=[fx_evt],
        )
        fallback_btn.click(
            generate_fallback_now,
            inputs=motion_ins,
            outputs=motion_outs,
        )
        queue_btn.click(
            enqueue_shot,
            inputs=[project_name, queue_state, *form_fields],
            outputs=[queue_state, queue_table, shot_id, saved_shots, status],
        )
        run_btn.click(
            run_queue_ui,
            inputs=[project_name, queue_state, generator],
            outputs=[queue_state, queue_table, result_video, gallery_picks, gallery_video, status, reel_table],
        )
        clear_done_btn.click(clear_finished, inputs=[queue_state], outputs=[queue_state, queue_table, status])
        clear_all_btn.click(clear_queue, inputs=[queue_state], outputs=[queue_state, queue_table, status])

        light_preset.change(lighting_mentor_ui, inputs=[light_preset], outputs=[light_mentor])
        apply_light_btn.click(
            apply_lighting_ui,
            inputs=[project_name, light_preset, saved_shots],
            outputs=[light_preset, light_chip, light_mentor, status],
        )
        light_to_motion.click(lambda: open_hub_tab("motion"), outputs=[studio_tabs])
        lighting_pick.change(expand_lighting, inputs=[lighting_pick], outputs=[lighting])
        lighting_enhance.change(expand_lighting, inputs=[lighting_enhance], outputs=[lighting])
        lighting_enhance.change(lambda v: v, inputs=[lighting_enhance], outputs=[lighting_pick])
        lighting_pick.change(lambda v: v, inputs=[lighting_pick], outputs=[lighting_enhance])
        pipe_lighting.change(expand_lighting, inputs=[pipe_lighting], outputs=[lighting])
        pipe_lighting.change(lambda v: v, inputs=[pipe_lighting], outputs=[lighting_enhance])
        lighting_enhance.change(lambda v: v, inputs=[lighting_enhance], outputs=[pipe_lighting])
        light_preset.change(lambda v: v, inputs=[light_preset], outputs=[pipe_lighting])
        pipe_lighting.change(lambda v: v, inputs=[pipe_lighting], outputs=[light_preset])
        load_voice_dir_btn.click(
            load_voice_direction_ui,
            inputs=[project_name, voice_character],
            outputs=[
                voice_intention,
                voice_breath,
                voice_pace,
                voice_register,
                voice_intensity,
                voice_backend,
                voice_id,
                voice_sample_path,
                status,
            ],
        )
        save_voice_profile_btn.click(
            save_voice_profile_ui,
            inputs=[
                project_name,
                voice_character,
                voice_backend,
                voice_id,
                voice_sample_file,
                voice_intention,
                voice_breath,
                voice_pace,
                voice_register,
                voice_intensity,
            ],
            outputs=[voice_backend, voice_id, voice_sample_path, status],
        )
        voice_micro.change(
            fold_voice_micro_ui,
            inputs=[voice_micro, voice_breath],
            outputs=[voice_breath],
        )
        speak_btn.click(
            speak_line_ui,
            inputs=[
                project_name,
                voice_provider,
                voice_character,
                voice_text,
                voice_start,
                voice_shot,
                voice_scene,
                voice_intention,
                voice_breath,
                voice_pace,
                voice_register,
                voice_intensity,
                voice_backend,
                voice_id,
            ],
            outputs=[voice_audio, voice_files, status],
        )
        voice_takes_btn.click(
            voice_takes_ui,
            inputs=[
                project_name,
                voice_provider,
                voice_character,
                voice_text,
                voice_start,
                voice_shot,
                voice_scene,
                voice_intention,
                voice_breath,
                voice_pace,
                voice_register,
                voice_intensity,
                voice_takes,
                voice_backend,
                voice_id,
            ],
            outputs=[voice_audio, voice_files, status],
        )
        speak_tagged_btn.click(
            speak_tagged_ui,
            inputs=[project_name, voice_provider, voice_tagged, voice_shot, voice_scene],
            outputs=[voice_audio, voice_files, status],
        )
        import_vo_btn.click(
            import_vo_ui,
            inputs=[project_name, voice_import],
            outputs=[voice_audio, voice_files, status],
        )
        import_sample_btn.click(
            import_vo_as_sample_ui,
            inputs=[project_name, voice_character, voice_import],
            outputs=[voice_audio, voice_files, voice_sample_path, status],
        )
        render_cue_btn.click(
            save_and_render_cue,
            inputs=[project_name, cue_name, cue_mood, cue_in, cue_out, cue_bpm, cue_notes, cue_intensity],
            outputs=[music_preview, cue_table, music_pick, status],
        )
        import_music_btn.click(
            import_music_ui,
            inputs=[project_name, music_import],
            outputs=[music_pick, status],
        )
        room_tone_save.click(
            save_scene_room_tone_ui,
            inputs=[project_name, room_tone_scene, room_tone_upload, room_tone_enabled, room_tone_gain, room_tone_fade_in, room_tone_fade_out, room_tone_note],
            outputs=[room_tone_preview, room_tone_status, status],
        )
        finish_btn.click(
            apply_finish_ui,
            inputs=[
                project_name,
                gallery_picks,
                lut_dd,
                vfx_op,
                vfx_strength,
                vfx_speed,
                do_lut,
                do_vfx,
                cinema_quality,
            ],
            outputs=[finish_video, download, gallery_picks, status],
        )
        preview_btn.click(
            preview_clip,
            inputs=[project_name, gallery_picks, cinema_quality],
            outputs=[gallery_video, download],
        )
        stitch_btn.click(
            stitch_selected,
            inputs=[project_name, gallery_picks, music_pick, cinema_quality],
            outputs=[gallery_video, download, gallery_picks, status, reel_table],
        )
        auto_stitch_btn.click(
            auto_stitch_sequence_ui,
            inputs=[project_name, cinema_quality],
            outputs=[gallery_video, download, gallery_picks, status, reel_table],
        )
        rebuild_btn.click(rebuild_reel_ui, inputs=[project_name], outputs=[reel_table, status])
        add_reel_btn.click(
            add_shot_to_reel,
            inputs=[project_name, saved_shots, reel_status],
            outputs=[reel_table, status],
        )
        set_status_btn.click(
            set_reel_status,
            inputs=[project_name, reel_entry_id, reel_status],
            outputs=[reel_table, status],
        )
        assemble_btn.click(
            assemble_reel_ui,
            inputs=[project_name, music_pick, include_dialogue, cinema_quality, cinema_light],
            outputs=[gallery_video, download, gallery_picks, reel_table, status],
        )

        def _boot():
            project = ensure_default_project()
            stills = [str(p) for p in project.list_stills()]
            start, end = still_dropdowns(project)
            still_names = project.still_choices()
            return (
                project.name,
                stills,
                start,
                end,
                shot_dropdown(project),
                gr.CheckboxGroup(choices=gallery_choices(project), value=[]),
                scene_dropdown(project),
                char_dropdown(project),
                _empty_reel(project),
                status_markdown(),
                "Studio ready. Script → bible → shots → voice/music → grade → reel.",
                gr.Dropdown(choices=still_names, value=still_names[0] if still_names else None),
                shot_dropdown(project),
                scene_dropdown(project),
                char_dropdown(project),
                shot_dropdown(project),
                scene_dropdown(project),
                gr.Dropdown(choices=lut_choices(project), value="warm_lamp.cube"),
                gr.CheckboxGroup(choices=tag_choices(project), value=list(CHARACTER_TAGS)),
                draft_dropdown(project),
                scene_dropdown(project),
                writing_api_markdown(),
                local_lot_html(),
                load_still_notes_ui(project.name),
                shot_dropdown(project),
                ugc_brief_dropdown(project),
                gr.Dropdown(choices=still_names, value=still_names[0] if still_names else None),
                getattr(project, "quality", DEFAULT_QUALITY),
                getattr(project, "quality", DEFAULT_QUALITY),
                getattr(project, "quality", DEFAULT_QUALITY),
                quality_debug_md(),
                getattr(project, "aspect", DEFAULT_ASPECT),
                getattr(project, "aspect", DEFAULT_ASPECT),
            )

        def _empty_reel(project):
            from film_lab.reel import load_reel, reel_rows

            return reel_rows(load_reel(project))

        demo.load(
            _boot,
            outputs=[
                project_name,
                stills_gallery,
                start_frame,
                end_frame,
                saved_shots,
                gallery_picks,
                scene_pick,
                char_pick,
                reel_table,
                machine,
                status,
                pin_still,
                link_shot_pick,
                shot_scene,
                voice_character,
                voice_shot,
                voice_scene,
                lut_dd,
                tags,
                draft_pick,
                write_scene,
                writing_api,
                lot_md,
                still_notes,
                take_source,
                ugc_pick,
                ugc_still,
                motion_quality,
                still_quality,
                cinema_quality,
                quality_help_md,
                aspect,
                still_aspect,
            ],
        )

    return demo


def main() -> None:
    demo = build_ui()
    allowed = [
        str(default_data_root().resolve()),
        str(Path.cwd().resolve()),
        str((Path.cwd() / "data").resolve()),
        *extra_allowed_paths(),
    ]
    demo.queue(default_concurrency_limit=1)
    demo.launch(
        server_name=HOST,
        server_port=PORT,
        show_api=False,
        inbrowser=False,
        allowed_paths=allowed,
    )


if __name__ == "__main__":
    main()
