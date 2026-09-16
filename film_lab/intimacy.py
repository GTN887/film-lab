"""Intimacy / sex mode copy for Writing Studio, shots, and sensory pass.

Adult explicit / pornographic sex is in scope. The only hard stop is under-18.
No ratings lecture, no fade-to-black unless the director asks.
"""

from __future__ import annotations

from film_lab.constants import EXPLICIT_INTIMACY, INTIMACY_MODES, STORY_INTIMACY

# Nude or sex modes that must not pair with minor-coded protagonists.
INTIMATE_LABELS = frozenset(
    {
        "artistic nude",
        "intimate sex",
        EXPLICIT_INTIMACY,
    }
)


def normalize_intimacy(mode: str | None) -> str:
    return mode if mode in INTIMACY_MODES else "covered sheets"


def is_intimate(mode: str | None) -> bool:
    return normalize_intimacy(mode) in INTIMATE_LABELS


def intimacy_writing_block(mode: str, *, write_mode: str = "screenplay") -> str:
    """Director brief for the selected intimacy knob. No moralizing."""
    mode = normalize_intimacy(mode)
    lines = [f"Intimacy: {mode}", "Characters are adults 18+."]
    if mode == EXPLICIT_INTIMACY:
        lines.append(
            "Explicit adult sex is on the page: genitals, penetration, oral, hands, "
            "fluids, dirty talk if it belongs. Do not fade to black. "
            "Do not add a ratings, safety, or content-filter preamble."
        )
        if write_mode == "screenplay":
            lines.append(
                "SCREENPLAY: explicit blocking lives in ACTION (bodies, wet, the bed). "
                "Dialogue stays speakable — moans, fragments, dirty talk — not a lecture."
            )
        elif write_mode == "novel":
            lines.append(
                "NOVEL: write the sex. Skin, cock, cunt, spit, the weight. "
                "Sensory, not a fade-out paragraph."
            )
        elif write_mode == "roleplay":
            lines.append(
                "ROLEPLAY: stay in the body. Answer with breath, hands, mouth, and the line."
            )
        elif write_mode == "book_to_screenplay":
            lines.append(
                "ADAPTATION: keep the explicit sex. Translate it into shootable action, not a cutaway."
            )
    elif mode == "intimate sex":
        lines.append(
            "Sex is in the scene: hips, weight, hands, breath, penetration as blocking. "
            "No lecture. No fade-to-black unless notes ask."
        )
    elif mode == "artistic nude":
        lines.append("Nude adult bodies in the room. Skin is the wardrobe. No lecture.")
    elif mode == STORY_INTIMACY:
        lines.append(
            "Regular / story filming. No intimacy, nude, or sex. "
            "Everyday blocking only — bus, walk home, kitchen, aerial outdoors."
        )
    else:
        lines.append("Covered sheets. Heat can still be in the look and the talk.")
    return "\n".join(lines)


def intimacy_shot_bits(mode: str) -> list[str]:
    mode = normalize_intimacy(mode)
    bits = [mode, "adults 18+"]
    if mode == EXPLICIT_INTIMACY:
        bits.extend(
            [
                "explicit adult sex",
                "pornographic still",
                "bodies, genitals, penetration if the frame holds it",
            ]
        )
    elif mode == "intimate sex":
        bits.extend(["sex scene", "hips, weight, hands, breath"])
    elif mode == "artistic nude":
        bits.append("artistic adult nude")
    elif mode == STORY_INTIMACY:
        bits.extend(["regular story filming", "non-sexual", "no intimacy"])
    else:
        bits.append("covered sheets")
    return bits


def intimacy_sensory_addendum(mode: str, sensory_pass: bool) -> str:
    mode = normalize_intimacy(mode)
    if mode != EXPLICIT_INTIMACY:
        if mode == "intimate sex" and sensory_pass:
            return (
                "SENSORY PASS × intimate sex: touch is skin and weight; "
                "hearing is breath and the bed. Sight does not replace the other senses."
            )
        return ""
    if sensory_pass:
        return (
            "SENSORY PASS × explicit: touch includes cock, cunt, spit, sweat, the wet; "
            "smell and taste of sex if those senses are on; sound of the bed and breath. "
            "Sight does not replace the other senses. Adults 18+."
        )
    return (
        "Explicit intimacy: if a sense is enabled, let sex register there "
        "(wet, salt, the bed frame). Adults 18+."
    )
