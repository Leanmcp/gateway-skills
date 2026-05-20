extends RefCounted
## The ground: one height function, and a mesh derived from it.
##
## `height_at()` is the single most important function in a city generator, and
## the rule that keeps a city coherent is that NOTHING may compute ground height
## any other way. The visible mesh, its collider, every building foundation and
## every spawn point all call this. When they all read one function they cannot
## drift out of agreement -- and drift is exactly what produces buildings
## floating a metre above a hill or a player falling through a slope.
##
## Swapping the analytic hills below for a sampled real-world heightmap is a
## change to this function alone. Every consumer follows for free.

## Smooth radial bumps. Cheap, C1-continuous, and stackable -- two overlapping
## hills add into a ridge rather than fighting.
static func height_at(x: float, z: float, spec: Dictionary) -> float:
	var h := 0.0
	for hill in spec.get("hills", []):
		var p: Vector2 = hill["position"]
		var r: float = hill["radius"]
		var d := Vector2(x, z).distance_to(p)
		if d < r:
			# smoothstep gives a flat top and a flat toe; a raw cosine gives a
			# pointed summit that reads as a tent, not a hill.
			h += hill["height"] * smoothstep(1.0, 0.0, d / r)
	return h


## Build the ground as one mesh plus a matching trimesh collider.
##
## Returns { "mesh": ArrayMesh, "body": StaticBody3D }.
##
## `cell` trades smoothness against cost quadratically: halving it quadruples
## both vertex count and collision build time. 8 m is a good default for a city
## you walk through; go finer only where the terrain is actually the subject.
static func build(spec: Dictionary, extent: Vector2, cell: float) -> Dictionary:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)

	var nx := int(ceil(extent.x / cell))
	var nz := int(ceil(extent.y / cell))
	var x0 := -extent.x * 0.5
	var z0 := -extent.y * 0.5

	for ix in nx:
		for iz in nz:
			var ax := x0 + ix * cell
			var az := z0 + iz * cell
			var bx := ax + cell
			var bz := az + cell
			var p00 := Vector3(ax, height_at(ax, az, spec), az)
			var p10 := Vector3(bx, height_at(bx, az, spec), az)
			var p11 := Vector3(bx, height_at(bx, bz, spec), bz)
			var p01 := Vector3(ax, height_at(ax, bz, spec), bz)
			# Counter-clockwise seen from above is front-facing in Godot.
			_tri(st, p00, p01, p11)
			_tri(st, p00, p11, p10)

	st.generate_normals()
	var mesh: ArrayMesh = st.commit()

	var body := StaticBody3D.new()
	body.name = "Ground"
	body.collision_layer = 1
	body.collision_mask = 0
	var shape := CollisionShape3D.new()
	# Derived from the same mesh, so what you see is exactly what you stand on.
	shape.shape = mesh.create_trimesh_shape()
	body.add_child(shape)

	return {"mesh": mesh, "body": body}


static func _tri(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3) -> void:
	# UVs in metres, so a tiling ground material keeps a constant real-world
	# scale no matter how big the map gets.
	st.set_uv(Vector2(a.x, a.z)); st.add_vertex(a)
	st.set_uv(Vector2(b.x, b.z)); st.add_vertex(b)
	st.set_uv(Vector2(c.x, c.z)); st.add_vertex(c)
