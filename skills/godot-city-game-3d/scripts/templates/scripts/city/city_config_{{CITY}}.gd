extends RefCounted
## {{CITY_TITLE}}: what goes where.
##
## This file is DATA. It contains no logic, and the generator contains no
## knowledge of {{CITY_TITLE}}. That separation is what lets a second city be a
## new file rather than a fork of the generator -- and it is why changing one
## number here re-rhythms a square kilometre without touching any code.
##
## Two functions make up the contract the generator relies on:
##   spec()        -> Dictionary of everything global to the city
##   district_at() -> which district a given block belongs to

const DOWNTOWN := "downtown"
const INDUSTRIAL := "industrial"
const RESIDENTIAL := "residential"


static func spec() -> Dictionary:
	return {
		"display_name": "{{CITY_TITLE}}",
		# Any fixed integer. The same seed always rebuilds the identical city,
		# which is what makes the level reproducible and lets you iterate on the
		# rules instead of on placement. Pick something meaningful; it is also
		# how you shuffle the whole city when you want a different one.
		"seed": 1849,

		"blocks": Vector2i(9, 7),
		"block_size": Vector2(120.0, 80.0),
		"street_width": 22.0,
		"sidewalk_width": 4.0,
		# Frontage of one lot along the block edge. Smaller means a finer,
		# older-feeling grain; larger means slabs.
		"lot_frontage": 8.0,

		"road_color": Color(0.11, 0.11, 0.12),
		"ground_color": Color(0.28, 0.30, 0.26),

		# Radial bumps, in world metres. Empty for a flat city.
		"hills": [
			{"position": Vector2(-180.0, -140.0), "radius": 320.0, "height": 42.0},
			{"position": Vector2(210.0, -60.0), "radius": 260.0, "height": 28.0},
		],

		"districts": {
			DOWNTOWN: {
				# How deep from the block edge the buildings run.
				"depth": 30.0,
				# Chance a lot is left empty -- gaps are what stop a street wall
				# from reading as one extruded ribbon.
				"gap_chance": 0.04,
				"types": [["tower", 0.45], ["midrise", 0.4], ["podium", 0.15]],
			},
			INDUSTRIAL: {
				"depth": 34.0,
				"gap_chance": 0.15,
				"types": [["warehouse", 0.8], ["podium", 0.2]],
			},
			RESIDENTIAL: {
				"depth": 22.0,
				"gap_chance": 0.06,
				"types": [["rowhouse", 0.85], ["midrise", 0.15]],
			},
		},
	}


## Blocks are addressed by integer grid coordinates, origin at the north-west
## corner. Keeping district assignment a pure function of (bx, bz) means it is
## deterministic, trivially testable, and easy to redraw -- a district map is
## just a different set of comparisons here.
static func district_at(bx: int, bz: int, blocks_x: int, blocks_z: int) -> String:
	var cx := blocks_x / 2
	var cz := blocks_z / 2
	if absi(bx - cx) <= 1 and absi(bz - cz) <= 1:
		return DOWNTOWN
	if bx >= blocks_x - 2:
		return INDUSTRIAL
	return RESIDENTIAL
