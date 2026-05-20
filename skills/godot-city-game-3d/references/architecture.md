# Architecture — rules that keep a Godot game from turning into spaghetti

Contents: [The four rules](#the-four-rules) · [Physics layers](#physics-layers) ·
[Scenes vs code](#scenes-vs-code) · [Autoloads](#autoloads) ·
[@tool scripts](#tool-scripts) · [Tuning knobs](#tuning-knobs) ·
[Performance order of operations](#performance-order-of-operations)

## The four rules

These are small, and they are the difference between a project that stays
editable at 5,000 lines and one that does not.

**1. Signals go up, calls go down.** A child emits; the parent listens and
tells other children. The player emits `health_changed`; the game manager hears
it and updates the HUD. The player must never reference the HUD. The moment a
leaf node reaches sideways across the tree, every scene becomes un-instantiable
on its own and the game stops being testable in pieces.

**2. The HUD holds no state.** It renders what it is told. If you can delete
the HUD and the game still runs correctly, the boundary is right. State living
in the display layer is how a health bar and actual health end up disagreeing.

**3. Levels hold no logic.** A level scene is geometry plus `Marker3D` spawn
points. Adding a level means adding markers, not code. This is what lets a
procedurally generated city be a drop-in replacement for a hand-built one — the
generator emits the same markers, so the game manager cannot tell the
difference.

**4. Contracts are duck-typed and tiny.** "Anything damageable implements
`take_damage(amount, point)`" is the entire interface. The weapon calls it
without knowing what it hit, so a new target type works with zero weapon
changes. Resist the urge to formalise this into a class hierarchy; the
hierarchy costs more than it returns at this scale.

The generator's contract with the rest of the game is one node:

```
CityGenerator emits:  PlayerSpawn (Marker3D)
                      EnemySpawns (Node3D of Marker3Ds)
```

That is all `game_manager.gd` needs. A new city is a new config file.

## Physics layers

Set names in `project.godot` so masks read as words in the Inspector rather
than as bit arithmetic:

| Layer | Bit | Used by |
|---|---|---|
| 1 `world` | 1 | terrain, buildings, level geometry |
| 2 `player` | 2 | player body |
| 3 `enemy` | 4 | enemy bodies |

Player mask `5` (world + enemy). Enemy mask `3` (world + player). Weapon
raycast mask `5`. Static world geometry sets `collision_layer = 1` and
`collision_mask = 0` — it collides with nothing, because nothing about it moves,
and leaving its mask at the default makes the physics server test it against
everything for no reason.

## Scenes vs code

For a procedural project the split that works is:

- **Scene files stay tiny.** `main.tscn` is a node with a script. Everything
  else is built in `_ready()`.
- **Generated nodes get no `owner`.** In Godot, only nodes with an owner are
  written into the `.tscn`. Adding a child without setting owner means the
  generated city is never serialised — the scene file stays a handful of lines,
  diffs cleanly, and cannot silently disagree with the generator.
- **Tag generated nodes with metadata** (`set_meta("city_generated", true)`) so
  a rebuild can clear exactly what it made and leave hand-added nodes alone.

The failure this avoids is real and unpleasant: a scene file containing 3,000
serialised buildings produces unreadable diffs, unresolvable merge conflicts,
and a version of the city that persists after you change the generator.

## Autoloads

Use them for genuinely global, stateless-ish services and nothing else:

| Autoload | Owns |
|---|---|
| `GameInput` | registering input actions in code |
| `Settings` | reading/writing `user://settings.cfg`, applying them |
| `CityChoice` | which city the menu picked, read by the loading scene |

Registering input actions in code rather than through the editor's Input Map
means the bindings live in a diffable file, survive a merge, and work on a
fresh clone before anyone opens the editor.

Passing scene-to-scene choices (which city, which difficulty) through a tiny
autoload is better than through a static var or a global singleton pattern,
because `get_tree().change_scene_to_file()` destroys everything else.

## @tool scripts

Marking the generator `@tool` makes it run in the editor, so you change a number
in the Inspector and watch a square kilometre re-rhythm. That is worth a lot for
tuning, and it costs two disciplines:

- Guard anything that must not run at edit time with `Engine.is_editor_hint()`
  (mouse capture, audio, autoload access).
- Give the script an explicit `regenerate` export that resets itself to `false`
  in its setter, so the checkbox works as a button.
- Provide `preview_in_editor` so opening the scene does not always pay the build
  cost.

## Tuning knobs

Everything balance-related should be `@export`, because a value you have to edit
source and relaunch to change is a value nobody will ever tune. Movement speed
in particular cannot be judged in the abstract — you have to feel it while it is
running.

Group them (`@export_group("Movement")`) once there are more than about six, or
the Inspector becomes a wall.

## Performance order of operations

For a city, in the order that actually pays:

1. **Batch repeated geometry into `MultiMesh`.** One per typology. This is the
   single biggest win and the hardest to retrofit — build it in from the start.
2. **Box colliders, never trimesh, for anything repeated.** A trimesh collider
   per building is the classic way a procedural city becomes unplayable.
   `shape_owner_add_shape` on one `StaticBody3D` avoids a node per building too.
3. **`visibility_range_end` on the building multimeshes.** Free LOD culling.
4. **Shadow distance.** `directional_shadow_max_distance` is the most expensive
   single number in a city scene. 200 m is generous.
5. **Cap the framerate.** Uncapped, the GPU renders frames past what the display
   shows and the laptop cooks for nothing. `run/max_fps=60` plus vsync typically
   halves power draw at zero latency cost.
6. Only then: render scale, renderer choice, mesh detail.
