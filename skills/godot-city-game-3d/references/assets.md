# Assets — generating models instead of downloading them

Contents: [Why generate](#why-generate) · [Conventions](#conventions) ·
[The kit pattern](#the-kit-pattern) · [What survives glTF export](#what-survives-gltf-export) ·
[Collision](#collision) · [Lighting](#lighting) ·
[Rigged humanoids](#rigged-humanoids) · [Borrowing animations](#borrowing-animations) ·
[Adding a generator](#adding-a-generator)

## Why generate

Hand-modelling and downloading both give you a binary blob. Generating with
headless Blender (`blender --background --python gen_x.py`) gives you something
maintainable:

- **It lives in git as diffable source.** "Make the crate braces thicker" is a
  one-line change with a reviewable diff, not 400 KB of binary churn.
- **It is parametric.** `crate(0.9)` and `crate(0.55)` are the same code. A
  level kit's `CELL = 4.0` is one constant — change it and every wall, floor and
  pillar re-tiles.
- **Conventions are enforced, not remembered.** Scale, origin, forward axis and
  the material palette are baked into the shared kit module. It becomes
  impossible to export something at 100× scale or facing backwards.
- **Budgets are visible.** Every export prints its triangle count against a
  budget, so you see an asset creeping up before it becomes a problem.

The tradeoff is real: this suits hard-surface, modular, architectural geometry.
It is the wrong tool for an organic character — see
[Rigged humanoids](#rigged-humanoids).

Three approaches exist; pick with eyes open:

| Approach | Good | Bad |
|---|---|---|
| `trimesh` / `pygltflib`, no DCC tool | pip-only, fast, CI-friendly | no bevels, no booleans, no UV unwrap, hand-authored skinning |
| **Headless Blender (`bpy`)** | modifiers, bevels, UV unwrap, armatures, NLA animation, a maintained spec-compliant exporter | ~200 MB dependency, API churn between versions |
| Houdini / CadQuery | heavy procedural / CAD | specialised |

Headless Blender is what studios do and what this pipeline assumes.

## Conventions

Define these once, in a shared `kit.py` that every generator imports, and never
fight them:

| | |
|---|---|
| **Units** | 1 Blender unit = 1 metre = 1 Godot unit. Export scale 1.0. |
| **Up** | `+Z` in Blender → `+Y` in glTF → correct in Godot. |
| **Forward** | `-Y` in Blender → `-Z` in Godot, which *is* Godot's forward. |
| **Origin** | On the floor, centred in X/Y. Drop it at a `Marker3D` and it stands up with no fudge transform. |
| **Scale ref** | Player capsule 1.8 m, eye height 1.65 m, doors 2.1 m. Build to that. |
| **Materials** | Principled BSDF only, from a fixed palette. |
| **Animation** | Clips are NLA tracks. Tracks sharing a name across objects merge into one glTF animation, so a multi-part rig animates as a unit. |

Because forward is handled at export, generated assets want **`Model Yaw Offset
Deg = 0`** — unlike downloaded packs, which usually need `180`.

## The kit pattern

One module owns primitives (`box`, `cylinder`, `sphere`, `torus`, `cone`), the
material palette, `reset_scene()`, `join()` and `export_glb(root, path,
budget=N)`. Generators import it and describe shapes; they never touch the
exporter or create materials directly.

A note on the palette: **adding a key is safe, editing one is not.** A new key
cannot change how an existing asset looks; changing an existing key silently
restyles every asset already using it.

Two things that will bite:

- **Join aggressively.** Every separate object is a draw call. Split only what
  animates independently or needs its own material.
- **Keyframe the same properties in every clip.** If `Run` keys a rotation that
  `Idle` does not, the tilt sticks after the chase ends and the model idles
  permanently hunched.

## What survives glTF export

glTF 2.0 carries a fixed PBR metallic-roughness model and nothing else:

- `baseColorFactor` / `baseColorTexture`
- `metallicFactor`, `roughnessFactor` (or a combined ORM texture)
- `normalTexture`, `occlusionTexture`
- `emissiveFactor` / `emissiveTexture`

**Everything else silently does not export.** Blender procedural node graphs,
noise textures, geometry nodes driving shading, subsurface, custom OSL — all
gone, with no warning. If you want it in the `.glb` it must be one of the above
factors or be *baked into a texture image* first. This is the single most common
surprise when moving from a Blender viewport to a game engine.

`.glb` over `.gltf`: one file, one read, no broken relative paths.

## Collision

Generated meshes carry no collision. Two ways to add it, and the choice matters:

1. **Name suffix on import** — rename a mesh so it ends in `-col` and Godot
   generates a matching `StaticBody3D` + trimesh collider automatically. Right
   for static level modules where collision should follow geometry exactly.
2. **Hand-placed primitives** — a box or capsule authored in the `.tscn`. Always
   cheaper at runtime than a trimesh. Right for anything that moves, and for
   props where a box is close enough.

An enemy's capsule should match its silhouette, so what you shoot at is what the
raycast hits.

## Lighting

**Emissive materials glow but do not illuminate.** A ceiling light strip, a lamp
tube and a drone's eye are all emissive meshes — they show up bright and they
light nothing. Pair each with an actual `OmniLight3D` or `SpotLight3D`. The mesh
is what you see; the light is what you see *by*. You need both.

Once level geometry stops being CSG, bake with `LightmapGI`.

## Rigged humanoids

Deliberately out of scope for a generator. Rigging a humanoid and producing
clean animation clips has a real skill floor and a multi-week cost; it is where
hobby projects die. Download them instead.

Use **one pack for bodies and one for animations that share a rig** — for
example Quaternius's Universal Base Characters plus Universal Animation Library
(both CC0, free, no account). Mixing packs from different sources means bone-
mapping every animation by hand, which is the part that eats a weekend.

Grab **GLB**, not FBX.

Two things go wrong with essentially every imported character:

- **Walking backwards** → `Model Yaw Offset Deg`. Most glTF characters face
  `+Z`; Godot's forward is `-Z`, so the default is `180`.
- **Giant or tiny** → `Model Scale`. Size the model to the 1.8 m capsule, not
  the other way around.

Also expect missing-texture import errors from packs whose `.gltf` references
filenames that differ from what shipped (a `_png` suffix mismatch is common).
Copy the files under the expected names; re-copying the pack reintroduces it.

## Borrowing animations

Base-character packs often ship **zero clips** — rigged, skinned, but no
animation, so Godot does not even create an `AnimationPlayer`. The animation
library is a separate file with clips on the same skeleton.

Bridging them at runtime is ~40 lines and worth doing properly:

1. Find the `Skeleton3D` inside whichever character model spawned.
2. Instantiate the animation source, take every clip off its `AnimationPlayer`.
3. **Rewrite each track's node path to address *this* model's skeleton.**
4. Create an `AnimationPlayer` on the model and hand it the rewritten library.

Step 3 is load-bearing. Clips address bones as `Armature/Skeleton3D:upperarm_l`;
if the character's node layout differs at all, every track silently fails to
resolve and you get a T-pose with no error. Rewriting the node half makes it
structure-independent. Cache the result per skeleton path so the rewrite runs
once, not once per spawn.

Pick the **non-root-motion** variant of an animation pack when movement is
driven by code — root motion will fight your controller.

Expose clip names as `@export` strings (`Idle` / `Walk` / `Run` / `Attack` /
`Death`), because every pack names them differently: `Punch` vs `Attack` vs
`Melee_01`. Print the available names on first run so wiring one up is copy and
paste.

Two limits to plan for: without a navmesh, wander targets get picked blind and
characters shove against obstacles; without root motion, feet skate unless
`walk_speed` is tuned to the clip (usually 1.4–1.8 m/s for a walk).

## Adding a generator

1. Copy the shape of an existing `gen_*.py`.
2. `import kit`, call `kit.reset_scene()` first.
3. Build with the kit primitives, parent to a root `kit.empty()`, `kit.join()`
   anything that never moves separately.
4. `kit.export_glb(root, path, budget=N)`.
5. Run `bash workspace/build_assets.sh <name>` — the runner discovers
   `gen_*.py` automatically.
6. `bash workspace/import_assets.sh` so Godot picks up the new `.glb`.

Use `--background --factory-startup` (the runner does) so the build ignores the
user's Blender preferences and addons and is identical on every machine.
