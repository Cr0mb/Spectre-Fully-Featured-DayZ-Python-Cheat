from __future__ import annotations
import json
import os, sys
sys.dont_write_bytecode = True
os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')
from dataclasses import dataclass, asdict, field
_APPDATA = os.getenv('APPDATA') or os.path.expanduser('~\\AppData\\Roaming')
_CONFIG_DIR = os.path.join(_APPDATA, 'GScript')
CONFIG_PATH = os.path.join(_CONFIG_DIR, 'dayz_esp_config.json')
WAYPOINTS_PATH = os.path.join(_CONFIG_DIR, 'dayz_waypoints.json')
@dataclass
class ESPConfig:
    esp_enabled: bool = True
    draw_actors: bool = True
    draw_players: bool = True
    draw_zombies: bool = True
    draw_player_corpses: bool = True
    draw_zombie_corpses: bool = True
    draw_items: bool = True
    draw_vehicles: bool = True
    crosshair_enabled: bool = True
    no_grass_enabled: bool = False
    sethour: bool = False
    seteye: bool = False
    sethour_value: float = 10.0
    seteye_value: float = 10.0
    draw_animal_text: bool = True
    draw_player_text: bool = True
    draw_zombie_text: bool = True
    draw_player_box: bool = False
    draw_zombie_box: bool = False
    debug_logging: bool = False
    aimbot_enabled: bool = False
    aimbot_players: bool = True
    aimbot_zombies: bool = True
    aimbot_fov: int = 250
    aimbot_smooth: float = 8.0
    aimbot_draw_fov: bool = True
    aimbot_key: int = 2
    aimbot_key_listen: bool = False
    aimbot_bone_head: bool = True
    aimbot_bone_neck: bool = False
    aimbot_bone_chest: bool = False
    aimbot_bone_spine: bool = False
    aimbot_bone_pelvis: bool = False
    aimbot_bone_multi: bool = False
    aimbot_closest_to_crosshair: bool = True
    silent_aim_enabled: bool = False
    silent_aim_debug: bool = False
    mouse_aim_max_distance: float = 800.0
    magic_bullet_max_distance: float = 800.0
    draw_head_cross: bool = False
    draw_player_skeleton: bool = True
    draw_player_text: bool = True
    draw_player_box: bool = True
    draw_player_head_cross: bool = False
    draw_zombie_text: bool = True
    draw_zombie_box: bool = False
    draw_zombie_skeleton: bool = True
    draw_zombie_head_cross: bool = False
    draw_items_weapon: bool = True
    draw_items_ammo: bool = True
    draw_items_magazine: bool = True
    draw_items_food: bool = True
    draw_items_drink: bool = True
    draw_items_medical: bool = True
    draw_items_tool: bool = True
    draw_items_crafting: bool = True
    draw_items_clothing: bool = True
    draw_items_backpack: bool = True
    draw_items_attachment: bool = True
    draw_items_explosive: bool = True
    draw_items_vehicle: bool = True
    draw_items_container: bool = True
    draw_items_misc: bool = True
    waypoint_esp_enabled: bool = False
    waypoint_show_cities: bool = True
    waypoint_show_towns: bool = True
    waypoint_show_villages: bool = True
    waypoint_show_military: bool = True
    waypoint_show_airfields: bool = True
    waypoint_show_hills_mountains: bool = True
    waypoint_show_industrial: bool = True
    waypoint_show_coastal: bool = True
    waypoint_show_custom: bool = True
    waypoint_max_distance: float = 5000.0
    waypoint_map: str = 'Chernarus'
    item_max_distance: float = 400.0
    draw_item_distance: bool = True
    draw_player_distance: bool = True
    draw_zombie_distance: bool = True
    item_search_filter: str = ''
    item_search_category_filter: str = ''
    item_show_clothing_colors: bool = True
    friend_steam_ids: list[str] = field(default_factory=list)
    friend_color_player: tuple[int, int, int] = (80, 200, 255)
    item_color_weapon: tuple[int, int, int] = (255, 120, 70)
    item_color_ammo: tuple[int, int, int] = (255, 220, 90)
    item_color_magazine: tuple[int, int, int] = (255, 190, 70)
    item_color_food: tuple[int, int, int] = (120, 230, 120)
    item_color_drink: tuple[int, int, int] = (80, 200, 255)
    item_color_medical: tuple[int, int, int] = (255, 120, 160)
    item_color_tool: tuple[int, int, int] = (255, 180, 110)
    item_color_crafting: tuple[int, int, int] = (210, 210, 120)
    item_color_clothing: tuple[int, int, int] = (190, 140, 255)
    item_color_backpack: tuple[int, int, int] = (120, 170, 255)
    item_color_attachment: tuple[int, int, int] = (255, 200, 130)
    item_color_explosive: tuple[int, int, int] = (255, 80, 80)
    item_color_vehicle: tuple[int, int, int] = (150, 220, 100)
    item_color_container: tuple[int, int, int] = (210, 180, 130)
    item_color_misc: tuple[int, int, int] = (130, 230, 230)
    obs_protection_enabled: bool = True
    def get_item_category_color(self, category: str) -> tuple[int, int, int]:
        key = (category or '').lower()
        if key == 'weapon':
            return self.item_color_weapon
        if key == 'ammo':
            return self.item_color_ammo
        if key == 'magazine':
            return self.item_color_magazine
        if key == 'food':
            return self.item_color_food
        if key == 'drink':
            return self.item_color_drink
        if key == 'medical':
            return self.item_color_medical
        if key == 'tool':
            return self.item_color_tool
        if key == 'crafting':
            return self.item_color_crafting
        if key == 'clothing':
            return self.item_color_clothing
        if key == 'backpack':
            return self.item_color_backpack
        if key == 'attachment':
            return self.item_color_attachment
        if key == 'explosive':
            return self.item_color_explosive
        if key == 'vehicle':
            return self.item_color_vehicle
        if key == 'container':
            return self.item_color_container
        return self.item_color_misc
    def set_item_category_color(self, category: str, rgb: tuple[int, int, int]) -> None:
        if not rgb or len(rgb) != 3:
            return
        r, g, b = (max(0, min(int(c), 255)) for c in rgb)
        key = (category or '').lower()
        if key == 'weapon':
            self.item_color_weapon = (r, g, b)
        elif key == 'ammo':
            self.item_color_ammo = (r, g, b)
        elif key == 'magazine':
            self.item_color_magazine = (r, g, b)
        elif key == 'food':
            self.item_color_food = (r, g, b)
        elif key == 'drink':
            self.item_color_drink = (r, g, b)
        elif key == 'medical':
            self.item_color_medical = (r, g, b)
        elif key == 'tool':
            self.item_color_tool = (r, g, b)
        elif key == 'crafting':
            self.item_color_crafting = (r, g, b)
        elif key == 'clothing':
            self.item_color_clothing = (r, g, b)
        elif key == 'backpack':
            self.item_color_backpack = (r, g, b)
        elif key == 'attachment':
            self.item_color_attachment = (r, g, b)
        elif key == 'explosive':
            self.item_color_explosive = (r, g, b)
        elif key == 'vehicle':
            self.item_color_vehicle = (r, g, b)
        elif key == 'container':
            self.item_color_container = (r, g, b)
        else:
            self.item_color_misc = (r, g, b)
    def to_dict(self) -> dict:
        return asdict(self)
    @classmethod
    def from_dict(cls, data: dict) -> 'ESPConfig':
        data = dict(data or {})
        if 'draw_players' not in data and 'draw_actors' in data:
            data['draw_players'] = data.get('draw_actors', True)
        if 'draw_zombies' not in data and 'draw_actors' in data:
            data['draw_zombies'] = data.get('draw_actors', True)
        kwargs = {}
        for field_name, field_def in cls.__dataclass_fields__.items():
            default = field_def.default
            kwargs[field_name] = data.get(field_name, default)
        return cls(**kwargs)
    def save(self, path: str=CONFIG_PATH) -> None:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception as e:
            print(f'[Config] Failed to save config: {e}')
def load_config(path: str=CONFIG_PATH) -> ESPConfig:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        cfg = ESPConfig()
        cfg.save(path)
        print('[Config] No config file found, created defaults.')
        return cfg
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        cfg = ESPConfig.from_dict(data)
        print('[Config] Loaded config from disk.')
        return cfg
    except Exception as e:
        print(f'[Config] Failed to load config, using defaults: {e}')
        cfg = ESPConfig()
        cfg.save(path)
        return cfg
def load_custom_waypoints(path: str=WAYPOINTS_PATH) -> list[dict]:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and isinstance(data.get('waypoints'), list):
            return data['waypoints']
    except Exception as e:
        print(f'[Waypoints] Failed to load custom waypoints: {e}')
    return []
def save_custom_waypoints(wps: list[dict], path: str=WAYPOINTS_PATH) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        payload = {'waypoints': wps}
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)
    except Exception as e:
        print(f'[Waypoints] Failed to save custom waypoints: {e}')
_custom_waypoints_cache: list[dict] | None = None
def get_custom_waypoints_cached() -> list[dict]:
    global _custom_waypoints_cache
    if _custom_waypoints_cache is None:
        _custom_waypoints_cache = load_custom_waypoints()
    return _custom_waypoints_cache
def set_custom_waypoints(wps: list[dict]) -> None:
    global _custom_waypoints_cache
    _custom_waypoints_cache = list(wps)
    save_custom_waypoints(_custom_waypoints_cache)