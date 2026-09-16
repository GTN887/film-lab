# 3D Set Desk

Virtual **set notes** plus a **LOCKED Environment from a photo**. Not a realtime 3D engine. Upload a still, invent the missing edges, look around / zoom / aerial. Optional: place Character Bible actors on that plate. Film Lab folds notes into Enhance → Pose → Animate. **Regenerate** is the retake.

## What landed

- **LOCKED Environment from photo** — invent plausible missing areas, then **look-around / zoom / aerial**
- **Pointer / Go-to** — click Actor A, point at a destination (bathroom / locked set), generate the walk-over, record it on Take Board
- Optional bible actors composited onto the locked plate (18+ Explicit stays adult-only)
- Camera notes: **orbit**, slow push-in, **aerial**, **drone**, **wide outdoor**
- Outdoor plates: street, sky, wide outdoor, bus stop, walk home, drone aerial
- Role marks: Mom, Dad, Teen, Adult, Child, Infant on the set
- Same filming-mode picker as Motion Desk (Regular | 18+ Explicit)
- Notes persist as `set_notes.json` on the project (runtime, gitignored with other project media)

**On this PC (offline, deletable):**

| Folder | What lives there |
| --- | --- |
| `data/projects/<name>/sets/<set-id>/` | Source photo, expanded plate, view stills, `env.json` |
| `data/projects/<name>/stills/` | Copies of the locked views |
| `data/projects/<name>/takes/` | Look-around / zoom / aerial clip |
| `data/projects/<name>/env_lock.json` + `env_refs/` | Active World / 3D Set lock |

**Delete this set** removes that package from the project folder. Deeper 3D (orbiting a mesh, true aerial photogrammetry) is future work. This desk does not claim that.

## Flow

1. Upload a photo → **Build locked environment** (look-around / zoom / aerial). Optional bible actors.
2. Files land on this PC under `sets/` · `stills/` · `takes/`. Delete anytime.
3. Pick Regular for a family walk / bus / porch, or 18+ Explicit for adult-only intimacy.
4. Place more roles on the set if you want, then **Apply 3D Set**.
5. **Pointer / Go-to:** Actor A → bathroom (or any locked room) → **Generate go-to take** → Take Board.
6. Animate, then Regenerate for another angle.

World Note outdoor plates stay available on Motion Desk and Take Board so weather + street/sky ride the same Apply path.

**Environment lock** on this desk (and World Note) pins one set still + optional style ref. Img2vid seeds from that still when the shot has no start frame. **Regenerate** keeps the World lock. See [ENV_LOCK.md](ENV_LOCK.md).
