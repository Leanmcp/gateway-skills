extends Node
## Autoload. Registers every input action in code.
##
## Actions can also be defined in project.godot through the editor's Input Map,
## but doing it here means the bindings live in a diffable file, survive a
## merge, and cannot be lost by someone re-saving project settings. It also
## means a fresh clone has working controls before anyone opens the editor.

const ACTIONS := {
	"move_forward": [KEY_W, KEY_UP],
	"move_back": [KEY_S, KEY_DOWN],
	"move_left": [KEY_A, KEY_LEFT],
	"move_right": [KEY_D, KEY_RIGHT],
	"jump": [KEY_SPACE],
	"sprint": [KEY_SHIFT],
	"pause": [KEY_ESCAPE],
}


func _ready() -> void:
	for action in ACTIONS:
		if not InputMap.has_action(action):
			InputMap.add_action(action)
		for key in ACTIONS[action]:
			var ev := InputEventKey.new()
			ev.physical_keycode = key
			InputMap.action_add_event(action, ev)
