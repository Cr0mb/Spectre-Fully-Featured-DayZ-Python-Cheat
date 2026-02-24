<img width="545" height="568" alt="image" src="https://github.com/user-attachments/assets/7a939e14-5ca3-4186-be86-3b989e7048ae" />


# Spectre

Spectre is an external DayZ ESP / aimbot overlay written in Python, using a custom PyQt5 UI and a pluggable memory backend (user-mode or kernel-mode). It is designed as a research framework for reverse-engineering, visualization, and experimentation with DayZ.

This is the free version from **GHaxLabs.com**

> Disclaimer  
> This does not work with battleye. Integrate your own kernel driver for that.

---

## Feature Overview

### Visual ESP

Core world overlay, fully driven by configuration:

- Global ESP toggle.
- Actor categories:
  - Players
  - Zombies / infected
  - Animals
  - Vehicles
- Additional visuals:
  - Corpses for players and zombies
  - Name text labels per actor type
  - 2D boxes for players and zombies
  - Skeleton drawing for players and zombies
  - Optional head cross / head marker
  - Distance text for players, zombies, and items
- Crosshair overlay toggle.
- World visuals:
  - No-grass toggle
  - World time override (set fixed hour)
  - “Eye” value override (exposure/eye-adapt style override)

All of these are controlled via `ESPConfig` and accessible from the in-game overlay menu.

---

### Item / Loot ESP

Fine-grained item visualization and filtering:

- Global item ESP toggle.
- Per-category visibility toggles:
  - Weapon
  - Ammo
  - Magazine
  - Food
  - Drink
  - Medical
  - Tool
  - Crafting
  - Clothing
  - Backpack
  - Attachment
  - Explosive
  - Vehicle
  - Container
  - Miscellaneous
- Maximum item distance (meters).
- Optional distance text for items.
- Search and filtering:
  - Free-text search (`item_search_filter`) matched against item names.
  - Category filter (`item_search_category_filter`).
- Visual polish:
  - Optional “real clothing colors” for clothing items.
  - Dedicated per-category colors: weapon, ammo, food, drink, medical, etc.
- Item name infrastructure:
  - Item name lists loaded from `Process/item_db.py`.
  - Configurable and cached in `Process/item_esp.py` for performance.

---

### Waypoints and Map Overlay

Built-in map and waypoint system for DayZ (Chernarus by default):

- Waypoint ESP toggle.
- Categories:
  - Cities
  - Towns
  - Villages
  - Military locations
  - Airfields
  - Hills / mountains
  - Industrial areas
  - Coastal areas
  - Custom waypoints
- Map selection (currently `Chernarus` via `waypoint_map`).
- Maximum waypoint distance (meters).
- Category-based colors (`WAYPOINT_CATEGORY_COLORS`):
  - Different colors for city, town, military, airfield, industrial, coastal, custom, etc.
- Custom waypoints:
  - Managed via the UI (add / rename / delete).
  - Persisted as JSON.
  - Used by both the ESP and the menu.

Waypoints and their labels are assembled in `Process/waypoint_esp.py` and integrated into the ESP scene.

---

### Mouse Aimbot, Silent Aim, and Magic Bullet

Spectre ships with a complete external aiming stack tailored to DayZ.

#### Mouse Aimbot

External aimbot driven by Win32 `GetAsyncKeyState` and `mouse_event`:

- Toggleable “Mouse Aimbot”.
- Target classes:
  - Players
  - Zombies
- Target selection:
  - FOV-based filter (`aimbot_fov`).
  - Closest to crosshair logic (`aimbot_closest_to_crosshair`).
- Aim smoothing:
  - Smoothing factor (`aimbot_smooth`) for more natural mouse movement.
- Bones:
  - Head
  - Neck
  - Chest
  - Spine
  - Pelvis
  - Multi-bone mode (cycle / choose among allowed bones).
- Configurable aim key:
  - `aimbot_key` (virtual key code).
  - `aimbot_key_listen` to capture a key directly from the menu.
- Internals:
  - Uses `HEAD_OFFSET_PLAYER` / `HEAD_OFFSET_ZOMBIE` from `Process/ent_esp.py` as a fallback.
  - Calls optional bone helpers on the game object if available.

#### Silent Aim

Silent aim path shares the same target selection as the mouse aimbot but manipulates bullet entities instead of the camera:

- Toggleable via:
  - `silent_aim_enabled`
  - `silent_aim_debug` for verbose logging.
- Implemented in `Features/esp.py` and `Features/mouse_aim.py`:
  - Locates the local bullet from the DayZ bullet list.
  - Reads the bullet’s VisualState position.
  - Writes a new world-space position pointing directly at the selected target.
- Safety and debugging:
  - Uses camera position as a reference.
  - Integrates with world-to-screen state for debugging.
  - Detailed “[SAIMDBG]” logging if debug is enabled.

Silent aim does not move your crosshair; it repositions the bullet to the chosen target inside the simulation.

#### Magic Bullet

Magic bullet is the distance limiter and control layer for silent aim:

- `magic_bullet_max_distance` (meters) restricts how far from the camera silent-aim / magic-bullet logic is allowed to snap bullets.
- If the target is beyond this distance, silent aim is skipped (with debug messages if enabled).
- The same path handles both “silent aim” and “magic bullet” behavior; the naming is reflected in config and code comments.

---

### Player List and Friends

Spectre maintains a player list for UX and filtering:

- Player list rows (name, Steam ID, distance, friend flag).
- Friend support:
  - `friend_steam_ids` list in config.
  - `friend_color_player` for friend highlighting.
- The list is updated in the memory helper and rendered in the PyQt menu.

---

### System / backend features

Spectre’s backend is designed around a clear separation between the overlay and game data:

- External user-mode reader  
  - Attaches to the DayZ process and reads memory using standard Windows APIs (for example `OpenProcess` / `ReadProcessMemory`), wrapped behind a helper layer.  
  - All higher-level features interact with an abstract “game” / “memory helper” object instead of calling Win32 APIs directly.
- Central memory helper  
  - A single helper (for example `ESPMemoryHelper`) is responsible for:
    - Locating the local player, actors, bullets, and items.
    - Producing world-space data used by ESP, aimbot, silent aim, and waypoints.
    - Maintaining the live player list used by the menu.
  - Offsets and game-specific logic are concentrated here, so updating for a new DayZ version is mostly a matter of touching this layer.
- Capture / streaming protection  
  - Optional OBS / capture protection flag (`obs_protection_enabled`) that can adjust how the overlay is presented to capture or streaming software.
- Debug logging  
  - When `debug_logging` is enabled, ESP-side logs are written to a debug file (for example `%TEMP%\gscript_esp_debug.log`) to help diagnose issues with actors, items, or aimbot targeting.

---


### Configuration and Persistence

Configuration is fully data-driven via `Process/esp_config.py`:

- Config file path:
  - `%APPDATA%\GScript\dayz_esp_config.json`
- Waypoints path:
  - `%APPDATA%\GScript\dayz_waypoints.json`
- Highlights:
  - All ESP toggles and distances.
  - Item categories and colors.
  - Aimbot, silent aim, and magic bullet settings.
  - Waypoint settings and map selection.
  - Friend list and friend color.
  - Backend options (`obs_protection_enabled`, `kernel_mode_enabled`, `kernel_fallback_to_usermode`).

Helper functions `load_config`, `save_config`, `load_custom_waypoints`, and `save_custom_waypoints` handle persistence, with caching via `get_custom_waypoints_cached` / `set_custom_waypoints`.
