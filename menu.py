from __future__ import annotations
import os, sys
sys.dont_write_bytecode = True
os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')
from typing import Callable, Dict, List, Tuple
import ctypes
from ctypes import wintypes
import math
from Process.esp_config import ESPConfig, get_custom_waypoints_cached, set_custom_waypoints
from PyQt5 import QtGui, QtCore, QtWidgets
user32 = ctypes.windll.user32
_MENU_OPTIONS: List[Dict[str, str]] = [{'label': 'ESP MASTER', 'attr': 'esp_enabled', 'group': 'ESP'}, {'label': 'Player ESP', 'attr': 'draw_players', 'group': 'ESP'}, {'label': '   Player Name', 'attr': 'draw_player_text', 'group': 'ESP'}, {'label': '   Player Box', 'attr': 'draw_player_box', 'group': 'ESP'}, {'label': '   Player Skeleton', 'attr': 'draw_player_skeleton', 'group': 'ESP'}, {'label': '   Player Head Cross', 'attr': 'draw_player_head_cross', 'group': 'ESP'}, {'label': '   Player Distance', 'attr': 'draw_player_distance', 'group': 'ESP'}, {'label': '   Player Corpses', 'attr': 'draw_player_corpses', 'group': 'ESP'}, {'label': 'Zombie ESP', 'attr': 'draw_zombies', 'group': 'ESP'}, {'label': '   Zombie Name', 'attr': 'draw_zombie_text', 'group': 'ESP'}, {'label': '   Zombie Box', 'attr': 'draw_zombie_box', 'group': 'ESP'}, {'label': '   Zombie Skeleton', 'attr': 'draw_zombie_skeleton', 'group': 'ESP'}, {'label': '   Zombie Head Cross', 'attr': 'draw_zombie_head_cross', 'group': 'ESP'}, {'label': '   Zombie Distance', 'attr': 'draw_zombie_distance', 'group': 'ESP'}, {'label': '   Zombie Corpses', 'attr': 'draw_zombie_corpses', 'group': 'ESP'}, {'label': 'Animal ESP', 'attr': 'draw_animal_text', 'group': 'ESP'}, {'label': 'Vehicle ESP', 'attr': 'draw_vehicles', 'group': 'ESP'}, {'label': 'Crosshair', 'attr': 'crosshair_enabled', 'group': 'ESP'}, {'label': 'Mouse Aimbot', 'attr': 'aimbot_enabled', 'group': 'Aimbot'}, {'label': 'Magic Bullet', 'attr': 'silent_aim_enabled', 'group': 'Aimbot'}, {'label': 'Aim at Players', 'attr': 'aimbot_players', 'group': 'Aimbot'}, {'label': 'Aim at Zombies', 'attr': 'aimbot_zombies', 'group': 'Aimbot'}, {'label': 'Draw FOV Circle', 'attr': 'aimbot_draw_fov', 'group': 'Aimbot'}, {'label': 'Draw Crosshair', 'attr': 'aimbot_draw_fov', 'group': 'Aimbot'}, {'label': 'Aim Key Listener', 'attr': 'aimbot_key_listen', 'group': 'Aimbot'}, {'label': 'Item ESP (All)', 'attr': 'draw_items', 'group': 'Items'}, {'label': 'Item Distance ESP', 'attr': 'draw_item_distance', 'group': 'Items'}, {'label': 'Show Clothing Colors', 'attr': 'item_show_clothing_colors', 'group': 'Items'}, {'label': 'Weapons', 'attr': 'draw_items_weapon', 'group': 'Items'}, {'label': 'Ammo', 'attr': 'draw_items_ammo', 'group': 'Items'}, {'label': 'Magazines', 'attr': 'draw_items_magazine', 'group': 'Items'}, {'label': 'Food', 'attr': 'draw_items_food', 'group': 'Items'}, {'label': 'Drink', 'attr': 'draw_items_drink', 'group': 'Items'}, {'label': 'Medical', 'attr': 'draw_items_medical', 'group': 'Items'}, {'label': 'Tools', 'attr': 'draw_items_tool', 'group': 'Items'}, {'label': 'Crafting / Base', 'attr': 'draw_items_crafting', 'group': 'Items'}, {'label': 'Clothing', 'attr': 'draw_items_clothing', 'group': 'Items'}, {'label': 'Backpacks', 'attr': 'draw_items_backpack', 'group': 'Items'}, {'label': 'Attachments', 'attr': 'draw_items_attachment', 'group': 'Items'}, {'label': 'Explosives', 'attr': 'draw_items_explosive', 'group': 'Items'}, {'label': 'Vehicle Parts', 'attr': 'draw_items_vehicle', 'group': 'Items'}, {'label': 'Containers', 'attr': 'draw_items_container', 'group': 'Items'}, {'label': 'Misc Items', 'attr': 'draw_items_misc', 'group': 'Items'}, {'label': 'Waypoint ESP', 'attr': 'waypoint_esp_enabled', 'group': 'Waypoints'}, {'label': '   Cities', 'attr': 'waypoint_show_cities', 'group': 'Waypoints'}, {'label': '   Towns', 'attr': 'waypoint_show_towns', 'group': 'Waypoints'}, {'label': '   Villages', 'attr': 'waypoint_show_villages', 'group': 'Waypoints'}, {'label': '   Military', 'attr': 'waypoint_show_military', 'group': 'Waypoints'}, {'label': '   Airfields', 'attr': 'waypoint_show_airfields', 'group': 'Waypoints'}, {'label': '   Hills / Mountains', 'attr': 'waypoint_show_hills_mountains', 'group': 'Waypoints'}, {'label': '   Industrial', 'attr': 'waypoint_show_industrial', 'group': 'Waypoints'}, {'label': '   Coastal', 'attr': 'waypoint_show_coastal', 'group': 'Waypoints'}, {'label': '   Custom (Saved)', 'attr': 'waypoint_show_custom', 'group': 'Waypoints'}, {'label': 'No Grass', 'attr': 'no_grass_enabled', 'group': 'System'}, {'label': 'OBS Protect', 'attr': 'obs_protection_enabled', 'group': 'System'}]
_ITEM_ATTR_TO_CATEGORY: Dict[str, str] = {'draw_items_weapon': 'Weapon', 'draw_items_ammo': 'Ammo', 'draw_items_magazine': 'Magazine', 'draw_items_food': 'Food', 'draw_items_drink': 'Drink', 'draw_items_medical': 'Medical', 'draw_items_tool': 'Tool', 'draw_items_crafting': 'Crafting', 'draw_items_clothing': 'Clothing', 'draw_items_backpack': 'Backpack', 'draw_items_attachment': 'Attachment', 'draw_items_explosive': 'Explosive', 'draw_items_vehicle': 'Vehicle', 'draw_items_container': 'Container', 'draw_items_misc': 'Misc'}
_ITEM_SEARCH_CATEGORY_LIST: list[str] = list(dict.fromkeys(_ITEM_ATTR_TO_CATEGORY.values()))
_ITEM_COLOR_PALETTE: list[tuple[int, int, int]] = [(255, 120, 70), (255, 220, 90), (120, 230, 120), (80, 200, 255), (255, 120, 160), (190, 140, 255), (130, 230, 230), (255, 255, 255)]
_AIMBOT_SLIDERS = [
    {'label': 'Aimbot FOV', 'attr': 'aimbot_fov', 'min': 50.0, 'max': 800.0, 'step': 10.0},
    {'label': 'Aimbot Smooth', 'attr': 'aimbot_smooth', 'min': 5.0, 'max': 10.0, 'step': 0.01},
    {'label': 'Mouse Aim Max Dist (m)', 'attr': 'mouse_aim_max_distance', 'min': 50.0, 'max': 1000.0, 'step': 10.0},
    {'label': 'Magic Bullet Max Dist (m)', 'attr': 'magic_bullet_max_distance', 'min': 50.0, 'max': 1000.0, 'step': 10.0},
]

_SYSTEM_SLIDERS = [
    {'label': 'World Time (hour)', 'attr': 'sethour_value', 'min': 0.0, 'max': 10.0, 'step': 0.1},
    {'label': 'Brightness', 'attr': 'seteye_value', 'min': 0.0, 'max': 10.0, 'step': 0.1},
]
_BONE_OPTIONS: List[Tuple[str, str]] = [('Head', 'aimbot_bone_head'), ('Neck', 'aimbot_bone_neck'), ('Chest', 'aimbot_bone_chest'), ('Spine', 'aimbot_bone_spine'), ('Pelvis', 'aimbot_bone_pelvis')]
_WAYPOINT_MAP_OPTIONS: List[str] = ['Chernarus', 'Livonia', 'Sakhal']
def _build_tabs() -> List[Tuple[str, List[Dict[str, str]]]]:
    tabs: Dict[str, List[Dict[str, str]]] = {}
    for opt in _MENU_OPTIONS:
        tabs.setdefault(opt['group'], []).append(opt)
    order = ['Aimbot', 'ESP', 'Items', 'Item Search', 'Players', 'Waypoints', 'System']
    out: List[Tuple[str, List[Dict[str, str]]]] = []
    for name in order:
        if name in ('Item Search', 'Players'):
            out.append((name, []))
        elif name in tabs:
            out.append((name, tabs[name]))
    for name in tabs.keys():
        if name not in order:
            out.append((name, tabs[name]))
    return out
_TABS = _build_tabs()

# Added: System tab toggles for world time and eye accommodation
_MENU_OPTIONS.extend([
    {'label': 'Set Hour (bright daytime)', 'attr': 'sethour', 'group': 'System'},
    {'label': 'Brightness', 'attr': 'seteye', 'group': 'System'},
])
_TABS = _build_tabs()

def _pick_item_category_color(attr: str, cfg: ESPConfig) -> None:
    global _active_color_attr, _color_slider_dragging
    category = _ITEM_ATTR_TO_CATEGORY.get(attr)
    if not category:
        return
    if _active_color_attr == attr:
        _active_color_attr = None
        _color_slider_dragging = None
        return
    _active_color_attr = attr
    _color_slider_dragging = None
def _get_item_category_rgb(attr: str, cfg: ESPConfig) -> tuple[int, int, int]:
    category = _ITEM_ATTR_TO_CATEGORY.get(attr)
    if not category:
        return (255, 255, 255)
    try:
        if hasattr(cfg, 'get_item_category_color'):
            r, g, b = cfg.get_item_category_color(category)
        else:
            field_name = f'item_color_{category.lower()}'
            rgb = getattr(cfg, field_name, (255, 255, 255))
            r, g, b = rgb
    except Exception:
        return (255, 255, 255)
    return (int(r), int(g), int(b))
def _set_item_category_rgb(attr: str, cfg: ESPConfig, rgb: tuple[int, int, int]) -> None:
    category = _ITEM_ATTR_TO_CATEGORY.get(attr)
    if not category:
        return
    r, g, b = rgb
    r = max(0, min(int(r), 255))
    g = max(0, min(int(g), 255))
    b = max(0, min(int(b), 255))
    try:
        if hasattr(cfg, 'set_item_category_color'):
            cfg.set_item_category_color(category, (r, g, b))
        else:
            field_name = f'item_color_{category.lower()}'
            setattr(cfg, field_name, (r, g, b))
        try:
            cfg.save()
        except Exception:
            pass
    except Exception:
        pass
def _draw_item_color_picker(painter: QtGui.QPainter, draw_text: Callable[[QtGui.QPainter, int, int, str, int, int, int], None], content_x: int, content_y: int, content_w: int, content_h: int, cfg: ESPConfig) -> None:
    global _color_slider_dragging
    if _active_color_attr is None or _active_color_attr not in _ITEM_ATTR_TO_CATEGORY:
        return
    attr = _active_color_attr
    category = _ITEM_ATTR_TO_CATEGORY.get(attr, 'Item')
    mx, my = _mouse_pos()
    panel_margin = BTN_INNER_MARGIN
    panel_w = content_w - 2 * panel_margin
    panel_h = 90
    panel_x = content_x + panel_margin
    panel_y = content_y + content_h - panel_h - 10
    _fill_rect(painter, panel_x, panel_y, panel_w, panel_h, THEME['panel_2'])
    _box(painter, panel_x, panel_y, panel_w, panel_h, THEME['divider'])
    title = f'Color: {category}'
    draw_text(painter, panel_x + 8, panel_y + 8, title, *THEME['text'])
    r, g, b = _get_item_category_rgb(attr, cfg)
    preview_w = 40
    preview_h = 20
    preview_x = panel_x + panel_w - preview_w - 10
    preview_y = panel_y + 8
    _fill_rect(painter, preview_x, preview_y, preview_w, preview_h, (r, g, b))
    _box(painter, preview_x, preview_y, preview_w, preview_h, THEME['border'])
    labels = ['R', 'G', 'B']
    values = [r, g, b]
    slider_left = panel_x + 40
    slider_right = panel_x + panel_w - 20
    slider_w = max(40, slider_right - slider_left)
    slider_start_y = panel_y + 34
    slider_spacing = 18
    track_h = 6
    for i, (label, value) in enumerate(zip(labels, values)):
        sy = slider_start_y + i * slider_spacing
        sx = slider_left
        sw = slider_w
        value = max(0, min(255, int(value)))
        _fill_rect(painter, sx, sy, sw, track_h, THEME['btn_bg'])
        t = value / 255.0 if sw > 0 else 0.0
        filled_w = int(sw * t)
        if filled_w > 0:
            if label == 'R':
                fill_rgb = (255, 120, 120)
            elif label == 'G':
                fill_rgb = (120, 230, 120)
            else:
                fill_rgb = (120, 190, 255)
            _fill_rect(painter, sx, sy, filled_w, track_h, fill_rgb)
        _box(painter, sx, sy - 3, sw, track_h + 6, THEME['divider'])
        knob_x = sx + filled_w
        knob_r = 5
        knob_rect = QtCore.QRect(int(knob_x - knob_r), int(sy + track_h // 2 - knob_r), int(knob_r * 2), int(knob_r * 2))
        knob_key = f'color_{label}'
        knob_col = THEME['accent_2'] if _color_slider_dragging == knob_key else (220, 220, 230)
        painter.setPen(_pen(THEME['border'], 1))
        painter.setBrush(QtGui.QColor(*knob_col))
        painter.drawEllipse(knob_rect)
        draw_text(painter, panel_x + 10, sy - 4, label, *THEME['muted'])
        draw_text(painter, sx + sw + 6, sy - 4, str(value), *THEME['muted'])
        inside_slider = sx <= mx <= sx + sw and sy - 4 <= my <= sy + track_h + 4
        if inside_slider and _mouse_down():
            _color_slider_dragging = knob_key
        if not _mouse_down() and _color_slider_dragging == knob_key:
            _color_slider_dragging = None
        if _color_slider_dragging == knob_key and sw > 0:
            t = (mx - sx) / float(sw)
            t = max(0.0, min(1.0, t))
            new_val = int(round(t * 255.0))
            if label == 'R':
                r = new_val
            elif label == 'G':
                g = new_val
            else:
                b = new_val
            _set_item_category_rgb(attr, cfg, (r, g, b))
def _get_tab_items(tab_index: int, cfg: ESPConfig) -> List[Dict[str, str]]:
    if not 0 <= tab_index < len(_TABS):
        return []
    name, items = _TABS[tab_index]
    if name == 'Item Search':
        return []
    if name == 'Aimbot':
        return items
    if name == 'ESP':
        items_by_attr: Dict[str, Dict[str, str]] = {opt['attr']: opt for opt in items}
        ordered_attrs: List[str] = []
        def add_if_present(attr: str) -> None:
            if attr in items_by_attr and attr not in ordered_attrs:
                ordered_attrs.append(attr)
        add_if_present('esp_enabled')
        add_if_present('draw_animal_text')
        add_if_present('draw_players')
        add_if_present('draw_zombies')
        if getattr(cfg, 'draw_players', False):
            add_if_present('draw_player_text')
            add_if_present('draw_player_box')
            add_if_present('draw_player_skeleton')
            add_if_present('draw_player_head_cross')
            add_if_present('draw_player_distance')
            add_if_present('draw_player_corpses')
        if getattr(cfg, 'draw_zombies', False):
            add_if_present('draw_zombie_text')
            add_if_present('draw_zombie_box')
            add_if_present('draw_zombie_skeleton')
            add_if_present('draw_zombie_head_cross')
            add_if_present('draw_zombie_distance')
            add_if_present('draw_zombie_corpses')
        add_if_present('draw_vehicles')
        add_if_present('draw_items')
        add_if_present('crosshair_enabled')
        return [items_by_attr[a] for a in ordered_attrs if a in items_by_attr]
    return items
def _draw_item_search_tab(painter: QtGui.QPainter, draw_text: Callable[[QtGui.QPainter, int, int, str, int, int, int], None], content_x: int, content_y: int, content_w: int, content_h: int, cfg: ESPConfig) -> None:
    global _item_search_hover_index, _item_search_scroll_offset, _scroll_offset_item_search, _item_search_drag_slider
    mx, my = _mouse_pos()
    raw_items = _item_search_items
    raw_cats = _item_search_item_categories
    margin = BTN_INNER_MARGIN
    inner_x = content_x + margin
    inner_y = content_y + 28
    inner_w = content_w - 2 * margin
    inner_h = content_h - (inner_y - content_y) - 10
    if inner_w <= 40 or inner_h <= 40:
        return
    _fill_rect(painter, inner_x, inner_y, inner_w, inner_h, (24, 24, 36))
    _box(painter, inner_x, inner_y, inner_w, inner_h, THEME['divider'])
    bar_h = 22
    bar_x = inner_x + 4
    bar_y = inner_y + 4
    bar_w = inner_w - 8
    _fill_rect(painter, bar_x, bar_y, bar_w, bar_h, (30, 30, 48))
    _box(painter, bar_x, bar_y, bar_w, bar_h, THEME['divider'])
    active_filter = getattr(cfg, 'item_search_filter', '') or ''
    has_filter = bool(active_filter)
    filter_label = active_filter if has_filter else 'All items'
    pill_x = bar_x + 6
    pill_y = bar_y + 3
    base_w = 14 + len(filter_label) * 7
    pill_w = min(bar_w // 2, max(110, base_w))
    pill_h = bar_h - 6
    pill_bg = (70, 50, 90) if has_filter else (40, 40, 60)
    pill_border = THEME['accent_2'] if has_filter else THEME['divider']
    _fill_rect(painter, pill_x, pill_y, pill_w, pill_h, pill_bg)
    _box(painter, pill_x, pill_y, pill_w, pill_h, pill_border)
    draw_text(painter, pill_x + 6, pill_y + 5, f'Filter: {filter_label}', 255, 255, 255)
    pill_hover = pill_x <= mx <= pill_x + pill_w and pill_y <= my <= pill_y + pill_h
    if has_filter and pill_hover and _mouse_clicked():
        cfg.item_search_filter = ''
        try:
            cfg.save()
        except Exception:
            pass
        _item_search_scroll_offset = 0
        _scroll_offset_item_search = 0
        active_filter = ''
        has_filter = False
    category_filter = getattr(cfg, 'item_search_category_filter', '') or ''
    if category_filter and category_filter not in _ITEM_SEARCH_CATEGORY_LIST:
        category_filter = ''
    has_cat_filter = bool(category_filter)
    category_label = category_filter if has_cat_filter else 'All categories'
    cat_pill_x = pill_x + pill_w + 8
    cat_pill_y = pill_y
    cat_text = f'Category: {category_label}'
    cat_base_w = 14 + len(cat_text) * 7
    max_cat_pill_w = max(100, bar_w - (cat_pill_x - bar_x) - 80)
    cat_pill_w = min(max_cat_pill_w, cat_base_w)
    cat_pill_h = pill_h
    cat_bg = (50, 70, 90) if has_cat_filter else (40, 40, 60)
    cat_border = THEME['accent'] if has_cat_filter else THEME['divider']
    _fill_rect(painter, cat_pill_x, cat_pill_y, cat_pill_w, cat_pill_h, cat_bg)
    _box(painter, cat_pill_x, cat_pill_y, cat_pill_w, cat_pill_h, cat_border)
    draw_text(painter, cat_pill_x + 6, cat_pill_y + 5, cat_text, 255, 255, 255)
    cat_hover = cat_pill_x <= mx <= cat_pill_x + cat_pill_w and cat_pill_y <= my <= cat_pill_y + cat_pill_h
    if cat_hover and _mouse_clicked():
        try:
            categories = _ITEM_SEARCH_CATEGORY_LIST
            next_cat = ''
            if categories:
                if category_filter and category_filter in categories:
                    idx = categories.index(category_filter)
                    if idx + 1 < len(categories):
                        next_cat = categories[idx + 1]
                    else:
                        next_cat = ''
                else:
                    next_cat = categories[0]
            cfg.item_search_category_filter = next_cat
            try:
                cfg.save()
            except Exception:
                pass
            _item_search_scroll_offset = 0
            _scroll_offset_item_search = 0
        except Exception:
            pass
    items = list(raw_items)
    cats = list(raw_cats) if isinstance(raw_cats, list) else []
    if not cats or len(cats) != len(items):
        cats = ['' for _ in items]
    if category_filter:
        items = [lab for lab, cat in zip(items, cats) if cat == category_filter]
    total_items = len(items)
    info_text = f'{total_items} item(s)'
    info_x = bar_x + bar_w - (len(info_text) * 7 + 8)
    draw_text(painter, info_x, pill_y + 5, info_text, *THEME['muted'])
    hint_y = bar_y + bar_h + 4
    draw_text(painter, inner_x + 8, hint_y, 'Click an item name to focus it in Item ESP.', *THEME['dim'])
    list_top = hint_y + 8
    list_bottom = inner_y + inner_h - 10
    row_h = 22
    if list_bottom <= list_top + row_h:
        return
    list_h = list_bottom - list_top
    max_rows = list_h // row_h
    if max_rows <= 1:
        return
    usable_rows = max_rows - 1
    list_x = inner_x + 8
    list_w = inner_w - 16
    try:
        _item_search_scroll_offset = int(_item_search_scroll_offset)
    except Exception:
        _item_search_scroll_offset = 0
    try:
        _scroll_offset_item_search = int(_scroll_offset_item_search)
    except Exception:
        _scroll_offset_item_search = _item_search_scroll_offset
    if _scroll_offset_item_search != _item_search_scroll_offset:
        _item_search_scroll_offset = _scroll_offset_item_search
    max_offset = max(0, len(items) - usable_rows)
    if _item_search_scroll_offset < 0:
        _item_search_scroll_offset = 0
    if _item_search_scroll_offset > max_offset:
        _item_search_scroll_offset = max_offset
    _scroll_offset_item_search = _item_search_scroll_offset
    all_x = list_x
    all_y = list_top
    all_w = list_w
    all_h = row_h
    hovered_all = all_x <= mx <= all_x + all_w and all_y <= my <= all_y + all_h
    is_all_selected = active_filter == ''
    if is_all_selected:
        all_bg = (80, 60, 110)
    else:
        all_bg = (55, 55, 78) if hovered_all else (40, 40, 60)
    _fill_rect(painter, all_x, all_y, all_w, all_h, all_bg)
    _box(painter, all_x, all_y, all_w, all_h, THEME['divider'])
    draw_text(painter, all_x + 8, all_y + 6, 'Show All Items', 255, 255, 255)
    if hovered_all and _mouse_clicked() and (not is_all_selected):
        cfg.item_search_filter = ''
        try:
            cfg.save()
        except Exception:
            pass
        _item_search_scroll_offset = 0
        _scroll_offset_item_search = 0
        active_filter = ''
    base_y = all_y + all_h + 2
    items_start = _item_search_scroll_offset
    visible_items = items[items_start:items_start + usable_rows]
    _item_search_hover_index = None
    if not items:
        empty_y = base_y + 8
        draw_text(painter, list_x, empty_y, 'No nearby items detected yet.', *THEME['dim'])
    else:
        for vis_idx, label in enumerate(visible_items):
            global_idx = items_start + vis_idx
            ry = base_y + vis_idx * row_h
            rx = list_x
            rw = list_w
            rh = row_h
            hovered = rx <= mx <= rx + rw and ry <= my <= ry + rh
            is_selected = label == active_filter
            if is_selected:
                row_bg = (90, 60, 120)
            else:
                row_bg = (60, 60, 88) if hovered else (35, 35, 55)
            _fill_rect(painter, rx, ry, rw, rh, row_bg)
            _box(painter, rx, ry, rw, rh, THEME['divider'])
            idx_label = f'{global_idx + 1:02d}'
            draw_text(painter, rx + 6, ry + 6, idx_label, *THEME['muted'])
            draw_text(painter, rx + 34, ry + 6, label, 255, 255, 255)
            if hovered:
                _item_search_hover_index = global_idx
                if _mouse_clicked():
                    cfg.item_search_filter = label
                    try:
                        cfg.save()
                    except Exception:
                        pass
    if len(items) > usable_rows:
        sb_x = inner_x + inner_w - 6
        sb_y = list_top
        sb_w = 8
        sb_h = list_h
        _fill_rect(painter, sb_x, sb_y, sb_w, sb_h, (26, 26, 40))
        _box(painter, sb_x, sb_y, sb_w, sb_h, THEME['divider'])
        slider_frac = usable_rows / float(len(items)) if len(items) > 0 else 1.0
        slider_h = max(18, int(sb_h * slider_frac))
        if max_offset > 0:
            slider_pos_frac = _item_search_scroll_offset / float(max_offset)
        else:
            slider_pos_frac = 0.0
        slider_y = sb_y + int((sb_h - slider_h) * slider_pos_frac)
        _fill_rect(painter, sb_x, slider_y, sb_w, slider_h, THEME['accent'])
        inside_slider = sb_x <= mx <= sb_x + sb_w and slider_y <= my <= slider_y + slider_h
        inside_track = sb_x <= mx <= sb_x + sb_w and sb_y <= my <= sb_y + sb_h
        if inside_slider and _mouse_down():
            _item_search_drag_slider = True
        if not _mouse_down() and _item_search_drag_slider:
            _item_search_drag_slider = False
        if _item_search_drag_slider and max_offset > 0:
            rel = my - sb_y - slider_h / 2.0
            if rel < 0:
                rel = 0
            if rel > sb_h - slider_h:
                rel = sb_h - slider_h
            slider_pos_frac = rel / float(sb_h - slider_h) if sb_h - slider_h > 0 else 0.0
            _item_search_scroll_offset = int(round(slider_pos_frac * max_offset))
            _scroll_offset_item_search = _item_search_scroll_offset
        if inside_track and _mouse_clicked() and (not inside_slider):
            page = max(1, usable_rows - 1)
            if my < slider_y:
                _item_search_scroll_offset = max(0, _item_search_scroll_offset - page)
            else:
                _item_search_scroll_offset = min(max_offset, _item_search_scroll_offset + page)
            _scroll_offset_item_search = _item_search_scroll_offset
THEME = {'bg': (12, 12, 16), 'panel': (18, 18, 24), 'panel_2': (22, 22, 30), 'header': (26, 26, 36), 'footer': (16, 16, 22), 'border': (70, 70, 95), 'divider': (28, 28, 40), 'accent': (180, 40, 40), 'accent_2': (200, 70, 70), 'hover': (50, 50, 70), 'active': (62, 62, 92), 'text': (245, 245, 245), 'muted': (175, 175, 190), 'dim': (140, 140, 155), 'btn_bg': (24, 24, 32), 'btn_bg_hover': (40, 40, 58), 'btn_bg_on': (70, 40, 60)}
HEADER_H = 24
SIDEBAR_W = 145
FOOTER_H = 32
MENU_W = 540
MENU_H = 560
BTN_COLS = 2
BTN_H = 26
BTN_V_SPACING = 4
BTN_H_SPACING = 10
BTN_INNER_MARGIN = 8
BONE_BOX_H = 22
BONE_ENTRY_H = 18
BONE_ENTRY_SPACING = 2
WAYPOINT_MAP_BOX_H = 22
WAYPOINT_MAP_ENTRY_H = 18
WAYPOINT_MAP_ENTRY_SPACING = 2
def _draw_players_tab(painter: QtGui.QPainter, draw_text: Callable[[QtGui.QPainter, int, int, str, int, int, int], None], content_x: int, content_y: int, content_w: int, content_h: int, cfg: ESPConfig) -> None:
    global _player_list_rows, _player_list_selected_index
    rows = _player_list_rows or []
    if content_w <= 40 or content_h <= 40:
        return
    mx, my = _mouse_pos()
    raw_friends = getattr(cfg, 'friend_steam_ids', None)
    if isinstance(raw_friends, (list, tuple, set)):
        friend_ids = set(raw_friends)
    else:
        friend_ids = set()
    margin = BTN_INNER_MARGIN
    inner_x = content_x + margin
    inner_y = content_y + 28
    inner_w = content_w - 2 * margin
    inner_h = content_h - (inner_y - content_y) - 42
    if inner_w <= 40 or inner_h <= 40:
        return
    _fill_rect(painter, inner_x, inner_y, inner_w, inner_h, THEME['panel'])
    _box(painter, inner_x, inner_y, inner_w, inner_h, THEME['divider'])
    header_y = inner_y + 4
    draw_text(painter, inner_x + 6, header_y, 'Name', *THEME['muted'])
    draw_text(painter, inner_x + 220, header_y, 'Dist', *THEME['muted'])
    draw_text(painter, inner_x + 280, header_y, 'SteamID', *THEME['muted'])
    list_y = header_y + 14
    row_h = 18
    max_rows = max(0, (inner_h - (list_y - inner_y) - 4) // row_h)
    visible_rows = rows[:max_rows]
    hover_idx = -1
    for idx, (name, steam_id, dist_m, is_friend_row) in enumerate(visible_rows):
        row_y = list_y + idx * row_h
        inside = inner_x <= mx <= inner_x + inner_w and row_y <= my <= row_y + row_h
        bg_col = None
        if idx == _player_list_selected_index:
            bg_col = THEME['active']
        elif inside:
            bg_col = THEME['hover']
        if bg_col is not None:
            _fill_rect(painter, inner_x + 2, row_y, inner_w - 4, row_h - 1, bg_col)
        txt_col = THEME['accent_2'] if steam_id in friend_ids else THEME['text']
        label = name or '<unknown>'
        dist_text = ''
        try:
            if dist_m > 0.0:
                dist_text = f'{int(dist_m)}m'
        except Exception:
            dist_text = ''
        draw_text(painter, inner_x + 6, row_y + 4, label, *txt_col)
        if dist_text:
            draw_text(painter, inner_x + 220, row_y + 4, dist_text, *THEME['muted'])
        display_sid = steam_id or '<no id>'
        draw_text(painter, inner_x + 280, row_y + 4, display_sid, *THEME['dim'])
        if inside:
            hover_idx = idx
    if _mouse_clicked() and hover_idx >= 0:
        _player_list_selected_index = hover_idx
    info_y = inner_y + inner_h + 4
    label = 'No player selected'
    action_steam_id = ''
    if 0 <= _player_list_selected_index < len(visible_rows):
        sel_name, sel_steam, sel_dist, sel_friend = visible_rows[_player_list_selected_index]
        label = f'Selected: {sel_name}'
        action_steam_id = sel_steam or ''
    draw_text(painter, content_x + 12, info_y, label, *THEME['muted'])
    if action_steam_id:
        is_friend = action_steam_id in friend_ids
        btn_label = 'Remove Friend' if is_friend else 'Add Friend'
        btn_w = 140
        btn_h = 22
        btn_x = content_x + content_w - btn_w - 18
        btn_y = info_y - 4
        hovered = btn_x <= mx <= btn_x + btn_w and btn_y <= my <= btn_y + btn_h
        base_col = (220, 80, 80) if is_friend else THEME['accent']
        if hovered:
            base_col = (min(base_col[0] + 16, 255), min(base_col[1] + 16, 255), min(base_col[2] + 16, 255))
        _fill_rect(painter, btn_x, btn_y, btn_w, btn_h, base_col)
        _box(painter, btn_x, btn_y, btn_w, btn_h, THEME['border'])
        draw_text(painter, btn_x + 10, btn_y + 5, btn_label, 255, 255, 255)
        if hovered and _mouse_clicked():
            ids = list(getattr(cfg, 'friend_steam_ids', []) or [])
            if is_friend:
                ids = [sid for sid in ids if sid != action_steam_id]
            elif action_steam_id not in ids:
                ids.append(action_steam_id)
            cfg.friend_steam_ids = ids
            try:
                cfg.save()
            except Exception:
                pass
def _draw_waypoint_custom_panel(painter: QtGui.QPainter, draw_text: Callable[[QtGui.QPainter, int, int, str, int, int, int], None], panel_x: int, panel_y: int, panel_w: int, panel_h: int) -> None:
    global _waypoint_custom_scroll_offset, _waypoint_custom_selected_index
    global _waypoint_custom_hover_index, _waypoint_custom_rename_active
    global _waypoint_custom_rename_buffer, _waypoint_custom_rename_index
    mx, my = _mouse_pos()
    bg = (26, 26, 40)
    _fill_rect(painter, panel_x, panel_y, panel_w, panel_h, bg)
    _box(painter, panel_x, panel_y, panel_w, panel_h, THEME['divider'])
    title = 'Custom Waypoints'
    draw_text(painter, panel_x + 8, panel_y + 6, title, *THEME['text'])
    hint = 'F7 in-game: add at your position'
    draw_text(painter, panel_x + 8, panel_y + 20, hint, *THEME['muted'])
    try:
        waypoints = list(get_custom_waypoints_cached())
    except Exception:
        waypoints = []
    if '_waypoint_custom_selected_index' not in globals():
        _waypoint_custom_selected_index = -1
    if '_waypoint_custom_hover_index' not in globals():
        _waypoint_custom_hover_index = -1
    if '_waypoint_custom_scroll_offset' not in globals():
        _waypoint_custom_scroll_offset = 0
    if '_waypoint_custom_rename_active' not in globals():
        _waypoint_custom_rename_active = False
    if '_waypoint_custom_rename_buffer' not in globals():
        _waypoint_custom_rename_buffer = ''
    if '_waypoint_custom_rename_index' not in globals():
        _waypoint_custom_rename_index = -1
    if _waypoint_custom_selected_index >= len(waypoints):
        _waypoint_custom_selected_index = -1
    if _waypoint_custom_rename_index >= len(waypoints):
        _waypoint_custom_rename_index = -1
    list_top = panel_y + 36
    list_left = panel_x + 8
    list_w = panel_w - 16
    list_bottom = panel_y + panel_h - 40
    row_h = 16
    max_rows = max(0, (list_bottom - list_top) // row_h)
    if max_rows <= 0:
        return
    if not waypoints:
        draw_text(painter, list_left, list_top + 4, 'No custom waypoints yet.', *THEME['muted'])
        draw_text(painter, list_left, list_top + 20, 'Press F7 in-game to add one at your position.', *THEME['muted'])
    else:
        start_idx = max(0, int(_waypoint_custom_scroll_offset))
        end_idx = min(len(waypoints), start_idx + max_rows)
        _waypoint_custom_hover_index = -1
        for i in range(start_idx, end_idx):
            wp = waypoints[i]
            row_y = list_top + (i - start_idx) * row_h
            if row_y + row_h > list_bottom:
                break
            name = str(wp.get('name', f'Custom {i + 1}'))
            try:
                wx = float(wp.get('x', 0.0))
                wz = float(wp.get('z', 0.0))
            except Exception:
                wx, wz = (0.0, 0.0)
            if _waypoint_custom_rename_active and _waypoint_custom_rename_index == i:
                display_name = _waypoint_custom_rename_buffer or name
            else:
                display_name = name
            label = f'{i + 1}. {display_name}  ({int(wx)}, {int(wz)})'
            hovered = list_left <= mx <= list_left + list_w and row_y <= my <= row_y + row_h
            selected = i == _waypoint_custom_selected_index
            if selected:
                base_col = (70, 60, 110)
            elif hovered:
                base_col = (55, 55, 78)
            else:
                base_col = (40, 40, 60)
            _fill_rect(painter, list_left, row_y, list_w, row_h, base_col)
            _box(painter, list_left, row_y, list_w, row_h, THEME['divider'])
            draw_text(painter, list_left + 6, row_y + 3, label, *THEME['text'])
            if hovered:
                _waypoint_custom_hover_index = i
                if _mouse_clicked():
                    _waypoint_custom_selected_index = i
                    _waypoint_custom_rename_active = False
                    _waypoint_custom_rename_buffer = ''
                if _mouse_right_clicked():
                    wps = list(waypoints)
                    if 0 <= i < len(wps):
                        del wps[i]
                        set_custom_waypoints(wps)
                    _waypoint_custom_selected_index = -1
                    _waypoint_custom_rename_active = False
                    _waypoint_custom_rename_buffer = ''
                    _waypoint_custom_rename_index = -1
                    return
    btn_h = 18
    btn_w = 110
    btn_y = panel_y + panel_h - 30
    rename_x = panel_x + 8
    delete_x = rename_x + btn_w + 8
    selected_valid = 0 <= _waypoint_custom_selected_index < len(waypoints)
    def _draw_button(label: str, bx: int, by: int, enabled: bool) -> bool:
        bw, bh = (btn_w, btn_h)
        hovered = bx <= mx <= bx + bw and by <= my <= by + bh
        bg = (60, 50, 90) if enabled and hovered else (40, 40, 60)
        if not enabled:
            bg = (30, 30, 40)
        _fill_rect(painter, bx, by, bw, bh, bg)
        _box(painter, bx, by, bw, bh, THEME['divider'])
        text_col = THEME['text'] if enabled else THEME['muted']
        draw_text(painter, bx + 8, by + 4, label, *text_col)
        return enabled and hovered and _mouse_clicked()
    if _draw_button('Rename Selected', rename_x, btn_y, selected_valid):
        idx = _waypoint_custom_selected_index
        if 0 <= idx < len(waypoints):
            _waypoint_custom_rename_active = True
            _waypoint_custom_rename_index = idx
            _waypoint_custom_rename_buffer = str(waypoints[idx].get('name', f'Custom {idx + 1}'))
    if _draw_button('Delete Selected', delete_x, btn_y, selected_valid):
        idx = _waypoint_custom_selected_index
        if 0 <= idx < len(waypoints):
            wps = list(waypoints)
            del wps[idx]
            set_custom_waypoints(wps)
        _waypoint_custom_selected_index = -1
        _waypoint_custom_rename_active = False
        _waypoint_custom_rename_buffer = ''
        _waypoint_custom_rename_index = -1
        return
    if _waypoint_custom_rename_active and 0 <= _waypoint_custom_rename_index < len(waypoints):
        vk = _capture_next_virtual_key()
        if vk is not None:
            name = _vk_to_name(vk)
            if name == 'BACKSPACE':
                _waypoint_custom_rename_buffer = _waypoint_custom_rename_buffer[:-1]
            elif name == 'ENTER':
                idx = _waypoint_custom_rename_index
                wps = list(waypoints)
                if 0 <= idx < len(wps):
                    final = _waypoint_custom_rename_buffer.strip() or str(wps[idx].get('name', f'Custom {idx + 1}'))
                    wps[idx]['name'] = final
                    set_custom_waypoints(wps)
                _waypoint_custom_rename_active = False
                _waypoint_custom_rename_buffer = ''
                _waypoint_custom_rename_index = -1
            elif name == 'ESC':
                _waypoint_custom_rename_active = False
                _waypoint_custom_rename_buffer = ''
                _waypoint_custom_rename_index = -1
            else:
                if len(name) == 1:
                    ch = name
                elif name == 'SPACE':
                    ch = ' '
                else:
                    ch = ''
                if ch and len(_waypoint_custom_rename_buffer) < 24:
                    _waypoint_custom_rename_buffer += ch
        edit_label = _waypoint_custom_rename_buffer or (str(waypoints[_waypoint_custom_rename_index].get('name', f'Custom {_waypoint_custom_rename_index + 1}')) if 0 <= _waypoint_custom_rename_index < len(waypoints) else '')
        draw_text(painter, panel_x + 8, btn_y - 16, f'Rename: {edit_label}_', *THEME['text'])
        draw_text(painter, panel_x + 8, btn_y - 4, 'Type letters, ENTER=OK, ESC=cancel', *THEME['muted'])
    else:
        draw_text(painter, panel_x + 8, btn_y - 16, 'Select a row, then use Rename/Delete.', *THEME['muted'])
def _clamp255(v: int) -> int:
    try:
        return 0 if v < 0 else 255 if v > 255 else int(v)
    except Exception:
        return 255
_BRUSH_CACHE: Dict[int, QtGui.QBrush] = {}
_PEN_CACHE: Dict[Tuple[int, int], QtGui.QPen] = {}
def _brush(rgb: Tuple[int, int, int]) -> QtGui.QBrush:
    r, g, b = map(_clamp255, rgb)
    key = r << 16 | g << 8 | b
    br = _BRUSH_CACHE.get(key)
    if br is None:
        br = QtGui.QBrush(QtGui.QColor(r, g, b))
        _BRUSH_CACHE[key] = br
    return br
def _pen(rgb: Tuple[int, int, int], width: int=1) -> QtGui.QPen:
    r, g, b = map(_clamp255, rgb)
    key = (r << 16 | g << 8 | b, int(width))
    pen = _PEN_CACHE.get(key)
    if pen is None:
        pen = QtGui.QPen(QtGui.QColor(r, g, b))
        pen.setWidth(int(width))
        _PEN_CACHE[key] = pen
    return pen
def _fill_rect(painter: QtGui.QPainter, x: int, y: int, w: int, h: int, rgb: Tuple[int, int, int]) -> None:
    rect = QtCore.QRect(int(x), int(y), int(w), int(h))
    painter.fillRect(rect, _brush(rgb))
def _box(painter: QtGui.QPainter, x: int, y: int, w: int, h: int, rgb: Tuple[int, int, int]) -> None:
    pen = _pen(rgb, 1)
    old_pen = painter.pen()
    old_brush = painter.brush()
    painter.setPen(pen)
    painter.setBrush(QtCore.Qt.NoBrush)
    painter.drawRect(int(x), int(y), int(w), int(h))
    painter.setPen(old_pen)
    painter.setBrush(old_brush)
def _shadow(painter: QtGui.QPainter, x: int, y: int, w: int, h: int, layers: int=3) -> None:
    for i in range(layers, 0, -1):
        off = i
        shade = 6 + (layers - i) * 3
        _fill_rect(painter, x + off, y + off, w, h, (shade, shade, shade))
VK_INSERT = 45
VK_LBUTTON = 1
VK_RBUTTON = 2
_prev_mouse_down = False
_prev_right_down = False
_aimkey_listening: bool = False
_aimkey_listen_skip: int = 0
menu_open: bool = True
active_tab: int = 0
hover_row: int | None = None
sidebar_hover: int | None = None
_item_search_items: List[str] = []
_item_search_item_categories: List[str] = []
_item_search_hover_index: int | None = None
_item_search_scroll_offset: int = 0
_scroll_offset_item_search: int = 0
_item_search_drag_slider: bool = False
_player_list_rows: List[Tuple[str, str, float, bool]] = []
_player_list_selected_index: int = -1
menu_x: int = 40
menu_y: int = 60
_dragging: bool = False
_drag_off_x: int = 0
_drag_off_y: int = 0
_slider_dragging: str | None = None
exit_hover: bool = False
_active_color_attr: str | None = None
_color_slider_dragging: str | None = None
_bone_dropdown_open: bool = False
_bone_dropdown_hover: bool = False
_bone_dropdown_entry_hover_index: int | None = None
_waypoint_map_dropdown_open: bool = False
_waypoint_map_dropdown_hover: bool = False
_waypoint_map_dropdown_entry_hover_index: int | None = None
menu_collapsed: bool = False
_last_header_click_ms: int = 0
def _pressed(vk: int) -> bool:
    try:
        return user32.GetAsyncKeyState(vk) & 1 != 0
    except Exception:
        return False
def _mouse_down() -> bool:
    try:
        return user32.GetAsyncKeyState(VK_LBUTTON) & 32768 != 0
    except Exception:
        return False
def _mouse_clicked() -> bool:
    global _prev_mouse_down
    down = _mouse_down()
    clicked = not down and _prev_mouse_down
    _prev_mouse_down = down
    return clicked
def _mouse_right_down() -> bool:
    try:
        return user32.GetAsyncKeyState(VK_RBUTTON) & 32768 != 0
    except Exception:
        return False
def _mouse_right_clicked() -> bool:
    global _prev_right_down
    down = _mouse_right_down()
    clicked = not down and _prev_right_down
    _prev_right_down = down
    return clicked
def _mouse_pos() -> Tuple[int, int]:
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return (int(pt.x), int(pt.y))
def update_item_search_items(labels: List[str]) -> None:
    global _item_search_items, _item_search_item_categories
    try:
        seen: set[str] = set()
        uniq_labels: List[str] = []
        uniq_cats: List[str] = []
        for lab in labels:
            label_str: str
            category_str: str = ''
            if isinstance(lab, (tuple, list)) and len(lab) >= 2:
                try:
                    label_str = str(lab[0] or '')
                    category_str = str(lab[1] or '')
                except Exception:
                    continue
            else:
                try:
                    label_str = str(lab or '')
                except Exception:
                    continue
            if not label_str or label_str in seen:
                continue
            seen.add(label_str)
            uniq_labels.append(label_str)
            uniq_cats.append(category_str)
        pairs = list(zip(uniq_labels, uniq_cats))
        pairs.sort(key=lambda p: p[0].lower())
        _item_search_items = [p[0] for p in pairs]
        _item_search_item_categories = [p[1] for p in pairs]
    except Exception:
        simple: List[str] = []
        for lab in labels:
            if not lab:
                continue
            try:
                if isinstance(lab, (tuple, list)) and len(lab) >= 1:
                    text = str(lab[0] or '')
                else:
                    text = str(lab)
            except Exception:
                continue
            if not text:
                continue
            simple.append(text)
            if len(simple) >= 64:
                break
        _item_search_items = simple
        _item_search_item_categories = ['' for _ in _item_search_items]
def update_player_list(rows: List[Tuple[str, str, float, bool]]) -> None:
    global _player_list_rows, _player_list_selected_index
    try:
        _player_list_rows = list(rows)
    except Exception:
        _player_list_rows = []
    if not _player_list_rows:
        _player_list_selected_index = -1
    elif _player_list_selected_index >= len(_player_list_rows):
        _player_list_selected_index = len(_player_list_rows) - 1
def _capture_next_virtual_key(ignore: Tuple[int, ...]=(VK_INSERT,)) -> int | None:
    for vk in range(1, 256):
        try:
            if vk in ignore:
                continue
            if user32.GetAsyncKeyState(vk) & 1:
                return vk
        except Exception:
            continue
    return None
def _vk_to_name(vk: int) -> str:
    mouse_names = {1: 'LMB', 2: 'RMB', 4: 'MMB', 5: 'X1', 6: 'X2'}
    if vk in mouse_names:
        return mouse_names[vk]
    if 48 <= vk <= 57:
        return chr(vk)
    if 65 <= vk <= 90:
        return chr(vk)
    if 112 <= vk <= 123:
        return f'F{vk - 111}'
    special = {8: 'BACKSPACE', 9: 'TAB', 13: 'ENTER', 16: 'SHIFT', 17: 'CTRL', 18: 'ALT', 20: 'CAPS', 27: 'ESC', 32: 'SPACE', 33: 'PGUP', 34: 'PGDN', 35: 'END', 36: 'HOME', 37: 'LEFT', 38: 'UP', 39: 'RIGHT', 40: 'DOWN'}
    if vk in special:
        return special[vk]
    return f'VK_{vk:02X}'
def _smooth_rating_label(v: float, min_v: float, max_v: float) -> str:
    if max_v <= min_v:
        return 'Balanced'
    t = (v - min_v) / (max_v - min_v)
    if t <= 0.2:
        return 'Ragey'
    if t <= 0.4:
        return 'Fast'
    if t <= 0.7:
        return 'Balanced'
    return 'Legit'
def _compute_esp_item_rects(items: List[Dict[str, str]], content_x: int, content_y: int, content_w: int) -> List[Tuple[int, int, int, int]]:
    x0 = int(content_x + BTN_INNER_MARGIN)
    y0 = int(content_y + 34)
    full_w = int(content_w - 2 * BTN_INNER_MARGIN)
    rects: List[Tuple[int, int, int, int]] = [(0, 0, 0, 0)] * len(items)
    idx_by_attr: Dict[str, int] = {}
    for i, opt in enumerate(items):
        a = opt.get('attr', '')
        if a:
            idx_by_attr[a] = i
    def _place_full(attr: str, cur_y: int) -> int:
        i = idx_by_attr.get(attr, -1)
        if i >= 0:
            rects[i] = (x0, cur_y, full_w, BTN_H)
            return cur_y + BTN_H + BTN_V_SPACING
        return cur_y
    def _place_children(attrs: Tuple[str, ...], cur_y: int) -> int:
        child_indices = [idx_by_attr.get(a, -1) for a in attrs]
        child_indices = [i for i in child_indices if i >= 0]
        if not child_indices:
            return cur_y
        indent = 18
        child_x0 = x0 + indent
        child_w = int((full_w - indent - BTN_H_SPACING) / 2)
        child_h = int(BTN_H * 0.8)
        for j, i in enumerate(child_indices):
            col = j % 2
            row = j // 2
            bx = child_x0 + col * (child_w + BTN_H_SPACING)
            by = cur_y + row * (child_h + BTN_V_SPACING)
            rects[i] = (bx, by, child_w, child_h)
        rows = int(math.ceil(len(child_indices) / 2.0))
        return cur_y + rows * (child_h + BTN_V_SPACING)
    cy = y0
    cy = _place_full('esp_enabled', cy)
    cy = _place_full('draw_players', cy)
    cy = _place_children(('draw_player_text', 'draw_player_box', 'draw_player_skeleton', 'draw_player_head_cross', 'draw_player_distance', 'draw_player_corpses'), cy)
    cy = _place_full('draw_zombies', cy)
    cy = _place_children(('draw_zombie_text', 'draw_zombie_box', 'draw_zombie_skeleton', 'draw_zombie_head_cross', 'draw_zombie_distance', 'draw_zombie_corpses'), cy)
    remaining: List[int] = []
    for i, opt in enumerate(items):
        if rects[i] != (0, 0, 0, 0):
            continue
        remaining.append(i)
    cols = 2
    if remaining:
        inner_w = full_w
        card_w = int((inner_w - BTN_H_SPACING * (cols - 1)) / cols)
        card_h = BTN_H
        for k, i in enumerate(remaining):
            row = k // cols
            col = k % cols
            bx = x0 + col * (card_w + BTN_H_SPACING)
            by = cy + row * (card_h + BTN_V_SPACING)
            rects[i] = (bx, by, card_w, card_h)
    for i in range(len(rects)):
        if rects[i] == (0, 0, 0, 0):
            rects[i] = (x0, cy, full_w, BTN_H)
            cy += BTN_H + BTN_V_SPACING
    return rects
def _compute_aimbot_bone_and_slider_layout(content_x: int, content_y: int, content_w: int, grid_x0: int, grid_y0: int, card_w: int, card_h: int, items_count: int, dropdown_open: bool, bone_count: int) -> Dict[str, object]:
    btn_cols_local = BTN_COLS if BTN_COLS > 0 else 1
    n_rows = (items_count + btn_cols_local - 1) // btn_cols_local
    bone_x = content_x + BTN_INNER_MARGIN
    bone_w = content_w - 2 * BTN_INNER_MARGIN
    bone_y = grid_y0 + n_rows * (card_h + BTN_V_SPACING) + 12
    bone_h = BONE_BOX_H
    bone_box = (bone_x, bone_y, bone_w, bone_h)
    bone_entries: List[Tuple[int, int, int, int]] = []
    if dropdown_open and bone_count > 0:
        for i in range(bone_count):
            ex = bone_x + 4
            ey = bone_y + bone_h + 4 + i * (BONE_ENTRY_H + BONE_ENTRY_SPACING)
            ew = bone_w - 8
            eh = BONE_ENTRY_H
            bone_entries.append((ex, ey, ew, eh))
        slider_y = bone_y + bone_h + 4 + bone_count * (BONE_ENTRY_H + BONE_ENTRY_SPACING) + 16
    else:
        slider_y = bone_y + bone_h + 16
    return {'n_rows': n_rows, 'bone_box': bone_box, 'bone_entries': bone_entries, 'slider_y': slider_y}


def _compute_waypoint_map_and_panel_layout(
    content_x: int,
    content_y: int,
    content_w: int,
    content_h: int,
    grid_y0: int,
    card_w: int,
    card_h: int,
    items_count: int,
    dropdown_open: bool,
    option_count: int,
) -> Dict[str, object]:
    btn_cols_local = BTN_COLS if BTN_COLS > 0 else 1
    n_rows = (items_count + btn_cols_local - 1) // btn_cols_local if items_count > 0 else 0
    if n_rows > 0:
        cards_bottom = grid_y0 + n_rows * (card_h + BTN_V_SPACING) - BTN_V_SPACING
    else:
        cards_bottom = grid_y0
    panel_x = content_x + BTN_INNER_MARGIN
    panel_w = content_w - 2 * BTN_INNER_MARGIN
    panel_y = cards_bottom + 14
    map_h = WAYPOINT_MAP_BOX_H
    map_box = (panel_x, panel_y, panel_w, map_h)
    entries: List[Tuple[int, int, int, int]] = []
    if dropdown_open and option_count > 0:
        for i in range(option_count):
            ex = panel_x + 4
            ey = panel_y + map_h + 4 + i * (WAYPOINT_MAP_ENTRY_H + WAYPOINT_MAP_ENTRY_SPACING)
            ew = panel_w - 8
            eh = WAYPOINT_MAP_ENTRY_H
            entries.append((ex, ey, ew, eh))
        custom_y = panel_y + map_h + 4 + option_count * (WAYPOINT_MAP_ENTRY_H + WAYPOINT_MAP_ENTRY_SPACING) + 10
    else:
        custom_y = panel_y + map_h + 10
    custom_h = max(60, content_y + content_h - custom_y - 8)
    custom_panel_box = (panel_x, custom_y, panel_w, custom_h)
    return {
        'map_box': map_box,
        'map_entries': entries,
        'custom_panel_box': custom_panel_box,
    }

def _update_bone_multi_flag(cfg: ESPConfig) -> None:
    try:
        selected = sum((1 for _, attr in _BONE_OPTIONS if getattr(cfg, attr, False)))
        setattr(cfg, 'aimbot_bone_multi', bool(selected > 1))
    except Exception:
        pass
def _sync_skeleton_master(cfg: ESPConfig) -> None:
    try:
        player = bool(getattr(cfg, 'draw_player_skeleton', False))
        zombie = bool(getattr(cfg, 'draw_zombie_skeleton', False))
        setattr(cfg, 'skeleton_esp_enabled', bool(player or zombie))
    except Exception:
        pass
def process_hotkeys(cfg: ESPConfig) -> None:
    global menu_open, active_tab, hover_row, sidebar_hover
    global menu_x, menu_y, _dragging, _drag_off_x, _drag_off_y
    global _slider_dragging, exit_hover
    global _bone_dropdown_open, _bone_dropdown_hover, _bone_dropdown_entry_hover_index
    global _waypoint_map_dropdown_open, _waypoint_map_dropdown_hover, _waypoint_map_dropdown_entry_hover_index
    global _aimkey_listening, _aimkey_listen_skip
    global menu_collapsed, _last_header_click_ms
    _sync_skeleton_master(cfg)
    if _pressed(VK_INSERT):
        menu_open = not menu_open
    if not menu_open:
        hover_row = None
        sidebar_hover = None
        _dragging = False
        _slider_dragging = None
        exit_hover = False
        _bone_dropdown_open = False
        _bone_dropdown_hover = False
        _bone_dropdown_entry_hover_index = None
        menu_collapsed = False
        return
    mx, my = _mouse_pos()
    x, y = (menu_x, menu_y)
    w, h = (MENU_W, MENU_H)
    header_h = HEADER_H
    sidebar_w = SIDEBAR_W
    footer_h = FOOTER_H
    header_hover = x <= mx <= x + w and y <= my <= y + header_h
    if header_hover and _mouse_clicked():
        try:
            now_ms = int(QtCore.QDateTime.currentMSecsSinceEpoch())
        except Exception:
            now_ms = _last_header_click_ms or 0
        DOUBLE_CLICK_MS = 350
        if _last_header_click_ms and now_ms - _last_header_click_ms <= DOUBLE_CLICK_MS:
            menu_collapsed = not menu_collapsed
            _last_header_click_ms = 0
        else:
            _last_header_click_ms = now_ms
    if header_hover and _mouse_down() and (not _dragging):
        _dragging = True
        _drag_off_x = mx - x
        _drag_off_y = my - y
    if _dragging:
        if _mouse_down():
            menu_x = mx - _drag_off_x
            menu_y = my - _drag_off_y
            return
        _dragging = False
    if menu_collapsed:
        hover_row = None
        sidebar_hover = None
        _bone_dropdown_hover = False
        _bone_dropdown_entry_hover_index = None
        _slider_dragging = None
        exit_hover = False
        return
    hover_row = None
    sidebar_hover = None
    _bone_dropdown_hover = False
    _bone_dropdown_entry_hover_index = None
    tab_top = y + header_h + 10
    tab_row_h = 24
    for i, (tab_name, _) in enumerate(_TABS):
        ty = tab_top + i * tab_row_h
        if x + 8 <= mx <= x + sidebar_w - 8 and ty <= my <= ty + tab_row_h:
            sidebar_hover = i
            if _mouse_clicked():
                active_tab = i
                _bone_dropdown_open = False
            return
    content_x = x + sidebar_w + 10
    content_y = y + header_h + 10
    content_w = w - sidebar_w - 20
    footer_y = y + h - footer_h
    tab_name = _TABS[active_tab][0]
    items = _get_tab_items(active_tab, cfg)
    esp_rects = _compute_esp_item_rects(items, content_x, content_y, content_w) if tab_name == 'ESP' else None
    inner_w = content_w - 2 * BTN_INNER_MARGIN
    btn_cols_local = BTN_COLS if BTN_COLS > 0 else 1
    card_w = int((inner_w - BTN_H_SPACING * (btn_cols_local - 1)) / btn_cols_local)
    card_h = BTN_H
    grid_x0 = content_x + BTN_INNER_MARGIN
    grid_y0 = content_y + 34
    for idx, opt in enumerate(items):
        if tab_name == 'ESP' and esp_rects is not None:
            bx, by, bw, bh = esp_rects[idx]
        else:
            row_idx = idx // btn_cols_local
            col_idx = idx % btn_cols_local
            bx = grid_x0 + col_idx * (card_w + BTN_H_SPACING)
            by = grid_y0 + row_idx * (card_h + BTN_V_SPACING)
            bw, bh = (card_w, card_h)
        if bx <= mx <= bx + bw and by <= my <= by + bh:
            hover_row = idx
            attr = opt['attr']
            if tab_name == 'Items' and attr in _ITEM_ATTR_TO_CATEGORY and _mouse_right_clicked():
                _pick_item_category_color(attr, cfg)
            elif _mouse_clicked():
                cur = bool(getattr(cfg, attr, False))
                new_val = not cur
                if attr == 'aimbot_key_listen':
                    setattr(cfg, attr, new_val)
                    if new_val:
                        _aimkey_listening = True
                        _aimkey_listen_skip = 2
                    else:
                        _aimkey_listening = False
                        _aimkey_listen_skip = 0
                else:
                    setattr(cfg, attr, new_val)
                if attr == 'aimbot_enabled' and (not new_val):
                    _bone_dropdown_open = False
                    _slider_dragging = None
                if attr in {'aimbot_bone_head', 'aimbot_bone_neck', 'aimbot_bone_chest', 'aimbot_bone_spine', 'aimbot_bone_pelvis'}:
                    _update_bone_multi_flag(cfg)
                if attr in {'draw_player_skeleton', 'draw_zombie_skeleton'}:
                    _sync_skeleton_master(cfg)
                try:
                    cfg.save()
                except Exception:
                    pass
            break
    aimbot_on = bool(getattr(cfg, 'aimbot_enabled', False))
    if tab_name == 'Aimbot':
        layout = _compute_aimbot_bone_and_slider_layout(content_x, content_y, content_w, grid_x0, grid_y0, card_w, card_h, len(items), _bone_dropdown_open, len(_BONE_OPTIONS))
        bone_x, bone_y, bone_w, bone_h = layout['bone_box']
        bone_entries = layout['bone_entries']
        if _bone_dropdown_open and bone_entries:
            clicked_entry = False
            for i, (ex, ey, ew, eh) in enumerate(bone_entries):
                if ex <= mx <= ex + ew and ey <= my <= ey + eh:
                    _bone_dropdown_entry_hover_index = i
                    if _mouse_clicked():
                        label, attr = _BONE_OPTIONS[i]
                        cur = bool(getattr(cfg, attr, False))
                        setattr(cfg, attr, not cur)
                        _update_bone_multi_flag(cfg)
                        try:
                            cfg.save()
                        except Exception:
                            pass
                        clicked_entry = True
                    break
            if not clicked_entry and _mouse_clicked():
                if not (bone_x <= mx <= bone_x + bone_w and bone_y <= my <= bone_y + bone_h):
                    _bone_dropdown_open = False
        _bone_dropdown_hover = bone_x <= mx <= bone_x + bone_w and bone_y <= my <= bone_y + bone_h
        if _bone_dropdown_hover and _mouse_clicked():
            _bone_dropdown_open = not _bone_dropdown_open
        slider_y = layout['slider_y']
        # Hitboxes for Aimbot sliders (FOV / Smooth) – mirror vertical spacing used in drawing.
        for i, s in enumerate(_AIMBOT_SLIDERS):
            sx = content_x + 14
            sy = slider_y + i * 44
            sw = content_w - 28
            sh = 18
            inside_slider = sx <= mx <= sx + sw and sy <= my <= sy + sh
            if inside_slider and _mouse_down():
                _slider_dragging = s['attr']
            if not _mouse_down() and _slider_dragging == s['attr']:
                _slider_dragging = None
            if _slider_dragging == s['attr'] and sw > 0:
                t = (mx - sx) / float(sw)
                t = max(0.0, min(1.0, t))
                value = s['min'] + t * (s['max'] - s['min'])
                value = round(value / s['step']) * s['step']
                setattr(cfg, s['attr'], float(value))
                try:
                    cfg.save()
                except Exception:
                    pass
    if tab_name == 'Waypoints':
        content_h = h - header_h - footer_h - 14
        layout_wp = _compute_waypoint_map_and_panel_layout(
            content_x,
            content_y,
            content_w,
            content_h,
            grid_y0,
            card_w,
            card_h,
            len(items),
            _waypoint_map_dropdown_open,
            len(_WAYPOINT_MAP_OPTIONS),
        )
        map_x, map_y, map_w, map_h = layout_wp['map_box']
        map_entries = layout_wp['map_entries']
        _waypoint_map_dropdown_hover = map_x <= mx <= map_x + map_w and map_y <= my <= map_y + map_h
        if _waypoint_map_dropdown_hover and _mouse_clicked():
            _waypoint_map_dropdown_open = not _waypoint_map_dropdown_open
        selected_map = getattr(cfg, 'waypoint_map', 'Chernarus')
        if _waypoint_map_dropdown_open and map_entries:
            clicked_entry = False
            for i, (ex, ey, ew, eh) in enumerate(map_entries):
                if ex <= mx <= ex + ew and ey <= my <= ey + eh:
                    _waypoint_map_dropdown_entry_hover_index = i
                    if _mouse_clicked():
                        try:
                            new_map = _WAYPOINT_MAP_OPTIONS[i]
                        except Exception:
                            new_map = 'Chernarus'
                        setattr(cfg, 'waypoint_map', new_map)
                        try:
                            cfg.save()
                        except Exception:
                            pass
                        clicked_entry = True
                    break
            if not clicked_entry and _mouse_clicked():
                if not (map_x <= mx <= map_x + map_w and map_y <= my <= map_y + map_h):
                    _waypoint_map_dropdown_open = False
        else:
            _waypoint_map_dropdown_entry_hover_index = None

        
    else:
        _bone_dropdown_open = False
        _bone_dropdown_entry_hover_index = None
        if not aimbot_on and _slider_dragging in {s['attr'] for s in _AIMBOT_SLIDERS}:
            _slider_dragging = None
    if tab_name == 'Items':
        rows = (len(items) + btn_cols_local - 1) // btn_cols_local if len(items) > 0 else 0
        if rows > 0:
            cards_bottom = grid_y0 + rows * (card_h + BTN_V_SPACING) - BTN_V_SPACING
        else:
            cards_bottom = grid_y0
        slider_y = cards_bottom + 28
        sx = content_x + 14
        sy = slider_y
        sw = content_w - 28
        sh = 18
        inside_slider = sx <= mx <= sx + sw and sy <= my <= sy + sh
        if inside_slider and _mouse_down():
            _slider_dragging = 'item_max_distance'
        if not _mouse_down() and _slider_dragging == 'item_max_distance':
            _slider_dragging = None
        if _slider_dragging == 'item_max_distance' and sw > 0:
            min_v = 0.0
            max_v = 2000.0
            t = (mx - sx) / float(sw)
            t = max(0.0, min(1.0, t))
            value = min_v + t * (max_v - min_v)
            value = round(value / 10.0) * 10.0
            try:
                setattr(cfg, 'item_max_distance', float(value))
                cfg.save()
            except Exception:
                pass
    
    if tab_name == 'System':
        # Sliders for world time and eye accommodation (sethour/seteye)
        rows = (len(items) + btn_cols_local - 1) // btn_cols_local if len(items) > 0 else 0
        if rows > 0:
            cards_bottom = grid_y0 + rows * (card_h + BTN_V_SPACING) - BTN_V_SPACING
        else:
            cards_bottom = grid_y0
        base_slider_y = cards_bottom + 28
        sx = content_x + 14
        sw = content_w - 28
        sh = 18
        for i, s in enumerate(_SYSTEM_SLIDERS):
            attr = s['attr']
            sy = base_slider_y + i * 40
            inside_slider = sx <= mx <= sx + sw and sy <= my <= sy + sh
            if inside_slider and _mouse_down():
                _slider_dragging = attr
            if not _mouse_down() and _slider_dragging == attr:
                _slider_dragging = None
            if _slider_dragging == attr and sw > 0:
                min_v = float(s.get('min', 0.0))
                max_v = float(s.get('max', 1.0))
                step = float(s.get('step', 0.1)) or 0.1
                t = (mx - sx) / float(sw)
                t = max(0.0, min(1.0, t))
                value = min_v + t * (max_v - min_v)
                value = round(value / step) * step
                try:
                    setattr(cfg, attr, float(value))
                    cfg.save()
                except Exception:
                    pass
    if _aimkey_listening:
        if _aimkey_listen_skip > 0:
            _aimkey_listen_skip -= 1
        else:
            vk = _capture_next_virtual_key()
            if vk is not None:
                try:
                    cfg.aimbot_key = int(vk)
                except Exception:
                    pass
                cfg.aimbot_key_listen = False
                _aimkey_listening = False
                _aimkey_listen_skip = 0
                try:
                    cfg.save()
                except Exception:
                    pass
    fy = footer_y
    exit_w, exit_h = (92, 26)
    exit_x = x + w - exit_w - 12
    exit_y = fy + (footer_h - exit_h) // 2
    if exit_x <= mx <= exit_x + exit_w and exit_y <= my <= exit_y + exit_h:
        exit_hover = True
        if _mouse_clicked():
            app = QtWidgets.QApplication.instance()
            if app is not None:
                app.quit()
            else:
                os._exit(0)
    else:
        exit_hover = False
def draw_menu(painter: QtGui.QPainter, draw_text: Callable[[QtGui.QPainter, int, int, str, int, int, int], None], x: int, y: int, cfg: ESPConfig) -> None:
    global menu_x, menu_y, menu_collapsed
    if menu_x == 40 and menu_y == 60:
        menu_x, menu_y = (int(x), int(y))
    if not menu_open:
        return
    x, y = (int(menu_x), int(menu_y))
    w, h = (MENU_W, MENU_H)
    header_h = HEADER_H
    sidebar_w = SIDEBAR_W
    footer_h = FOOTER_H
    if menu_collapsed:
        h = header_h + 4
    _shadow(painter, x, y, w, h, layers=3)
    _fill_rect(painter, x, y, w, h, THEME['panel'])
    _box(painter, x, y, w, h, THEME['border'])
    _fill_rect(painter, x, y, w, header_h, THEME['header'])
    _fill_rect(painter, x, y + header_h - 2, w, 2, THEME['accent'])
    draw_text(painter, x + 12, y + 10, 'Spectre | Made by Cr0mb & SameOldMistakes', *THEME['text'])
    indicator = '▼' if menu_collapsed else '▲'
    draw_text(painter, x + w - 20, y + 8, indicator, *THEME['muted'])
    if menu_collapsed:
        return
    sidebar_h = h - header_h - footer_h
    _fill_rect(painter, x, y + header_h, sidebar_w, sidebar_h, THEME['panel_2'])
    _fill_rect(painter, x + sidebar_w - 1, y + header_h, 1, sidebar_h, THEME['divider'])
    tab_top = y + header_h + 10
    tab_row_h = 24
    for i, (tab, _) in enumerate(_TABS):
        ty = tab_top + i * tab_row_h
        if i == active_tab:
            _fill_rect(painter, x + 8, ty, sidebar_w - 16, tab_row_h, THEME['active'])
            _fill_rect(painter, x + 8, ty, 3, tab_row_h, THEME['accent'])
        elif sidebar_hover == i:
            _fill_rect(painter, x + 8, ty, sidebar_w - 16, tab_row_h, THEME['hover'])
        col = THEME['text'] if i == active_tab else THEME['muted']
        draw_text(painter, x + 18, ty + 6, tab, *col)
    content_x = x + sidebar_w + 10
    content_y = y + header_h + 10
    content_w = w - sidebar_w - 20
    content_h = h - header_h - footer_h - 14
    _fill_rect(painter, content_x, content_y, content_w, content_h, THEME['bg'])
    _box(painter, content_x, content_y, content_w, content_h, THEME['divider'])
    tab_name = _TABS[active_tab][0]
    items = _get_tab_items(active_tab, cfg)
    draw_text(painter, content_x + 12, content_y + 8, tab_name, *THEME['muted'])
    if tab_name == 'Item Search':
        _draw_item_search_tab(painter, draw_text, content_x, content_y, content_w, content_h, cfg)
    elif tab_name == 'Players':
        _draw_players_tab(painter, draw_text, content_x, content_y, content_w, content_h, cfg)
    else:
        esp_rects = _compute_esp_item_rects(items, content_x, content_y, content_w) if tab_name == 'ESP' else None
        inner_w = content_w - 2 * BTN_INNER_MARGIN
        btn_cols_local = BTN_COLS if BTN_COLS > 0 else 1
        card_w = int((inner_w - BTN_H_SPACING * (btn_cols_local - 1)) / btn_cols_local)
        card_h = BTN_H
        grid_x0 = content_x + BTN_INNER_MARGIN
        grid_y0 = content_y + 34
        def _draw_card_button(idx: int, opt: Dict[str, str]) -> None:
            if tab_name == 'ESP' and esp_rects is not None:
                bx, by, bw, bh = esp_rects[idx]
            else:
                bx_row = idx // btn_cols_local
                bx_col = idx % btn_cols_local
                bx = grid_x0 + bx_col * (card_w + BTN_H_SPACING)
                by = grid_y0 + bx_row * (card_h + BTN_V_SPACING)
                bw, bh = (card_w, card_h)
            attr = opt.get('attr', '')
            enabled = bool(getattr(cfg, attr, False))
            esp_player_children = {'draw_player_text', 'draw_player_box', 'draw_player_skeleton', 'draw_player_head_cross'}
            esp_zombie_children = {'draw_zombie_text', 'draw_zombie_box', 'draw_zombie_skeleton', 'draw_zombie_head_cross'}
            is_esp_child = tab_name == 'ESP' and (attr in esp_player_children or attr in esp_zombie_children)
            if is_esp_child:
                base_color = THEME['panel_2'] if not enabled else THEME['active']
            else:
                base_color = THEME['btn_bg_on'] if enabled else THEME['btn_bg']
            if hover_row == idx:
                if is_esp_child:
                    base_color = THEME['hover']
                elif enabled:
                    base_color = (min(THEME['btn_bg_on'][0] + 20, 255), min(THEME['btn_bg_on'][1] + 20, 255), min(THEME['btn_bg_on'][2] + 20, 255))
                else:
                    base_color = THEME['btn_bg_hover']
            _fill_rect(painter, bx, by, bw, bh, base_color)
            _box(painter, bx, by, bw, bh, THEME['divider'])
            if is_esp_child:
                strip_col = THEME['accent'] if enabled else THEME['divider']
                _fill_rect(painter, bx, by, 3, card_h, strip_col)
            label_x = bx + (14 if is_esp_child else 8)
            draw_text(painter, label_x, by + 6, opt['label'].strip(), *THEME['text'])
            if tab_name == 'Items' and attr in _ITEM_ATTR_TO_CATEGORY:
                chip_rgb = None
                if hasattr(cfg, 'get_item_category_color'):
                    try:
                        chip_rgb = cfg.get_item_category_color(_ITEM_ATTR_TO_CATEGORY[attr])
                    except Exception:
                        chip_rgb = None
                if chip_rgb:
                    chip_w = 16
                    chip_h = 10
                    chip_x = bx + bw - 64
                    chip_y = by + (bh - chip_h) // 2
                    _fill_rect(painter, chip_x, chip_y, chip_w, chip_h, tuple((int(c) for c in chip_rgb)))
                    _box(painter, chip_x, chip_y, chip_w, chip_h, THEME['border'])
            state_str = 'ON' if enabled else 'OFF'
            state_col = THEME['accent_2'] if enabled else THEME['dim']
            led_center_x = bx + bw - 12
            led_center_y = by + bh // 2
            led_radius = 4
            led_rect = QtCore.QRect(int(led_center_x - led_radius), int(led_center_y - led_radius), led_radius * 2, led_radius * 2)
            led_col = THEME['accent'] if enabled else THEME['dim']
            painter.setPen(_pen(THEME['border'], 1))
            painter.setBrush(QtGui.QColor(*led_col))
            painter.drawEllipse(led_rect)
            state_y = int(led_center_y - 6)
            draw_text(painter, bx + bw - 40, state_y, state_str, *state_col)
        for idx, opt in enumerate(items):
            _draw_card_button(idx, opt)
        if tab_name == 'Waypoints':
            content_h = h - header_h - footer_h - 14
            layout_wp = _compute_waypoint_map_and_panel_layout(
                content_x,
                content_y,
                content_w,
                content_h,
                grid_y0,
                card_w,
                card_h,
                len(items),
                _waypoint_map_dropdown_open,
                len(_WAYPOINT_MAP_OPTIONS),
            )
            map_x, map_y, map_w, map_h = layout_wp['map_box']
            map_entries = layout_wp['map_entries']
            custom_panel_x, custom_panel_y, custom_panel_w, custom_panel_h = layout_wp['custom_panel_box']
            # draw map dropdown box
            base_col = THEME['btn_bg']
            if _waypoint_map_dropdown_open or _waypoint_map_dropdown_hover:
                base_col = THEME['btn_bg_hover']
            _fill_rect(painter, map_x, map_y, map_w, map_h, base_col)
            _box(painter, map_x, map_y, map_w, map_h, THEME['divider'])
            draw_text(painter, map_x + 8, map_y + 5, 'Map', *THEME['text'])
            current_map = getattr(cfg, 'waypoint_map', 'Chernarus')
            try:
                summary = str(current_map)
            except Exception:
                summary = 'Chernarus'
            draw_text(painter, map_x + 80, map_y + 5, summary, *THEME['muted'])
            arrow_cx = map_x + map_w - 14
            arrow_cy = map_y + map_h // 2
            tri = QtGui.QPolygon([
                QtCore.QPoint(arrow_cx - 5, arrow_cy - (3 if _waypoint_map_dropdown_open else 1)),
                QtCore.QPoint(arrow_cx + 5, arrow_cy - (3 if _waypoint_map_dropdown_open else 1)),
                QtCore.QPoint(arrow_cx, arrow_cy + (4 if _waypoint_map_dropdown_open else 5)),
            ])
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtGui.QColor(*THEME['muted']))
            painter.drawPolygon(tri)
            if _waypoint_map_dropdown_open and map_entries:
                for i, (ex, ey, ew, eh) in enumerate(map_entries):
                    hovered = _waypoint_map_dropdown_entry_hover_index == i
                    entry_base = THEME['panel'] if not hovered else THEME['hover']
                    _fill_rect(painter, ex, ey, ew, eh, entry_base)
                    _box(painter, ex, ey, ew, eh, THEME['divider'])
                    try:
                        label = _WAYPOINT_MAP_OPTIONS[i]
                    except Exception:
                        label = 'Chernarus'
                    draw_text(painter, ex + 8, ey + 3, label, *THEME['text'])
            # draw custom waypoint panel below dropdown
            _draw_waypoint_custom_panel(painter, draw_text, custom_panel_x, custom_panel_y, custom_panel_w, custom_panel_h)
        if tab_name == 'Items':
            rows = (len(items) + btn_cols_local - 1) // btn_cols_local if len(items) > 0 else 0
            if rows > 0:
                cards_bottom = grid_y0 + rows * (card_h + BTN_V_SPACING) - BTN_V_SPACING
            else:
                cards_bottom = grid_y0
            slider_y = cards_bottom + 28
            max_slider_y = content_y + content_h - 40
            if slider_y > max_slider_y:
                slider_y = max_slider_y
            min_v = 0.0
            max_v = 2000.0
            try:
                v = float(getattr(cfg, 'item_max_distance', 400.0))
            except Exception:
                v = 400.0
            if v < min_v:
                v = min_v
            if v > max_v:
                v = max_v
            setattr(cfg, 'item_max_distance', float(v))
            draw_text(painter, content_x + 14, slider_y - 12, 'Item Draw Distance', *THEME['text'])
            sx = content_x + 14
            sy = slider_y
            sw = content_w - 28
            sh = 18
            t = (v - min_v) / (max_v - min_v) if max_v > min_v else 0.0
            t = max(0.0, min(1.0, t))
            track_y = sy + sh // 2 - 2
            track_h = 4
            track_bg = (30, 30, 44)
            _fill_rect(painter, sx, track_y, sw, track_h, track_bg)
            filled_w = int(sw * t)
            if filled_w > 0:
                _fill_rect(painter, sx, track_y, filled_w, track_h, THEME['accent'])
            _box(painter, sx, track_y - 4, sw, track_h + 8, THEME['divider'])
            knob_x = sx + filled_w
            knob_r = 6
            knob_rect = QtCore.QRect(int(knob_x - knob_r), int(track_y + track_h // 2 - knob_r), int(knob_r * 2), int(knob_r * 2))
            knob_col = THEME['accent_2'] if _slider_dragging == 'item_max_distance' else (220, 220, 230)
            painter.setPen(_pen(THEME['border'], 1))
            painter.setBrush(QtGui.QColor(*knob_col))
            painter.drawEllipse(knob_rect)
            if v <= 0.0:
                value_text = 'All (unlimited)'
            else:
                value_text = f'{int(v)} m'
            draw_text(painter, content_x + content_w - 200, sy - 10, value_text, *THEME['muted'])
            draw_text(painter, sx, track_y + track_h + 6, '0 = unlimited', *THEME['dim'])
            draw_text(painter, sx + sw - 120, track_y + track_h + 6, 'Max 2000 m', *THEME['dim'])
        aimbot_on = bool(getattr(cfg, 'aimbot_enabled', False))
        if tab_name == 'Aimbot':
            layout = _compute_aimbot_bone_and_slider_layout(content_x, content_y, content_w, grid_x0, grid_y0, card_w, card_h, len(items), _bone_dropdown_open, len(_BONE_OPTIONS))
            bone_x, bone_y, bone_w, bone_h = layout['bone_box']
            bone_entries = layout['bone_entries']
            slider_y = layout['slider_y']
            base_col = THEME['btn_bg']
            if _bone_dropdown_open or _bone_dropdown_hover:
                base_col = THEME['btn_bg_hover']
            _fill_rect(painter, bone_x, bone_y, bone_w, bone_h, base_col)
            _box(painter, bone_x, bone_y, bone_w, bone_h, THEME['divider'])
            draw_text(painter, bone_x + 8, bone_y + 5, 'Bones', *THEME['text'])
            selected_names = []
            for name, attr in _BONE_OPTIONS:
                if bool(getattr(cfg, attr, False)):
                    selected_names.append(name)
            if selected_names:
                summary = ', '.join(selected_names)
            else:
                summary = 'None selected'
            draw_text(painter, bone_x + 80, bone_y + 5, summary, *THEME['muted'])
            arrow_cx = bone_x + bone_w - 14
            arrow_cy = bone_y + bone_h // 2
            tri = QtGui.QPolygon([QtCore.QPoint(arrow_cx - 5, arrow_cy - 3 if _bone_dropdown_open else arrow_cy - 1), QtCore.QPoint(arrow_cx + 5, arrow_cy - 3 if _bone_dropdown_open else arrow_cy - 1), QtCore.QPoint(arrow_cx, arrow_cy + 4 if _bone_dropdown_open else arrow_cy + 5)])
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtGui.QColor(*THEME['muted']))
            painter.drawPolygon(tri)
            if _bone_dropdown_open and bone_entries:
                for i, (ex, ey, ew, eh) in enumerate(bone_entries):
                    hovered = _bone_dropdown_entry_hover_index == i
                    entry_base = THEME['panel'] if not hovered else THEME['hover']
                    _fill_rect(painter, ex, ey, ew, eh, entry_base)
                    _box(painter, ex, ey, ew, eh, THEME['divider'])
                    label, attr = _BONE_OPTIONS[i]
                    enabled = bool(getattr(cfg, attr, False))
                    cb_size = 12
                    cb_x = ex + 6
                    cb_y = ey + (eh - cb_size) // 2
                    _box(painter, cb_x, cb_y, cb_size, cb_size, THEME['divider'])
                    if enabled:
                        _fill_rect(painter, cb_x + 2, cb_y + 2, cb_size - 3, cb_size - 3, THEME['accent'])
                    draw_text(painter, cb_x + cb_size + 6, ey + 3, label, *THEME['text'])
            for s in _AIMBOT_SLIDERS:
                attr = s['attr']
                min_v = s['min']
                max_v = s['max']
                try:
                    v = float(getattr(cfg, attr, min_v))
                except Exception:
                    v = min_v
                # Clamp into slider range
                v = max(min_v, min(max_v, v))
                setattr(cfg, attr, float(v))
                # Label above slider
                draw_text(painter, content_x + 14, slider_y - 12, s['label'], *THEME['text'])
                sx = content_x + 14
                sy = slider_y
                sw = content_w - 28
                sh = 18
                t = (v - min_v) / (max_v - min_v) if max_v > min_v else 0.0
                t = max(0.0, min(1.0, t))
                track_y = sy + sh // 2 - 2
                track_h = 4
                track_bg = (30, 30, 44)
                _fill_rect(painter, sx, track_y, sw, track_h, track_bg)
                filled_w = int(sw * t)
                if filled_w > 0:
                    _fill_rect(painter, sx, track_y, filled_w, track_h, THEME['accent'])
                _box(painter, sx, track_y - 4, sw, track_h + 8, THEME['divider'])
                knob_x = sx + filled_w
                knob_r = 6
                knob_rect = QtCore.QRect(int(knob_x - knob_r), int(track_y + track_h // 2 - knob_r), int(knob_r * 2), int(knob_r * 2))
                knob_col = THEME['accent_2'] if _slider_dragging == attr else (220, 220, 230)
                painter.setPen(_pen(THEME['border'], 1))
                painter.setBrush(QtGui.QColor(*knob_col))
                painter.drawEllipse(knob_rect)
                # Value / hint text differs per slider
                if attr == 'aimbot_smooth':
                    value_text = f'{v:.2f}'
                    rating_text = _smooth_rating_label(v, min_v, max_v)
                    combined = f'{value_text} | {rating_text}'
                    draw_text(painter, content_x + content_w - 150, sy - 10, combined, *THEME['muted'])
                    draw_text(painter, sx, track_y + track_h + 6, 'Fast', *THEME['dim'])
                    draw_text(painter, sx + sw - 52, track_y + track_h + 6, 'Smooth', *THEME['dim'])
                elif attr == 'aimbot_fov':
                    # Show FOV radius as integer and small/large hints
                    value_text = f'{int(v):d}'
                    draw_text(painter, content_x + content_w - 150, sy - 10, f'{value_text} radius', *THEME['muted'])
                    draw_text(painter, sx, track_y + track_h + 6, 'Small FOV', *THEME['dim'])
                    draw_text(painter, sx + sw - 80, track_y + track_h + 6, 'Large FOV', *THEME['dim'])
                else:
                    # Fallback generic label
                    value_text = f'{v:.2f}'
                    draw_text(painter, content_x + content_w - 150, sy - 10, value_text, *THEME['muted'])
                slider_y += 44
        if tab_name == 'Aimbot':
            try:
                vk = int(getattr(cfg, 'aimbot_key', VK_RBUTTON))
            except Exception:
                vk = VK_RBUTTON
            key_name = _vk_to_name(vk)
            listening = bool(getattr(cfg, 'aimbot_key_listen', False))
            if listening:
                status_msg = 'Listening for key / mouse press...'
            else:
                status_msg = "Click 'Aim Key Listener' and press a key or mouse button."
            info = f'Aim Key: {key_name}   |   {status_msg}'
            draw_text(painter, content_x + 14, slider_y - 6, info, *THEME['muted'])
    
    if tab_name == 'System':
        # Draw sliders for configurable world time and eye accommodation
        rows = (len(items) + btn_cols_local - 1) // btn_cols_local if len(items) > 0 else 0
        if rows > 0:
            cards_bottom = grid_y0 + rows * (card_h + BTN_V_SPACING) - BTN_V_SPACING
        else:
            cards_bottom = grid_y0
        slider_y = cards_bottom + 28
        max_slider_y = content_y + content_h - 40
        if slider_y > max_slider_y:
            slider_y = max_slider_y
        for i, s in enumerate(_SYSTEM_SLIDERS):
            attr = s['attr']
            min_v = float(s.get('min', 0.0))
            max_v = float(s.get('max', 1.0))
            try:
                v = float(getattr(cfg, attr, min_v))
            except Exception:
                v = min_v
            if v < min_v:
                v = min_v
            if v > max_v:
                v = max_v
            setattr(cfg, attr, float(v))
            label = s.get('label', attr)
            sy = slider_y + i * 40
            draw_text(painter, content_x + 14, sy - 12, label, *THEME['text'])
            sx = content_x + 14
            sw = content_w - 28
            sh = 18
            t = (v - min_v) / (max_v - min_v) if max_v > min_v else 0.0
            t = max(0.0, min(1.0, t))
            track_y = sy + sh // 2 - 2
            track_h = 4
            track_bg = (30, 30, 44)
            _fill_rect(painter, sx, track_y, sw, track_h, track_bg)
            filled_w = int(sw * t)
            if filled_w > 0:
                _fill_rect(painter, sx, track_y, filled_w, track_h, THEME['accent'])
            _box(painter, sx, track_y - 4, sw, track_h + 8, THEME['divider'])
            knob_x = sx + filled_w
            knob_r = 6
            knob_rect = QtCore.QRect(int(knob_x - knob_r), int(track_y + track_h // 2 - knob_r), int(knob_r * 2), int(knob_r * 2))
            knob_col = THEME['accent_2'] if _slider_dragging == attr else (220, 220, 230)
            painter.setPen(_pen(THEME['border'], 1))
            painter.setBrush(QtGui.QColor(*knob_col))
            painter.drawEllipse(knob_rect)
            value_text = f'{v:.2f}'
            draw_text(painter, sx, track_y + track_h + 6, value_text, *THEME['muted'])
    if tab_name == 'Items' and _active_color_attr in _ITEM_ATTR_TO_CATEGORY:
        _draw_item_color_picker(painter, draw_text, content_x, content_y, content_w, content_h, cfg)
    fy = y + h - footer_h
    _fill_rect(painter, x, fy, w, footer_h, THEME['footer'])
    _fill_rect(painter, x, fy, w, 1, THEME['divider'])
    draw_text(painter, content_x + 8, fy + 12, 'Click cards / use Bones dropdown / drag sliders. Auto-saves.', *THEME['dim'])
    exit_w, exit_h = (92, 26)
    exit_x = x + w - exit_w - 12
    exit_y = fy + (footer_h - exit_h) // 2
    fill_rgb = THEME['accent_2'] if exit_hover else (135, 30, 30)
    _fill_rect(painter, exit_x, exit_y, exit_w, exit_h, fill_rgb)
    _box(painter, exit_x, exit_y, exit_w, exit_h, THEME['accent_2'])
    draw_text(painter, exit_x + 26, exit_y + 6, 'EXIT', *THEME['text'])