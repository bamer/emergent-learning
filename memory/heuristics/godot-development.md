# Heuristics: godot-development

Generated from failures, successes, and observations in the **godot-development** domain.

---

## H-106: Never use is_action_just_pressed() on InputEventKey or InputEventMouseButton - only on Input singleton. In _input(), check event.keycode (KEY_W=87, KEY_S=83, KEY_A=65, KEY_D=68, KEY_SPACE=32, KEY_Q=81) or event.button_index directly. Use Input.get_vector() in _physics_process() for continuous movement.

**Confidence**: 0.95
**Source**: observation
**Created**: 2026-02-10

Godot InputEvent types (Key, MouseButton) do NOT have action methods. Action methods are on Input singleton or InputEventAction type. Confusing error: 'Invalid call. Nonexistent function is_action_just_pressed in base InputEventMouseMotion/Key.' Reference: https://docs.godotengine.org/en/latest/tutorials/inputs/inputevent.html

---

## H-107: Key code constants in Godot: WASD (W=87, A=65, S=83, D=68), Arrows (UP=4194320, LEFT=4194319, DOWN=4194322, RIGHT=4194321), Space=32, Q=81 for ultimate. Mouse button: LEFT=1, RIGHT=2, MIDDLE=3.

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-02-10

Godot uses different keycodes for physical vs position keys. Arrows are position keys (high values), WASD are physical keys (low values 65-87). Define constants at top of file for readability.

---

## H-108: Godot project.godot input actions need BOTH keyboard and arrow keys for ui_left/RIGHT/UP/DOWN to work both on WASD and arrow keys. If events array is empty, Input.get_vector() returns ZERO Vector2 and movement won't work.

**Confidence**: 0.95
**Source**: observation
**Created**: 2026-02-10

InputMap actions define reusable action names (ui_left, ui_right, etc.) that map to multiple physical keys. project.godot [input] section should have events array populated with InputEventKey objects for both WASD and arrow keys. Empty events = no input detected.

---

