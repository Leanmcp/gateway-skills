extends RefCounted
## Building typologies: the lookup table that turns a name into a shape.
##
## A typology is a *kind* of building -- a shophouse, a warehouse, a glass
## tower -- described by ranges rather than fixed numbers. The generator rolls
## inside those ranges, so one entry produces a street of related but individual
## buildings, which is what a real block looks like.
##
## Keeping this a plain table has a specific payoff: adding a building kind is
## a data edit that touches no generator code, and every typology automatically
## gets batching, collision and facade shading for free because the generator
## treats them all identically.
##
##   height        metres, min/max, rolled per building
##   width_scale   fraction of the lot frontage actually built on
##   color         base facade colour, jittered slightly per building
##   roof          extra box on top: Vector2(inset, height), zero for none

const TABLE := {
	"rowhouse": {
		"height": Vector2(8.0, 13.0),
		"width_scale": Vector2(0.92, 1.0),
		"color": Color(0.78, 0.74, 0.66),
		"roof": Vector2(0.0, 1.4),
	},
	"warehouse": {
		"height": Vector2(9.0, 14.0),
		"width_scale": Vector2(0.95, 1.0),
		"color": Color(0.50, 0.34, 0.28),
		"roof": Vector2(0.0, 0.0),
	},
	"midrise": {
		"height": Vector2(22.0, 45.0),
		"width_scale": Vector2(0.85, 1.0),
		"color": Color(0.62, 0.60, 0.58),
		"roof": Vector2(1.2, 2.5),
	},
	"tower": {
		"height": Vector2(60.0, 160.0),
		"width_scale": Vector2(0.6, 0.85),
		"color": Color(0.30, 0.38, 0.45),
		"roof": Vector2(2.0, 6.0),
	},
	"podium": {
		"height": Vector2(14.0, 24.0),
		"width_scale": Vector2(0.95, 1.0),
		"color": Color(0.55, 0.55, 0.53),
		"roof": Vector2(0.0, 0.0),
	},
}


## Pick a typology name from a weighted table like [["tower", 0.7], ["podium", 0.3]].
## Weights need not sum to 1 -- they are normalised here, so adding a kind does
## not mean rebalancing every other number in the config.
static func pick(weighted: Array, rng: RandomNumberGenerator) -> String:
	var total := 0.0
	for entry in weighted:
		total += float(entry[1])
	var roll := rng.randf() * total
	for entry in weighted:
		roll -= float(entry[1])
		if roll <= 0.0:
			return entry[0]
	return weighted[0][0]
