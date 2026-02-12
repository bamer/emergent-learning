# Heuristics: godot

Generated from failures, successes, and observations in the **godot** domain.

---

## H-110: Converting free-movement to horizontal shooting requires camera redesign - follow player Y, scroll X continuously

**Confidence**: 0.7
**Source**: orchestration
**Project**: `/home/bamer/shootemup_game`
**Created**: 2026-02-10

R-Type games use camera that tracks player Y but autoscrolls X at fixed speed, different from free-movement camera

---

## H-111: R-Type enemy spawning from fixed X position enables formation patterns

**Confidence**: 0.7
**Source**: orchestration
**Project**: `/home/bamer/shootemup_game`
**Created**: 2026-02-10

Spawn all enemies from right side (x=2200) allows Grid, Line, V-formation patterns for authentic gameplay

---

## H-221: Godot WaveSystem formation-based spawning

**Confidence**: 0.95
**Source**: observation
**Created**: 2026-02-11

Ported from C++ reference project. Use Array[float] for TimeTilWave delays and Array[PackedScene] for WaveScenes with pre-made enemy formations. Signals: wave_started, wave_completed, waves_finished. Key benefit: Designer-friendly waves edited as scenes, not code. Supports wave formations not just random spawning.

---

## H-222: Godot TSCN nodes must have explicit type attribute

**Confidence**: 1.0
**Source**: observation
**Created**: 2026-02-11

In .tscn files, nodes MUST have explicit type='xxx' attribute before export and script properties. Example: CORRECT [node name='WaveSystem' type='Node' parent='.'] WRONG [node name='WaveSystem' parent='.' script='...']. Missing type='Node' caused WaveSystem instantiation failure - enemies not spawning bug.

---

## H-223: Godot signals for decoupled game systems

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-02-11

Enemy emits enemy_died(score: int) signal -> BaseWave tracks enemies_defeated -> wave_cleared signal -> WaveSystem spawns next wave. This eliminates hard dependencies no more get_node_or_null, allows multiple listeners (HUD, ScoreManager, Boss AI). Follows publish-subscribe pattern for cleaner architecture.

---

## H-224: Godot centered sprite and hitbox must both be at (0,0)

**Confidence**: 0.95
**Source**: observation
**Created**: 2026-02-11

When sprite.centered=true: Sprite2D.position must be (0, 0) relative to parent, CollisionShape2D.position must also be (0, 0). Both share same visual center point. Problem: CollisionShape2D with position offset causes misalignment with visual sprite 20cm offset bug. Fix: Set Sprite2D.centered=true, Sprite2D.position=(0,0), CollisionShape2D.position=(0,0).

---

## H-225: Godot Parallax2D for automatic differential scrolling

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-02-11

Use Parallax2D with ParallaxLayer children for automatic differential scrolling. Configuration: Far layer motion_scale=(0.1,0.1), Slow clouds=(0.3,0.3), Fast clouds=(0.5,0.5), Dust=(0.8,0.8), Foreground=(1.0,1.0). Key property: repeat_size=Vector2(1920,1080) for seamless HD looping. Parallax2D automatically handles scrolling based on camera movement - no manual _process updates needed.

---

## H-226: Godot collision layer matrix standard layout

**Confidence**: 0.95
**Source**: observation
**Created**: 2026-02-11

Standard layout: Layer1=Player, Layer2=Enemies, Layer3=Projectiles/Bullets, Layer4=Pickups, Layer5=Walls, Layer10=All. Required config: Projectiles collision_layer=3, collision_mask=2 (detect enemies). Enemies collision_layer=2, collision_mask=4 (detect pickups). Powerups collision_layer=8, collision_mask=1 (detect player). Wrong layer/mask causes collision failure.

---

## H-227: Godot TSCN missing type='Node' causes instantiation failure

**Confidence**: 1.0
**Source**: observation
**Created**: 2026-02-11

WaveSystem failed to spawn enemies due to malformed node definition in Main.tscn. Root cause: Missing type='Node' attribute. Godot couldn't instantiate the node. Script attached but type was missing. Fix: [node name='WaveSystem' type='Node' parent='.']. Result: Enemies now instantiate correctly at positions like (1450, 300) and move left.

---

## H-228: Godot ship sprite quality impacts user feedback

**Confidence**: 1.0
**Source**: observation
**Created**: 2026-02-11

User feedback: sprite du vaisseau ne ressemble pas du tout a un vaisseau et il est tres moche. Change: ship_5.png (ugly, doesn't look like spacecraft) -> ship_10.png (Interceptor-style, fast, sleek spacecraft look). Location: assets/200Starships/Shaded/ship_10.png (220x220). Result: Visual quality significantly improved.

---

## H-229: Godot CanvasLayer with layer=100 for full-screen flash effects

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-02-11

Use CanvasLayer with layer=100 (above everything) for full-screen flash effects. Architecture: Main -> CanvasLayer(layer=100) -> FlashOverlay(ColorRect) with color=Color(1,1,1,0). Lightning trigger: if randf() < 0.002: trigger_lightning(). Sets flash_overlay.modulate.a=0.4 then tweens back to 0.0. Applications: Random lightning, boss alerts, nuke explosions, damage feedback.

---

## H-237: Audio buses must be configured in Project Settings BEFORE implementing volume controls via AudioManager.set_volume()

**Confidence**: 0.95
**Source**: failure
**Created**: 2026-02-12

Godot's AudioServer.get_bus_index() returns -1 for non-existent buses, causing 'Index p_bus = -1 is out of bounds' error when calling set_bus_volume_db(). Must create Master, Music, SFX buses in default_bus_layout.tres or via Project Settings → Audio before implementing volume sliders.

---

## H-238: Prefix unused function parameters with underscore to suppress GDScript warnings

**Confidence**: 0.9
**Source**: success
**Created**: 2026-02-12

GDScript warns on declared but unused parameters. By prefixing with underscore (e.g., _action_name), the compiler recognizes the parameter as intentionally unused and suppresses the warning. This is idiomatic GDScript.

---

## H-239: Use ConfigFile with user:// path for cross-platform game settings persistence

**Confidence**: 0.9
**Source**: success
**Created**: 2026-02-12

ConfigFile provides built-in section-based configuration that automatically handles platform-specific save locations. Using user:// prefix ensures settings are saved in the user's data directory (AppData on Windows, ~/.local on Linux, ~/Library on macOS), surviving game updates and maintaining platform compatibility.

---

## H-247: Complete game pipeline: Assets → Mechanics → Polish → Level Design

**Confidence**: 0.95
**Source**: success
**Created**: 2026-02-12

Full game development pipeline executed autonomously: Phase A (asset integration - backgrounds, projectiles, explosions, power-ups), Phase B (mechanics - ship classes, weapons, shields, bosses), Phase C (polish - audio, optimization), Phase D (level design - waves, scoring). Used parallel task execution via subagents. Total: ~3000 lines of GDScript across 40+ files.

---

