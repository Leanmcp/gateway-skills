extends Node3D
## Assembles the run: environment, sun, city, player.
##
## Everything here is built in code rather than saved into main.tscn. That is a
## deliberate choice for a procedural project -- a .tscn full of generated nodes
## produces enormous diffs, merge conflicts nobody can read, and a scene file
## that silently disagrees with the generator that was supposed to own it. One
## small scene plus one assembly script keeps the source of truth in one place.

const CityGenerator := preload("res://scripts/city/city_generator.gd")
const Player := preload("res://scripts/player.gd")

## Which city config to build. Overridable from the environment so a headless
## check or a CI job can boot each variant without editing anything:
##   CITY=downtown godot --headless --quit-after 600 res://scenes/main.tscn
@export var city: String = "{{CITY}}"

var _city: Node3D


func _ready() -> void:
	var chosen := OS.get_environment("CITY")
	if chosen != "":
		city = chosen

	_add_environment()
	_add_sun()

	_city = CityGenerator.new()
	_city.name = "City"
	_city.city = city
	add_child(_city)

	_add_player()


func _add_environment() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	var mat := ProceduralSkyMaterial.new()
	mat.sky_top_color = Color(0.28, 0.42, 0.68)
	mat.sky_horizon_color = Color(0.72, 0.78, 0.84)
	mat.ground_bottom_color = Color(0.22, 0.22, 0.24)
	mat.ground_horizon_color = Color(0.62, 0.62, 0.62)
	sky.sky_material = mat
	env.sky = sky
	# Ambient from the sky is what keeps the shaded side of a building from
	# reading as flat black. Without it a city at any sun angle looks wrong.
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.6
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	# Distance haze does most of the work of making a city feel large.
	env.fog_enabled = true
	env.fog_density = 0.0012
	env.fog_light_color = Color(0.72, 0.78, 0.86)

	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)


func _add_sun() -> void:
	var sun := DirectionalLight3D.new()
	sun.name = "Sun"
	sun.rotation_degrees = Vector3(-48.0, -125.0, 0.0)
	sun.light_energy = 1.1
	sun.light_color = Color(1.0, 0.96, 0.88)
	sun.shadow_enabled = true
	# 200 m of shadow is generous for a city you walk through, and shadow
	# distance is the single most expensive knob here -- lower it first if the
	# machine runs hot.
	sun.directional_shadow_max_distance = 200.0
	add_child(sun)


func _add_player() -> void:
	var spawn := _city.get_node_or_null("PlayerSpawn")
	var player := Player.new()
	player.name = "Player"
	add_child(player)
	player.global_position = spawn.global_position if spawn else Vector3(0, 2, 0)
