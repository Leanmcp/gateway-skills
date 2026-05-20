@tool
extends Node3D
## Builds a city block by block, at load time, from a config script.
##
## Three decisions do most of the work here, and they are the ones worth
## preserving in any city you grow out of this:
##
##   * Every repeated box goes into a MultiMesh, one per typology. ~2,000
##     buildings then cost a handful of draw calls instead of 2,000. This is
##     the difference between a city that runs and a slideshow, and it is far
##     easier to build in from the start than to retrofit.
##   * Collision is one box per building, never the visual mesh. A trimesh
##     collider per building is the classic way a procedural city becomes
##     unplayable; a box is what the player actually bumps into anyway.
##   * Nothing is saved into the scene file. Generated nodes are added without
##     an owner, so the .tscn stays a few lines and diffs cleanly, and the
##     generator remains the only source of truth for what exists.
##
## The generator emits a `PlayerSpawn` marker, which is the entire contract the
## rest of the game needs -- so a new city drops in with no gameplay changes.

const Terrain := preload("res://scripts/city/terrain.gd")
const Typology := preload("res://scripts/city/typology.gd")
const FacadeShader := preload("res://shaders/facade.gdshader")

const CONFIGS := {
	"{{CITY}}": preload("res://scripts/city/city_config_{{CITY}}.gd"),
}

## Marks nodes this script created, so a rebuild can clear them safely without
## touching anything a human added to the scene by hand.
const GENERATED := "city_generated"

@export var city: String = "{{CITY}}":
	set(value):
		city = value
		if is_inside_tree():
			generate()

@export_group("Build")
## Ground mesh and collision resolution, metres. Lower is smoother and slower,
## quadratically -- halving this quadruples the work.
@export var terrain_cell: float = 8.0
## How far the ground runs past the last block.
@export var surround: float = 400.0
## Buildings stop drawing past this distance. The single cheapest performance
## knob in the whole generator.
@export var draw_distance: float = 1400.0
## Rebuild live in the editor viewport. Costs a second or two on scene open.
@export var preview_in_editor: bool = true
## Tick in the Inspector to rebuild after changing anything.
@export var regenerate: bool = false:
	set(value):
		regenerate = false
		if value:
			generate()

var _rng := RandomNumberGenerator.new()
var _spec: Dictionary = {}
## Kept so a day/night cycle can light windows without knowing how the city was
## built. Handing out the materials is a much smaller contract than handing out
## the geometry.
var _facade_materials: Array[ShaderMaterial] = []


func _ready() -> void:
	if Engine.is_editor_hint() and not preview_in_editor:
		return
	generate()


# ------------------------------------------------------------------ building
func generate() -> void:
	var started := Time.get_ticks_msec()
	_clear()
	_facade_materials.clear()

	if not CONFIGS.has(city):
		push_error("[city] no config named '%s'. Known: %s" % [city, CONFIGS.keys()])
		return

	var config: GDScript = CONFIGS[city]
	_spec = config.spec()
	_rng.seed = int(_spec["seed"])

	var blocks: Vector2i = _spec["blocks"]
	var block_size: Vector2 = _spec["block_size"]
	var street: float = _spec["street_width"]
	var period := block_size + Vector2(street, street)
	var extent := Vector2(blocks.x * period.x, blocks.y * period.y)

	_build_ground(extent + Vector2(surround, surround) * 2.0)

	# Buildings are collected per typology first and batched afterwards. Doing
	# it in one pass would mean either a MultiMesh per building or resizing
	# every instance array constantly; collecting is simpler and much faster.
	var batches: Dictionary = {}
	var roads: Array[Transform3D] = []
	var count := 0

	for bx in blocks.x:
		for bz in blocks.y:
			var origin := Vector2(
				-extent.x * 0.5 + bx * period.x + street * 0.5,
				-extent.y * 0.5 + bz * period.y + street * 0.5
			)
			var district: String = config.district_at(bx, bz, blocks.x, blocks.y)
			var rules: Dictionary = _spec["districts"][district]
			count += _build_block(origin, block_size, rules, batches)

	roads = _road_transforms(blocks, period, street, extent)

	var bodies := StaticBody3D.new()
	bodies.name = "BuildingColliders"
	bodies.collision_layer = 1
	bodies.collision_mask = 0
	_adopt(bodies)

	for type_name in batches:
		_commit_batch(type_name, batches[type_name], bodies)

	_build_roads(roads)
	_place_spawn(extent)

	print("[city] %s: %d blocks, %d buildings, %d batches, %d ms" % [
		_spec.get("display_name", city), blocks.x * blocks.y, count,
		batches.size(), Time.get_ticks_msec() - started,
	])


## Returns how many buildings it placed. One block is four street-facing rows;
## a perimeter block is the right default because it is what produces a street
## *wall*, and a continuous street wall is most of what makes a city read as
## urban rather than as objects on a plane.
func _build_block(origin: Vector2, size: Vector2, rules: Dictionary, batches: Dictionary) -> int:
	var depth: float = rules["depth"]
	var gap: float = rules["gap_chance"]
	var frontage: float = _spec["lot_frontage"]
	var placed := 0

	# along, inward, and the span of the edge. Insetting the two side edges by
	# `depth` stops the four rows from piling up on top of each other at the
	# corners.
	var edges := [
		{"along": Vector2(1, 0), "inward": Vector2(0, 1),
		 "start": origin, "length": size.x, "inset": 0.0},
		{"along": Vector2(1, 0), "inward": Vector2(0, -1),
		 "start": origin + Vector2(0, size.y), "length": size.x, "inset": 0.0},
		{"along": Vector2(0, 1), "inward": Vector2(1, 0),
		 "start": origin, "length": size.y, "inset": depth},
		{"along": Vector2(0, 1), "inward": Vector2(-1, 0),
		 "start": origin + Vector2(size.x, 0), "length": size.y, "inset": depth},
	]

	for edge in edges:
		var usable: float = edge["length"] - edge["inset"] * 2.0
		if usable < frontage:
			continue
		var lots := int(usable / frontage)
		for i in lots:
			if _rng.randf() < gap:
				continue
			var type_name: String = Typology.pick(rules["types"], _rng)
			var t: Dictionary = Typology.TABLE[type_name]

			var w: float = frontage * _rng.randf_range(t["width_scale"].x, t["width_scale"].y)
			var h: float = _rng.randf_range(t["height"].x, t["height"].y)
			var d: float = minf(depth, size.y * 0.45)

			var along_offset: float = edge["inset"] + (i + 0.5) * frontage
			var centre: Vector2 = edge["start"] \
				+ edge["along"] * along_offset \
				+ edge["inward"] * (d * 0.5)

			# Along-edge size and depth swap on the two side edges, because the
			# box is axis-aligned and never rotated -- rotating would break the
			# facade shader's assumption that a face is one of two orientations.
			var footprint := Vector2(w, d) if edge["along"].x != 0.0 else Vector2(d, w)

			if not batches.has(type_name):
				batches[type_name] = []
			batches[type_name].append(_building(centre, footprint, h, t))
			placed += 1

			if t["roof"].y > 0.0:
				var inset: float = t["roof"].x
				var roof_fp := footprint - Vector2(inset, inset) * 2.0
				if roof_fp.x > 0.5 and roof_fp.y > 0.5:
					batches[type_name].append(
						_roof(centre, roof_fp, h, t["roof"].y, t))
	return placed


## One building, as everything the MultiMesh needs to know about it.
func _building(centre: Vector2, footprint: Vector2, height: float, t: Dictionary) -> Dictionary:
	var ground := Terrain.height_at(centre.x, centre.y, _spec)
	# Sink the box below ground so a building on a slope has a foundation
	# instead of a visible gap under its uphill corner.
	const FOUNDATION := 8.0
	var total := height + FOUNDATION
	var centre_y := ground + height * 0.5 - FOUNDATION * 0.5

	var basis := Basis.IDENTITY.scaled(Vector3(footprint.x, total, footprint.y))
	var xform := Transform3D(basis, Vector3(centre.x, centre_y, centre.y))

	var base: Color = t["color"]
	# A small per-building jitter is what stops a row of one typology from
	# looking like a single extruded ribbon.
	var tint := Color(
		clampf(base.r + _rng.randf_range(-0.05, 0.05), 0.0, 1.0),
		clampf(base.g + _rng.randf_range(-0.05, 0.05), 0.0, 1.0),
		clampf(base.b + _rng.randf_range(-0.05, 0.05), 0.0, 1.0)
	)

	return {
		"transform": xform,
		"color": tint,
		# The shader needs real-world dimensions to space windows correctly,
		# and the seed decides which windows are lit at night.
		"custom": Color(footprint.x, total, footprint.y, _rng.randf()),
		"collide": true,
	}


func _roof(centre: Vector2, footprint: Vector2, height: float, roof_h: float, t: Dictionary) -> Dictionary:
	var ground := Terrain.height_at(centre.x, centre.y, _spec)
	var basis := Basis.IDENTITY.scaled(Vector3(footprint.x, roof_h, footprint.y))
	var xform := Transform3D(basis, Vector3(centre.x, ground + height + roof_h * 0.5, centre.y))
	return {
		"transform": xform,
		"color": (t["color"] as Color).darkened(0.25),
		# Zero height in the custom data tells the shader "no windows here".
		"custom": Color(footprint.x, 0.0, footprint.y, 0.0),
		"collide": false,
	}


## Turn a list of buildings into one MultiMesh plus one collider per building.
func _commit_batch(type_name: String, items: Array, bodies: StaticBody3D) -> void:
	var mesh := BoxMesh.new()
	mesh.size = Vector3.ONE

	var mat := ShaderMaterial.new()
	mat.shader = FacadeShader
	mesh.material = mat
	_facade_materials.append(mat)

	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	# Both of these must be set before instance_count -- Godot allocates the
	# per-instance buffer at that point, and toggling them afterwards silently
	# discards what you wrote.
	mm.use_colors = true
	mm.use_custom_data = true
	mm.mesh = mesh
	mm.instance_count = items.size()

	for i in items.size():
		var item: Dictionary = items[i]
		mm.set_instance_transform(i, item["transform"])
		mm.set_instance_color(i, item["color"])
		mm.set_instance_custom_data(i, item["custom"])

		if item["collide"]:
			var shape := BoxShape3D.new()
			shape.size = (item["transform"].basis * Vector3.ONE).abs()
			# shape_owner_* adds collision without a node per building. At a few
			# thousand buildings the node overhead is what you actually feel.
			var owner_id := bodies.create_shape_owner(bodies)
			bodies.shape_owner_add_shape(owner_id, shape)
			bodies.shape_owner_set_transform(owner_id,
				Transform3D(Basis.IDENTITY, item["transform"].origin))

	var mmi := MultiMeshInstance3D.new()
	mmi.name = "Buildings_" + type_name
	mmi.multimesh = mm
	mmi.visibility_range_end = draw_distance
	mmi.visibility_range_end_margin = 100.0
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	_adopt(mmi)


func _road_transforms(blocks: Vector2i, period: Vector2, street: float, extent: Vector2) -> Array[Transform3D]:
	var out: Array[Transform3D] = []
	const THICK := 0.12
	for bx in blocks.x + 1:
		var x := -extent.x * 0.5 + bx * period.x
		out.append(Transform3D(
			Basis.IDENTITY.scaled(Vector3(street, THICK, extent.y)),
			Vector3(x, Terrain.height_at(x, 0.0, _spec) + THICK * 0.5, 0.0)))
	for bz in blocks.y + 1:
		var z := -extent.y * 0.5 + bz * period.y
		out.append(Transform3D(
			Basis.IDENTITY.scaled(Vector3(extent.x, THICK, street)),
			Vector3(0.0, Terrain.height_at(0.0, z, _spec) + THICK * 0.5, z)))
	return out


## Roads are drawn, not collided with -- the ground already carries collision,
## and a second surface a few centimetres above it only creates a lip to trip on.
func _build_roads(transforms: Array[Transform3D]) -> void:
	var mesh := BoxMesh.new()
	mesh.size = Vector3.ONE
	var mat := StandardMaterial3D.new()
	mat.albedo_color = _spec.get("road_color", Color(0.11, 0.11, 0.12))
	mat.roughness = 0.85
	mesh.material = mat

	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = mesh
	mm.instance_count = transforms.size()
	for i in transforms.size():
		mm.set_instance_transform(i, transforms[i])

	var mmi := MultiMeshInstance3D.new()
	mmi.name = "Roads"
	mmi.multimesh = mm
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_adopt(mmi)


func _build_ground(extent: Vector2) -> void:
	var built := Terrain.build(_spec, extent, terrain_cell)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = _spec.get("ground_color", Color(0.28, 0.30, 0.26))
	mat.roughness = 0.95

	var mi := MeshInstance3D.new()
	mi.name = "GroundMesh"
	mi.mesh = built["mesh"]
	mi.material_override = mat
	_adopt(mi)
	_adopt(built["body"])


func _place_spawn(extent: Vector2) -> void:
	var marker := Marker3D.new()
	marker.name = "PlayerSpawn"
	var x: float = -extent.x * 0.5 + float(_spec["street_width"]) * 0.5
	var z := 0.0
	marker.position = Vector3(x, Terrain.height_at(x, z, _spec) + 1.2, z)
	_adopt(marker)


# ------------------------------------------------------------------- plumbing
func _adopt(node: Node) -> void:
	node.set_meta(GENERATED, true)
	add_child(node)
	# Deliberately NOT setting owner: a node with no owner is never written into
	# the .tscn, which is what keeps a generated city out of version control.


func _clear() -> void:
	for child in get_children():
		if child.has_meta(GENERATED):
			remove_child(child)
			child.queue_free()


## Exposed so a sky/time-of-day system can drive night lighting without knowing
## anything about how the city was generated.
func facade_materials() -> Array[ShaderMaterial]:
	return _facade_materials
