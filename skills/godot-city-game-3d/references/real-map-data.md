# Real map data — deriving a city instead of inventing one

Contents: [What changes](#what-changes) · [The coordinate contract](#the-coordinate-contract) ·
[Fetching from OSM](#fetching-from-osm) · [Elevation](#elevation) ·
[Buildings and heights](#buildings-and-heights) · [Tags to typologies](#tags-to-typologies) ·
[The acceptance test](#the-acceptance-test) · [Licensing](#licensing)

## What changes

Almost nothing, and that is the point. The generator's block loop goes from

```gdscript
for bx in blocks.x:
    for bz in blocks.y:          # invent a block here
```

to

```gdscript
for block in map.blocks:         # read a real block here
```

Everything downstream — typology buckets, MultiMesh batching, per-block
colliders, tree scatter, spawn emission — is unchanged. **You are replacing the
source of the block list, not the renderer.**

Three properties of a well-built generator make this cheap, and they are worth
protecting for exactly this reason:

1. One height function drives ground mesh, collision, foundations and navmesh.
   Swap its guts from analytic hills to a sampled heightmap and every consumer
   follows for free.
2. Config is data, generator is logic. A map bake is just a much larger
   dictionary from a different producer.
3. Typologies are a lookup table, so OSM tags map onto them directly.

Bake offline into files the game loads. Do **not** call a map API at runtime:
it makes the game require network, non-deterministic, rate-limited and slow.

## The coordinate contract

**This is the most important decision in the whole pipeline.** Get it wrong and
nothing can be made to line up; get it right and every real-world coordinate has
exactly one world position, forever.

Convert WGS84 lat/lon to a **local East-North-Up tangent plane** in metres, with
the origin at a fixed reference point:

```
lat0, lon0  = tangent point (fixed forever, written to origin.json)
N = a / sqrt(1 - e²sin²lat0)            normal radius of curvature
M = a(1-e²) / (1 - e²sin²lat0)^1.5      meridional radius

east  = (lon - lon0) * (π/180) * N * cos(lat0)
north = (lat - lat0) * (π/180) * M
```

`a` and `e²` are the WGS84 ellipsoid constants. Over a few kilometres this is
accurate to a couple of centimetres — far below the resolution of anything in
the game.

**Not** UTM and **not** Web Mercator. A tangent plane needs no dependency, is
exact at the origin, and has no zone seam. Web Mercator is wrong by the secant
of the latitude — about 27% at San Francisco — and that error is the classic way
a city bake ends up subtly stretched in one axis.

Then map onto Godot's axes:

| Godot | Real world |
|---|---|
| `+X` | east |
| `−Z` | north |
| `+Y` | up |

```
x =  east
z = -north
y =  elevation
```

Freeze `lat0`/`lon0` in an `origin.json` that every stage reads and none
recompute. Changing it invalidates every baked file and every hand-placed
coordinate in the configs, so treat it as immutable once anything is placed.

## Fetching from OSM

Overpass API, one query per layer (streets, buildings, coastline, water, parks,
landmarks) so a single failure never loses the set. Cache to disk and skip what
is already there — Overpass is a shared free service and hammering it is both
rude and slow.

Stdlib-only is achievable. The trick that makes it possible is `out geom;`,
which inlines each way's coordinates into the response. Without it you must
fetch every node and dereference by id, which is the only genuinely annoying
part of working with raw OSM.

Operational notes that save an afternoon:

- **429 and 504 are normal responses**, not failures. Retry with backoff.
- **Rotate mirrors.** `overpass.kumi.systems`, `overpass-api.de`,
  `overpass.private.coffee`, `overpass.osm.jp` are independent installations of
  the same software over the same data with very different load. Rotating turns
  "this mirror is swamped" into a few seconds of delay instead of a failed run.
- **Send a real User-Agent** identifying the project.
- Pick a bounding box that is a *walkable* area. A few square kilometres is a
  lot of city; a whole metro is a data-processing project, not a game level.

## Elevation

Sources, roughly in order of convenience:

| Source | Resolution | Notes |
|---|---|---|
| SRTM 1-arcsec | ~30 m | global, free, good enough for hills |
| USGS 3DEP / national LIDAR | 1–10 m | best where available |
| Mapzen/Terrarium PNG tiles | ~30 m | trivially fetchable, decode RGB → metres |

Resample onto the same tangent-plane grid the rest of the bake uses, and feed it
to `height_at()` with bilinear sampling. Smooth lightly: raw 30 m DEM data has
stair-steps that read as terracing on a hillside.

## Buildings and heights

OSM footprints are polygons; the game wants extruded prisms with a height.

- `height` tag (metres) when present — trust it.
- Otherwise `building:levels` × ~3.2 m.
- Otherwise a default from the typology, which is what the invented generator
  was doing anyway.

Coverage of height tags varies enormously by city — dense in Singapore and
central London, sparse in most places. Plan for the fallback path being the
common one.

Simplify footprints before extruding (Douglas–Peucker at ~0.5 m). Raw OSM
polygons carry vertices you will never see, and every one of them is a triangle
in a mesh you are drawing thousands of times.

## Tags to typologies

The existing typology table is the target; OSM tags are the source. A direct
lookup is enough:

| OSM | Typology |
|---|---|
| `building=house`, `terrace`, `residential` | rowhouse |
| `building=apartments` + levels ≥ 8 | midrise / slab |
| `building=commercial|office` + height ≥ 60 | tower |
| `building=warehouse|industrial` | warehouse |
| `building=retail` | podium |
| `building=church|civic|government` | civic |

Anything unmatched falls back to a district default. Resist adding a typology
per tag — the table's value is that it is small enough to hold in your head.

## The acceptance test

Render the whole projected dataset to a top-down SVG, to scale, and open it in a
browser. **It either looks like the city or it does not.** That single image is
the acceptance test for the entire front half of the pipeline, and it catches
axis flips, projection errors and unit mistakes in one glance — all of which are
nearly invisible once the data is inside the engine.

Do this before writing a single line of the Godot-side loader.

## Licensing

OpenStreetMap data is © OpenStreetMap contributors, **ODbL**. It requires
attribution, and it has share-alike obligations on derived databases. Baked
geometry in a game is generally fine with attribution in the credits, but if you
are shipping commercially, read the licence rather than trusting a summary.
Elevation sources have their own terms — SRTM and USGS are public domain,
commercial DEM providers are not.
