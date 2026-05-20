extends CharacterBody3D
## First-person walker sized against the city: 1.8 m tall, eyes at 1.65 m.
##
## Every number a designer would want to feel out is @export, so it can be
## changed in the Inspector while the game runs. Tuning movement by editing
## source and relaunching is how movement ends up feeling wrong -- you cannot
## judge a walk speed you have to imagine.

@export_group("Movement")
@export var walk_speed: float = 5.5
@export var sprint_speed: float = 9.0
@export var jump_velocity: float = 7.0
@export var acceleration: float = 12.0
@export var mouse_sensitivity: float = 0.0022

## Cycled with the speed key. Crossing a square kilometre at walking pace to
## check one building is the fastest way to stop checking buildings.
@export var speed_multipliers: PackedFloat32Array = [1.0, 3.0, 8.0]

var _camera: Camera3D
var _pitch: float = 0.0
var _speed_step: int = 0


func _ready() -> void:
	# Layer 2 = player, mask 5 = world + enemy. Set here so the node works
	# whether it is instanced from code or dropped into a scene.
	collision_layer = 2
	collision_mask = 5

	var shape := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.height = 1.8
	capsule.radius = 0.4
	shape.shape = capsule
	shape.position.y = 0.9
	add_child(shape)

	_camera = Camera3D.new()
	_camera.position.y = 1.65
	_camera.current = true
	# A city needs a far plane that reaches the skyline; the default 4000 is
	# fine, but the near plane matters more -- too small and distant geometry
	# z-fights, which reads as flickering building faces.
	_camera.near = 0.1
	_camera.far = 4000.0
	add_child(_camera)

	if not Engine.is_editor_hint():
		Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED:
		rotate_y(-event.relative.x * mouse_sensitivity)
		_pitch = clamp(_pitch - event.relative.y * mouse_sensitivity, -1.5, 1.5)
		_camera.rotation.x = _pitch
	elif event.is_action_pressed("pause"):
		var captured := Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED
		Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE if captured else Input.MOUSE_MODE_CAPTURED)
	elif event is InputEventKey and event.pressed and event.physical_keycode == KEY_U:
		_speed_step = (_speed_step + 1) % speed_multipliers.size()
		print("[player] speed x%.0f" % speed_multipliers[_speed_step])


func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity.y -= ProjectSettings.get_setting("physics/3d/default_gravity", 20.0) * delta
	elif Input.is_action_just_pressed("jump"):
		velocity.y = jump_velocity

	var input := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var dir := (transform.basis * Vector3(input.x, 0.0, input.y)).normalized()
	var speed := walk_speed
	if Input.is_action_pressed("sprint"):
		speed = sprint_speed
	speed *= speed_multipliers[_speed_step]

	# Lerping toward the target rather than snapping is the difference between
	# a body with weight and a camera on rails.
	var target := dir * speed
	velocity.x = move_toward(velocity.x, target.x, acceleration * speed * delta)
	velocity.z = move_toward(velocity.z, target.z, acceleration * speed * delta)

	move_and_slide()
