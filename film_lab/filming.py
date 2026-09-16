"""Filming modes: Regular / story vs 18+ Explicit.

Hard split. Intimate / nude / sex intensity is allowed only in
``18+ Explicit`` when every selected cast member is 18+ and not a
Teen / Child / Infant role. Regular mode is everyday story filming
(bus, walk home, aerial outdoors) and is non-sexual — including when
adults are in the frame.

Family roles (Mom, Dad, Teen, Adult, Child, Infant) live on the
Character Bible for Regular + 3D Set. Under-18 roles never unlock
explicit tools. Zero credits.
"""

from __future__ import annotations

from typing import Any

MODE_REGULAR = "Regular"
MODE_EXPLICIT = "18+ Explicit"
FILMING_MODES: tuple[str, ...] = (MODE_REGULAR, MODE_EXPLICIT)
DEFAULT_MODE = MODE_EXPLICIT

ROLE_ADULT = "Adult"
ROLE_MOM = "Mom"
ROLE_DAD = "Dad"
ROLE_TEEN = "Teen"
ROLE_CHILD = "Child"
ROLE_INFANT = "Infant"

CAST_ROLES: tuple[str, ...] = (
    ROLE_ADULT,
    ROLE_MOM,
    ROLE_DAD,
    ROLE_TEEN,
    ROLE_CHILD,
    ROLE_INFANT,
)
MINOR_ROLES: frozenset[str] = frozenset({ROLE_TEEN, ROLE_CHILD, ROLE_INFANT})
ADULT_ROLES: frozenset[str] = frozenset({ROLE_ADULT, ROLE_MOM, ROLE_DAD})

ROLE_AGE_DEFAULTS: dict[str, int] = {
    ROLE_ADULT: 28,
    ROLE_MOM: 42,
    ROLE_DAD: 44,
    ROLE_TEEN: 16,
    ROLE_CHILD: 8,
    ROLE_INFANT: 1,
}

ROLE_AGE_BANDS: dict[str, str] = {
    ROLE_ADULT: "late 20s (adult)",
    ROLE_MOM: "early 40s (adult)",
    ROLE_DAD: "mid 40s (adult)",
    ROLE_TEEN: "teen (story role, non-sexual)",
    ROLE_CHILD: "child (story role, non-sexual)",
    ROLE_INFANT: "infant (story role, non-sexual)",
}

ROLE_AGE_BOUNDS: dict[str, tuple[int, int]] = {
    ROLE_INFANT: (0, 2),
    ROLE_CHILD: (3, 12),
    ROLE_TEEN: (13, 17),
    ROLE_ADULT: (18, 120),
    ROLE_MOM: (18, 120),
    ROLE_DAD: (18, 120),
}

SAFETY_COPY = (
    "Filming mode is a hard split. Regular / story is non-sexual "
    "(bus, walk home, aerial outdoors) and may include Teen / Child / Infant. "
    "Intimate / nude / sex intensity unlocks only in 18+ Explicit when every "
    "cast member is 18+ with an adult role. Under-18 roles never unlock "
    "explicit tools. Regular vs 18+ is a filming-mode toggle — "
    "one purple + soft cyan studio, not two apps."
)


class FilmingError(ValueError):
    """Regular/explicit split or family-role age gate failed."""


def normalize_mode(mode: str | None) -> str:
    text = (mode or "").strip()
    if text in FILMING_MODES:
        return text
    low = text.lower()
    if low in {"regular", "story", "everyday", "none"}:
        return MODE_REGULAR
    if "explicit" in low or low in {"18+", "adult", "intimate"}:
        return MODE_EXPLICIT
    return DEFAULT_MODE


def is_explicit_mode(mode: str | None) -> bool:
    return normalize_mode(mode) == MODE_EXPLICIT


def is_regular_mode(mode: str | None) -> bool:
    return normalize_mode(mode) == MODE_REGULAR


def normalize_role(role: str | None) -> str:
    text = (role or "").strip()
    if text in CAST_ROLES:
        return text
    low = text.lower()
    aliases = {
        "mom": ROLE_MOM,
        "mother": ROLE_MOM,
        "mum": ROLE_MOM,
        "dad": ROLE_DAD,
        "father": ROLE_DAD,
        "teen": ROLE_TEEN,
        "teenager": ROLE_TEEN,
        "child": ROLE_CHILD,
        "kid": ROLE_CHILD,
        "infant": ROLE_INFANT,
        "baby": ROLE_INFANT,
        "adult": ROLE_ADULT,
    }
    return aliases.get(low, ROLE_ADULT)


def role_is_minor(role: str | None) -> bool:
    return normalize_role(role) in MINOR_ROLES


def role_is_adult(role: str | None) -> bool:
    return normalize_role(role) in ADULT_ROLES


def _years(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def default_years_for_role(role: str | None) -> int:
    return ROLE_AGE_DEFAULTS[normalize_role(role)]


def default_band_for_role(role: str | None) -> str:
    return ROLE_AGE_BANDS[normalize_role(role)]


def validate_role_age(role: str | None, years: int | None, *, name: str = "Character") -> None:
    role_n = normalize_role(role)
    lo, hi = ROLE_AGE_BOUNDS[role_n]
    if years is None:
        return
    if years < lo or years > hi:
        if role_is_minor(role_n):
            raise FilmingError(
                f"{name}: {role_n} is a Regular-story role for ages {lo}–{hi}. "
                f"Age {years} does not fit. Use Adult for anyone 18+."
            )
        raise FilmingError(
            f"{name}: {role_n} requires Age (years) {lo}+. "
            f"Under-18 story parts use Teen / Child / Infant in Regular mode only."
        )


def profile_is_adult(profile: Any) -> bool:
    """Adult for explicit tools: adult role AND numeric age 18+ when set."""
    if role_is_minor(getattr(profile, "role", ROLE_ADULT)):
        return False
    years = _years(getattr(profile, "age_years", None))
    if years is not None:
        return years >= 18
    return True


_UNDRESS = frozenset({"undress through motion", "into explicit sex"})


def asks_sex_tools(
    intimacy: str | None = "",
    intensity: float | int | str | None = 0,
    wardrobe: str | None = "",
) -> bool:
    from film_lab.intensity import intensity_requires_numeric_age
    from film_lab.intimacy import is_intimate

    motion = (wardrobe or "").strip().lower()
    return (
        is_intimate(intimacy)
        or intensity_requires_numeric_age(intensity)
        or motion in _UNDRESS
    )


def filming_help() -> str:
    return (
        "Pick Regular or 18+ Explicit before the intensity dial. "
        f"{SAFETY_COPY} Director Notes on any age are performance / placement. "
        "Never route minors into intimacy or porn intensity."
    )


def filming_ui_help() -> str:
    return filming_help()


def assert_explicit_cast(profiles: list[Any], *, context: str = "18+ Explicit") -> None:
    """Under-18 roles and under-18 ages never unlock explicit tools."""
    if not profiles:
        raise FilmingError(
            f"Select adult characters (Adult / Mom / Dad, Age 18+) before {context}."
        )
    for profile in profiles:
        name = getattr(profile, "name", None) or getattr(profile, "id", "cast")
        role = normalize_role(getattr(profile, "role", ROLE_ADULT))
        if role_is_minor(role):
            raise FilmingError(
                f"{name} is a {role} story role. Under-18 roles never unlock "
                f"intimate / nude / sex tools. Switch filming mode to Regular "
                f"for non-sexual story, or recast as Adult 18+."
            )
        years = _years(getattr(profile, "age_years", None))
        if years is not None and years < 18:
            raise FilmingError(
                f"{name} is {years} (under 18). {context} is adult 18+ ONLY."
            )
        if not profile_is_adult(profile):
            raise FilmingError(
                f"{name} is not a confirmed adult. {context} is adult 18+ ONLY."
            )


def assert_filming_safe(
    mode: str | None,
    profiles: list[Any] | None = None,
    *,
    intimacy: str = "",
    intensity: float | int | str | None = 0,
    wardrobe: str = "",
    context: str = "this beat",
) -> None:
    """Hard gate used by Enhance, Animate, notes, and the intensity dial."""
    from film_lab.characters import CharacterError, assert_adult_cast

    resolved = normalize_mode(mode)
    cast = list(profiles or [])
    sex = asks_sex_tools(intimacy, intensity, wardrobe)
    if is_regular_mode(resolved):
        if sex:
            raise FilmingError(
                "Regular / story filming is non-sexual. "
                "Intimate / nude / sex intensity unlocks only in 18+ Explicit "
                "with an adult 18+ cast. Under-18 roles stay in Regular."
            )
        return
    if not sex:
        if any(not profile_is_adult(p) for p in cast):
            return
        return
    try:
        assert_explicit_cast(cast, context=context)
        assert_adult_cast(
            cast,
            intimacy_mode=intimacy,
            content_intensity=intensity or 0,
            context=context,
        )
    except CharacterError as exc:
        raise FilmingError(str(exc)) from exc
