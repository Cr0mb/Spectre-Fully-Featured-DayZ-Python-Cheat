from __future__ import annotations
import os, sys
sys.dont_write_bytecode = True
os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')
from typing import Dict, List, Tuple, Optional, Any
from Process.esp_config import ESPConfig, get_custom_waypoints_cached
WAYPOINT_CATEGORY_COLORS: Dict[str, Tuple[int, int, int]] = {'CITIES': (255, 255, 120), 'TOWNS': (120, 220, 255), 'VILLAGES': (120, 255, 180), 'MILITARY': (255, 140, 140), 'AIRFIELDS': (255, 200, 120), 'HILLS_MOUNTAINS': (200, 180, 255), 'INDUSTRIAL': (255, 200, 255), 'COASTAL': (160, 220, 255), 'CUSTOM': (255, 255, 255)}
CHERNARUS_LOCATIONS: Dict[str, List[Tuple[str, int, int]]] = {'CITIES': [('Chernogorsk', 6472, 2568), ('Elektrozavodsk', 10196, 2130), ('Novodmitrovsk', 11450, 14450), ('Svetlojarsk', 13850, 13250), ('Zelenogorsk', 2752, 5276)], 'TOWNS': [('Kamenka', 1942, 2242), ('Komarovo', 3663, 2482), ('Balota', 4492, 2445), ('Prigorodki', 7732, 3288), ('Kamyshovo', 12067, 3517), ('Tulga', 12720, 4398), ('Pogorevka', 4451, 6427), ('Rogovo', 4766, 6791), ('Mogilevka', 7556, 5163), ('Kabanino', 5328, 8617), ('Vybor', 3840, 8921), ('Gorka', 9558, 8823)], 'VILLAGES': [('Kamy', 13285, 6475), ('Dubrovka', 10467, 9412), ('Grishino', 5990, 10370), ('Krasnostav', 11210, 12290), ('Stary Sobor', 6030, 7790), ('Novy Sobor', 7140, 7720), ('Vyshnoye', 6530, 6025), ('Guglovo', 8360, 6685), ('Staroye', 10180, 5465), ('Shakhovka', 9812, 6563), ('Msta', 11280, 4620), ('Pusta', 9185, 3130), ('Nizhnoye', 12920, 7985)], 'MILITARY': [('NWAF', 4500, 10200), ('Tisy Base', 1640, 13990), ('Zelenogorsk Base', 2780, 5270), ('Myshkino Base', 2720, 9310), ('Severograd Base', 7790, 12850)], 'AIRFIELDS': [('NWAF Runway', 4500, 10000), ('Balota Airfield', 4560, 2470), ('Krasnostav Airfield', 12035, 12625)], 'HILLS_MOUNTAINS': [('Green Mountain', 3720, 6000), ('Altar', 8150, 11930), ('Devils Castle', 6900, 11400), ('Black Mountain', 10200, 12000), ('Three Valleys', 12850, 6000)], 'INDUSTRIAL': [('Metalurg', 1076, 6630), ('Kometa', 10338, 3562), ('Vyhnoye', 6570, 6060)], 'COASTAL': [('Kamenka', 1942, 2242), ('Komarovo', 3663, 2482), ('Balota', 4492, 2445), ('Chernogorsk', 6472, 2568), ('Elektrozavodsk', 10196, 2130), ('Kamyshovo', 12067, 3517), ('Solnechny', 13395, 6240)]}
LIVONIA_LOCATIONS: Dict[str, List[Tuple[str, int, int]]] = {
    'CITIES': [
        ('Brena', 6618, 11211),
        ('Tarnow', 9328, 10905),
        ('Topolin', 1859, 7331),
        ('Radunin', 7298, 6492),
        ('Nadbor', 6110, 3983),
    ],
    'TOWNS': [
        ('Gliniska', 4993, 9922),
        ('Lukow', 3530, 11967),
        ('Sitnik', 11502, 9573),
        ('Lembork', 8680, 6636),
        ('Radacz', 4008, 7940),
        ('Grabin', 10666, 11026),
    ],
    'VILLAGES': [
        ('Bielawa', 1573, 9677),
        ('Borek', 9807, 8495),
        ('Zapadlisko', 8058, 8712),
        ('Nidek', 6129, 8013),
        ('Adamow', 3076, 6851),
        ('Muratyn', 4568, 6384),
        ('Gieraltow', 11240, 4380),
        ('Zalesie', 896, 5536),
        ('Huta', 5141, 5473),
        ('Olszanka', 4819, 7674),
        ('Lipina', 5942, 6820),
        ('Kolembrody', 8417, 11982),
        ('Karlin', 10073, 6957),
        ('Sobotka', 6257, 10253),
        ('Roztoka', 7695, 5317),
        ('Polana', 3280, 2132),
        ('Dolnik', 11312, 656),
    ],
    'MILITARY': [
        ('Nadbor Military', 5628, 3921),
        ('Nadbor East', 6407, 3802),
        ('Brena Military', 7919, 9715),
        ('Brena North Military', 8144, 10928),
        ('Radunin Military', 9902, 3888),
        ('Kulno Checkpoint', 11150, 2392),
        ('Power Plant', 11512, 7062),
        ('Branzow Castle', 1073, 11419),
    ],
    'AIRFIELDS': [
        ('Lukow Airfield', 3990, 10256),
        ('Gliniska Airfield', 3557, 9862),
    ],
    'HILLS_MOUNTAINS': [
        ('Sowa', 11663, 12064),
        ('Krsnik', 7875, 10081),
        ('Dambog', 577, 1125),
        ('Skala', 2999, 1956),
        ('Swarog', 4855, 2224),
        ('Rodzanica', 8882, 2042),
        ('Piorun', 646, 12159),
        ('Kopa', 5519, 8768),
    ],
    'INDUSTRIAL': [
        ('Quarry', 1182, 8870),
        ('Topolin Industrial', 1668, 7589),
        ('Sawmill', 1663, 3705),
        ('Drewniki', 5835, 5093),
        ('Wrzeszcz', 9043, 4438),
        ('Hrud Rail Yard', 6453, 9371),
        ('Sitnik Industrial West', 11016, 9002),
        ('Sitnik Industrial East', 11377, 9397),
        ('Lakeside Industrial', 11155, 11456),
        ('Power Plant', 11512, 7062),
    ],
    'COASTAL': [
        ('Jantar', 3532, 8955),
        ('Grabinskie Lake', 11249, 10993),
        ('Wolisko', 12369, 10884),
        ('Sitnickie Lake', 11412, 10440),
        ('Brena', 6618, 11211),
        ('Bielawa', 1573, 9677),
    ],
}

SAKHAL_LOCATIONS: Dict[str, List[Tuple[str, int, int]]] = {
    # DayZ Wiki doesn’t currently expose GPS for the two “major towns”
    # (Petropavlovsk-Sakhalinsk, Severomorsk), so this is left empty
    # for you to fill from your own map / GPS later if needed.
    'CITIES': [],

    'TOWNS': [
        ('Aniva', 4600, 1600),          # 046 016
        ('Nogovo', 7900, 7200),         # 079 072
        ('Rudnogorsk', 13400, 4600),    # 134 046
    ],

    'VILLAGES': [
        ('Lesogorovka', 10900, 5600),   # 109 056
        ('Zhupanovo', 5700, 2800),      # 057 028
        ('Tikhoye', 6200, 6600),        # 062 066
        ('Yasnomorsk', 6900, 2000),     # 069 020
        ('Tugur', 1700, 9200),          # 017 092
        ('Dudino', 7800, 7400),         # 078 074
        ('Matrosovo', 14200, 3700),     # 142 037
        ('Kekra', 7100, 11100),         # 071 111
        ('Ayan', 1200, 12300),          # 012 123 (island, but also a “village”-style POI)
        ('Slomanyy', 6300, 8900),       # 063 089
    ],

    'MILITARY': [
        ('Burukan', 2700, 8800),                    # 027 088 – whole peninsula / complex
        ('Military Base (Ice Ridge)', 10300, 6700), # 103 067
        ("Military Base (Wolf's Peak)", 8100, 3300),# 081 033
        ('Sakhalskaj GeoES', 8300, 5000),           # 083 050
        ('Sakhalag', 12100, 5600),                  # 121 056
    ],

    'AIRFIELDS': [
        # Approximated as between Nogovo (079 072) and Dudino (078 074)
        # – tweak if you want the exact runway midpoint.
        ('Nogovo Airfield (approx)', 7900, 7300),
    ],

    'HILLS_MOUNTAINS': [
        ('Odinokiy Vulkan', 10000, 3200),  # 100 032
        ('Troika', 9000, 6000),           # 090 060
        ('Ice Ridge', 10700, 6600),       # 107 066 (ridge itself, not the base)
        ('Storozh', 8700, 2500),          # 087 025
    ],

    'INDUSTRIAL': [
        # These are all heavy-installation / industrial-style locations
        ('Burukan Main Port', 2700, 8800),         # same GPS as Burukan
        ('Sakhalskaj GeoES', 8300, 5000),          # geothermal plant + military
        ('Ice Ridge Industrial', 10300, 6700),     # military base w/ big infrastructure
    ],

    'COASTAL': [
        ('Aniva', 4600, 1600),
        ('Nogovo', 7900, 7200),
        ('Dudino', 7800, 7400),
        ('Tugur', 1700, 9200),
        ('Yasnomorsk', 6900, 2000),
        ('Kekra', 7100, 11100),
        ('Matrosovo', 14200, 3700),
        ('Ayan', 1200, 12300),
        ('Slomanyy', 6300, 8900),
    ],
}

WAYPOINT_CATEGORY_CONFIG_ATTRS: Dict[str, str] = {'CITIES': 'waypoint_show_cities', 'TOWNS': 'waypoint_show_towns', 'VILLAGES': 'waypoint_show_villages', 'MILITARY': 'waypoint_show_military', 'AIRFIELDS': 'waypoint_show_airfields', 'HILLS_MOUNTAINS': 'waypoint_show_hills_mountains', 'INDUSTRIAL': 'waypoint_show_industrial', 'COASTAL': 'waypoint_show_coastal', 'CUSTOM': 'waypoint_show_custom'}
def build_waypoint_labels(cfg: ESPConfig, game: Any, cam_state, screen_w: int, screen_h: int, local_pos: Optional[Tuple[float, float, float]], *, scene: Any) -> Any:
    if not getattr(cfg, 'waypoint_esp_enabled', False):
        return scene
    waypoint_labels: List[Tuple[int, int, str, Tuple[int, int, int]]] = []
    cam_pos = cam_state[0] if cam_state else None
    max_dist = float(getattr(cfg, 'waypoint_max_distance', 0.0) or 0.0)
    max_dist2 = max_dist * max_dist if max_dist > 0.0 else 0.0
    map_name = str(getattr(cfg, 'waypoint_map', 'Chernarus') or 'Chernarus')
    map_key = map_name.lower()
    if map_key.startswith('liv'):
        location_table = LIVONIA_LOCATIONS
    elif map_key.startswith('sakh'):
        location_table = SAKHAL_LOCATIONS
    else:
        location_table = CHERNARUS_LOCATIONS
    for cat_key, places in location_table.items():
        attr_name = WAYPOINT_CATEGORY_CONFIG_ATTRS.get(cat_key)
        if attr_name and (not getattr(cfg, attr_name, True)):
            continue
        color = WAYPOINT_CATEGORY_COLORS.get(cat_key, (255, 255, 255))
        for name, wx, wz in places:
            wy = 0.0
            if local_pos is not None:
                wy = local_pos[1]
            elif cam_pos is not None:
                wy = cam_pos[1]
            world_pos = (float(wx), float(wy), float(wz))
            w2s = game.world_to_screen_state(world_pos, cam_state)
            if not w2s:
                continue
            sx_w, sy_w, depth = w2s
            if depth <= 0.1:
                continue
            dist_m = 0.0
            if local_pos is not None:
                dx = float(wx) - float(local_pos[0])
                dz = float(wz) - float(local_pos[2])
                dist_m = (dx * dx + dz * dz) ** 0.5
            elif cam_pos is not None:
                dx = float(wx) - float(cam_pos[0])
                dz = float(wz) - float(cam_pos[2])
                dist_m = (dx * dx + dz * dz) ** 0.5
            if max_dist2 > 0.0 and dist_m > 0.0 and (dist_m * dist_m > max_dist2):
                continue
            label = name
            if dist_m > 0.0:
                label = f'{name} [{int(dist_m)}m]'
            sx_i = int(max(0, min(screen_w - 1, sx_w)))
            sy_i = int(max(0, min(screen_h - 1, sy_w)))
            waypoint_labels.append((sx_i, sy_i, label, color))
    if getattr(cfg, 'waypoint_show_custom', True):
        color_custom = WAYPOINT_CATEGORY_COLORS.get('CUSTOM', (255, 255, 255))
        for wp in get_custom_waypoints_cached():
            try:
                name = str(wp.get('name', 'Custom'))
                wx = float(wp.get('x', 0.0))
                wz = float(wp.get('z', 0.0))
            except Exception:
                continue
            wy = 0.0
            if local_pos is not None:
                wy = local_pos[1]
            elif cam_pos is not None:
                wy = cam_pos[1]
            world_pos = (wx, wy, wz)
            w2s = game.world_to_screen_state(world_pos, cam_state)
            if not w2s:
                continue
            sx_w, sy_w, depth = w2s
            if depth <= 0.1:
                continue
            dist_m = 0.0
            if local_pos is not None:
                dx = wx - float(local_pos[0])
                dz = wz - float(local_pos[2])
                dist_m = (dx * dx + dz * dz) ** 0.5
            elif cam_pos is not None:
                dx = wx - float(cam_pos[0])
                dz = wz - float(cam_pos[2])
                dist_m = (dx * dx + dz * dz) ** 0.5
            if max_dist2 > 0.0 and dist_m > 0.0 and (dist_m * dist_m > max_dist2):
                continue
            label = name
            if dist_m > 0.0:
                label = f'{name} [{int(dist_m)}m]'
            sx_i = int(max(0, min(screen_w - 1, sx_w)))
            sy_i = int(max(0, min(screen_h - 1, sy_w)))
            waypoint_labels.append((sx_i, sy_i, label, color_custom))
    scene.waypoint_labels = waypoint_labels
    return scene
__all__ = ['WAYPOINT_CATEGORY_COLORS', 'CHERNARUS_LOCATIONS', 'LIVONIA_LOCATIONS', 'SAKHAL_LOCATIONS', 'WAYPOINT_CATEGORY_CONFIG_ATTRS', 'build_waypoint_labels']
