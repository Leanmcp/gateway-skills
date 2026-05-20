---
name: godot-city-game-3d
description: Build, run, debug and ship 3D city games in Godot 4 — procedurally generated cities (block grids, districts, weighted building typologies, MultiMesh batching, facade shaders, terrain, day/night, landmarks), first-person controllers, headless verification, Blender-generated .glb assets, rigged character and animation packs, real OpenStreetMap-derived cities, WebAssembly export, and cloud GPU streaming on GCP. Use this skill whenever the work involves Godot or a .gd/.tscn/.gdshader/project.godot file; whenever someone wants to start, set up, clone onto a new machine, or stand up a 3D game or city generator; whenever they mention procedural city, city generator, block grid, building typology, MultiMesh, facade shader, terrain heightmap, navmesh, Godot export templates, export presets, headless Godot, .glb pipeline, Blender asset generation, character rigs or borrowed animations; and whenever they want to deploy or share a game — web export, SharedArrayBuffer/COOP/COEP, Selkies, pixel streaming, GPU VM, or "let people play this without installing anything." Reach for it even on vague asks like "get this running", "why is my city slow", "my model faces backwards", "make it work on a cloud machine", or "set this up somewhere else too" when a Godot 3D project is in play.
---

# Godot city game (3D)

A complete toolkit for procedurally generated 3D city games in Godot 4: scaffold
a new one in a minute, stand an existing one up on any machine, and ship it to a
browser or a cloud GPU.

Everything here assumes Godot 4.x. Godot 3 differs enough in GDScript,
rendering and node API that this guidance does not transfer.

## Start here — pick the situation

| Situation | Do this |
|---|---|
| Empty directory, want a city game | [Bootstrap](#bootstrap-a-new-project) |
| Existing repo, new machine / fresh clone | [Set up an existing project](#set-up-an-existing-project) |
| Something is broken | `references/troubleshooting.md` — symptom-to-cause, read it before debugging from scratch |
| Changing how the city looks or is built | `references/city-generation.md` |
| Adding gameplay, worried about structure | `references/architecture.md` |
| Models, Blender, characters, animations | `references/assets.md` |
| Driving the city from real map data | `references/real-map-data.md` |
| Getting other people playing it | `references/deploy.md` |
| Install details, CI, version pinning | `references/setup.md` |

Read the reference file rather than reconstructing its content — each one exists
because the details in it are the kind that cost hours when guessed.

## Bootstrap a new project

```bash
python3 scripts/bootstrap_project.py ~/code/my-city --name "My City"
```

Produces a project that runs immediately: a hilly ~60-block city with batched,
window-shaded buildings, box collision, a walkable first-person player, and a
`workspace/` carrying its own copies of every install/run/check/export/cloud
script. Then:

```bash
bash ~/code/my-city/workspace/install_godot.sh --templates
time bash ~/code/my-city/workspace/check_project.sh     # headless, proves it builds
bash ~/code/my-city/workspace/run.sh                    # play it
```

The scaffold is deliberately a *working small city* rather than an empty
skeleton, because its value is the architecture it demonstrates — config as
data, one height function, MultiMesh batching, box collision, nothing generated
saved into the scene — and an empty skeleton demonstrates none of it.

Copying the scripts into the new repo (rather than referencing this skill) is
what makes the result portable: the repo can then stand itself up on another
laptop, a CI runner or a cloud VM with nothing else installed.

## Set up an existing project

```bash
bash workspace/install_godot.sh --templates     # or scripts/install_godot.sh
time bash workspace/check_project.sh
bash workspace/run.sh
```

Three things make this work identically everywhere, and they are worth
preserving in any project touched:

- **Nothing hardcodes a path.** `lib.sh` finds the Godot binary by searching
  (`$GODOT_BIN`, `PATH`, `~/.local/bin`, the macOS bundle, `/opt/godot`) and
  finds the project by walking up from the working directory looking for
  `project.godot`. Override with environment variables, never by editing
  scripts.
- **`--templates` matters.** Export templates are a separate download that Godot
  normally fetches through an editor dialog — which does not exist on a headless
  VM. Skipping this is the single most common reason a cloud or web export fails
  later, and the error message blames the preset instead.
- **`check_project.sh` is the real gate.** Godot exits 0 even when GDScript
  throws at runtime, so exit codes prove nothing. The script boots each scene
  headless and fails on `SCRIPT ERROR` / `Parse Error` in the log. Run it before
  believing anything works, and use it as the CI check.

## The scripts

All under `scripts/`, all safe to copy into a project's `workspace/`.

| Script | Does |
|---|---|
| `install_godot.sh [--templates]` | Godot 4 on macOS/Linux, PATH shim, quarantine fix, export templates |
| `check_project.sh [scenes…]` | headless import + boot each scene, fail on script/shader errors |
| `run.sh [--editor]` | play, or open the editor |
| `import_assets.sh` | reimport `.glb`/textures without the GUI |
| `build_assets.sh [names…]` | run the Blender `gen_*.py` generators |
| `ensure_export_presets.py` | write the `Web`/`Linux`/`macOS`/`Windows` presets the editor would otherwise have to create |
| `export_web.sh [--no-serve]` | WebAssembly export + a server that sends COOP/COEP |
| `serve_web.py` | that server, standalone |
| `bootstrap_project.py` | scaffold a new project |
| `cloud/provision_gcp.sh` | GPU VM + firewall + driver/Docker/Selkies setup |
| `cloud/deploy_game.sh` | Linux export, upload, restart the stream |
| `cloud/stop.sh [--status]` | stop billing (`DELETE=1` to remove the disk too) |

Every one accepts `GODOT_BIN`, `GODOT_PROJECT` and `GODOT_VERSION` from the
environment.

## How a city generator is put together

Full detail in `references/city-generation.md`. The shape:

```
city_config_<name>.gd   DATA  block sizes, districts, weighted building tables, hills, seed
        ↓ spec()
city_generator.gd       LOGIC loops blocks, places buildings, batches, collides
        ↓ uses
terrain.gd              one height function + the ground mesh derived from it
typology.gd             building kind → shape ranges
facade.gdshader         storeys and windows drawn procedurally on plain boxes
        ↓ emits
PlayerSpawn, EnemySpawns          ← the entire contract the rest of the game needs
```

Five properties carry the whole design. Preserve them; each one is expensive to
retrofit and cheap to keep:

1. **The generator knows nothing about any specific city.** A second city is a
   new data file, not a fork. If adding one required touching the generator,
   something city-specific has leaked in.
2. **One height function.** Ground mesh, its collider, every foundation, every
   spawn point and every navmesh polygon call `terrain.height_at()`. Two systems
   computing ground independently *will* drift, and drift is what floats
   buildings above hills and drops players through slopes. It also means
   swapping analytic hills for a real heightmap is a one-function change.
3. **MultiMesh per typology.** ~2,000 buildings cost a handful of draw calls
   instead of 2,000. Set `use_colors`/`use_custom_data` *before* `instance_count`
   — Godot allocates the buffer at that point and silently discards writes to
   flags enabled afterwards.
4. **Box collision, never trimesh, for anything repeated.** Use
   `create_shape_owner` / `shape_owner_add_shape` on one `StaticBody3D` so there
   is not even a node per building.
5. **Generated nodes get no `owner`.** Only owned nodes are written into the
   `.tscn`, so the scene file stays a few lines, diffs cleanly, and cannot
   silently disagree with the generator. Tag them with metadata so a rebuild
   clears exactly what it made.

Determinism is the sixth: seed the RNG from the config so the same seed rebuilds
the identical city. Without it you cannot reproduce a bug or judge a change.

### The facade trick worth knowing

Plain boxes read as programmer art; windows make them buildings. Lay the window
grid out in **metres**, derived from each instance's real dimensions passed in
`INSTANCE_CUSTOM`, not in UV space. A 12 m house and a 160 m tower then get
windows the same physical size instead of the same *count* stretched to fit —
which is the most obvious tell of a procedural city. Suppress windows on
top/bottom faces and across the ground-floor band, and light them at night from
a hash of `(bay, storey, seed)` so they do not flicker.

## Architecture rules for the rest of the game

Detail in `references/architecture.md`. In brief:

- **Signals go up, calls go down.** The player emits `health_changed`; the game
  manager hears it and tells the HUD. The player never touches the HUD.
- **The HUD holds no state.** Delete it and the game still runs correctly.
- **Levels hold no logic** — geometry plus `Marker3D` spawn points. This is what
  lets a generated city be a drop-in replacement for a hand-built level.
- **Contracts stay tiny and duck-typed.** "Anything damageable implements
  `take_damage(amount, point)`" is the whole interface.
- **Everything tunable is `@export`.** A value you must edit source and relaunch
  to change is a value nobody will ever tune — and movement feel in particular
  cannot be judged in the abstract.
- **Physics layers by name:** 1 `world`, 2 `player`, 3 `enemy`. Static geometry
  is layer 1, mask 0 — it moves against nothing, and a default mask makes the
  physics server test it against everything for free.
- **Register input actions in code** (an autoload), so bindings are diffable,
  survive merges, and work on a fresh clone before anyone opens the editor.

Performance, in the order that actually pays: batch into MultiMesh → box
colliders → `visibility_range_end` → `directional_shadow_max_distance` → cap the
framerate → only then render scale and renderer choice.

## Assets

Detail in `references/assets.md`. Generate models from headless Blender
(`blender --background --factory-startup --python gen_x.py`) rather than
hand-modelling: the source is diffable Python in git, assets are parametric, and
conventions (metre scale, floor origin, `-Y` forward, a fixed palette) are
enforced by a shared `kit.py` rather than remembered.

Two things bite everyone:

- **Only glTF's PBR factors survive export** — base colour, metallic, roughness,
  normal, occlusion, emission. Blender procedural node graphs, noise textures
  and geometry-node shading are silently dropped. Bake to a texture first.
- **Emissive materials glow but do not illuminate.** Pair every emissive mesh
  with a real light node.

Rigged humanoids are the exception: download them, do not generate them. Use one
pack for bodies and one for animations **that share a rig** (Quaternius's
Universal Base Characters + Universal Animation Library, both CC0) — mixing
sources means bone-mapping every clip by hand. Base packs often ship zero clips,
so animations get borrowed at runtime; the load-bearing step is rewriting each
track's node path to address the target skeleton, because a mismatch produces a
silent T-pose with no error.

## Real map data

Detail in `references/real-map-data.md`. Driving the city from OpenStreetMap
replaces the *source of the block list*, not the renderer — everything
downstream is unchanged, which is the payoff for keeping config separate from
generator.

The one decision that must be right first: project lat/lon onto a **local
East-North tangent plane** in metres with a frozen origin, mapped as
`x = east`, `z = -north`, `y = elevation`. Not UTM, not Web Mercator — Mercator
is wrong by the secant of the latitude (~27% at San Francisco), which is the
classic way a bake ends up subtly stretched. Bake offline to files; never call a
map API at runtime.

The acceptance test for the whole front half of the pipeline is one top-down SVG
of the projected data. It either looks like the city or it does not, and it
catches axis flips and unit errors that are nearly invisible once the data is
inside the engine.

## Shipping it

Detail in `references/deploy.md`. Godot has **no built-in pixel streaming**; its
WebRTC support is for multiplayer networking, which is a common and expensive
confusion. Two real paths:

**Web export — the default.** Runs on the player's machine: ~$0, zero latency,
unlimited concurrent players.

```bash
bash scripts/export_web.sh
```

Three things must all be true: export templates installed, a preset named
exactly `Web` (`ensure_export_presets.py` writes it), and the Compatibility
renderer — browsers run WebGL 2 only. Override just the web platform so desktop
keeps Forward+:

```ini
renderer/rendering_method="forward_plus"
renderer/rendering_method.web="gl_compatibility"
```

Hosting needs `Cross-Origin-Opener-Policy: same-origin` and
`Cross-Origin-Embedder-Policy: require-corp`, or `SharedArrayBuffer` is
unavailable and the game silently never boots. `python3 -m http.server` sends
neither; `serve_web.py` exists solely for those two headers. GitHub Pages cannot
set them.

**Cloud GPU streaming — when players genuinely cannot run the game.**

```bash
bash scripts/cloud/provision_gcp.sh     # L4 spot by default
bash scripts/cloud/deploy_game.sh
bash scripts/cloud/stop.sh              # STOP BILLING
```

~$0.90/hr for an L4 plus egress (12 Mbit/s ≈ 5.4 GB/hr), realistically 3–4
concurrent players — rendering binds long before encoding does. Request the GPU
quota first: new GCP projects have a quota of zero and approval takes hours to
days.

If the actual motivation is "my laptop runs hot", neither path is the answer —
cap the framerate (`run/max_fps=60` + vsync roughly halves GPU draw at no
latency cost), then cut shadow distance and building draw distance.

## Working on someone's existing city project

Before changing generation code, run `check_project.sh` to establish that it
builds, and read the config file rather than the generator — the config is where
intent lives. When something looks wrong in-game, check
`references/troubleshooting.md` first; most city-generation symptoms (floating
buildings, ribbon streets, stretched windows, ignored instance colours, collapsed
framerate) have one specific cause each, and guessing at them is expensive.
