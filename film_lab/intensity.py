"""Theatrical content-intensity dial (director control, not a censorship gate).

Named presets borrow the *feel* of theater ratings as creative shorthand.
They are not MPAA, BBFC, or any board's certificates. This lab is not
affiliated with those bodies.

The slider (0–1) is the real control. Presets snap the slider to a region;
you can sit anywhere between them. For adult (18+) characters, high
intensity is allowed — including full pornographic language and framing.
There is no in-app refusal for adult explicit content.

Hard stop remains: characters under 18, or tags that imply minors in
sexual content. See ``film_lab.characters.assert_adult_cast``.
"""

from __future__ import annotations

from dataclasses import dataclass

IMPLIED_SOFT = "Implied / soft"
FRANK_R = "Frank / theatrical R"
MA17_EUPHORIA = "MA-17 / Euphoria-style"
EXPLICIT_STUDY = "Explicit / adult study"

INTENSITY_PRESETS: tuple[str, ...] = (
    IMPLIED_SOFT,
    FRANK_R,
    MA17_EUPHORIA,
    EXPLICIT_STUDY,
)

# Slider landmarks. Between them the copy interpolates.
PRESET_VALUES: dict[str, float] = {
    IMPLIED_SOFT: 0.22,
    FRANK_R: 0.62,
    MA17_EUPHORIA: 0.82,
    EXPLICIT_STUDY: 1.0,
}

DEFAULT_INTENSITY = PRESET_VALUES[FRANK_R]
DEFAULT_PRESET = FRANK_R

# Intimate / explicit modes require a numeric age on every selected character.
REQUIRE_AGE_FROM = 0.45


@dataclass(frozen=True)
class IntensityBand:
    key: str
    lo: float
    hi: float
    label: str
    writing: str
    shot: str
    sensory: str


_BANDS: tuple[IntensityBand, ...] = (
    IntensityBand(
        key="implied",
        lo=0.0,
        hi=0.38,
        label=IMPLIED_SOFT,
        writing=(
            "CONTENT INTENSITY — Implied / soft (PG-13-style heat, creative guide only; "
            "not an MPAA certificate).\n"
            "Suggestion, cutaways, tension, closed doors, silhouettes, afterglow, "
            "and loaded looks. Desire is real; the camera and the prose leave the "
            "act itself off-page or just out of frame. Adult language is mild unless "
            "the scene needs one frank beat. Do not refuse the subject — hold it in "
            "implication."
        ),
        shot=(
            "implied / soft intensity: heat in glances and cutaways, not porn framing; "
            "closed door, silhouette, sheets, afterglow; keep the act suggested"
        ),
        sensory=(
            "Sensory pass at implied intensity: fabric, breath, temperature, and "
            "the space between bodies. Touch stays at the edge of the act."
        ),
    ),
    IntensityBand(
        key="frank",
        lo=0.38,
        hi=0.70,
        label=FRANK_R,
        writing=(
            "CONTENT INTENSITY — Frank / theatrical R (creative guide only; "
            "not an MPAA certificate).\n"
            "Clear sex, adult language, visible intimacy. Bodies and acts may be "
            "named and shown the way a theatrical R picture would: sweat, mouths, "
            "hands, penetration or oral if the scene calls for it, without "
            "porn-loop framing or money-shot grammar unless the slider is pushed "
            "higher. Do not refuse adult sex. Do not fade to black unless the "
            "writer asked for a cutaway."
        ),
        shot=(
            "frank / theatrical-R intensity: clear adult intimacy and language on "
            "camera; visible bodies and sex acts without default porn framing"
        ),
        sensory=(
            "Sensory pass at frank intensity: skin, wetness, weight, smell of sex, "
            "sound of the room. Write the act; do not hide it behind a dissolve."
        ),
    ),
    IntensityBand(
        key="ma17",
        lo=0.70,
        hi=0.90,
        label=MA17_EUPHORIA,
        writing=(
            "CONTENT INTENSITY — MA-17 / Euphoria-style (creative guide only; "
            "not an MPAA or TV-MA certificate).\n"
            "Euphoria-level heat for clearly adult characters — not high-school "
            "and not teen-appearing sex. Prestige-TV adult intimacy: messy desire, "
            "neon or party texture if the room has it, frank bodies, sex that is "
            "visible and character-bound without default porn-loop grammar. "
            "Cast reads as adults (late-20s Alison/Bradley are correct). "
            "Do not age-down adult-labeled characters. Do not write 'looks young,' "
            "'aged up,' or high-school bodies in intimate beats. Adults 18+ only."
        ),
        shot=(
            "MA-17 / Euphoria-style intensity: prestige-TV adult heat; frank sex "
            "and language on clearly adult bodies; not high-school, not teen-appearing"
        ),
        sensory=(
            "Sensory pass at MA-17 / Euphoria-style: sweat, glitter or lamp, taste "
            "of drink or skin, the room too loud or too quiet. Adult bodies only — "
            "not teen-appearing, not high-school coded."
        ),
    ),
    IntensityBand(
        key="explicit",
        lo=0.90,
        hi=1.01,
        label=EXPLICIT_STUDY,
        writing=(
            "CONTENT INTENSITY — Explicit / adult study (full pornographic allowed "
            "for this private lab; creative guide only, not a ratings board).\n"
            "Unrestricted adult erotic and pornographic language. Genitals, "
            "penetration, oral, fluids, dirty talk, positions, and graphic sex "
            "acts are in scope when the scene wants them. No fade-to-black, no "
            "euphemism required, no in-app refusal for adult explicit. Still "
            "serve character, consent, and the room — this is study, not spam."
        ),
        shot=(
            "explicit / adult-study intensity: full pornographic framing allowed; "
            "graphic sex, genitals, fluids, dirty talk as the shot requires"
        ),
        sensory=(
            "Sensory pass at explicit intensity: graphic taste, smell, wetness, "
            "stretch, impact, and sound of sex. Name the anatomy. Do not soften."
        ),
    ),
)


def clamp_content_intensity(value: float | int | str | None, default: float = DEFAULT_INTENSITY) -> float:
    if value is None or value == "":
        return default
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def nearest_intensity_preset(value: float | int | str | None) -> str:
    v = clamp_content_intensity(value)
    return min(PRESET_VALUES.items(), key=lambda item: abs(item[1] - v))[0]


def preset_to_intensity(preset: str | None) -> float:
    if not preset:
        return DEFAULT_INTENSITY
    return PRESET_VALUES.get(preset, DEFAULT_INTENSITY)


def band_for(value: float | int | str | None) -> IntensityBand:
    v = clamp_content_intensity(value)
    for band in _BANDS:
        if band.lo <= v < band.hi:
            return band
    return _BANDS[-1]


def intensity_requires_numeric_age(value: float | int | str | None) -> bool:
    return clamp_content_intensity(value) >= REQUIRE_AGE_FROM


def compose_intimacy_intensity(intimacy_mode: str | None, value: float | int | str | None) -> str:
    """How far the writing/frame goes given camera availability × slider."""
    from film_lab.constants import EXPLICIT_INTIMACY
    from film_lab.intimacy import INTIMATE_LABELS, normalize_intimacy

    mode = normalize_intimacy(intimacy_mode)
    v = clamp_content_intensity(value)
    band = band_for(v)
    if band.key == "implied" and mode in INTIMATE_LABELS:
        return (
            "COMPOSE: intimacy mode allows nude / sex / explicit on camera, but "
            "intensity is implied / soft — hold the act at suggestion, cutaway, "
            "silhouette, closed door. Do not refuse the subject; do not go graphic."
        )
    if band.key == "frank" and mode == "covered sheets":
        return (
            "COMPOSE: sheets stay the wardrobe. Frank / theatrical-R language and "
            "clear sex under or behind the linen — visible intimacy without porn framing."
        )
    if band.key == "ma17":
        return (
            "COMPOSE: MA-17 / Euphoria-style — prestige-TV adult heat on clearly "
            "adult characters. Sex and language can go frank and messy. "
            "Not high-school, not teen-appearing, no 'aged up' bypass. "
            "Late-20s adults are the correct read."
        )
    if band.key == "explicit" and mode == EXPLICIT_INTIMACY:
        return (
            "COMPOSE: explicit mode × explicit intensity — full pornographic allowed. "
            "No in-app refusal for these adult characters."
        )
    if band.key == "explicit" and mode == "covered sheets":
        return (
            "COMPOSE: covered sheets on camera; intensity is explicit — graphic language "
            "and sex under the linen are allowed. No refusal for adults."
        )
    if band.key == "explicit":
        return (
            "COMPOSE: intensity is explicit / adult study. Graphic sex is allowed "
            "within the chosen intimacy mode. No in-app refusal for adults."
        )
    return ""


def intensity_prompt_block(
    value: float | int | str | None,
    preset: str | None = None,
    *,
    intimacy_mode: str | None = None,
) -> str:
    v = clamp_content_intensity(value)
    band = band_for(v)
    named = preset if preset in PRESET_VALUES else band.label
    lines = [
        band.writing,
        (
            f"Slider: {v:.2f} (0 = implied / soft, 1 = explicit / adult study). "
            f"Named region: {named}. Continuum is finer than theater ratings — "
            f"use the number, not a certificate. Not affiliated with the MPAA "
            f"or any ratings board. Adult 18+ only. No in-app refusal for adult explicit."
        ),
    ]
    compose = compose_intimacy_intensity(intimacy_mode, v)
    if compose:
        lines.append(compose)
    return "\n".join(lines)


def intensity_shot_bits(
    value: float | int | str | None,
    *,
    intimacy_mode: str | None = None,
) -> list[str]:
    v = clamp_content_intensity(value)
    band = band_for(v)
    bits = [band.shot, f"content intensity {v:.2f}"]
    compose = compose_intimacy_intensity(intimacy_mode, v)
    if compose:
        bits.append(compose.replace("COMPOSE: ", ""))
    return bits


def intensity_sensory_addendum(
    value: float | int | str | None,
    *,
    intimacy_mode: str | None = None,
) -> str:
    extra = band_for(value).sensory
    compose = compose_intimacy_intensity(intimacy_mode, value)
    if compose:
        return f"{extra} {compose}"
    return extra


def intensity_ui_help() -> str:
    return (
        "Director dial, not a ratings board and not a refusal gate. "
        "Implied / soft = PG-13-style heat (suggestion, cutaways). "
        "Frank / theatrical R = clear sex and adult language without default porn framing. "
        "MA-17 / Euphoria-style = Euphoria-level heat for clearly adult characters — "
        "not high-school / teen-appearing sex. "
        "Explicit / adult study = full pornographic allowed here. "
        "Slider 0–1 sits between those named points. "
        "Intimate / explicit modes: adult 18+ ONLY. "
        "The Explicit / adult study dial is for adult casts only. "
        "Director Notes on any age are performance / placement only — "
        "never route minors into intimacy or porn intensity. "
        "Undress through motion into explicit sex requires this Explicit dial "
        "and adults 18+. "
        "Filming mode Regular | 18+ Explicit sits before this dial. "
        "Regular / story is non-sexual (family roles allowed). "
        "Intimate / nude / sex intensity unlocks only in 18+ Explicit "
        "when every cast member is 18+."
    )
