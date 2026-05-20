# City generation — building a square kilometre from a table

Contents: [The shape of the system](#the-shape-of-the-system) ·
[Config as data](#config-as-data) · [One height function](#one-height-function) ·
[Typologies](#typologies) · [Batching](#batching) · [Collision](#collision) ·
[Facade shading](#facade-shading) · [Landmarks](#landmarks) ·
[Day/night](#daynight) · [Adding a second city](#adding-a-second-city) ·
[Making a city feel like itself](#making-a-city-feel-like-itself)

## The shape of the system

```
city_config_<name>.gd   data: block sizes, districts, weighted building tables
        ↓ spec()
city_generator.gd       logic: loops blocks, places buildings, batches, collides
        ↓ uses
terrain.gd              one height function + the ground mesh derived from it
typology.gd             name → shape ranges
facade.gdshader         storeys and windows, drawn procedurally on plain boxes
        ↓ emits
PlayerSpawn, EnemySpawns
```

The generator contains **no knowledge of any specific city**. That is the load-
bearing property. It means a second city is a new data file, not a fork, and it
means the same generator can later be fed real map data instead of an invented
grid without the renderer changing at all.

## Config as data

A config returns a `Dictionary` from `spec()` and answers `district_at(bx, bz)`.
Nothing else. Keeping `district_at` a pure function of block coordinates makes
district layout deterministic, testable, and easy to redraw.

The seed matters more than it looks. A fixed seed means the same city every
launch — the level is reproducible, bugs are reproducible, and you iterate on
*rules* rather than on placement. Change the seed and you get a different city
from the same rules, which is a good way to check that your rules produce a city
rather than one lucky arrangement.

## One height function

**Nothing may compute ground height any way other than `terrain.height_at()`.**
The visible mesh, its collider, every building foundation, every spawn point and
every navmesh polygon call the same function.

This single rule prevents an entire category of bug. When two systems compute
ground independently they drift, and drift shows up as buildings floating above
a hill, a player falling through a slope, or spawn points inside terrain. When
they all read one function, disagreement is impossible by construction.

The payoff arrives later: swapping analytic hills for a sampled real-world
heightmap is a change to that one function, and every consumer follows for free.

Two details that matter in practice:

- **Foundations.** A building on a slope needs its box sunk below the lowest
  corner of its footprint, or the uphill side shows daylight underneath. Sinking
  every building by a fixed amount (8 m works) is cheaper and more robust than
  sampling all four corners.
- **Smoothstep, not cosine, for hills.** A cosine bump has a pointed summit that
  reads as a tent. `smoothstep` gives a flat top and a flat toe, and overlapping
  hills add into a ridge instead of fighting.

## Typologies

A typology is a *kind* of building described by ranges, not fixed numbers:
height min/max, width as a fraction of the lot frontage, base colour, roof cap.
The generator rolls inside the ranges, so one entry produces a street of related
but individual buildings.

Districts reference typologies with weights: `[["tower", 0.45], ["midrise",
0.4], ["podium", 0.15]]`. Weights are normalised, so adding a kind does not mean
rebalancing everything else.

Two knobs do most of the character work:

- **`lot_frontage`** — the grain of the city. 6 m gives you shophouses; 25 m
  gives you slabs. This one number changes the feel of a whole district more
  than any other.
- **`gap_chance`** — the probability a lot is left empty. Without gaps a
  perimeter block reads as one extruded ribbon rather than as separate
  buildings. 3–15% depending on how dense the district should feel.

## Batching

Every repeated box goes into a `MultiMesh`, one per typology. ~2,000 buildings
then cost a handful of draw calls instead of 2,000. This is the difference
between a city that runs and a slideshow, and it is far easier to build in from
the start than to retrofit.

Mechanics that bite:

```gdscript
mm.transform_format = MultiMesh.TRANSFORM_3D
mm.use_colors = true          # set BEFORE instance_count
mm.use_custom_data = true     # set BEFORE instance_count
mm.mesh = mesh
mm.instance_count = n         # allocates the buffer; earlier flags are baked in
```

Setting `use_colors` after `instance_count` silently discards everything you
write. There is no warning.

Use **one unit cube** scaled by each instance transform rather than a mesh per
size. The instance's real dimensions travel in `set_instance_custom_data()` as a
`Color(width, height, depth, seed)`, which the shader reads to lay windows out
in metres.

`visibility_range_end` on the `MultiMeshInstance3D` gives free distance culling.

## Collision

**One box per building, never the visual mesh.** A trimesh collider per building
is the classic way a procedural city becomes unplayable — and the player only
ever bumps into the box anyway.

Avoid a `CollisionShape3D` node per building too. At a few thousand buildings
the node overhead is measurable on its own. Use the shape-owner API on a single
`StaticBody3D`:

```gdscript
var owner_id := body.create_shape_owner(body)
body.shape_owner_add_shape(owner_id, box_shape)
body.shape_owner_set_transform(owner_id, Transform3D(Basis.IDENTITY, centre))
```

The ground is the exception: its collider is a trimesh generated from the same
mesh (`mesh.create_trimesh_shape()`), so what you see is exactly what you stand
on. That is fine because there is one of it.

Roads and other decoration get **no collision**. A road surface a few
centimetres above the ground that also collides just creates a lip to trip on.

## Facade shading

Plain boxes read as programmer art. Windows are what make them buildings, and
drawing them in a shader keeps the batching intact.

The key idea is to lay the window grid out in **metres**, derived from the
instance's real size, not in UV space. A 12 m rowhouse and a 160 m tower then
get windows the same physical size, instead of the same *number* of windows
stretched to fit — which is the single most obvious tell of a procedural city.

```glsl
float up     = (v_local.y + 0.5) * v_dims.y;   // metres up the facade
float across = (v_local.x + 0.5) * v_dims.x;   // metres along it
vec2 f = vec2(fract(across / window_pitch), fract(up / floor_height));
```

Things worth getting right:

- Suppress windows on the top and bottom faces (`abs(normal.y) < 0.5`). A window
  in a roof reads instantly as a bug.
- Suppress them below street level and across the ground-floor band. A blank
  base is what makes a building sit on the pavement rather than float on it.
- Light windows at night from a hash of `(bay, storey, instance_seed)` so the
  same windows stay lit frame to frame. A hash of anything view-dependent
  flickers.
- Mark decorative caps with height 0 in the custom data so they skip the whole
  branch.

## Landmarks

Generated blocks give you texture; landmarks give you orientation. A city
becomes navigable the moment there is something visible from far away that you
can walk toward.

Two placement modes, both worth having:

- **Block replacement** — `"landmark_blocks": {"7,4": "marina_bay_sands"}`. The
  named block is skipped by the normal builder and the landmark model is placed
  instead. Best for anything that occupies a city block.
- **Absolute position** — `{"kind": "merlion", "position": Vector3(...), "yaw":
  -90.0}`. For anything on a waterfront, a bridge, or a hilltop that has no
  relationship to the block grid.

Landmarks are the natural place for hand-authored `.glb` models, since there is
one of each and they carry the city's identity. Give each one a marker the HUD
can read for a compass or objective arrow — knowing which way the tower is
turns a maze into a city.

## Day/night

A real solar cycle is cheap and pays out of proportion to its cost. Place the
sun from the actual solar position for the city's latitude and day of year, and
the light behaves like the place: 38°N arcs across the southern sky and rakes
long shadows down the streets; 1.4°N goes nearly overhead and flattens shadows
to nothing at noon.

Export `hour`, `day_length_seconds`, `latitude_deg`, `day_of_year` and
`peak_sun_energy` on the sky node, and give the player a key to scrub the clock.
Being able to hold a key and run from dawn to dusk is worth more for judging a
city's lighting than any amount of screenshotting.

The sky system should reach the city only through the material list the
generator hands out (`facade_materials()`), setting the `night` uniform. It must
not know how the city was built.

## Adding a second city

1. Copy `city_config_<a>.gd` to `city_config_<b>.gd`, change the numbers.
2. Add it to `CONFIGS` in the generator.
3. Run it: `CITY=b bash workspace/run.sh`.

If step 2 required touching anything else in the generator, something city-
specific has leaked into it — pull that back into the config.

## Making a city feel like itself

Contrast between cities should be structural, not cosmetic. Recolouring the same
grid produces two versions of nowhere. Vary the things that actually differ:

| Axis | One city | The other |
|---|---|---|
| Layout | rigid grid, small lots | superblocks, towers in setbacks |
| Terrain | hills that break sightlines | dead flat, water instead |
| Grain | 8 m frontages, continuous street wall | 30 m setbacks, isolated slabs |
| Light | low warm sun, long shadows | near-vertical sun, no shadows at noon |
| Water | none | a quarter of the map |

Water deserves special mention: an unbuildable region does more for a skyline
than any building, because it creates the long sightlines that let you *see* a
skyline. Reserve a rectangle, skip blocks inside it, and drop the terrain.
