# Spectre Overlay / ESP Framework

ZFusion is a Python-based external overlay and visualization framework for reverse-engineering and experimentation with 3D games.  
It renders a configurable 2D overlay (entities, items, waypoints, etc.) on top of a running game using a custom GUI, and reads game state through an external memory helper.

 **Disclaimer**  
> This project is for educational and research purposes only (graphics, UI, and reverse-engineering experiments).  
> This will not work with battleye. Integrate your own kernel driver for that.

---

## Features

- **Entity Overlay**
  - Toggleable master ESP switch
  - Separate categories for:
    - Player entities (name, box, skeleton, head marker, distance, corpses)
    - NPC / zombie-like entities (name, box, skeleton, head marker, distance, corpses)
    - Animal / wildlife entities
    - Vehicle-type entities
  - Distance-based drawing, visibility culling, and configurable max range

-  **Item & Loot Visualization**
  - Item ESP with categorization (weapons, food, medical, clothing, tools, containers, misc, etc.)
  - Fine-grained toggles per item category
  - Item name database and helper functions for consistent display
  - Optional debug logging for item names and filters

-  **Map & Waypoints System**
  - Built-in location/region data for a large open-world style map
  - Category-based waypoints (cities, towns, villages, military, airfields, industrial, coastal, etc.)
  - Custom waypoints:
    - Saved and loaded from JSON in the user config directory
    - Editable via the in-game menu
  - Distinct colors per waypoint category for fast recognition

-  **Mouse-Assisted Targeting (Experimental)**
  - External mouse movement helper driven by game data
  - Head/neck position helpers using bone queries or smart fallbacks
  - Configurable maximum distance and smoothing parameters
  - Implemented purely via user-mode APIs (`GetAsyncKeyState`, `mouse_event`, etc.)

-  **Configurable GUI Menu**
  - Overlay menu is drawn using **PyQt5** and **QtOpenGL**
  - Sidebar navigation for:
    - ESP settings (per entity type)
    - Item filters
    - Waypoints & map categories
    - Misc / visual tweaks (e.g., brightness/time controls, “no grass” toggle, capture/stream protection)
  - Custom theme branded as **“ZFusion | GHaxLabs.com”** with:
    - Modern layout
    - Grouped sections
    - Slider controls for distances/FOV/smoothing
    - Support for custom fonts and colors (see `menu.py`)

- **Config & Persistence**
  - All configuration stored in the user’s roaming profile directory (e.g. `%APPDATA%\GScript\…`)
  - JSON config files:
    - Main ESP config
    - Custom waypoint list
  - Helper functions to load/save configs with graceful fallback if files are missing or corrupted
