# Family Genetics (Character Bible)

Regular / story only. Two adult bible faces → blended child stills → a new Character Bible card that **belongs to both parents**.

Not InstantID. Not a hosted face model. Zero credits. Teen / Child / Infant **never** unlock 18+ intimacy.

## Flow

1. Pin **face-locked refs** on Actor A and Actress B (Adult / Mom / Dad, Age 18+).
2. Character Consistency → **Family Genetics**.
3. Pick **Actor A** + **Actress B**.
4. Age picker: **infant / child / teen**.
5. **What would their kids look like?**
6. Film Lab writes two local blended PNGs into `stills/` (Still Desk) and pins them on a new bible card.
7. The card stores `parent_ids` — belongs to both parents. Role is Infant / Child / Teen with the Regular-story age band.

## What the blend is

An honest Pillow composite of the two parent refs (face crop, 50/50-ish bias, a light age wash). It is **not** a live InstantID / FaceID rewrite. Caption on the still: `Family Genetics · Regular / story · non-sexual`.

## Safety

| Rule | Why |
| --- | --- |
| Parents must be adult 18+ | Kids are not generated from Teen / Child / Infant cards |
| Child role is Infant / Child / Teen | Age bounds stay Regular-story |
| Wardrobe is everyday clothes | Adult bedroom / nude copy is stripped |
| No intimacy fields | Never routed through 18+ Explicit tools |
| `assert_adult_cast` still blocks | Under-18 roles cannot enter sex / nude intensity |

Switching the lot to 18+ Explicit does **not** unlock these cards for intimate generation.

See [FILMING.md](FILMING.md) and [CHARACTER_CONSISTENCY.md](CHARACTER_CONSISTENCY.md).
