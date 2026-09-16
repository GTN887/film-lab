"""Living style and living conditions — lifestyle plus material reality.

Story labels only. Not real household PII.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

LIVING_STYLES: tuple[str, ...] = (
    "Minimalist",
    "Maximalist",
    "Bohemian",
    "Traditional",
    "Modern / contemporary",
    "Urban apartment",
    "Suburban house",
    "Rural / farm",
    "Small-town",
    "Nomadic / travel-heavy",
    "Campus / dorm (adult students only)",
    "Military housing",
    "Luxury / high-rise",
    "Middle-class comfort",
    "Working-class practical",
    "Creative studio loft",
    "Shared flatmates",
    "Multi-generational home",
    "Newlywed nest",
)

INCOME_BANDS: tuple[str, ...] = ("comfortable", "tight", "unstable", "unspecified")
HOUSING_QUALITY: tuple[str, ...] = ("spacious", "cramped", "temporary", "under renovation", "unspecified")
PRIVACY_LEVELS: tuple[str, ...] = ("private bedroom", "thin walls", "shared bath", "no privacy", "unspecified")
CLEANLINESS: tuple[str, ...] = ("tidy", "lived-in", "cluttered", "unspecified")
NEIGHBORHOODS: tuple[str, ...] = ("quiet / safe", "mixed", "tense / watched", "unspecified")
UTILITIES: tuple[str, ...] = (
    "heat/AC working",
    "unreliable power",
    "noisy street",
    "unreliable heat",
    "unspecified",
)
DEPENDENTS: tuple[str, ...] = ("none on page", "occasional care", "heavy caregiving load", "unspecified")
WORK_PATTERNS: tuple[str, ...] = ("work from home", "long commute", "mixed / shifts", "unspecified")

CAMPUS_STYLE = "Campus / dorm (adult students only)"


def _clean_list(raw: list[str] | None) -> list[str]:
    found: list[str] = []
    for item in raw or []:
        text = str(item).strip()
        if text and text not in found:
            found.append(text)
    return found


@dataclass
class LivingBrief:
    styles: list[str] = field(default_factory=list)
    custom_style: str = ""
    household_norms: str = ""
    income_band: str = "unspecified"
    housing_quality: str = "unspecified"
    privacy: str = "unspecified"
    cleanliness: str = "unspecified"
    neighborhood: str = "unspecified"
    utilities: str = "unspecified"
    dependents: str = "unspecified"
    work_pattern: str = "unspecified"
    health_notes: str = ""
    override: bool = False

    def __post_init__(self) -> None:
        self.styles = [s for s in _clean_list(self.styles) if s in LIVING_STYLES or s]
        self.styles = [s for s in self.styles if s in LIVING_STYLES]
        if self.income_band not in INCOME_BANDS:
            self.income_band = "unspecified"
        if self.housing_quality not in HOUSING_QUALITY:
            self.housing_quality = "unspecified"
        if self.privacy not in PRIVACY_LEVELS:
            self.privacy = "unspecified"
        if self.cleanliness not in CLEANLINESS:
            self.cleanliness = "unspecified"
        if self.neighborhood not in NEIGHBORHOODS:
            self.neighborhood = "unspecified"
        if self.utilities not in UTILITIES:
            self.utilities = "unspecified"
        if self.dependents not in DEPENDENTS:
            self.dependents = "unspecified"
        if self.work_pattern not in WORK_PATTERNS:
            self.work_pattern = "unspecified"
        self.override = bool(self.override)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> LivingBrief:
        if not isinstance(data, dict):
            return cls()
        known = {k: data[k] for k in cls.__dataclass_fields__ if k in data}
        return cls(**known)

    def has_content(self) -> bool:
        if self.styles or (self.custom_style or "").strip() or (self.household_norms or "").strip():
            return True
        if (self.health_notes or "").strip():
            return True
        specified = (
            self.income_band,
            self.housing_quality,
            self.privacy,
            self.cleanliness,
            self.neighborhood,
            self.utilities,
            self.dependents,
            self.work_pattern,
        )
        return any(v != "unspecified" for v in specified)

    def style_line(self) -> str:
        bits = list(self.styles)
        extra = (self.custom_style or "").strip()
        if extra:
            bits.append(extra)
        return ", ".join(bits) or "unspecified"


def merge_living(briefs: list[LivingBrief]) -> LivingBrief:
    """Union styles; take the first specified condition from each field."""
    out = LivingBrief()
    styles: list[str] = []
    customs: list[str] = []
    norms: list[str] = []
    health: list[str] = []
    for brief in briefs:
        if not brief or not brief.has_content():
            continue
        for style in brief.styles:
            if style not in styles:
                styles.append(style)
        if brief.custom_style.strip() and brief.custom_style.strip() not in customs:
            customs.append(brief.custom_style.strip())
        if brief.household_norms.strip() and brief.household_norms.strip() not in norms:
            norms.append(brief.household_norms.strip())
        if brief.health_notes.strip() and brief.health_notes.strip() not in health:
            health.append(brief.health_notes.strip())
        for field_name in (
            "income_band",
            "housing_quality",
            "privacy",
            "cleanliness",
            "neighborhood",
            "utilities",
            "dependents",
            "work_pattern",
        ):
            value = getattr(brief, field_name)
            if value != "unspecified" and getattr(out, field_name) == "unspecified":
                setattr(out, field_name, value)
    out.styles = styles
    out.custom_style = "; ".join(customs)
    out.household_norms = " ".join(norms)
    out.health_notes = " ".join(health)
    return out


@dataclass(frozen=True)
class LivingPreset:
    id: str
    label: str
    brief: LivingBrief
    env_location: str = ""
    env_light: str = ""
    env_ambient: str = ""
    env_blocking: str = ""
    env_props: str = ""


def _p(gid: str, label: str, brief: LivingBrief, **env: str) -> LivingPreset:
    return LivingPreset(gid, label, brief, **env)


LIVING_PRESETS: tuple[LivingPreset, ...] = (
    _p(
        "newlywed_warm_apartment",
        "Newlywed warm apartment",
        LivingBrief(
            styles=["Newlywed nest", "Urban apartment", "Middle-class comfort", "Modern / contemporary"],
            household_norms="Two adults. Wedding bands are a story prop, not a lecture.",
            income_band="comfortable",
            housing_quality="cramped",
            privacy="private bedroom",
            cleanliness="lived-in",
            neighborhood="quiet / safe",
            utilities="heat/AC working",
            dependents="none on page",
            work_pattern="mixed / shifts",
        ),
        env_location="INT. APARTMENT BEDROOM - NIGHT",
        env_light="warm lamp",
        env_ambient="building hush, one neighbor TV far away",
        env_blocking="The bed takes most of the room. They share it.",
        env_props="sheets, lamp, wedding bands, a moving box not yet unpacked",
    ),
    _p(
        "tight_budget_thin_walls",
        "Tight budget thin walls",
        LivingBrief(
            styles=["Working-class practical", "Urban apartment", "Shared flatmates"],
            household_norms="Money is a third character. Do not invent real bank details.",
            income_band="tight",
            housing_quality="cramped",
            privacy="thin walls",
            cleanliness="lived-in",
            neighborhood="mixed",
            utilities="noisy street",
            dependents="none on page",
            work_pattern="long commute",
        ),
        env_location="INT. SMALL BEDROOM - NIGHT",
        env_light="warm lamp",
        env_ambient="neighbors through plaster, street, a pipe",
        env_blocking="They keep voices down. The wall is close to the bed.",
        env_props="thin sheet, phone charger, a bill on the dresser",
    ),
    _p(
        "quiet_suburban_house",
        "Quiet suburban house",
        LivingBrief(
            styles=["Suburban house", "Traditional", "Middle-class comfort", "Newlywed nest"],
            income_band="comfortable",
            housing_quality="spacious",
            privacy="private bedroom",
            cleanliness="tidy",
            neighborhood="quiet / safe",
            utilities="heat/AC working",
            dependents="none on page",
            work_pattern="long commute",
        ),
        env_location="INT. MASTER BEDROOM - NIGHT",
        env_light="warm lamp",
        env_ambient="HVAC, distant lawn, almost nothing",
        env_blocking="They can leave space and choose not to.",
        env_props="good sheets, two nightstands, wedding bands",
    ),
    _p(
        "noisy_city_loft",
        "Noisy city loft",
        LivingBrief(
            styles=["Creative studio loft", "Urban apartment", "Bohemian"],
            income_band="tight",
            housing_quality="spacious",
            privacy="no privacy",
            cleanliness="cluttered",
            neighborhood="mixed",
            utilities="noisy street",
            dependents="none on page",
            work_pattern="work from home",
        ),
        env_location="INT. LOFT - NIGHT",
        env_light="neon",
        env_ambient="street, bass from below, a truck",
        env_blocking="Open plan. The bed is in the room that is also the kitchen.",
        env_props="canvas, cheap wine, a mattress on a platform, wet street in the window",
    ),
)

PRESET_BY_LABEL: dict[str, LivingPreset] = {p.label: p for p in LIVING_PRESETS}
LIVING_PRESET_LABELS: tuple[str, ...] = tuple(p.label for p in LIVING_PRESETS)
DEFAULT_LIVING_PRESET = "Newlywed warm apartment"


def living_preset(label: str | None) -> LivingPreset:
    return PRESET_BY_LABEL.get((label or "").strip()) or PRESET_BY_LABEL[DEFAULT_LIVING_PRESET]


def living_preset_brief(label: str | None) -> LivingBrief:
    src = living_preset(label).brief
    return LivingBrief.from_dict(src.to_dict())


def living_sense_couplings(brief: LivingBrief) -> list[str]:
    """How material conditions land on the body / the mix."""
    lines: list[str] = []
    if brief.privacy in {"thin walls", "shared bath", "no privacy"}:
        lines.append(
            "Hearing ↔ privacy: thin walls / shared plumbing — neighbors, pipes, a cough next door. "
            "Voices drop if they care who hears."
        )
    if brief.housing_quality == "cramped":
        lines.append(
            "Touch ↔ housing: the room is small. Proximity is architecture, not only desire."
        )
    if brief.housing_quality == "under renovation":
        lines.append("Smell / touch ↔ reno: dust, primer, a drop cloth where a rug should be.")
    if brief.utilities == "noisy street":
        lines.append("Hearing ↔ street: traffic is the score under the scene. Do not write silence unless they close a window.")
    if brief.utilities in {"unreliable power", "unreliable heat"}:
        lines.append("Touch / sight ↔ utilities: the lamp or the heat may fail. Cold and dark are blocking.")
    if brief.income_band in {"tight", "unstable"}:
        lines.append(
            "Props ↔ money: cheap sheets, a bill, a phone on 12%. Story pressure, not real PII."
        )
    if brief.cleanliness == "cluttered":
        lines.append("Sight / touch ↔ clutter: laundry, dishes, a chair that is a closet.")
    if CAMPUS_STYLE in brief.styles:
        lines.append("AGE RULE: campus / dorm here means adult students 18+ only. No minors.")
    return lines


def living_prompt_block(
    brief: LivingBrief,
    *,
    mode: str,
    source: str = "resolved",
    sensory_pass: bool = False,
) -> str:
    if not brief.has_content():
        return ""
    lines = [
        f"Living style & conditions ({source} — story labels, not real PII)",
        f"- Style: {brief.style_line()}",
        f"- Income / pressure: {brief.income_band}",
        f"- Housing: {brief.housing_quality}",
        f"- Privacy: {brief.privacy}",
        f"- Cleanliness: {brief.cleanliness}",
        f"- Neighborhood: {brief.neighborhood}",
        f"- Utilities / comfort: {brief.utilities}",
        f"- Dependents / care: {brief.dependents}",
        f"- Work pattern: {brief.work_pattern}",
    ]
    if (brief.household_norms or "").strip():
        lines.append(f"- Household / cultural norms: {brief.household_norms.strip()}")
    if (brief.health_notes or "").strip():
        lines.append(f"- Health / accessibility (story): {brief.health_notes.strip()}")
    couplings = living_sense_couplings(brief)
    if couplings:
        lines.append("Couple living conditions to the sensory pass / environment:")
        lines.extend(f"- {c}" for c in couplings)
    if mode == "screenplay":
        lines.append(
            "SCREENPLAY: let living conditions show in ACTION (thin walls, cramped blocking, a bill on the dresser). "
            "Do not lecture money in dialogue unless a character would."
        )
    elif mode == "novel":
        lines.append(
            "NOVEL: the nest is texture — rent pressure, plaster, the size of the bed — felt through the body."
        )
    elif mode == "roleplay":
        lines.append(
            "ROLEPLAY: react to the nest (keep your voice down, bump the dresser, hear the street) before the line."
        )
    elif mode == "book_to_screenplay":
        lines.append(
            "ADAPTATION: translate living conditions into shootable geography and props, not exposition."
        )
    if sensory_pass:
        lines.append(
            "SENSORY PASS: ground every enabled sense in this nest. Thin walls and a noisy street must be heard; "
            "a cramped room must be felt."
        )
    return "\n".join(lines)


def living_shot_line(brief: LivingBrief) -> str:
    if not brief.has_content():
        return ""
    bits = [brief.style_line()]
    if brief.housing_quality != "unspecified":
        bits.append(f"{brief.housing_quality} room")
    if brief.privacy != "unspecified":
        bits.append(brief.privacy)
    if brief.utilities != "unspecified":
        bits.append(brief.utilities)
    if brief.income_band in {"tight", "unstable"}:
        bits.append(f"{brief.income_band} money pressure (story)")
    if brief.cleanliness != "unspecified":
        bits.append(brief.cleanliness)
    return "living: " + ", ".join(b for b in bits if b and b != "unspecified")


def living_to_ui(brief: LivingBrief) -> tuple:
    return (
        bool(brief.override),
        list(brief.styles),
        brief.custom_style,
        brief.household_norms,
        brief.income_band,
        brief.housing_quality,
        brief.privacy,
        brief.cleanliness,
        brief.neighborhood,
        brief.utilities,
        brief.dependents,
        brief.work_pattern,
        brief.health_notes,
    )


def living_from_form(
    override,
    styles,
    custom_style,
    household_norms,
    income_band,
    housing_quality,
    privacy,
    cleanliness,
    neighborhood,
    utilities,
    dependents,
    work_pattern,
    health_notes,
) -> LivingBrief:
    return LivingBrief(
        styles=list(styles or []),
        custom_style=custom_style or "",
        household_norms=household_norms or "",
        income_band=income_band or "unspecified",
        housing_quality=housing_quality or "unspecified",
        privacy=privacy or "unspecified",
        cleanliness=cleanliness or "unspecified",
        neighborhood=neighborhood or "unspecified",
        utilities=utilities or "unspecified",
        dependents=dependents or "unspecified",
        work_pattern=work_pattern or "unspecified",
        health_notes=health_notes or "",
        override=bool(override),
    )
