# Troubleshooting — symptom to cause

The failures below are the ones that cost hours, because the symptom points
somewhere other than the cause.

## Engine and project

**"Godot not found" from a script that worked yesterday**
`lib.sh` searches `$GODOT_BIN`, `PATH`, `~/.local/bin/godot`, the macOS bundle,
`/usr/local/bin`, `/opt/godot`. A brew upgrade can move the bundle. Fix with
`export GODOT_BIN=/actual/path`, not by editing the scripts.

**macOS: "Godot is damaged and can't be opened"**
Quarantine flag on a manually downloaded app. `xattr -dr com.apple.quarantine
/Applications/Godot.app`.

**Headless run exits 0 but the game is broken**
Godot exits 0 even when GDScript throws at runtime. Exit codes prove nothing on
their own — scrape the log for `SCRIPT ERROR`, `Parse Error`, `Compile Error`.
This is what `check_project.sh` does and why it exists.

**Assets missing or pink after a fresh clone**
`.godot/` is gitignored and the import cache has to be rebuilt:
`bash workspace/import_assets.sh`. If it persists, a `.import` file is missing
from the commit — those are source, not derived.

**Changes to a `@tool` script do nothing in the editor**
The editor caches the old script instance. Project → Reload Current Project.

## City generation

**Buildings float above a hillside, or sink into it**
Something computed ground height without going through `terrain.height_at()`.
Find it and route it through. If the whole building is right but its uphill
corner shows daylight, that is the foundation depth — sink the box further.

**A street of buildings reads as one extruded ribbon**
`gap_chance` is 0 and the per-building colour jitter is missing. Both matter;
gaps more than colour.

**Windows are stretched, or a tower has as many windows as a house**
The facade shader is working in UV space instead of metres. Windows must be laid
out from the instance's real dimensions (passed in `INSTANCE_CUSTOM`), not from
UVs, or every building gets the same *count* scaled to fit.

**Windows appear on roofs**
Missing the `abs(normal.y) < 0.5` guard in the fragment shader.

**Per-instance colours or custom data are ignored**
`use_colors` / `use_custom_data` were set *after* `instance_count`. Godot
allocates the per-instance buffer at `instance_count` and silently discards
writes to flags enabled afterwards. Set the flags, then the mesh, then the count.

**The city rebuilds differently every launch**
The RNG is not seeded from the config, or something calls `randf()` on the
global RNG rather than the seeded instance. Determinism is worth defending —
without it you cannot reproduce a bug or judge a change.

**Frame rate collapses as the city grows**
In order: buildings are not batched into MultiMesh; colliders are trimesh rather
than box; there is a node per building; `visibility_range_end` is unset;
`directional_shadow_max_distance` is too large.

**The `.tscn` diff is enormous after opening the scene**
Generated nodes are being given an `owner`, so they are serialised into the
scene. Add children without setting owner.

**The player falls through the ground**
The ground collider was built from a different mesh than the one drawn, or the
`StaticBody3D` is on the wrong layer. World geometry wants
`collision_layer = 1`, `collision_mask = 0`; the player wants mask `5`.

## Assets

**A model imports facing backwards**
Godot's forward is `-Z`. Most downloaded glTF characters face `+Z`, so they need
a 180° yaw offset. Assets generated with the `-Y`-forward Blender convention
need `0`. Both are correct; they just differ.

**An imported character is a T-pose with no error**
Animation tracks failed to resolve. Clips address bones by full node path
(`Armature/Skeleton3D:upperarm_l`); if the target model's node layout differs,
every track silently misses. Rewrite the node half of each track path to address
the actual skeleton.

**A model looks nothing like it did in Blender**
Only glTF's PBR factors survive export: base colour, metallic, roughness,
normal, occlusion, emission. Procedural node graphs, noise textures, geometry-
node shading and subsurface are silently dropped. Bake to a texture first.

**Emissive parts glow but the room stays dark**
Emissive materials do not illuminate. Pair each with a real light node.

**A character's feet skate**
No root motion, and `walk_speed` does not match the clip's implied speed. Tune
the speed to the animation (usually 1.4–1.8 m/s for a walk), not the reverse.

## Export and deploy

**`--export-release` fails with "Unknown export preset"**
No preset with that exact name exists in `export_presets.cfg`, which is normally
only written by the editor. Run `ensure_export_presets.py`.

**Export fails and the message mentions templates**
Export templates are a separate download and must match the engine build
exactly. `bash install_godot.sh --templates`.

**The web build downloads, then a blank page**
Missing COOP/COEP headers, so `SharedArrayBuffer` is unavailable and the engine
never boots. Serve with `serve_web.py` or configure the host's headers.

**The web build boots but looks flat and wrong**
It is running the Compatibility renderer, which is the only one browsers
support. Effects authored for Forward+ (SSAO, SSIL, glow, volumetric fog) drop
or degrade. Set `renderer/rendering_method.web="gl_compatibility"` explicitly and
tune the art for it.

**The web build shows the previous version**
Cached `.wasm`/`.pck`. Serve with `Cache-Control: no-store` in development.

## Cloud

**`gcloud compute instances create` fails on quota**
New GCP projects have a GPU quota of zero. Request an increase for
`NVIDIA_L4_GPUS` in your region; approval takes hours to days and blocks
everything else.

**"invalid machine type" with a GPU flag**
L4 ships only on `g2-*` machines, where the GPU is part of the machine type and
must **not** be passed as an accelerator. T4 attaches to `n1-*` and must.

**Godot exits instantly on the VM: "cannot open display"**
Datacenter GPUs have no display output. The game needs a virtual X server bound
to the GPU — that is what the streaming container provides. Check the container
is actually running: `systemctl status godot-stream`.

**The stream connects but the picture is a slideshow**
Software encoding. Confirm `SELKIES_ENCODER=nvh264enc` and that
`nvidia-smi` works inside the container — if the NVIDIA container runtime is not
configured, it silently falls back to CPU.

**The VM was reclaimed mid-session**
It is a spot instance. Expected behaviour. `SPOT=0` costs 3× more and does not
happen.

**A surprise bill**
The VM was left running, or deleted-looking-but-stopped disks are still billing.
`bash cloud/stop.sh --status` lists what exists; `DELETE=1` removes it entirely.
