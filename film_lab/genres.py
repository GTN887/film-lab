"""Writing Studio genre catalog, presets, and adult-age guard."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from film_lab.constants import INTIMACY_MODES
from film_lab.intimacy import INTIMATE_LABELS

_NOT_ADULT_PROTAG = re.compile(
    r"\b(child|children|kid|kids|toddler|infant|preteen|middle[- ]school|"
    r"high[- ]school|underage|minor protagonist|"
    r"teen(?:age(?:r|d)?)?(?!\s*(?:film|movie|pic|cinema))|"
    r"seventeen|sixteen|fifteen|fourteen|thirteen|"
    r"12[- ]year|13[- ]year|14[- ]year|15[- ]year|16[- ]year|17[- ]year)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class GenreSpec:
    id: str
    label: str
    family: str
    tone: str
    pacing: str
    tropes: tuple[str, ...]
    adaptation: str
    youth_shelf: bool = False
    examples: tuple[str, ...] = field(default_factory=tuple)


def _g(
    gid: str,
    label: str,
    family: str,
    tone: str,
    pacing: str,
    tropes: tuple[str, ...],
    adaptation: str,
    *,
    youth_shelf: bool = False,
    examples: tuple[str, ...] = (),
) -> GenreSpec:
    return GenreSpec(gid, label, family, tone, pacing, tropes, adaptation, youth_shelf, examples)


GENRES: tuple[GenreSpec, ...] = (
    _g(
        "literary_fiction",
        "Literary fiction",
        "literary",
        "interior, precise, unhurried",
        "image and thought over plot turns",
        ("motif return", "subtext in ordinary talk", "unresolved aftertaste"),
        "Adapt interiority into playable action and silence, not voice-over essays.",
        examples=("A single object on the nightstand does more work than a speech.",),
    ),
    _g(
        "contemporary",
        "Contemporary",
        "realist",
        "present-tense social, clean, specific",
        "scene-to-scene, phone and room geography",
        ("class/work friction", "found family or marriage under pressure", "city vs. home"),
        "Keep phones, money, and rooms visible. Cut lyrical summary into beats.",
        examples=("They are already married. The fight is about the lamp, not the lamp.",),
    ),
    _g(
        "historical_fiction",
        "Historical fiction",
        "historical",
        "period texture without museum tour",
        "research worn lightly; scenes move on desire and duty",
        ("anachronism watch", "class and custom as blocking", "letters / public vs private"),
        "Period detail is production design. Conflict stays human and present-tense.",
        examples=("INT. LODGING HOUSE - NIGHT. The washbasin, then the glance.",),
    ),
    _g(
        "romance",
        "Romance",
        "romance",
        "yearning, warmth, earned closeness",
        "emotional set pieces: meet, turn, rupture, repair, landing",
        ("yearning look", "almost-touch", "misread then repair", "public vs private intimacy"),
        "Build the adaptation on emotional set pieces, not plot synopsis. The kiss is a scene, not a sting.",
        examples=("They have already said the hard thing. Now they have to stay in the room.",),
    ),
    _g(
        "steamy_romance",
        "Romance — steamy / erotic (adult)",
        "romance",
        "heat with character, not inventory",
        "slow build, then committed scenes; aftercare is a beat",
        ("consent-in-fiction as blocking", "body as character", "afterglow talk"),
        "Intimate scenes are blocking and faces first. Cut around heat only when the cut is motivated.",
        examples=("Covered sheets first. Then a decision, not a smash cut.",),
    ),
    _g(
        "romantic_comedy",
        "Romantic comedy",
        "romance",
        "warm, specific, not sitcom-broad unless asked",
        "banter, button, then a real landing",
        ("wrong assumption", "public embarrassment", "honest last scene"),
        "Comic turns need geography. The button is visual. The landing still has to be felt.",
        examples=("The joke dies when he sees the wedding band. Stay there.",),
    ),
    _g(
        "thriller",
        "Thriller",
        "crime",
        "pressure, withheld information, clean dread",
        "set-piece turns: clock, reversal, no-exit room",
        ("ticking clock", "false safety", "one object that shouldn't be there"),
        "Adapt as set-piece turns. Each scene changes who has the information.",
        examples=("The hallway light works. The bedroom door does not stay shut.",),
    ),
    _g(
        "mystery",
        "Mystery",
        "crime",
        "curious, ordered, clue-honest",
        "question, misdirect, reveal you could have seen",
        ("clue in plain sight", "red herring with character cost", "reveal restages the room"),
        "Plant clues as props and blocking. The reveal should restage a room we already know.",
        examples=("She notices the second glass after we have already seen it twice.",),
    ),
    _g(
        "crime",
        "Crime",
        "crime",
        "procedural grit or quiet professionalism",
        "job, consequence, loyalty test",
        ("the job vs the marriage", "body as evidence, not spectacle", "debt"),
        "Procedure is blocking. Keep the personal cost in the same frame as the work.",
        examples=("He washes his hands like it is still a kitchen.",),
    ),
    _g(
        "noir",
        "Noir",
        "crime",
        "fatalistic, lamp-cut shadows, dry talk",
        "descent; each favor costs more",
        ("voice with a limp", "city as trap", "loyalty that fails at 3 a.m."),
        "Light is story. Adapt in rooms, alleys, and bargains — not plot maps.",
        examples=("INT. CHEAP HOTEL - NIGHT. The fan. Then the lie.",),
    ),
    _g(
        "legal_thriller",
        "Legal thriller",
        "crime",
        "argument as sport, private cost after court",
        "hearing / deposition set pieces, then the kitchen",
        ("exhibit as object", "off-record in a corridor", "the story the jury will not hear"),
        "Court is a set piece. The adaptation lives in corridors and the night after.",
        examples=("They rehearse testimony in bed because that is the only unlocked room.",),
    ),
    _g(
        "horror",
        "Horror",
        "horror",
        "dread first, shock second",
        "scare set pieces with silence between",
        ("safe space violated", "sound offscreen", "rule revealed too late"),
        "Adapt as scare set pieces: hold, deny, then pay off. Do not explain the dark in dialogue.",
        examples=("The lamp is still on. Something in the wardrobe answers it.",),
    ),
    _g(
        "gothic",
        "Gothic",
        "horror",
        "lush, doomed, house-as-mind",
        "atmosphere, then a threshold you should not cross",
        ("the house wants them", "inheritance", "a locked wing"),
        "Architecture is antagonist. Cross a threshold each scene.",
        examples=("The guest room was their room ten years ago. The wallpaper remembers.",),
    ),
    _g(
        "supernatural_horror",
        "Supernatural horror",
        "horror",
        "uncanny made physical",
        "rule, test, violation, cost",
        ("the rule on paper", "a witness who will not be believed", "body as proof"),
        "Give the supernatural a rule you can shoot. Pay it off in blocking, not lore dumps.",
        examples=("She counts three knocks. We only hear two.",),
    ),
    _g(
        "fantasy_high",
        "Fantasy — high",
        "speculative",
        "mythic clarity, ritual weight",
        "quest stages as scenes; wonder then cost",
        ("oath", "threshold guardian", "map vs desire"),
        "Wonder is production design. Cut lore into objects, vows, and arrivals.",
        examples=("They take the rings off before the rite. That is the scene.",),
    ),
    _g(
        "fantasy_low",
        "Fantasy — low",
        "speculative",
        "dirt, hunger, small magic",
        "one impossibility in a real room",
        ("magic has a price in the body", "politics at table", "the road"),
        "Keep magic scarce and visible. The rest is crime, marriage, or war.",
        examples=("The charm only works if they are touching. They argue about that.",),
    ),
    _g(
        "fantasy_urban",
        "Fantasy — urban",
        "speculative",
        "night city, secret system under neon",
        "case-of-the-week pressure + hidden court",
        ("the veil", "a bar that is a court", "true name"),
        "City geography is the map. Secret rules should change a location we already shot.",
        examples=("The 24-hour laundromat is the only place the dead will talk.",),
    ),
    _g(
        "science_fiction",
        "Science fiction",
        "speculative",
        "idea made tactile",
        "premise, human test, new normal",
        ("tech as blocking", "who owns the body", "the window onto the dark"),
        "Show the idea as a tool or a room. Do not lecture the future.",
        examples=("The implant logs every kiss. Tonight they pull the battery.",),
    ),
    _g(
        "dystopian",
        "Dystopian",
        "speculative",
        "controlled, watched, small rebellions",
        "rule of the world, then a private violation",
        ("ration", "permit", "love as contraband"),
        "World rules should be visible in costumes and doors. The private scene is the revolt.",
        examples=("They are allowed one hour without the monitor. They waste four minutes on courage.",),
    ),
    _g(
        "cyberpunk",
        "Cyberpunk",
        "speculative",
        "wet neon, corporate cold, body-mod intimacy",
        "heist / jack-in set pieces, crash after",
        ("augment as vulnerability", "the corp owns the footage", "rain on plastic"),
        "Interface is a set piece. Crash and aftercare still need faces.",
        examples=("She unplugs first. He is still in the feed, looking at her from the ceiling.",),
    ),
    _g(
        "adventure",
        "Adventure",
        "adventure",
        "forward, weather, companionship",
        "set-piece travel: depart, ordeal, campfire",
        ("the map is wrong", "a companion debt", "weather as antagonist"),
        "Travel is scenes, not montage unless you earn it. Campfire is character.",
        examples=("They share the last dry blanket. The mountain can wait one page.",),
    ),
    _g(
        "action",
        "Action",
        "adventure",
        "kinetic, clear geography",
        "set-piece, button, breath, next set-piece",
        ("geography first", "a weapon that is also a relationship", "the cost after the win"),
        "Every fight needs a room we understand. Cut to the breath after.",
        examples=("He puts the gun on the dresser because she asked. That is the stunt.",),
    ),
    _g(
        "war",
        "War",
        "adventure",
        "exhaustion, dark humor, sudden quiet",
        "before / during / after; letters home",
        ("the letter", "a stupid joke that keeps them alive", "home that does not fit"),
        "Do not aestheticize injury. Private scenes carry the war home.",
        examples=("INT. BILLET - NIGHT. Two adults. The boots stay on because taking them off means staying.",),
    ),
    _g(
        "western",
        "Western",
        "adventure",
        "dust, moral weather, few words",
        "ride, town, threshold, dusk",
        ("the horse as time", "a porch negotiation", "the law arrives late"),
        "Landscape is the cutaway. Town scenes do the talking.",
        examples=("They wash at the same basin. The town will hear about it by noon.",),
    ),
    _g(
        "young_adult",
        "Young adult (18+ protagonists only)",
        "youth",
        "first-intensity feeling, clear stakes",
        "set pieces of becoming; no minor protagonists in this studio",
        ("first real choice", "friend group as chorus", "a door they cannot go back through"),
        "This studio labels YA as 18+ adults only. Adapt voice and first-intensity, never underage bodies.",
        youth_shelf=True,
        examples=("They are eighteen and already married in secret. Treat them as adults.",),
    ),
    _g(
        "new_adult",
        "New adult (18+ / early 20s)",
        "youth",
        "early-adult hunger, money, first home",
        "campus-to-apartment; intimacy is adult",
        ("first apartment", "work shift after class", "the band or the ring"),
        "New adult here means adults. Intimate study is allowed; minors are not.",
        youth_shelf=True,
        examples=("The first apartment has one lamp. That is the whole production design.",),
    ),
    _g(
        "magical_realism",
        "Magical realism",
        "speculative",
        "deadpan wonder, ordinary rooms",
        "one impossibility accepted by the scene",
        ("the impossible is domestic", "no explanation", "community as witness"),
        "Do not explain the miracle. Shoot it like the kettle.",
        examples=("She hangs her wet hair over the chair. It flowers. He asks about dinner.",),
    ),
    _g(
        "speculative",
        "Speculative",
        "speculative",
        "what-if held close to the skin",
        "premise then a human night",
        ("the rule", "the exception they make for each other", "morning after the idea"),
        "The speculative rule should change blocking, not only theme.",
        examples=("If they fall asleep touching, they share a dream. Tonight they keep a gap.",),
    ),
    _g(
        "slipstream",
        "Slipstream",
        "speculative",
        "uneasy realist, genre leaking in",
        "real room, then a seam",
        ("the seam", "deny, then look again", "no clean bin"),
        "Stay realist until the seam. Do not announce the genre.",
        examples=("The second wedding band on the dresser is his. He is wearing one.",),
    ),
    _g(
        "comedy",
        "Comedy",
        "comic",
        "specific, character-first funny",
        "setup, turn, button; protect the landing",
        ("status flip", "the body betrays the joke", "callback prop"),
        "Comic adaptation needs buttons you can shoot. Do not punch down at the marriage.",
        examples=("He tries to be dignified with a sheet. She will not help.",),
    ),
    _g(
        "satire",
        "Satire",
        "comic",
        "cool blade, target clear",
        "escalate the system, keep the couple human",
        ("institution as farce", "the sincere person in the machine", "the last un-ironic beat"),
        "Satirize the system, not the adults' tenderness unless that is the point.",
        examples=("The wellness app wants a sex score. They put the phone in the drawer.",),
    ),
    _g(
        "absurdist",
        "Absurdist",
        "comic",
        "deadpan, logic sideways",
        "repeat, escalate, refuse explanation",
        ("a rule that should not exist", "polite response to the impossible", "no moral"),
        "Keep performances sincere. The world is the joke.",
        examples=("A third adult is in the bed. They all agree not to discuss it yet.",),
    ),
    _g(
        "memoir_autofiction",
        "Memoir-style / autofiction (fictionalized)",
        "literary",
        "intimate witness, shaped memory",
        "selected nights, not a life dump",
        ("the tellable scene", "what the narrator will not say", "a real object"),
        "Treat as fiction for adaptation. One night, not a biopic.",
        examples=("I remember the lamp more than his mouth. Write the lamp.",),
    ),
    _g(
        "family_saga",
        "Family saga",
        "literary",
        "generational weather, long loyalties",
        "table scenes, inheritances, time jumps you can costume",
        ("the table", "who keeps the house", "a secret the children are too old for now"),
        "One table, two generations if needed — all adults on this desk. Time jumps via costume and rooms.",
        examples=("Mother's wedding band does not fit Alison. She wears it anyway.",),
    ),
    _g(
        "coming_of_age_adult",
        "Coming-of-age (adult)",
        "youth",
        "late firsts, second starts",
        "a threshold in an already-adult life",
        ("the job they outgrew", "a parent dies offstage", "first honest marriage night"),
        "Adult coming-of-age only. No adolescent protagonists.",
        youth_shelf=True,
        examples=("They are twenty-eight and finally moving in. Treat it as a first time anyway.",),
    ),
    _g(
        "teen_film_theatrical",
        "Teen film / coming-of-age (theatrical)",
        "youth",
        "first-intensity, formal, the last summer — theatrical teen-movie grammar",
        "set pieces of becoming; college-senior / newly-adult bodies only",
        (
            "the last party as adults",
            "a car talk after the dance",
            "the house they will not return to",
            "college senior / 18–19 newly adult",
        ),
        (
            "Theatrical teen-movie style only. Protagonists must be 18+ "
            "(college senior, 18–19, newly adult). Never write high-school minors. "
            "Intimate or explicit study is allowed for those adults."
        ),
        youth_shelf=True,
        examples=(
            "They are eighteen, college seniors, already legal adults. "
            "The formal is a campus dance, not a high-school prom with minors.",
        ),
    ),
    _g(
        "slice_of_life",
        "Slice of life",
        "realist",
        "low plot, high texture",
        "ordinary duration; let chores be scenes",
        ("tea / dishes / sheets", "a small kindness", "no speech required"),
        "Do not invent a plot engine. Sequence the room.",
        examples=("She folds the shirt he will not wear tomorrow. Hold.",),
    ),
    _g(
        "erotica_literary",
        "Erotica / adult literary (explicit adult only)",
        "adult",
        "explicit, character-bound, unashamed",
        "desire as structure; aftercare on the page",
        ("want named", "body detail that is character", "the morning is part of it"),
        "Adults only. Adapt heat as blocking and faces. No minor-coded language.",
        examples=("Intimate sex study: hips, hands, breath. Write it so a camera can hold it.",),
    ),
    _g(
        "experimental_hybrid",
        "Experimental / hybrid",
        "literary",
        "form-forward, still playable",
        "break the page, not the performers",
        ("braid / list / chorus", "a form you can still shoot", "repeat with variation"),
        "If it cannot be blocked, mark it as text-on-screen or voice, not fake coverage.",
        examples=("The scene is only stage directions. Then one line of dialogue at the end.",),
    ),
)

GENRE_BY_ID: dict[str, GenreSpec] = {g.id: g for g in GENRES}
GENRE_LABELS: tuple[str, ...] = tuple(g.label for g in GENRES)
LABEL_TO_ID: dict[str, str] = {g.label: g.id for g in GENRES}

DEFAULT_PRIMARY = "Romance"
CUSTOM_PRIMARY = "Custom (free-text tags)"
PRIMARY_CHOICES: tuple[str, ...] = GENRE_LABELS + (CUSTOM_PRIMARY,)


def join_custom_tags(tags: list[str] | None) -> str:
    return ", ".join(tags or [])


class GenreGuardError(ValueError):
    """Intimate mode paired with minor protagonists is blocked."""


def spec_for_label(label: str) -> GenreSpec | None:
    gid = LABEL_TO_ID.get((label or "").strip())
    return GENRE_BY_ID.get(gid) if gid else None


def collect_specs(primary: str | None, secondary: list[str] | None) -> list[GenreSpec]:
    found: list[GenreSpec] = []
    seen: set[str] = set()
    for label in [primary or "", *(secondary or [])]:
        spec = spec_for_label(label)
        if spec and spec.id not in seen:
            found.append(spec)
            seen.add(spec.id)
    return found


def parse_custom_tags(raw: str | list[str] | None) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        text = ", ".join(str(part) for part in raw if str(part).strip())
    else:
        text = str(raw)
    tags: list[str] = []
    for part in re.split(r"[,;\n]+", text):
        tag = part.strip()
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def genre_line(primary: str | None, secondary: list[str] | None, custom: list[str] | None) -> str:
    bits = []
    if primary:
        bits.append(f"primary: {primary}")
    extra = [s for s in (secondary or []) if s and s != primary]
    if extra:
        bits.append("also: " + ", ".join(extra))
    if custom:
        bits.append("custom: " + ", ".join(custom))
    return "; ".join(bits) or "unspecified"


def preset_for(primary: str | None, secondary: list[str] | None = None) -> dict[str, str]:
    specs = collect_specs(primary, secondary)
    if not specs:
        return {
            "tone": "",
            "pacing": "",
            "tropes": "",
            "adaptation": "",
        }
    head = specs[0]
    tropes: list[str] = []
    adaptations: list[str] = []
    tones: list[str] = []
    pacings: list[str] = []
    for spec in specs:
        tones.append(f"{spec.label}: {spec.tone}")
        pacings.append(f"{spec.label}: {spec.pacing}")
        for trope in spec.tropes:
            if trope not in tropes:
                tropes.append(trope)
        adaptations.append(f"{spec.label}: {spec.adaptation}")
    return {
        "tone": head.tone if len(specs) == 1 else " | ".join(tones),
        "pacing": head.pacing if len(specs) == 1 else " | ".join(pacings),
        "tropes": "\n".join(f"- {t}" for t in tropes),
        "adaptation": " ".join(adaptations),
    }


def examples_for(primary: str | None, secondary: list[str] | None = None) -> list[str]:
    specs = collect_specs(primary, secondary)
    examples: list[str] = []
    for spec in specs:
        for ex in spec.examples:
            if ex not in examples:
                examples.append(ex)
    if not examples:
        examples.append("INT. BEDROOM - NIGHT. Two adults. A lamp. A decision.")
    return examples


def genre_prompt_block(
    primary: str | None,
    secondary: list[str] | None,
    custom: list[str] | None,
    tropes: str | None,
    *,
    mode: str,
) -> str:
    specs = collect_specs(primary, secondary)
    preset = preset_for(primary, secondary)
    lines = [f"Genre: {genre_line(primary, secondary, custom)}"]
    if preset["adaptation"] and mode in {"book_to_screenplay", "screenplay", "director_rewrite"}:
        lines.append(f"Genre-aware adaptation: {preset['adaptation']}")
    if tropes and tropes.strip():
        lines.append("Trope checklist (editable):\n" + tropes.strip())
    elif preset["tropes"]:
        lines.append("Trope checklist:\n" + preset["tropes"])
    youth = [s.label for s in specs if s.youth_shelf]
    if youth:
        extra = ""
        if any(s.id == "teen_film_theatrical" for s in specs):
            extra = (
                " Teen film / coming-of-age (theatrical) means college senior, "
                "18–19+, newly adult — not high-school minors."
            )
        lines.append(
            "AGE RULE: "
            + ", ".join(youth)
            + " in this studio requires 18+ adult protagonists. Do not write minors."
            + extra
        )
    return "\n".join(lines)


def youth_shelf_active(primary: str | None, secondary: list[str] | None = None) -> bool:
    return any(s.youth_shelf for s in collect_specs(primary, secondary))


def check_genre_intimacy(
    primary: str | None,
    secondary: list[str] | None,
    custom: list[str] | None,
    intimacy: str,
    *text_blobs: str,
    content_intensity: float = 0.0,
) -> str:
    """Block minor protagonists in intimate / frank+ modes; warn on youth shelf."""
    from film_lab.intensity import intensity_requires_numeric_age
    from film_lab.intimacy import is_intimate

    intimacy = intimacy if intimacy in INTIMACY_MODES else "covered sheets"
    blob = " ".join(t or "" for t in text_blobs)
    custom_l = " ".join(custom or [])
    youth = [s for s in collect_specs(primary, secondary) if s.youth_shelf]
    sexual = is_intimate(intimacy) or intensity_requires_numeric_age(content_intensity)
    if sexual and _NOT_ADULT_PROTAG.search(blob):
        raise GenreGuardError(
            "Blocked: sexual or intimate generation cannot pair with minor or "
            "under-18 protagonists. Adults 18+ only. No sexual content involving "
            "minors under any framing."
        )
    if (sexual or youth) and _NOT_ADULT_PROTAG.search(custom_l):
        raise GenreGuardError(
            "Blocked: custom genre tags look like they target minors. Adults 18+ only."
        )
    if youth and _NOT_ADULT_PROTAG.search(blob):
        raise GenreGuardError(
            "Blocked: teen-film / YA / coming-of-age tags in this studio require "
            "18+ protagonists (college senior, newly adult). High-school minors "
            "are not allowed."
        )
    if youth and (is_intimate(intimacy) or intensity_requires_numeric_age(content_intensity)):
        return (
            "Note: "
            + ", ".join(s.label for s in youth)
            + " — intimacy requires 18+ adult protagonists "
            "(college senior / newly adult for theatrical teen film). "
            "The prompt will forbid minors. Adult explicit is allowed."
        )
    if youth:
        return (
            "Note: "
            + ", ".join(s.label for s in youth)
            + " is labeled for 18+ protagonists in this studio."
        )
    return ""
