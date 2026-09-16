"""Optional cinematic lighting presets for local prompt injection.

User chooses or skips. Never forced. Zero Film Lab credits. Adults 18+ only.
"""

from __future__ import annotations

from dataclasses import dataclass

SKIP_LABEL = "None — skip (optional)"
PICKER_LABEL = "Lighting (optional — pick one or skip)"
SKIP_ALIASES = frozenset(
    {
        "",
        "none",
        "skip",
        "off",
        "no lighting",
        SKIP_LABEL.lower(),
        "none — skip",
        "none - skip (optional)",
    }
)


@dataclass(frozen=True)
class LightingPreset:
    key: str
    title: str
    chip: str
    mentor: str
    intimacy: str
    group: str = "look"


LIGHTING_PRESETS: tuple[LightingPreset, ...] = (
    LightingPreset(
        key="rembrandt",
        title="Rembrandt",
        chip="Rembrandt lighting, triangle of light on the shadow cheek, single motivated key",
        mentor="One key, 45° and slightly above. The triangle on the far cheek is the lock.",
        intimacy="Good for a still face during sex — want without showing every pore. Keep the key motivated (lamp, not a fresnel).",
        group="look",
    ),
    LightingPreset(
        key="neon",
        title="Neon",
        chip="neon lighting, magenta-cyan practicals through blinds, wet color on skin",
        mentor="Color from a sign or LED strip. Not a club wash — a leak through the blinds.",
        intimacy="After a street walk, hotel, or city nest. Keep faces adult. Color is mood, not a filter pack.",
        group="look",
    ),
    LightingPreset(
        key="overcast",
        title="Overcast",
        chip="overcast daylight, large soft sky, gentle wrap, low contrast, cool fill",
        mentor="Soft even day. No hard sun. Faces wrap. Good for windows and streets.",
        intimacy="Tender, not clinical. Sheets go linen; skin stays adult, not glossy.",
        group="look",
    ),
    LightingPreset(
        key="key",
        title="Key",
        chip="key light only, directional 45°, modeled face, open shadow side",
        mentor="The main source. Place it, then stop. Fill and rim are optional extras.",
        intimacy="One motivated key keeps bodies readable without flattening.",
        group="basic",
    ),
    LightingPreset(
        key="fill",
        title="Fill",
        chip="soft fill light, lifted shadows, key still dominates, no second sun",
        mentor="Opens the dark side a stop. Do not match the key or the face goes flat.",
        intimacy="A little fill so both adults read under a sheet. Then stop.",
        group="basic",
    ),
    LightingPreset(
        key="rim",
        title="Rim / silhouette",
        chip="rim light, backlight edge on hair and shoulders, faces mostly silhouette",
        mentor="Separates bodies from the wall. Edge light, not a beauty key.",
        intimacy="Bodies as shape. Sweat sheen, outline, coming back from the bathroom.",
        group="basic",
    ),
    LightingPreset(
        key="three_point",
        title="Three-point",
        chip="three-point lighting, key at 45, soft fill, hair light separation",
        mentor="Classic readable faces. Key models, fill opens shadows, back light lifts hair from the wall.",
        intimacy="Keeps both adults readable under a sheet without flattening skin.",
        group="basic",
    ),
    LightingPreset(
        key="day",
        title="Day",
        chip="daylight, motivated window sun, natural color, readable room",
        mentor="Day interior or street. Sun or sky is the source — not a studio kit.",
        intimacy="Playful or frank daylight. Easy to look like a catalog if you over-fill.",
        group="time",
    ),
    LightingPreset(
        key="night",
        title="Night",
        chip="night interior, practical lamps only, deep falloff, cool window if any",
        mentor="Night is darkness plus a few motivated sources. Let corners die.",
        intimacy="Private. Skin goes amber then black. Wedding bands catch a lamp.",
        group="time",
    ),
    LightingPreset(
        key="practical_lamps",
        title="Practical lamps",
        chip="practical lamps, tungsten table lamp and phone as the only sources, amber falloff",
        mentor="Light comes from objects in the room. The lamp is the story.",
        intimacy="Honest bedroom sex light. Far body falls into brown shadow.",
        group="practical",
    ),
    LightingPreset(
        key="motivated_practicals",
        title="Motivated practicals",
        chip="motivated practical lighting, lamp and phone as the only sources, falloff in the corners",
        mentor="Same school as practical lamps. Objects in frame do the lighting.",
        intimacy="Honest bedroom sex light. Wedding bands catch the practical.",
        group="practical",
    ),
    LightingPreset(
        key="warm_lamp_bedroom",
        title="Warm lamp bedroom",
        chip="warm lamp bedroom, tungsten practical, amber falloff, soft shadow on the far wall",
        mentor="Default nest light when you want one. One lamp, close, warm.",
        intimacy="Intimacy reads as private, not porn-flat.",
        group="practical",
    ),
    LightingPreset(
        key="soft_window",
        title="Soft window",
        chip="soft window light, overcast, large source, gentle wrap, cool fill in the room",
        mentor="Big soft source. Faces wrap. Morning-after and late afternoon stills.",
        intimacy="Tender, not clinical. Cooler than the lamp.",
        group="look",
    ),
    LightingPreset(
        key="candle",
        title="Candle / firelight",
        chip="candle and firelight, small warm flicker, deep falloff, gold catchlights",
        mentor="Tiny source, huge falloff. Faces live or die in two feet. Fire is the same school.",
        intimacy="Slow, close, whispered. Do not add a second key.",
        group="practical",
    ),
    LightingPreset(
        key="bedside_lamp",
        title="Practical bedside lamp",
        chip="practical bedside lamp, close tungsten, amber pool on the pillow, far wall dies",
        mentor="The nightstand lamp is the only source. Sit it in frame if you can.",
        intimacy="Honest bedroom sex light. Skin goes gold then brown.",
        group="practical",
    ),
    LightingPreset(
        key="high_key",
        title="High-key bright",
        chip="high-key lighting, bright soft wrap, lifted shadows, clean walls",
        mentor="Shadows almost gone. Daytime, bathroom, or a frank comedy beat.",
        intimacy="Rare for sex unless it is playful daylight.",
        group="look",
    ),
    LightingPreset(
        key="low_key",
        title="Moody low-key",
        chip="low-key lighting, crushed blacks, one motivated highlight, graphic shadows",
        mentor="Most of the frame is dark. One highlight is the sentence.",
        intimacy="Graphic bodies, not a beauty reel.",
        group="look",
    ),
    LightingPreset(
        key="golden_hour",
        title="Golden hour",
        chip="golden hour, low warm sun, long shadows, honey sidelight",
        mentor="Sun near the horizon. Directional, warm, short window.",
        intimacy="Afternoon sex with blinds cracked. Do not add a second sun.",
        group="time",
    ),
    LightingPreset(
        key="hard_noon",
        title="Hard noon sun",
        chip="hard noon sun, overhead hard key, short dark shadows, hot pavement or bare room",
        mentor="Sun straight up. Hard, ugly-pretty, no wrap. Hide or own the shadows.",
        intimacy="Frank daylight sex or a street beat. Sweat reads. Do not add fill.",
        group="time",
    ),
    LightingPreset(
        key="blue_hour",
        title="Blue hour / twilight",
        chip="blue hour twilight, cool cobalt sky, leftover warm windows, long quiet falloff",
        mentor="After sunset, before night. Sky is the fill. Windows are the keys.",
        intimacy="Quiet undress at the window. Cool skin, warm lamp in the room.",
        group="time",
    ),
    LightingPreset(
        key="moonlight",
        title="Cool moonlight exterior",
        chip="cool moonlight exterior, blue-green wash, soft window shape, deep room blacks",
        mentor="Cool, dim, shaped by the moon or the night sky. Not silver spray.",
        intimacy="Quiet afterglow or a 3 a.m. look.",
        group="time",
    ),
    LightingPreset(
        key="fluorescent",
        title="Fluorescent / office",
        chip="fluorescent office light, green-white overheads, flat shadows, institutional ceiling",
        mentor="Ugly motivated overheads. Cubicle, hallway, late office. Not a beauty key.",
        intimacy="Affair-in-the-office or after-hours. Keep it adult and specific, not a sitcom.",
        group="look",
    ),
    LightingPreset(
        key="rain_overcast",
        title="Rain / wet overcast",
        chip="rain wet overcast, soaked pavement, window streaks, soft sky, specular wet skin",
        mentor="Overcast plus weather. Highlights live on wet glass and coats.",
        intimacy="Come-in-from-the-rain stills. Water on skin, not a shower-gel ad.",
        group="look",
    ),
    LightingPreset(
        key="neon_noir",
        title="Neon noir",
        chip="neon noir, wet street, magenta-cyan slash, deep blacks, hard color on faces",
        mentor="Night + neon + wet. Graphic, not a club wash. One color does the talking.",
        intimacy="Hotel, alley, after the walk. Adult faces. Color is mood.",
        group="look",
    ),
    LightingPreset(
        key="anamorphic_night",
        title="Anamorphic night",
        chip="anamorphic night, widescreen, stretched speculars, cool street, shallow falloff",
        mentor="Night as a wide plate. Speculars smear. Keep the key motivated — a sign, a lamp, a car.",
        intimacy="Hotel glass, wet street, adult faces. Do not flatten with a beauty fill.",
        group="cinema",
    ),
    LightingPreset(
        key="teal_orange",
        title="Teal & orange",
        chip="teal and orange grade, cool shadows, warm skin key, split complementary night",
        mentor="Warm key, cool fill. A grade, not a LUT pack. Keep skin adult and specific.",
        intimacy="Bodies stay warm. Walls go teal. Do not turn skin into plastic.",
        group="cinema",
    ),
    LightingPreset(
        key="god_rays",
        title="Volumetric god-rays",
        chip="volumetric god-rays, shafts through blinds or dust, bright beams, dark room",
        mentor="One hard source punching haze. The beam is the sentence.",
        intimacy="Dust and sweat in the shaft. Faces can go silhouette. Adults only.",
        group="cinema",
    ),
    LightingPreset(
        key="fog_haze",
        title="Fog / haze",
        chip="fog and haze, soft bloom, lifted blacks, atmosphere between bodies and the wall",
        mentor="Air you can see. Lower contrast. Edges melt a stop.",
        intimacy="Close, humid, private. Not a horror fog machine.",
        group="cinema",
    ),
    LightingPreset(
        key="rain_glass",
        title="Rain on glass",
        chip="rain on glass, window streaks as the key, specular drops, soft room beyond",
        mentor="The pane is the light. Streaks, not a weather overlay sticker.",
        intimacy="Watching from inside. Skin on the near side, rain on the far.",
        group="cinema",
    ),
    LightingPreset(
        key="handheld_doc",
        title="Handheld documentary",
        chip="handheld documentary light, mixed available sources, bounce, imperfect exposure",
        mentor="Whatever is in the room. Slightly dirty. No beauty kit.",
        intimacy="Frank, adult, present. A little ugly is honest.",
        group="cinema",
    ),
    LightingPreset(
        key="studio_beauty",
        title="Clean studio beauty",
        chip="clean studio beauty, large softboxes, even wrap, clean backdrop, controlled catchlights",
        mentor="Catalog-pretty. Soft, even, no dirt in the corners.",
        intimacy="Rare for sex unless it is a posed still. Easy to go plastic — stop early.",
        group="cinema",
    ),
    LightingPreset(
        key="noir_venetian",
        title="Noir venetian",
        chip="noir venetian blinds, hard slash stripes, deep blacks, graphic face cuts",
        mentor="Blinds as a cookie. One hard key. Most of the frame dies.",
        intimacy="Graphic bodies in the slashes. Adult, not a poster parody.",
        group="cinema",
    ),
    LightingPreset(
        key="warm_tungsten",
        title="Warm tungsten interior",
        chip="warm tungsten interior, 3200K practicals, amber walls, cozy falloff",
        mentor="Every lamp is tungsten. Rooms feel closed and warm.",
        intimacy="Nest light. Skin goes gold. Far wall browns out.",
        group="cinema",
    ),
    LightingPreset(
        key="prestige_night",
        title="Prestige-TV night",
        chip="prestige-TV night, saturated candy practicals, glossy skin, hotel and club falloff",
        mentor="Saturated night interior. Candy lamps, wet highlight on cheekbones. Original look — not a show clone.",
        intimacy="Adult glamour, hotel, after the party. Keep faces 18+.",
        group="cinema",
    ),
    LightingPreset(
        key="space_opera_rim",
        title="Space-opera rim",
        chip="space-opera rim, dual-color edge light, mythic backlight, deep blacks, face held then revealed",
        mentor="Two rims, opposite hues. Mythic outline. Original look — not a franchise kit.",
        intimacy="Bodies as silhouette, then a reveal. Adult, graphic, not a toy commercial.",
        group="cinema",
    ),
)

STUDIO_TITLES: tuple[str, ...] = (
    "Rembrandt",
    "Soft window",
    "Hard noon sun",
    "Golden hour",
    "Blue hour / twilight",
    "Overcast",
    "Rain / wet overcast",
    "High-key bright",
    "Moody low-key",
    "Fluorescent / office",
    "Practical lamps",
    "Candle / firelight",
    "Rim / silhouette",
    "Neon",
    "Neon noir",
)

CINEMA_TITLES: tuple[str, ...] = (
    "Anamorphic night",
    "Teal & orange",
    "Volumetric god-rays",
    "Fog / haze",
    "Rain on glass",
    "Handheld documentary",
    "Clean studio beauty",
    "Noir venetian",
    "Warm tungsten interior",
    "Cool moonlight exterior",
    "Prestige-TV night",
    "Space-opera rim",
)

DEFAULT_LIGHTING_KEY = "warm_lamp_bedroom"


def is_lighting_skipped(text: str | None) -> bool:
    return (text or "").strip().lower() in SKIP_ALIASES


def preset_titles() -> list[str]:
    return [p.title for p in LIGHTING_PRESETS]


def preset_choices() -> list[str]:
    """Radio / dropdown choices. Skip is first — never required."""
    return [SKIP_LABEL, *preset_titles()]


def find_preset(text: str | None) -> LightingPreset | None:
    if is_lighting_skipped(text):
        return None
    raw = (text or "").strip().lower()
    aliases = {
        "neon night": "neon",
        "rim": "rim",
        "rim / backlight": "rim",
        "rim light": "rim",
        "silhouette": "rim",
        "practical lamp": "practical_lamps",
        "bedside lamp": "bedside_lamp",
        "daylight": "day",
        "night interior": "night",
        "candle": "candle",
        "firelight": "candle",
        "high-key": "high_key",
        "high key": "high_key",
        "low-key": "low_key",
        "low key": "low_key",
        "blue hour": "blue_hour",
        "twilight": "blue_hour",
        "hard noon": "hard_noon",
        "noon sun": "hard_noon",
        "fluorescent": "fluorescent",
        "office": "fluorescent",
        "wet overcast": "rain_overcast",
        "rain": "rain_overcast",
        "rain/wet": "rain_overcast",
        "candle/fire": "candle",
        "moonlight": "moonlight",
        "cool moonlight": "moonlight",
        "teal and orange": "teal_orange",
        "teal orange": "teal_orange",
        "god-rays": "god_rays",
        "god rays": "god_rays",
        "volumetric": "god_rays",
        "fog": "fog_haze",
        "haze": "fog_haze",
        "venetian": "noir_venetian",
        "venetian blinds": "noir_venetian",
        "prestige night": "prestige_night",
        "prestige tv": "prestige_night",
        "space opera": "space_opera_rim",
        "space-opera": "space_opera_rim",
        "anamorphic": "anamorphic_night",
        "documentary": "handheld_doc",
        "studio beauty": "studio_beauty",
        "tungsten": "warm_tungsten",
        "warm tungsten": "warm_tungsten",
    }
    raw = aliases.get(raw, raw)
    for preset in LIGHTING_PRESETS:
        if raw in {preset.key, preset.title.lower(), preset.chip.lower()}:
            return preset
    for preset in sorted(LIGHTING_PRESETS, key=lambda p: -len(p.title)):
        title = preset.title.lower()
        key_sp = preset.key.replace("_", " ")
        if raw == title or raw == key_sp:
            return preset
        if len(title) >= 4 and title in raw:
            return preset
        if len(key_sp) >= 4 and key_sp in raw:
            return preset
    return None


def expand_lighting(text: str | None) -> str:
    """Chip text, or empty when skipped. Empty is valid — optional."""
    if is_lighting_skipped(text):
        return ""
    preset = find_preset(text)
    if preset:
        return preset.chip
    return (text or "").strip()


def mentor_markdown(text: str | None = None) -> str:
    if is_lighting_skipped(text):
        return (
            "### Optional lighting\n"
            "Skip to leave the still's light alone. "
            "Studio / natural: Rembrandt, soft window, hard noon, golden hour, blue hour, "
            "overcast, rain / wet, high-key, low-key, fluorescent, practical lamp, "
            "candle / fire, rim / silhouette, neon, neon noir. "
            "Cinematic pack: anamorphic night, teal & orange, volumetric god-rays, "
            "fog / haze, rain on glass, handheld documentary, clean studio beauty, "
            "noir venetian, warm tungsten interior, cool moonlight exterior, "
            "prestige-TV night, space-opera rim. "
            "Pick one or skip. Never forced.\n\n"
            "Chip: *(none)*"
        )
    preset = find_preset(text)
    if not preset:
        return mentor_markdown(SKIP_LABEL)
    return (
        f"### {preset.title}\n"
        f"{preset.mentor}\n\n"
        f"**Intimacy / sex (adults 18+):** {preset.intimacy}\n\n"
        f"Chip: `{preset.chip}`"
    )


def catalog_markdown() -> str:
    lines = [
        "### Lighting Desk — optional",
        "Choose a preset or **None — skip**. Never required. "
        "Same list on Pipeline Enhance, Still / Motion Enhance, Effects, and Cinema. "
        "Zero credits. Local tags only. Original looks — no show or franchise clones.",
        "",
        "**Studio / natural:** Rembrandt · Soft window · Hard noon sun · Golden hour · "
        "Blue hour / twilight · Overcast · Rain / wet overcast · High-key bright · "
        "Moody low-key · Fluorescent / office · Practical lamps · Candle / firelight · "
        "Rim / silhouette · Neon · Neon noir",
        "**Cinematic pack:** Anamorphic night · Teal & orange · Volumetric god-rays · "
        "Fog / haze · Rain on glass · Handheld documentary · Clean studio beauty · "
        "Noir venetian · Warm tungsten interior · Cool moonlight exterior · "
        "Prestige-TV night · Space-opera rim",
        "**Also:** Key · Fill · Three-point · Day · Night · Practical bedside lamp · "
        "Motivated practicals · Warm lamp bedroom",
        "",
    ]
    for preset in LIGHTING_PRESETS:
        lines.append(f"- **{preset.title}** — {preset.mentor}")
    return "\n".join(lines)


def lighting_bible_line(text: str | None) -> str:
    chip = expand_lighting(text)
    if not chip:
        return ""
    return f"Lighting lock: {chip}."


def lighting_prompt_bit(text: str | None) -> str:
    chip = expand_lighting(text)
    return f"lighting: {chip}" if chip else ""


def lighting_chips_html() -> str:
    chips = "".join(
        f"<span class='look-chip'><b>{_esc(p.title)}</b>{_esc(p.mentor)}</span>"
        for p in LIGHTING_PRESETS
    )
    return (
        "<div class='looks-head'>"
        "<p class='section-kicker'>Lighting shelf — optional</p>"
        "<h2>CHOOSE OR SKIP</h2>"
        "<p class='section-lede'>Studio / natural plus a cinematic pack. "
        "Pick one or skip. Original looks only.</p>"
        f"<div class='look-chips'>{chips}</div>"
        "</div>"
    )


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
