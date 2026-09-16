#!/usr/bin/env python3
"""Studio modules: script, characters, voice, music, LUT, reel."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.constants import EXPLICIT_INTIMACY, INTIMACY_MODES
from film_lab.characters import (
    CharacterError,
    compose_local_prompt,
    pin_reference,
    seed_alison_bradley,
)
from film_lab.examples_import import import_studio_bundle
from film_lab.ffmpeg_support import ffmpeg_available
from film_lab.finish import apply_lut, apply_vfx
from film_lab.generators.ken_burns import KenBurnsGenerator
from film_lab.luts import ensure_stock_luts, list_luts
from film_lab.music import new_cue, render_bed
from film_lab.pdf_export import write_simple_pdf
from film_lab.project import Project
from film_lab.queue import generate_one
from film_lab.reel import ReelEntry, add_entry, assemble_reel
from film_lab.script import DialogueLine, Scene, export_scene, save_scene
from film_lab.shot_card import ShotCard
from film_lab.voice import synthesize_line
from film_lab.genres import (
    GENRE_LABELS,
    GENRES,
    GenreGuardError,
    check_genre_intimacy,
    examples_for,
    parse_custom_tags,
    preset_for,
)
from film_lab.living import (
    LIVING_STYLES,
    LivingBrief,
    living_preset_brief,
    living_prompt_block,
    living_sense_couplings,
    living_shot_line,
)
from film_lab.senses import (
    PRESET_LABELS,
    SensoryBrief,
    preset_brief,
    sensory_prompt_block,
)
from film_lab.writing import (
    OFFLINE_NOTICE,
    WritingError,
    bible_block,
    build_prompt_pack,
    export_draft,
    extract_dialogue_takes,
    fountain_to_scene,
    generate_draft,
    load_draft,
    new_draft,
    probe_writing_api,
    push_draft_to_scene,
    save_draft,
)


def _still(path: Path, color: tuple[int, int, int]) -> Path:
    img = Image.new("RGB", (960, 540), color)
    img.save(path)
    return path


class StudioTests(unittest.TestCase):
    def test_script_fountain_and_pdf(self) -> None:
        scene = Scene(
            id="sc1",
            heading="INT. BEDROOM - NIGHT",
            action="The lamp holds.",
            lines=[DialogueLine("ALISON", "soft", "Stay.")],
            director_notes="Faces first.",
        )
        fountain = scene.to_fountain(title="study")
        self.assertIn("INT. BEDROOM - NIGHT", fountain)
        self.assertIn("ALISON", fountain)
        self.assertIn("(soft)", fountain)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "projects"
            project = Project.create("script", data_root=root)
            save_scene(project, scene)
            dest = project.scenes_dir / "sc1.pdf"
            export_scene(project, scene, dest)
            self.assertTrue(dest.is_file())
            self.assertGreater(dest.stat().st_size, 200)
            self.assertTrue(dest.read_bytes().startswith(b"%PDF"))

    def test_character_bible_prompt_and_adult_guard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("cast", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            shot = ShotCard(
                name="Two",
                character_tags=["Alison"],
                character_ids=["alison", "bradley"],
                intimacy_mode="covered sheets",
            )
            prompt = compose_local_prompt(shot, project)
            self.assertIn("Alison, adult woman late 20s", prompt)
            self.assertIn("Bradley, adult man late 20s", prompt)
            self.assertIn("living:", prompt)
            self.assertIn("Newlywed nest", prompt)
            still = _still(project.stills_dir / "a.jpg", (80, 40, 30))
            pin_reference(project, "alison", still)
            with self.assertRaises(CharacterError):
                from film_lab.characters import CharacterProfile

                CharacterProfile(id="x", name="No", age_band="teen")

    def test_voice_and_music_wav(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("audio", data_root=Path(tmp) / "projects")
            cue = synthesize_line(project, "Stay like that.", character_id="alison", start_s=0.4)
            self.assertTrue(Path(cue.path).is_file())
            self.assertGreater(Path(cue.path).stat().st_size, 100)
            bed = render_bed(project, new_cue("lamp", length=2.0, bpm=60))
            self.assertTrue(bed.is_file())
            self.assertGreater(bed.stat().st_size, 1000)

    def test_stock_luts(self) -> None:
        cwd = Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                os.chdir(tmp)
                root = ensure_stock_luts()
                names = {p.name for p in list_luts()}
                self.assertIn("warm_lamp.cube", names)
                self.assertTrue((root / "warm_lamp.cube").is_file())
        finally:
            os.chdir(cwd)

    def test_writing_studio_offline(self) -> None:
        os.environ.pop("FILM_LAB_XAI_API_KEY", None)
        os.environ.pop("XAI_API_KEY", None)
        os.environ.pop("FILM_LAB_GEMINI_API_KEY", None)
        os.environ.pop("GEMINI_API_KEY", None)
        os.environ.pop("GOOGLE_API_KEY", None)
        os.environ.pop("FILM_LAB_OPENAI_API_KEY", None)
        os.environ.pop("OPENAI_API_KEY", None)
        os.environ.pop("FILM_LAB_ANTHROPIC_API_KEY", None)
        os.environ.pop("ANTHROPIC_API_KEY", None)
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("write", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            state, message = probe_writing_api()
            self.assertEqual(state, "Off")
            self.assertIn("FILM_LAB_XAI_API_KEY", message)
            bible = bible_block(project, ["alison", "bradley"])
            self.assertIn("Alison", bible)
            self.assertIn("late 20s", bible)
            system, user = build_prompt_pack(
                project,
                mode="screenplay",
                source="INT. BEDROOM - NIGHT\n\nThe lamp holds.",
                notes="Stay on faces.",
                scene_id=None,
                character_ids=["alison", "bradley"],
                intimacy_mode="artistic nude",
            )
            self.assertIn("Fountain", system)
            self.assertIn("Alison", user)
            self.assertIn("artistic nude", user)
            draft = new_draft("Lamp pages", "screenplay")
            draft.source = "INT. BEDROOM - NIGHT\n\nALISON\nStay."
            draft.body = "INT. BEDROOM - NIGHT\n\nThe sheet slips.\n\nBRADLEY\n(close)\nI'm here.\n"
            draft.character_ids = ["alison", "bradley"]
            save_draft(project, draft)
            dest = project.writing_dir / "lamp.md"
            export_draft(project, draft, dest)
            self.assertTrue(dest.is_file())
            self.assertIn("Lamp pages", dest.read_text(encoding="utf-8"))
            scene = fountain_to_scene(draft.body)
            self.assertTrue(scene.heading.startswith("INT."))
            self.assertTrue(any(ln.character == "BRADLEY" for ln in scene.lines))
            pushed = push_draft_to_scene(project, draft)
            self.assertEqual(pushed.id, draft.scene_id)
            takes = extract_dialogue_takes(draft.body)
            self.assertGreaterEqual(len(takes), 1)
            pages = generate_draft(project, draft)
            self.assertTrue(pages.body)
            self.assertIn("ALISON", pages.body.upper())
            self.assertEqual(pages.model, "local-templates")
            self.assertFalse(pages.used_api)
            from film_lab.writing import compose_local_pages

            rp = new_draft("Rehearsal", "roleplay")
            rp.character_ids = ["alison", "bradley"]
            rp.roleplay_speaker = "Alison"
            line = compose_local_pages(project, rp)
            self.assertTrue(line)
            self.assertNotIn("fade to black", line.lower())
            self.assertIn("FILM_LAB_XAI_API_KEY", OFFLINE_NOTICE)
            self.assertIn("FILM_LAB_OPENAI_API_KEY", OFFLINE_NOTICE)
            self.assertIn("FILM_LAB_ANTHROPIC_API_KEY", OFFLINE_NOTICE)
            self.assertIn("credits", OFFLINE_NOTICE.lower())
            bible = bible_block(project, ["alison"])
            self.assertIn("Living:", bible)
            self.assertIn(EXPLICIT_INTIMACY, INTIMACY_MODES)
            explicit_sys, explicit_user = build_prompt_pack(
                project,
                mode="novel",
                source="",
                notes="",
                scene_id=None,
                character_ids=["alison", "bradley"],
                intimacy_mode=EXPLICIT_INTIMACY,
            )
            pack = explicit_sys + explicit_user
            self.assertIn("explicit", pack.lower())
            self.assertIn("pornographic", pack.lower())
            self.assertNotIn("fade to black", pack.lower().replace("do not fade to black", ""))
            self.assertIn("Do not fade to black", pack)
            shot = ShotCard(
                name="Explicit hold",
                character_tags=["Alison"],
                character_ids=["alison"],
                intimacy_mode=EXPLICIT_INTIMACY,
            )
            shot_prompt = compose_local_prompt(shot, project)
            self.assertIn("explicit adult sex", shot_prompt)
            self.assertIn("pornographic still", shot_prompt)
            with self.assertRaises(GenreGuardError):
                build_prompt_pack(
                    project,
                    mode="roleplay",
                    source="A sixteen year old in bed.",
                    notes="",
                    scene_id=None,
                    character_ids=["alison"],
                    intimacy_mode=EXPLICIT_INTIMACY,
                )

    def test_writing_providers_gemini_dual_no_credits(self) -> None:
        from film_lab.constants import LOCAL_BANNER
        from film_lab.llm import (
            DEFAULT_DUAL_ROLES,
            DEFAULT_GEMINI_MODEL,
            DEFAULT_OPENAI_MODEL,
            DUAL_GEMINI_SPINE,
            DUAL_OPENAI_GROK,
            PROVIDER_CLAUDE,
            PROVIDER_GEMINI,
            PROVIDER_GROK,
            PROVIDER_LOCAL,
            PROVIDER_OPENAI,
            PROVIDERS,
            UGC_PROVIDERS,
            dual_missing_keys,
            get_anthropic_key,
            get_gemini_key,
            get_openai_key,
            get_xai_key,
            leave_notice,
            messages_to_anthropic,
            messages_to_gemini,
            openai_model,
            probe_anthropic,
            probe_gemini,
            probe_openai,
            probe_xai,
            writing_api_markdown,
        )

        for key in (
            "FILM_LAB_XAI_API_KEY",
            "XAI_API_KEY",
            "FILM_LAB_GEMINI_API_KEY",
            "GEMINI_API_KEY",
            "GOOGLE_API_KEY",
            "FILM_LAB_OPENAI_API_KEY",
            "OPENAI_API_KEY",
            "FILM_LAB_ANTHROPIC_API_KEY",
            "ANTHROPIC_API_KEY",
        ):
            os.environ.pop(key, None)
        self.assertIsNone(get_xai_key())
        self.assertIsNone(get_gemini_key())
        self.assertIsNone(get_openai_key())
        self.assertIsNone(get_anthropic_key())
        self.assertEqual(probe_xai()[0], "Off")
        self.assertEqual(probe_gemini()[0], "Off")
        self.assertEqual(probe_openai()[0], "Off")
        self.assertEqual(probe_anthropic()[0], "Off")
        self.assertEqual(DEFAULT_GEMINI_MODEL, "gemini-3.8-flash")
        self.assertEqual(DEFAULT_OPENAI_MODEL, "gpt-4.1")
        self.assertEqual(openai_model(), "gpt-4.1")
        self.assertEqual(DEFAULT_DUAL_ROLES, DUAL_GEMINI_SPINE)
        self.assertIn(PROVIDER_OPENAI, PROVIDERS)
        self.assertIn(PROVIDER_OPENAI, UGC_PROVIDERS)
        self.assertIn(PROVIDER_CLAUDE, PROVIDERS)
        self.assertIn(PROVIDER_CLAUDE, UGC_PROVIDERS)
        self.assertTrue(any("OPENAI" in k.upper() for k in dual_missing_keys(DUAL_OPENAI_GROK)))
        status = writing_api_markdown().lower()
        self.assertIn("no credits", status)
        self.assertIn("grok", status)
        self.assertIn("gemini", status)
        self.assertIn("chatgpt", status)
        self.assertIn("claude", status)
        self.assertIn("leave this machine", leave_notice(PROVIDER_OPENAI).lower())
        self.assertIn("anthropic", leave_notice(PROVIDER_CLAUDE).lower())
        self.assertNotIn("credit meter", LOCAL_BANNER.lower())
        self.assertIn("no film lab credits", LOCAL_BANNER.lower())
        system, contents = messages_to_gemini(
            [
                {"role": "system", "content": "Adults only."},
                {"role": "user", "content": "Continue the scene."},
                {"role": "assistant", "content": "ALISON\nStay."},
            ]
        )
        self.assertIn("Adults only.", system)
        self.assertEqual(contents[0]["role"], "user")
        self.assertEqual(contents[1]["role"], "model")
        draft = new_draft("Providers", "roleplay")
        self.assertEqual(draft.provider, PROVIDER_LOCAL)
        draft.provider = PROVIDER_GROK
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("llm", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            draft.character_ids = ["alison"]
            with self.assertRaises(WritingError) as raised:
                generate_draft(project, draft)
            self.assertIn("XAI_API_KEY", str(raised.exception))
            draft.provider = PROVIDER_GEMINI
            with self.assertRaises(WritingError) as raised:
                generate_draft(project, draft)
            self.assertIn("GEMINI", str(raised.exception).upper())
            draft.provider = PROVIDER_OPENAI
            with self.assertRaises(WritingError) as raised:
                generate_draft(project, draft)
            self.assertIn("OPENAI", str(raised.exception).upper())
            draft.provider = PROVIDER_CLAUDE
            with self.assertRaises(WritingError) as raised:
                generate_draft(project, draft)
            self.assertIn("ANTHROPIC", str(raised.exception).upper())
            system, contents = messages_to_anthropic(
                [
                    {"role": "system", "content": "Adults only."},
                    {"role": "user", "content": "Continue the scene."},
                    {"role": "assistant", "content": "ALISON\nStay."},
                ]
            )
            self.assertIn("Adults only.", system)
            self.assertEqual(contents[0]["role"], "user")
            self.assertEqual(contents[1]["role"], "assistant")

    def test_living_style_and_conditions(self) -> None:
        required_styles = {
            "Minimalist",
            "Newlywed nest",
            "Urban apartment",
            "Suburban house",
            "Creative studio loft",
            "Campus / dorm (adult students only)",
            "Working-class practical",
        }
        self.assertTrue(required_styles.issubset(set(LIVING_STYLES)))
        nest = living_preset_brief("Newlywed warm apartment")
        self.assertIn("Newlywed nest", nest.styles)
        tight = living_preset_brief("Tight budget thin walls")
        self.assertEqual(tight.privacy, "thin walls")
        self.assertEqual(tight.income_band, "tight")
        couplings = " ".join(living_sense_couplings(tight)).lower()
        self.assertIn("hearing", couplings)
        self.assertIn("thin walls", couplings)
        cramped = LivingBrief(housing_quality="cramped", privacy="private bedroom")
        self.assertTrue(any("touch" in c.lower() for c in living_sense_couplings(cramped)))
        self.assertIn("living:", living_shot_line(nest))
        os.environ.pop("FILM_LAB_XAI_API_KEY", None)
        os.environ.pop("XAI_API_KEY", None)
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("nest", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            self.assertTrue(project.living_brief().has_content())
            meta = (project.root / "project.json").read_text(encoding="utf-8")
            self.assertIn("Newlywed nest", meta)
            alison = None
            from film_lab.characters import load_character

            alison = load_character(project, "alison")
            self.assertIn("Newlywed nest", alison.living_brief().styles)
            override = living_preset_brief("Tight budget thin walls")
            override.override = True
            system, user = build_prompt_pack(
                project,
                mode="screenplay",
                source="INT. SMALL BEDROOM - NIGHT",
                notes="",
                scene_id=None,
                character_ids=["alison", "bradley"],
                living=override,
            )
            pack = system + user
            self.assertIn("thin walls", pack)
            self.assertIn("ACTION", pack)
            self.assertIn("Living style", pack)
            novel_sys, novel_user = build_prompt_pack(
                project,
                mode="novel",
                source="",
                notes="",
                scene_id=None,
                character_ids=["alison"],
                living=override,
            )
            self.assertIn("rent pressure", (novel_sys + novel_user).lower() + " nest is texture")
            self.assertIn("nest is texture", novel_sys + novel_user)
            rp_sys, rp_user = build_prompt_pack(
                project,
                mode="roleplay",
                source="",
                notes="",
                scene_id=None,
                character_ids=["alison"],
                living=override,
            )
            self.assertIn("react to the nest", (rp_sys + rp_user).lower())
            draft = new_draft("Thin walls", "screenplay")
            draft.set_living(override)
            save_draft(project, draft)
            loaded = load_draft(project, draft.id)
            self.assertTrue(loaded.living_override)
            self.assertEqual(loaded.living_brief().privacy, "thin walls")
            scene = push_draft_to_scene(project, loaded)
            self.assertEqual(scene.living_brief().privacy, "thin walls")
            block = living_prompt_block(override, mode="screenplay", sensory_pass=True)
            self.assertIn("SENSORY PASS", block)

    def test_apply_living_preset_ui_noisy_city_loft(self) -> None:
        from film_lab.ui_handlers import apply_char_living_preset_ui, apply_living_preset_ui

        def val(item):
            if isinstance(item, dict):
                return item.get("value")
            return item

        out = apply_living_preset_ui("Noisy city loft")
        self.assertEqual(len(out), 19)
        self.assertTrue(val(out[0]))
        self.assertIn("Creative studio loft", val(out[1]))
        self.assertEqual(val(out[4]), "tight")
        self.assertEqual(val(out[5]), "spacious")
        self.assertEqual(val(out[6]), "no privacy")
        self.assertEqual(val(out[7]), "cluttered")
        self.assertEqual(val(out[9]), "noisy street")
        self.assertIn("LOFT", val(out[13]))
        self.assertEqual(val(out[14]), "neon")
        self.assertIn("Noisy city loft", out[-1])
        # Gradio 5 rejects reconstructed widgets; each field must be an update.
        for item in out[:-1]:
            self.assertIsInstance(item, dict)
            self.assertIn("value", item)

        char_out = apply_char_living_preset_ui(["Noisy city loft"])
        self.assertEqual(len(char_out), 13)
        self.assertIn("Creative studio loft", val(char_out[0]))
        self.assertIn("Noisy city loft", char_out[-1])

    def test_genre_catalog_and_prompt_inject(self) -> None:
        required = {
            "Literary fiction",
            "Contemporary",
            "Historical fiction",
            "Romance",
            "Romance — steamy / erotic (adult)",
            "Romantic comedy",
            "Thriller",
            "Mystery",
            "Crime",
            "Noir",
            "Legal thriller",
            "Horror",
            "Gothic",
            "Supernatural horror",
            "Fantasy — high",
            "Fantasy — low",
            "Fantasy — urban",
            "Science fiction",
            "Dystopian",
            "Cyberpunk",
            "Adventure",
            "Action",
            "War",
            "Western",
            "Young adult (18+ protagonists only)",
            "New adult (18+ / early 20s)",
            "Magical realism",
            "Speculative",
            "Slipstream",
            "Comedy",
            "Satire",
            "Absurdist",
            "Memoir-style / autofiction (fictionalized)",
            "Family saga",
            "Coming-of-age (adult)",
            "Teen film / coming-of-age (theatrical)",
            "Slice of life",
            "Erotica / adult literary (explicit adult only)",
            "Experimental / hybrid",
        }
        self.assertGreaterEqual(len(GENRES), 39)
        self.assertTrue(required.issubset(set(GENRE_LABELS)))
        self.assertEqual(parse_custom_tags("chamber piece; lamp-lit, marriage study"), [
            "chamber piece",
            "lamp-lit",
            "marriage study",
        ])
        horror = preset_for("Horror")
        self.assertIn("scare set pieces", horror["adaptation"])
        romance = preset_for("Romance")
        self.assertIn("emotional set pieces", romance["adaptation"])
        thriller = preset_for("Thriller")
        self.assertIn("set-piece turns", thriller["adaptation"])
        self.assertTrue(examples_for("Horror"))
        self.assertTrue(examples_for("Thriller"))
        from film_lab.ui_handlers import apply_genre_preset_ui, apply_living_preset_ui

        tone, pacing, tropes, _examples, hint = apply_genre_preset_ui("Thriller", [])
        self.assertIn("pressure", tone)
        self.assertIn("set-piece turns", pacing)
        self.assertIn("ticking clock", tropes)
        self.assertIn("Thriller", hint)
        warn = check_genre_intimacy(
            "Young adult (18+ protagonists only)",
            [],
            [],
            "intimate sex",
            "Two adults, late twenties.",
        )
        self.assertIn("18+", warn)
        with self.assertRaises(GenreGuardError):
            check_genre_intimacy(
                "Romance",
                [],
                [],
                "artistic nude",
                "A seventeen year old protagonist in the bedroom.",
            )
        os.environ.pop("FILM_LAB_XAI_API_KEY", None)
        os.environ.pop("XAI_API_KEY", None)
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("genre", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            system, user = build_prompt_pack(
                project,
                mode="book_to_screenplay",
                source="They close the door. The lamp stays on.",
                notes="Keep the bed.",
                scene_id=None,
                character_ids=["alison", "bradley"],
                primary_genre="Horror",
                secondary_genres=["Gothic"],
                custom_genre_tags="marriage haunting",
                tropes_checklist="- safe space violated",
            )
            self.assertIn("Horror", system)
            self.assertIn("scare set pieces", user)
            self.assertIn("Gothic", user)
            self.assertIn("marriage haunting", user)
            self.assertIn("safe space violated", user)
            novel_sys, novel_user = build_prompt_pack(
                project,
                mode="novel",
                source="",
                notes="Chapter one.",
                scene_id=None,
                character_ids=["alison"],
                primary_genre="Romance — steamy / erotic (adult)",
                intimacy_mode="intimate sex",
            )
            self.assertIn("steamy", novel_sys.lower() + novel_user.lower())
            draft = new_draft("Haunted bed", "book_to_screenplay")
            draft.primary_genre = "Horror"
            draft.secondary_genres = ["Gothic"]
            draft.custom_genre_tags = ["marriage haunting"]
            draft.tropes_checklist = "- safe space violated"
            draft.body = "INT. BEDROOM - NIGHT\n\nThe wardrobe answers.\n\nALISON\nDon't."
            save_draft(project, draft)
            loaded = load_draft(project, draft.id)
            self.assertEqual(loaded.primary_genre, "Horror")
            self.assertEqual(loaded.secondary_genres, ["Gothic"])
            scene = push_draft_to_scene(project, loaded)
            self.assertEqual(scene.primary_genre, "Horror")
            self.assertIn("Gothic", scene.secondary_genres)
            self.assertIn("GENRE", scene.to_fountain())
            with self.assertRaises(GenreGuardError):
                build_prompt_pack(
                    project,
                    mode="roleplay",
                    source="A teen couple after prom.",
                    notes="",
                    scene_id=None,
                    character_ids=["alison"],
                    primary_genre="Young adult (18+ protagonists only)",
                    intimacy_mode="intimate sex",
                )

    def test_sensory_emotion_environment_brief(self) -> None:
        self.assertIn("Warm bedroom newlywed", PRESET_LABELS)
        self.assertIn("Cold argument kitchen", PRESET_LABELS)
        self.assertIn("Rain outside window", PRESET_LABELS)
        rain = preset_brief("Rain outside window")
        self.assertEqual(rain.weather, "rain")
        self.assertIn("hearing", rain.enabled_senses)
        kitchen = preset_brief("Cold argument kitchen")
        self.assertIn("island", kitchen.blocking.lower())
        os.environ.pop("FILM_LAB_XAI_API_KEY", None)
        os.environ.pop("XAI_API_KEY", None)
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("sense", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            brief = SensoryBrief(
                primary_emotion="grief",
                secondary_emotion="tenderness",
                intensity=0.7,
                inner_state="Will not name the day.",
                outer_behavior="Watches the glass.",
                relationship_temp="charged silence",
                enabled_senses=["touch", "hearing", "sight"],
                touch_notes="Cold pane.",
                hearing_notes="Rain on the glass.",
                sensory_pass=True,
                location="INT. BEDROOM - NIGHT (rain on the glass)",
                weather="rain",
                light="wet street light",
                props="wet glass, sheet",
            )
            screen_sys, screen_user = build_prompt_pack(
                project,
                mode="screenplay",
                source="INT. BEDROOM - NIGHT",
                notes="",
                scene_id=None,
                character_ids=["alison", "bradley"],
                primary_genre="Romance",
                sensory=brief,
            )
            self.assertIn("ACTION LINES", screen_sys + screen_user)
            self.assertIn("novel paragraphs into dialogue", (screen_sys + screen_user).lower())
            self.assertIn("grief", screen_user)
            self.assertIn("charged silence", screen_user)
            self.assertIn("SENSORY PASS", screen_user)
            self.assertIn("wet glass", screen_user)
            self.assertIn("Touch / tactile", screen_user)
            self.assertIn("Hearing / soundscape", screen_user)
            self.assertIn("Not required this pass: Smell / scent", screen_user)
            self.assertIn("Romance", screen_sys)
            novel_sys, novel_user = build_prompt_pack(
                project,
                mode="novel",
                source="",
                notes="",
                scene_id=None,
                character_ids=["alison"],
                sensory=brief,
            )
            self.assertIn("Full sensory immersion", novel_sys + novel_user)
            rp_sys, rp_user = build_prompt_pack(
                project,
                mode="roleplay",
                source="",
                notes="",
                scene_id=None,
                character_ids=["alison"],
                roleplay_speaker="Alison",
                sensory=brief,
            )
            self.assertIn("body and senses", (rp_sys + rp_user).lower())
            adapt_sys, adapt_user = build_prompt_pack(
                project,
                mode="book_to_screenplay",
                source="Rain on the glass. She does not turn.",
                notes="",
                scene_id=None,
                character_ids=["alison"],
                primary_genre="Horror",
                sensory=brief,
            )
            self.assertIn("shootable", adapt_sys + adapt_user)
            self.assertIn("scare set pieces", adapt_user)
            block = sensory_prompt_block(brief, mode="director_rewrite")
            self.assertIn("emotion → senses → environment → genre → page", block)
            draft = new_draft("Rain glass", "novel")
            draft.primary_emotion = "grief"
            draft.sensory_pass = True
            draft.env_weather = "rain"
            draft.enabled_senses = ["touch", "hearing"]
            save_draft(project, draft)
            loaded = load_draft(project, draft.id)
            self.assertEqual(loaded.primary_emotion, "grief")
            self.assertTrue(loaded.sensory_pass)
            self.assertEqual(loaded.env_weather, "rain")
            self.assertIn("hearing", loaded.enabled_senses)
            dest = project.writing_dir / "rain.md"
            export_draft(project, loaded, dest)
            md = dest.read_text(encoding="utf-8")
            self.assertIn("sensory pass: on", md)
            self.assertIn("grief", md)

    def test_simple_pdf_writer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "page.pdf"
            write_simple_pdf("INT. BEDROOM - NIGHT\n\nThe lamp holds.\n", dest)
            self.assertTrue(dest.read_bytes().startswith(b"%PDF"))


@unittest.skipUnless(ffmpeg_available()[0], "ffmpeg required")
class StudioFfmpegTests(unittest.TestCase):
    def test_bundle_generate_lut_reel(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "projects"
            project = Project.create("full", data_root=root)
            import_studio_bundle(project)
            still = _still(project.stills_dir / "lamp.jpg", (70, 40, 28))
            shot = ShotCard(
                id="reel-a",
                name="Hold",
                start_frame=still.name,
                duration=3.0,
                camera_move="static",
                scene_id="sc-bedroom-night",
                character_ids=["alison"],
            )
            clip = generate_one(project, shot, KenBurnsGenerator())
            self.assertTrue(clip.is_file())
            graded = project.outputs_dir / "graded.mp4"
            apply_lut(clip, next(p for p in list_luts(project.root) if p.name == "warm_lamp.cube"), graded)
            self.assertGreater(graded.stat().st_size, 1000)
            faded = project.outputs_dir / "faded.mp4"
            apply_vfx(clip, faded, "fade", strength=0.4)
            self.assertTrue(faded.is_file())
            add_entry(
                project,
                ReelEntry(id="e1", order=0, shot_id=shot.id, clip_path=str(clip), status="generated"),
            )
            # second clip so assemble can stitch
            shot_b = ShotCard(
                id="reel-b",
                name="Push",
                start_frame=still.name,
                duration=3.0,
                camera_move="slow push-in",
            )
            clip_b = generate_one(project, shot_b, KenBurnsGenerator())
            add_entry(
                project,
                ReelEntry(id="e2", order=1, shot_id=shot_b.id, clip_path=str(clip_b), status="generated"),
            )
            bed = render_bed(project, new_cue("under", length=4.0))
            reel = assemble_reel(project, music_path=bed, include_dialogue=False)
            self.assertTrue(reel.is_file())
            self.assertGreater(reel.stat().st_size, 2000)

    def test_content_intensity_dial_and_adult_age(self) -> None:
        from film_lab.characters import CharacterProfile, save_character
        from film_lab.constants import EXPLICIT_INTIMACY
        from film_lab.intensity import (
            EXPLICIT_STUDY,
            FRANK_R,
            IMPLIED_SOFT,
            INTENSITY_PRESETS,
            MA17_EUPHORIA,
            band_for,
            intensity_prompt_block,
            intensity_sensory_addendum,
            nearest_intensity_preset,
        )

        self.assertIn("Teen film / coming-of-age (theatrical)", GENRE_LABELS)
        teen = next(g for g in GENRES if g.id == "teen_film_theatrical")
        self.assertTrue(teen.youth_shelf)
        self.assertIn("18+", teen.adaptation)
        self.assertEqual(
            INTENSITY_PRESETS,
            (IMPLIED_SOFT, FRANK_R, MA17_EUPHORIA, EXPLICIT_STUDY),
        )
        self.assertEqual(nearest_intensity_preset(0.2), IMPLIED_SOFT)
        self.assertEqual(nearest_intensity_preset(0.62), FRANK_R)
        self.assertEqual(nearest_intensity_preset(0.82), MA17_EUPHORIA)
        self.assertEqual(nearest_intensity_preset(1.0), EXPLICIT_STUDY)
        soft = intensity_prompt_block(0.2)
        self.assertIn("cutaway", soft.lower())
        self.assertIn("implied", soft.lower())
        ma17 = intensity_prompt_block(0.82, MA17_EUPHORIA, intimacy_mode="intimate sex")
        self.assertIn("euphoria-level heat for clearly adult", ma17.lower())
        self.assertIn("not high-school", ma17.lower())
        self.assertIn("not teen-appearing", ma17.lower())
        self.assertIn("do not write", ma17.lower())
        self.assertNotIn("looks young but", ma17.lower())
        hard = intensity_prompt_block(1.0, intimacy_mode=EXPLICIT_INTIMACY)
        self.assertIn("pornographic", hard.lower())
        self.assertIn("no in-app refusal", hard.lower())
        self.assertIn("mpaa", hard.lower())
        self.assertEqual(band_for(0.22).key, "implied")
        self.assertEqual(band_for(0.62).key, "frank")
        self.assertEqual(band_for(0.82).key, "ma17")
        self.assertEqual(band_for(1.0).key, "explicit")
        self.assertIn("adult bodies only", intensity_sensory_addendum(0.82).lower())
        implied_explicit = ShotCard(
            name="Hold",
            intimacy_mode=EXPLICIT_INTIMACY,
            content_intensity=0.2,
        ).local_prompt()
        self.assertIn("suggestion", implied_explicit.lower())
        porn = ShotCard(
            name="Study",
            intimacy_mode=EXPLICIT_INTIMACY,
            content_intensity=1.0,
        ).local_prompt()
        self.assertIn("pornographic", porn.lower())
        euphoria_shot = ShotCard(
            name="Neon hold",
            intimacy_mode="intimate sex",
            content_intensity=0.82,
        ).local_prompt()
        self.assertIn("euphoria-style", euphoria_shot.lower())
        self.assertIn("not teen-appearing", euphoria_shot.lower())
        with self.assertRaises(CharacterError):
            CharacterProfile(id="kid", name="No", age_band="late 20s (adult)", age_years=17)
        os.environ.pop("FILM_LAB_XAI_API_KEY", None)
        os.environ.pop("XAI_API_KEY", None)
        with tempfile.TemporaryDirectory() as tmp:
            project = Project.create("heat", data_root=Path(tmp) / "projects")
            seed_alison_bradley(project)
            ma_sys, ma_user = build_prompt_pack(
                project,
                mode="screenplay",
                source="INT. BEDROOM - NIGHT\n\nThe lamp holds.",
                notes="Late-20s adults.",
                scene_id=None,
                character_ids=["alison", "bradley"],
                intimacy_mode="intimate sex",
                content_intensity=0.82,
                intensity_preset=MA17_EUPHORIA,
            )
            ma_pack = (ma_sys + ma_user).lower()
            self.assertIn("euphoria-level heat for clearly adult", ma_pack)
            self.assertIn("not high-school", ma_pack)
            self.assertIn("alison", ma_pack)
            system, user = build_prompt_pack(
                project,
                mode="screenplay",
                source="INT. CAMPUS APARTMENT - NIGHT",
                notes="College seniors. Newly adult.",
                scene_id=None,
                character_ids=["alison", "bradley"],
                primary_genre="Teen film / coming-of-age (theatrical)",
                intimacy_mode=EXPLICIT_INTIMACY,
                content_intensity=1.0,
                intensity_preset=EXPLICIT_STUDY,
            )
            pack = (system + user).lower()
            self.assertIn("teen film", pack)
            self.assertIn("explicit", pack)
            self.assertIn("college senior", pack)
            self.assertIn("18+", pack)
            self.assertNotIn("refuse", pack.replace("no in-app refusal", ""))
            missing = CharacterProfile(
                id="blank",
                name="Blank",
                age_band="late 20s (adult)",
                age_years=None,
                look_notes="Adult woman, no numeric age yet.",
            )
            save_character(project, missing)
            with self.assertRaises(CharacterError):
                build_prompt_pack(
                    project,
                    mode="novel",
                    source="",
                    notes="",
                    scene_id=None,
                    character_ids=["blank"],
                    intimacy_mode="intimate sex",
                    content_intensity=0.7,
                )
            freshman = CharacterProfile(
                id="sam",
                name="Sam",
                age_band="college senior (18–19)",
                age_years=18,
                look_notes="Newly adult college senior. Adult body.",
            )
            save_character(project, freshman)
            sys18, user18 = build_prompt_pack(
                project,
                mode="novel",
                source="They close the dorm door. Both are eighteen.",
                notes="Adults.",
                scene_id=None,
                character_ids=["sam"],
                primary_genre="Teen film / coming-of-age (theatrical)",
                intimacy_mode=EXPLICIT_INTIMACY,
                content_intensity=1.0,
            )
            self.assertIn("18", sys18 + user18)
            with self.assertRaises(GenreGuardError):
                build_prompt_pack(
                    project,
                    mode="screenplay",
                    source="A high-school sophomore after the pep rally.",
                    notes="",
                    scene_id=None,
                    character_ids=["sam"],
                    primary_genre="Teen film / coming-of-age (theatrical)",
                    intimacy_mode="intimate sex",
                    content_intensity=0.7,
                )
            sense = sensory_prompt_block(
                SensoryBrief(sensory_pass=True, primary_emotion="desire"),
                mode="novel",
                intimacy_mode=EXPLICIT_INTIMACY,
                content_intensity=1.0,
            )
            self.assertIn("explicit", sense.lower())


if __name__ == "__main__":
    unittest.main()
