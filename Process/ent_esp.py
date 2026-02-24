from __future__ import annotations
import os, sys
sys.dont_write_bytecode = True
os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')
from typing import Any, Dict, List, Optional, Tuple
from Process.esp_config import ESPConfig
from Process.item_esp import esp_log
HEAD_OFFSET_PLAYER = 1.6
HEAD_OFFSET_ZOMBIE = 1.4
PLAYER_COLOR = (0, 255, 0)
ZOMBIE_COLOR = (255, 0, 0)
VEHICLE_COLOR = (0, 128, 255)
ANIMAL_COLOR = (255, 165, 0)
CORPSE_COLOR = (160, 160, 160)
AIMBOT_SKELETON_COLOR_PLAYER = (255, 255, 0)
AIMBOT_SKELETON_COLOR_ZOMBIE = (0, 255, 255)
MAX_ACTOR_ESPS_PER_TICK = 96
MAX_SKELETON_ACTORS_PER_TICK = MAX_ACTOR_ESPS_PER_TICK
SKELETON_VISUAL_MAX_DISTANCE = 175.0
SKELETON_VISUAL_MAX_DISTANCE_SQ = SKELETON_VISUAL_MAX_DISTANCE * SKELETON_VISUAL_MAX_DISTANCE
def classify_actor_from_name(name: str) -> str:
    if not name:
        return 'PLAYER'
    n = name.lower().strip()
    if name == 'zombie':
        return 'ZOMBIE'
    if name.startswith('TreeEffecter') or 'AreaDamageTriggerBase' in name or 'AreaDamage' in name:
        return 'WORLD_OBJECT'
    if any((k in n for k in ('boat', 'ship'))):
        return 'VEHICLE'
    if any((k in n for k in ('truck', 'bus', 'sedan', 'hatchback', 'offroad', 'tractor', 'car '))):
        return 'VEHICLE'
    if any((k in n for k in ('animal', 'cow', 'goat', 'sheep', 'chicken', 'hen', 'rooster', 'wolf', 'bear', 'deer', 'stag', 'boar', 'fox', 'rabbit'))):
        return 'ANIMAL'
    if 'survivor' in n:
        return 'PLAYER'
    return 'PLAYER'
def normalize_player_name(name: str, actor_kind: str) -> str:
    if not name:
        return ''
    if actor_kind == 'PLAYER' and name.startswith(('SurvivorM', 'SurvivorF')):
        return 'Survivor'
    return name
def build_actor_scene(helper: Any, cfg: ESPConfig, game: Any, cam_state, screen_w: int, screen_h: int, frame_index: int, actor_ptrs: List[int], *, scene: Any) -> Tuple[Any, Optional[Tuple[float, float, float]], int]:
    if not cfg.esp_enabled or not actor_ptrs:
        return (scene, None, 0)
    draw_players = getattr(cfg, 'draw_players', True)
    draw_zombies = getattr(cfg, 'draw_zombies', True)
    draw_animals = getattr(cfg, 'draw_animal_text', True)
    draw_vehicles = getattr(cfg, 'draw_vehicles', True)
    any_actor_esp = draw_players or draw_zombies or draw_animals or draw_vehicles
    if not any_actor_esp:
        return (scene, None, 0)
    player_list_rows: List[Tuple[str, str, float, bool]] = []
    draw_player_skeleton = bool(getattr(cfg, 'draw_player_skeleton', False))
    draw_zombie_skeleton = bool(getattr(cfg, 'draw_zombie_skeleton', False))
    draw_player_head_cross = bool(getattr(cfg, 'draw_player_head_cross', True))
    draw_zombie_head_cross = bool(getattr(cfg, 'draw_zombie_head_cross', True))
    draw_player_text = bool(getattr(cfg, 'draw_player_text', True))
    draw_zombie_text = bool(getattr(cfg, 'draw_zombie_text', True))
    draw_animal_text = bool(getattr(cfg, 'draw_animal_text', True))
    draw_player_distance = bool(getattr(cfg, 'draw_player_distance', True))
    draw_zombie_distance = bool(getattr(cfg, 'draw_zombie_distance', True))
    draw_player_corpses = bool(getattr(cfg, 'draw_player_corpses', True))
    draw_zombie_corpses = bool(getattr(cfg, 'draw_zombie_corpses', True))
    if actor_ptrs and len(actor_ptrs) > MAX_ACTOR_ESPS_PER_TICK:
        actor_ptrs = actor_ptrs[:MAX_ACTOR_ESPS_PER_TICK]
    pos_cache: Dict[int, Tuple[float, float, float]] = {}
    name_cache: Dict[int, str] = {}
    skel_actors_used = 0
    local_player_ent = 0
    local_player_pos: Optional[Tuple[float, float, float]] = None
    try:
        cam_pos = cam_state[0]
    except Exception:
        cam_pos = (0.0, 0.0, 0.0)
    closest_dist2 = float('inf')
    for ent in actor_ptrs:
        pos = game.get_entity_position(ent)
        if not pos:
            continue
        pos_cache[ent] = pos
        dx = pos[0] - cam_pos[0]
        dy = pos[1] - cam_pos[1]
        dz = pos[2] - cam_pos[2]
        dist2 = dx * dx + dy * dy + dz * dz
        if dist2 < closest_dist2:
            closest_dist2 = dist2
            local_player_ent = ent
            local_player_pos = pos
    if not (local_player_ent and closest_dist2 < 25.0):
        local_player_ent = 0
        local_player_pos = None
    try:
        aimbot_target_ent = int(getattr(helper, 'aimbot_target_ent', 0) or 0)
    except Exception:
        aimbot_target_ent = 0
    for ent in actor_ptrs:
        if local_player_ent and ent == local_player_ent:
            continue
        pos = pos_cache.get(ent)
        if pos is None:
            pos = game.get_entity_position(ent)
            if not pos:
                continue
            pos_cache[ent] = pos
        dx = pos[0] - cam_pos[0]
        dy = pos[1] - cam_pos[1]
        dz = pos[2] - cam_pos[2]
        dist2 = dx * dx + dy * dy + dz * dz
        dist_m = dist2 ** 0.5
        w2s = game.world_to_screen_state(pos, cam_state)
        if not w2s:
            continue
        sx_raw, sy_raw, depth = w2s
        sx = int(max(0, min(screen_w - 1, sx_raw)))
        sy = int(max(0, min(screen_h - 1, sy_raw)))
        name: Optional[str] = name_cache.get(ent)
        if name is None:
            name = game.get_entity_name(ent)
            if name:
                name_cache[ent] = name
        actor_kind = classify_actor_from_name(name or '')
        wants_player_for_esp = draw_players
        wants_zombie_for_esp = draw_zombies
        wants_animal_for_esp = draw_animals
        wants_vehicle_for_esp = draw_vehicles
        if actor_kind == 'PLAYER' and (not wants_player_for_esp):
            continue
        if actor_kind == 'ZOMBIE' and (not wants_zombie_for_esp):
            continue
        if actor_kind == 'ANIMAL' and (not wants_animal_for_esp):
            continue
        if actor_kind == 'VEHICLE' and (not wants_vehicle_for_esp):
            continue
        is_dead = False
        if actor_kind in ('PLAYER', 'ZOMBIE') and hasattr(game, 'is_dead'):
            try:
                is_dead = bool(game.is_dead(ent))
            except Exception:
                is_dead = False
        if is_dead:
            if actor_kind == 'PLAYER' and (not draw_player_corpses):
                continue
            if actor_kind == 'ZOMBIE' and (not draw_zombie_corpses):
                continue
        is_friend = False
        if actor_kind == 'PLAYER' and hasattr(game, 'is_friend_entity'):
            try:
                is_friend = bool(game.is_friend_entity(ent))
            except Exception:
                is_friend = False
        if actor_kind == 'PLAYER':
            steam_id = ''
            nid_value = 0
            if hasattr(game, 'get_entity_network_id'):
                try:
                    nid_value = int(game.get_entity_network_id(ent))
                except Exception:
                    nid_value = 0
            if hasattr(game, 'get_entity_steam_id'):
                try:
                    steam_id = game.get_entity_steam_id(ent) or ''
                except Exception:
                    steam_id = ''
            if not steam_id and nid_value:
                steam_id = f'nid:{nid_value}'
            label_name = normalize_player_name(name or '', actor_kind)
            try:
                dist_value = float(dist_m)
            except Exception:
                dist_value = 0.0
            player_list_rows.append((label_name, steam_id, dist_value if dist_value > 0.0 else 0.0, bool(is_friend)))
            if is_friend:
                fr = getattr(cfg, 'friend_color_player', (80, 200, 255))
                try:
                    cr, cg, cb = (int(fr[0]), int(fr[1]), int(fr[2]))
                except Exception:
                    cr, cg, cb = PLAYER_COLOR
            elif is_dead:
                cr, cg, cb = CORPSE_COLOR
            else:
                cr, cg, cb = PLAYER_COLOR
        elif actor_kind == 'ZOMBIE':
            cr, cg, cb = ZOMBIE_COLOR
        elif actor_kind == 'VEHICLE':
            cr, cg, cb = VEHICLE_COLOR
        elif actor_kind == 'ANIMAL':
            cr, cg, cb = ANIMAL_COLOR
        else:
            cr, cg, cb = PLAYER_COLOR
        is_zombie = actor_kind == 'ZOMBIE'
        is_aim_target = bool(aimbot_target_ent and ent == aimbot_target_ent and (actor_kind in ('PLAYER', 'ZOMBIE')))
        if is_aim_target:
            if actor_kind == 'PLAYER':
                skel_color = AIMBOT_SKELETON_COLOR_PLAYER
            else:
                skel_color = AIMBOT_SKELETON_COLOR_ZOMBIE
            cr, cg, cb = skel_color
        else:
            skel_color = (cr, cg, cb)
        if actor_kind == 'PLAYER':
            need_skeleton_for_visual = bool(draw_player_skeleton or draw_player_head_cross)
        elif actor_kind == 'ZOMBIE':
            need_skeleton_for_visual = bool(draw_zombie_skeleton or draw_zombie_head_cross)
        else:
            need_skeleton_for_visual = False
        use_skeleton = need_skeleton_for_visual
        keypoints: Dict[str, Optional[Tuple[int, int]]] = {}
        skel_segments: List[Tuple[int, int, int, int]] = []
        if use_skeleton:
            dx = pos[0] - cam_pos[0]
            dy = pos[1] - cam_pos[1]
            dz = pos[2] - cam_pos[2]
            dist2 = dx * dx + dy * dy + dz * dz
            if dist2 > SKELETON_VISUAL_MAX_DISTANCE_SQ:
                use_skeleton = False
        if use_skeleton and skel_actors_used >= MAX_SKELETON_ACTORS_PER_TICK:
            use_skeleton = False
        if use_skeleton:
            keypoints, skel_segments = game.build_skeleton_2d(ent, actor_kind, cam_state, screen_w, screen_h)
            if skel_segments:
                skel_actors_used += 1
        head_2d = keypoints.get('head') if keypoints else None
        if skel_segments:
            if actor_kind == 'PLAYER' and draw_player_skeleton:
                for x0, y0, x1, y1 in skel_segments:
                    scene.actor_skeletons.append((x0, y0, x1, y1, skel_color))
            elif actor_kind == 'ZOMBIE' and draw_zombie_skeleton:
                for x0, y0, x1, y1 in skel_segments:
                    scene.actor_skeletons.append((x0, y0, x1, y1, skel_color))
        if head_2d:
            hx_raw, hy_raw = head_2d
        else:
            head_offset = HEAD_OFFSET_ZOMBIE if is_zombie else HEAD_OFFSET_PLAYER
            head_pos = (pos[0], pos[1] + head_offset, pos[2])
            w2s_head = game.world_to_screen_state(head_pos, cam_state)
            if not w2s_head:
                continue
            hx_raw, hy_raw, _ = w2s_head
        if actor_kind in ('PLAYER', 'ZOMBIE', 'ANIMAL'):
            if skel_segments:
                min_y = screen_h
                max_y = 0
                for x0, y0, x1, y1 in skel_segments:
                    if y0 < min_y:
                        min_y = y0
                    if y1 < min_y:
                        min_y = y1
                    if y0 > max_y:
                        max_y = y0
                    if y1 > max_y:
                        max_y = y1
                top = int(max(0, min(screen_h - 1, min_y - 2)))
                bottom = int(max(0, min(screen_h - 1, max_y + 2)))
                box_h = bottom - top
            else:
                top_raw = min(sy_raw, hy_raw) - 4.0
                bottom_raw = max(sy_raw, hy_raw) + 4.0
                top = int(max(0, min(screen_h - 1, top_raw)))
                bottom = int(max(0, min(screen_h - 1, bottom_raw)))
                box_h = bottom - top
            MIN_HEIGHT = 18
            MAX_HEIGHT = screen_h // 2
            if box_h < MIN_HEIGHT:
                center_y = (top + bottom) // 2
                half = MIN_HEIGHT // 2
                top = max(0, center_y - half)
                bottom = min(screen_h - 1, center_y + half)
                box_h = bottom - top
            elif box_h > MAX_HEIGHT:
                center_y = (top + bottom) // 2
                half = MAX_HEIGHT // 2
                top = max(0, center_y - half)
                bottom = min(screen_h - 1, center_y + half)
                box_h = bottom - top
            if actor_kind == 'VEHICLE':
                width_scale = 1.5
            elif actor_kind == 'ANIMAL':
                width_scale = 0.6
            else:
                width_scale = 0.45
            box_w = int(max(8, box_h * width_scale))
            left = int(sx - box_w // 2)
            right = int(sx + box_w // 2)
            left = max(0, min(screen_w - 1, left))
            right = max(0, min(screen_w - 1, right))
            if right > left and bottom > top:
                if actor_kind == 'PLAYER' and getattr(cfg, 'draw_player_box', False):
                    scene.actor_boxes.append((left, top, right, bottom, (cr, cg, cb)))
                elif actor_kind == 'ZOMBIE' and getattr(cfg, 'draw_zombie_box', False):
                    scene.actor_boxes.append((left, top, right, bottom, (cr, cg, cb)))
                hx = int(max(0, min(screen_w - 1, hx_raw)))
                hy = int(max(0, min(screen_h - 1, hy_raw)))
                if actor_kind == 'PLAYER' and draw_player_head_cross:
                    scene.actor_heads.append((hx, hy))
                elif actor_kind == 'ZOMBIE' and draw_zombie_head_cross:
                    scene.actor_heads.append((hx, hy))
                text_x = left + (right - left) // 2
                if is_zombie or actor_kind == 'PLAYER':
                    text_y = min(screen_h - 16, bottom + 2)
                else:
                    text_y = max(0, top - 14)
                if name:
                    if actor_kind == 'PLAYER' and (not draw_player_text):
                        pass
                    elif actor_kind == 'ZOMBIE' and (not draw_zombie_text):
                        pass
                    elif actor_kind == 'ANIMAL' and (not draw_animal_text):
                        pass
                    else:
                        display_name = normalize_player_name(name, actor_kind) if actor_kind in ('PLAYER', 'ZOMBIE') else name
                        offset_x = len(display_name) * 3
                        scene.actor_labels.append((text_x - offset_x, text_y, display_name, (cr, cg, cb)))
                if dist_m > 0.0:
                    show_dist = False
                    if actor_kind == 'PLAYER' and draw_player_distance:
                        show_dist = True
                    elif actor_kind == 'ZOMBIE' and draw_zombie_distance:
                        show_dist = True
                    if show_dist:
                        try:
                            dist_text = f'{int(dist_m)}m'
                        except Exception:
                            dist_text = ''
                        if dist_text:
                            dist_y = text_y + 12
                            dist_offset_x = len(dist_text) * 3
                            scene.actor_labels.append((text_x - dist_offset_x, dist_y, dist_text, (cr, cg, cb)))
    try:
        player_list_rows.sort(key=lambda row: row[2])
    except Exception:
        pass
    try:
        scene.player_list_rows = player_list_rows
    except Exception:
        pass
    return (scene, local_player_pos, local_player_ent)
__all__ = ['HEAD_OFFSET_PLAYER', 'HEAD_OFFSET_ZOMBIE', 'PLAYER_COLOR', 'ZOMBIE_COLOR', 'VEHICLE_COLOR', 'ANIMAL_COLOR', 'MAX_ACTOR_ESPS_PER_TICK', 'MAX_SKELETON_ACTORS_PER_TICK', 'SKELETON_VISUAL_MAX_DISTANCE', 'SKELETON_VISUAL_MAX_DISTANCE_SQ', 'classify_actor_from_name', 'normalize_player_name', 'build_actor_scene']
