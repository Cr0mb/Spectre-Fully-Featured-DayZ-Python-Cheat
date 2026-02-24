from __future__ import annotations
import os, sys
sys.dont_write_bytecode = True
os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')
from typing import List, Sequence, Tuple
import ctypes
import math
from Process.ent_esp import classify_actor_from_name, HEAD_OFFSET_PLAYER, HEAD_OFFSET_ZOMBIE
from Process.item_esp import esp_log
from Process.esp_config import ESPConfig
user32 = ctypes.windll.user32
MOUSEEVENTF_MOVE = 1
def _is_vk_down(vk: int) -> bool:
    try:
        return user32.GetAsyncKeyState(vk) & 32768 != 0
    except Exception:
        return False
_last_aim_debug: float = 0.0
_last_target_ent: int = 0
_last_best_dist: float = 0.0
def get_last_target_ent() -> int:
    return _last_target_ent
_AIM_BONE_FIELDS: Sequence[Tuple[str, str]] = (('head', 'aimbot_bone_head'), ('neck', 'aimbot_bone_neck'), ('chest', 'aimbot_bone_chest'), ('spine', 'aimbot_bone_spine'), ('pelvis', 'aimbot_bone_pelvis'))
def _get_enabled_logical_bones(cfg: ESPConfig) -> List[str]:
    enabled: List[str] = []
    for logical, attr in _AIM_BONE_FIELDS:
        try:
            if bool(getattr(cfg, attr, False)):
                enabled.append(logical)
        except Exception:
            continue
    if not enabled:
        enabled = ['head']
    return enabled
def _get_bone_world_pos(game, ent: int, actor_kind: str, logical_bone: str, fallback_pos: Tuple[float, float, float] | None):
    has_bone_helper = hasattr(game, 'get_bone_position_ws_for_entity')
    if logical_bone == 'head':
        if has_bone_helper:
            pos = game.get_bone_position_ws_for_entity(ent, actor_kind, 'head')
            if pos:
                return pos
        if fallback_pos is not None:
            x, y, z = fallback_pos
            off = HEAD_OFFSET_ZOMBIE if actor_kind == 'ZOMBIE' else HEAD_OFFSET_PLAYER
            return (x, y + off, z)
        return None
    if logical_bone == 'neck':
        if has_bone_helper:
            pos = game.get_bone_position_ws_for_entity(ent, actor_kind, 'neck')
            if pos:
                return pos
            pos = game.get_bone_position_ws_for_entity(ent, actor_kind, 'head')
            if pos:
                return pos
        if fallback_pos is not None:
            x, y, z = fallback_pos
            off = HEAD_OFFSET_ZOMBIE if actor_kind == 'ZOMBIE' else HEAD_OFFSET_PLAYER
            return (x, y + off * 0.9, z)
        return None
    if logical_bone == 'chest':
        if has_bone_helper:
            for name in ('spine3', 'spine2', 'spine1', 'spine'):
                pos = game.get_bone_position_ws_for_entity(ent, actor_kind, name)
                if pos:
                    return pos
        if fallback_pos is not None:
            x, y, z = fallback_pos
            off = HEAD_OFFSET_ZOMBIE if actor_kind == 'ZOMBIE' else HEAD_OFFSET_PLAYER
            return (x, y + off * 0.6, z)
        return None
    if logical_bone == 'spine':
        if has_bone_helper:
            for name in ('spine2', 'spine1', 'spine3', 'spine'):
                pos = game.get_bone_position_ws_for_entity(ent, actor_kind, name)
                if pos:
                    return pos
        if fallback_pos is not None:
            x, y, z = fallback_pos
            return (x, y + 0.5, z)
        return None
    if logical_bone == 'pelvis':
        if has_bone_helper:
            pos = game.get_bone_position_ws_for_entity(ent, actor_kind, 'pelvis')
            if pos:
                return pos
        if fallback_pos is not None:
            x, y, z = fallback_pos
            return (x, y + 0.1, z)
        return None
    return None
def _select_ent_for_aim(*, cfg: ESPConfig, game, cam_state, screen_w: int, screen_h: int, actor_ptrs: List[int], local_player_ent: int, logical_bones: List[str], fov_radius_sq: float) -> Tuple[int, float, float, float] | None:
    global _last_target_ent
    aim_players = bool(getattr(cfg, 'aimbot_players', True))
    aim_zombies = bool(getattr(cfg, 'aimbot_zombies', True))
    cx = screen_w / 2.0
    cy = screen_h / 2.0
    locked_candidate: Tuple[int, float, float, float] | None = None
    if _last_target_ent and _last_target_ent in actor_ptrs:
        ent = _last_target_ent
        try:
            name = game.get_entity_name(ent) or ''
        except Exception:
            name = ''
        actor_kind = classify_actor_from_name(name)
        is_dead = False
        if actor_kind == 'PLAYER' and hasattr(game, 'is_dead'):
            try:
                is_dead = bool(game.is_dead(ent))
            except Exception:
                is_dead = False
        if is_dead:
            pass
        elif actor_kind == 'PLAYER' and hasattr(game, 'is_friend_entity'):
            try:
                if game.is_friend_entity(ent):
                    pass
                elif not aim_players:
                    pass
                else:
                    raise RuntimeError
            except RuntimeError:
                pass
            except Exception:
                if not aim_players:
                    pass
        elif actor_kind == 'PLAYER' and (not aim_players):
            pass
        elif actor_kind == 'ZOMBIE' and (not aim_zombies):
            pass
        elif actor_kind not in ('PLAYER', 'ZOMBIE'):
            pass
        else:
            try:
                ent_pos = game.get_entity_position(ent)
            except Exception:
                ent_pos = None
            if ent_pos:
                best_for_ent = None
                for logical in logical_bones:
                    wpos = _get_bone_world_pos(game, ent, actor_kind, logical, ent_pos)
                    if not wpos:
                        continue
                    try:
                        proj = game.world_to_screen_state(wpos, cam_state)
                    except Exception:
                        proj = None
                    if not proj:
                        continue
                    sx, sy, _ = proj
                    dx = float(sx) - cx
                    dy = float(sy) - cy
                    dist_sq = dx * dx + dy * dy
                    if dist_sq > fov_radius_sq * 4.0:
                        continue
                    if best_for_ent is None or dist_sq < best_for_ent[0]:
                        best_for_ent = (dist_sq, dx, dy)
                if best_for_ent is not None:
                    dist_sq, dx, dy = best_for_ent
                    locked_candidate = (ent, dx, dy, dist_sq)
    if locked_candidate is not None:
        return locked_candidate
    best_ent = 0
    best_dx = 0.0
    best_dy = 0.0
    best_dist_sq: float | None = None
    prefer_crosshair = bool(getattr(cfg, 'aimbot_closest_to_crosshair', True))
    for ent in actor_ptrs:
        if not ent or ent == local_player_ent:
            continue
        try:
            name = game.get_entity_name(ent) or ''
        except Exception:
            name = ''
        actor_kind = classify_actor_from_name(name)
        is_dead = False
        if actor_kind == 'PLAYER' and hasattr(game, 'is_dead'):
            try:
                is_dead = bool(game.is_dead(ent))
            except Exception:
                is_dead = False
        if is_dead:
            continue
        if actor_kind == 'PLAYER':
            if not aim_players:
                continue
        elif actor_kind == 'ZOMBIE':
            if not aim_zombies:
                continue
        else:
            continue
        try:
            ent_pos = game.get_entity_position(ent)
        except Exception:
            ent_pos = None
        if not ent_pos:
            continue

        # Limit mouse aim to a maximum world distance from the camera (in meters)
        try:
            max_dist = float(getattr(cfg, 'mouse_aim_max_distance', 0.0) or 0.0)
        except Exception:
            max_dist = 0.0
        if max_dist > 0.0:
            cam_pos = None
            if cam_state:
                try:
                    cam_pos = cam_state[0]
                except Exception:
                    cam_pos = None
            if cam_pos is not None:
                try:
                    ex, ey, ez = ent_pos
                    cxw, cyw, czw = cam_pos
                    dxw = float(ex) - float(cxw)
                    dyw = float(ey) - float(cyw)
                    dzw = float(ez) - float(czw)
                    dist_sq = dxw * dxw + dyw * dyw + dzw * dzw
                    if dist_sq > (max_dist * max_dist):
                        continue
                except Exception:
                    pass
        best_for_ent = None
        for logical in logical_bones:
            wpos = _get_bone_world_pos(game, ent, actor_kind, logical, ent_pos)
            if not wpos:
                continue
            try:
                proj = game.world_to_screen_state(wpos, cam_state)
            except Exception:
                proj = None
            if not proj:
                continue
            sx, sy, _ = proj
            dx = float(sx) - cx
            dy = float(sy) - cy
            dist_sq = dx * dx + dy * dy
            if dist_sq > fov_radius_sq:
                continue
            if best_for_ent is None or dist_sq < best_for_ent[0]:
                best_for_ent = (dist_sq, dx, dy)
        if best_for_ent is None:
            continue
        dist_sq, dx, dy = best_for_ent
        if prefer_crosshair:
            score = dist_sq
        else:
            wx, wy, wz = ent_pos
            score = wx * wx + wy * wy + wz * wz
        if best_dist_sq is None or score < best_dist_sq:
            best_dist_sq = score
            best_ent = ent
            best_dx = dx
            best_dy = dy
    if best_dist_sq is None or not best_ent:
        return None
    dist_sq = best_dx * best_dx + best_dy * best_dy
    return (best_ent, best_dx, best_dy, dist_sq)
def run_external_mouse_aim(*, cfg: ESPConfig, game, cam_state, screen_w: int, screen_h: int, actor_ptrs: List[int], local_player_ent: int, scene, now: float) -> None:
    global _last_aim_debug, _last_target_ent, _last_best_dist
    if not (getattr(cfg, 'aimbot_enabled', False) or getattr(cfg, 'silent_aim_enabled', False)):
        if hasattr(scene, 'aimbot_active'):
            scene.aimbot_active = False
        _last_target_ent = 0
        _last_best_dist = 0.0
        return
    try:
        vk = int(getattr(cfg, 'aimbot_key', 2))
    except Exception:
        vk = 2
    if vk <= 0 or not _is_vk_down(vk):
        if hasattr(scene, 'aimbot_active'):
            scene.aimbot_active = False
        _last_target_ent = 0
        _last_best_dist = 0.0
        return
    if not actor_ptrs or not local_player_ent:
        if hasattr(scene, 'aimbot_active'):
            scene.aimbot_active = False
        _last_target_ent = 0
        _last_best_dist = 0.0
        return
    try:
        fov_radius = float(getattr(cfg, 'aimbot_fov', 250.0))
    except Exception:
        fov_radius = 250.0
    if fov_radius <= 0.0:
        if hasattr(scene, 'aimbot_active'):
            scene.aimbot_active = False
        _last_target_ent = 0
        _last_best_dist = 0.0
        return
    fov_radius_sq = fov_radius * fov_radius
    logical_bones = _get_enabled_logical_bones(cfg)
    try:
        base_smooth = float(getattr(cfg, 'aimbot_smooth', 8.0))
    except Exception:
        base_smooth = 8.0
    if base_smooth < 1.0:
        base_smooth = 1.0
    sel = _select_ent_for_aim(cfg=cfg, game=game, cam_state=cam_state, screen_w=screen_w, screen_h=screen_h, actor_ptrs=actor_ptrs, local_player_ent=local_player_ent, logical_bones=logical_bones, fov_radius_sq=fov_radius_sq)
    if sel is None:
        if hasattr(scene, 'aimbot_active'):
            scene.aimbot_active = False
        _last_target_ent = 0
        _last_best_dist = 0.0
        return
    ent, best_dx, best_dy, best_dist_sq = sel
    dist = math.sqrt(best_dist_sq)
    deadzone_base = max(1.5, fov_radius * 0.01)
    deadzone = deadzone_base / max(1.0, base_smooth / 4.0)
    if dist <= deadzone:
        if hasattr(scene, 'aimbot_active'):
            scene.aimbot_active = False
        _last_target_ent = ent
        _last_best_dist = dist
        return
    smooth = base_smooth
    step_x = best_dx / smooth
    step_y = best_dy / smooth
    if abs(step_x) < 1.0 and abs(best_dx) > deadzone:
        step_x = 1.0 if best_dx > 0.0 else -1.0
    if abs(step_y) < 1.0 and abs(best_dy) > deadzone:
        step_y = 1.0 if best_dy > 0.0 else -1.0
    move_x = int(step_x)
    move_y = int(step_y)
    if move_x == 0 and move_y == 0:
        if hasattr(scene, 'aimbot_active'):
            scene.aimbot_active = False
        _last_target_ent = ent
        _last_best_dist = dist
        return
    max_step = 18
    if move_x > max_step:
        move_x = max_step
    elif move_x < -max_step:
        move_x = -max_step
    if move_y > max_step:
        move_y = max_step
    elif move_y < -max_step:
        move_y = -max_step
    if getattr(cfg, 'aimbot_enabled', False):
        try:
            user32.mouse_event(MOUSEEVENTF_MOVE, move_x, move_y, 0, 0)
        except Exception:
            if hasattr(scene, 'aimbot_active'):
                scene.aimbot_active = False
            _last_target_ent = 0
            _last_best_dist = 0.0
            return
    if hasattr(scene, 'aimbot_active'):
        scene.aimbot_active = True
    _last_target_ent = ent
    _last_best_dist = dist
    if getattr(cfg, 'debug_logging', False):
        if now - _last_aim_debug >= 0.25:
            try:
                esp_log(f'aim step: dx={move_x} dy={move_y} dist={dist:.1f} smooth={smooth:.2f} raw_dx={best_dx:.1f} raw_dy={best_dy:.1f}')
            except Exception:
                pass
            _last_aim_debug = now
