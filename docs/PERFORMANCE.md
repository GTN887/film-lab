# Micro-expressions, behavior, and prop actions

Film Lab directs **the face**, **the whole body**, and **the room**. One catalog is shared by Character Bible, Director Note, Pose Desk, Voice Desk, Writing Studio, Mark & Direct, and World Note.

This is not a hosted face-puppet. Regular / story actions stay everyday (swallow, glance, pick up a book). Intimate / explicit routes stay **adult 18+ ONLY**. Zero credits.

## Catalog

| Control | What it is | Examples |
| --- | --- | --- |
| **Micro-expression** | The face | held look, swallow, brow flick, lip press, tear well |
| **Behavior** | Full human body | still breath, weight shift, reach then hold, listen with the body |
| **Prop action** | Environment / object | pick up book, set glass down, open door, switch lamp |

`none` is the default. Empty / none never injects.

## Where it lives

| Desk | Control | What Apply does |
| --- | --- | --- |
| **Character Bible** | Micro-expression + behavior | Saved on the profile. `injection_line()` and the studio library JSON carry them. Director Note inherits these when you click a new face. |
| **Director Note** | Same two pickers + emotion / beats / wardrobe | Folds `micro-expression swallow; behavior weight shift` into Enhance → Pose → Animate. |
| **Pose Desk** | Same two pickers next to body / hands / face | Writes into `.pose.json` and the posed-still status. Face pixels stay locked. |
| **Voice Desk** | Micro-expression next to Breath | Folds into Breath (`close-mic, audible inhale; micro-expression swallow`). |
| **Writing Studio** | Accordion (not a sixth mode) | **Inject into notes** prepends a performance + prop line. |
| **World Note** | Prop action | `WORLD NOTE … prop pick up book` on the mise-en-scène line. |
| **Mark & Direct** | Prop action + region note | Empty note fills with `pick up book`. Clothing / prop target becomes **prop action**. Works on a still or a frozen take frame. |

Hub stays **15 cards**. Shot form stays **25 fields**. Writing stays **5 modes**.

## Pick up a book

1. Drop the still (or pause a take and enter **Mark & Direct**).
2. Circle the book. Pick **pick up book**. Apply.
3. Or set the same action on **World Note** if the whole room should play it.
4. Enhance → Animate. The seed now carries the prop line.

Typed notes still win when you write more than the picker.

## Safety

- Teen / Child / Infant keep Regular / story performance (glance, pick up a book). Those fields **do not** unlock 18+ intimacy.
- Undress / explicit wardrobe still needs **18+ Explicit** and an adult 18+ cast.
- Genetics kids stay Regular / story. Do not route them through intimate intensity.

See [DIRECTOR_NOTES.md](DIRECTOR_NOTES.md), [MARK.md](MARK.md), [POSE.md](POSE.md), [CHARACTER_CONSISTENCY.md](CHARACTER_CONSISTENCY.md), [VOICE.md](VOICE.md), [WRITING.md](WRITING.md).
