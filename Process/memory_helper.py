from __future__ import annotations
import os, sys
sys.dont_write_bytecode = True
os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')
from typing import List, Tuple, Optional, Dict, Callable
import ctypes
import os
import re
import time
from functools import lru_cache
from Process.esp_config import ESPConfig, get_custom_waypoints_cached, set_custom_waypoints
from menu import update_item_search_items, update_player_list
user32 = ctypes.windll.user32
VK_F7 = 118
def _pressed_once_vk(vk: int) -> bool:
    try:
        return user32.GetAsyncKeyState(vk) & 1 != 0
    except Exception:
        return False
def _get_custom_waypoints_cached() -> list[dict]:
    return get_custom_waypoints_cached()
def _add_custom_waypoint_from_pos(name: str, x: float, z: float) -> None:
    wps = list(get_custom_waypoints_cached())
    wps.append({'name': str(name), 'x': float(x), 'z': float(z)})
    set_custom_waypoints(wps)
from Process.item_esp import ITEM_NAME_FILE, esp_log, load_item_names, save_item_names, MAX_ITEM_ESPS_PER_TICK, ITEM_SEARCH_REFRESH_INTERVAL, ITEM_WORLD_REFRESH_INTERVAL, ITEM_CATEGORY_COLORS, ITEM_CATEGORY_CONFIG_ATTR, categorize_item, get_item_display, build_item_scene
from Process.ent_esp import build_actor_scene, MAX_ACTOR_ESPS_PER_TICK, classify_actor_from_name
from Process.waypoint_esp import build_waypoint_labels
from Features.mouse_aim import run_external_mouse_aim, get_last_target_ent
class ESPScene:
    __slots__ = ('actor_boxes', 'actor_heads', 'actor_labels', 'actor_skeletons', 'item_labels', 'waypoint_labels', 'player_list_rows')
    def __init__(self) -> None:
        self.actor_boxes: List[Tuple[int, int, int, int, Tuple[int, int, int]]] = []
        self.actor_heads: List[Tuple[int, int]] = []
        self.actor_labels: List[Tuple[int, int, str, Tuple[int, int, int]]] = []
        self.actor_skeletons: List[Tuple[int, int, int, int, Tuple[int, int, int]]] = []
        self.item_labels: List[Tuple[int, int, str, Tuple[int, int, int]]] = []
        self.waypoint_labels: List[Tuple[int, int, str, Tuple[int, int, int]]] = []
        self.player_list_rows: List[Tuple[str, str, float, bool]] = []
class ESPMemoryHelper:
    def __init__(self, item_name_set: Optional[set[str]]=None) -> None:
        self.item_name_set: set[str] = item_name_set if item_name_set is not None else set()
        self.item_names_dirty: bool = False
        self.last_item_names_flush: float = time.perf_counter()
        self._last_item_world_refresh: float = 0.0
        self._cached_item_ptrs: List[int] = []
        self._cached_item_positions: Dict[int, Tuple[float, float, float]] = {}
        self._last_item_search_refresh: float = 0.0
        self._item_search_labels_cache: List[str] = []
        self._item_name_cache: Dict[int, str] = {}
        self._last_debug_print: float = 0.0
        self.last_actor_count: int = 0
        self.last_item_count: int = 0
        self.last_scene_build_ms: float = 0.0
        self.aimbot_target_ent: int = 0
    def build_scene(self, cfg: ESPConfig, game, cam_state, screen_w: int, screen_h: int, frame_index: int=0, scene_cls=ESPScene) -> 'ESPScene':
        start_ts = time.perf_counter()
        now = start_ts
        scene = scene_cls()
        draw_players = getattr(cfg, 'draw_players', True)
        draw_zombies = getattr(cfg, 'draw_zombies', True)
        draw_animals = getattr(cfg, 'draw_animal_text', True)
        draw_vehicles = getattr(cfg, 'draw_vehicles', True)
        any_actor_esp = draw_players or draw_zombies or draw_animals or draw_vehicles
        want_actors = bool(cfg.esp_enabled and any_actor_esp)
        want_items = bool(cfg.esp_enabled and getattr(cfg, 'draw_items', False))
        actor_ptrs: list[int] = []
        if want_actors:
            try:
                actor_ptrs = game.get_actor_entity_ptrs() or []
            except Exception:
                actor_ptrs = []
            if actor_ptrs and len(actor_ptrs) > MAX_ACTOR_ESPS_PER_TICK:
                actor_ptrs = actor_ptrs[:MAX_ACTOR_ESPS_PER_TICK]
            filtered_actor_ptrs: list[int] = []
            for ent in actor_ptrs:
                try:
                    entity_name = game.get_entity_name(ent) or ''
                except Exception:
                    entity_name = ''
                actor_kind = classify_actor_from_name(entity_name)
                if actor_kind == 'WORLD_OBJECT':
                    continue
                if 'TrapTrigger' in entity_name or 'ContaminatedTrigger_Dynamic' in entity_name:
                    continue
                filtered_actor_ptrs.append(ent)
            actor_ptrs = filtered_actor_ptrs
        item_ptrs: list[int] = []
        if want_items:
            try:
                raw_item_ptrs = game.get_item_entity_ptrs() or []
            except Exception:
                raw_item_ptrs = []
            if raw_item_ptrs and len(raw_item_ptrs) > MAX_ITEM_ESPS_PER_TICK:
                raw_item_ptrs = raw_item_ptrs[:MAX_ITEM_ESPS_PER_TICK]
            if not self._cached_item_ptrs or not self._cached_item_positions or now - self._last_item_world_refresh >= ITEM_WORLD_REFRESH_INTERVAL:
                self._cached_item_ptrs = list(raw_item_ptrs)
                cached_positions: dict[int, tuple[float, float, float]] = {}
                for ent in self._cached_item_ptrs:
                    try:
                        pos = game.get_entity_position(ent)
                    except Exception:
                        pos = None
                    if pos:
                        cached_positions[ent] = pos
                self._cached_item_positions = cached_positions
                self._last_item_world_refresh = now
            item_ptrs = list(self._cached_item_ptrs)
        else:
            self._cached_item_ptrs = []
            self._cached_item_positions.clear()
        if getattr(cfg, 'debug_logging', False):
            try:
                if now - self._last_debug_print >= 1.0:
                    esp_log(f'frame={frame_index} actors={len(actor_ptrs)} items={len(item_ptrs)}')
                    self._last_debug_print = now
            except Exception:
                pass
        local_player_pos = None
        local_player_ent = 0
        if want_actors and actor_ptrs:
            scene, local_player_pos, local_player_ent = build_actor_scene(helper=self, cfg=cfg, game=game, cam_state=cam_state, screen_w=screen_w, screen_h=screen_h, frame_index=frame_index, actor_ptrs=actor_ptrs, scene=scene)
        if want_actors and actor_ptrs and local_player_ent:
    # ←←← INSERT THE NEW PLAYER LIST BLOCK HERE ←←←
            # === PLAYER LIST FOR MENU (full server + SteamIDs) ===
            try:
                if hasattr(game, 'get_player_list_for_menu'):
                    scene.player_list_rows = game.get_player_list_for_menu()
                # else: keep rows set by build_actor_scene as fallback
            except Exception as e:
                if getattr(cfg, 'debug_logging', False):
                    esp_log(f"[MENU] Failed to get full player list: {e}")
            try:
                run_external_mouse_aim(cfg=cfg, game=game, cam_state=cam_state, screen_w=screen_w, screen_h=screen_h, actor_ptrs=actor_ptrs, local_player_ent=local_player_ent, scene=scene, now=now)
            except Exception:
                pass
            try:
                self.aimbot_target_ent = int(get_last_target_ent() or 0)
            except Exception:
                self.aimbot_target_ent = 0
            try:
                if hasattr(scene, 'aimbot_target_ent'):
                    scene.aimbot_target_ent = int(self.aimbot_target_ent)
            except Exception:
                pass
            try:
                if getattr(cfg, 'silent_aim_enabled', False):
                    target_ent = int(self.aimbot_target_ent or 0)
                    if target_ent:
                        try:
                            name = game.get_entity_name(target_ent)
                        except Exception:
                            name = ''
                        try:
                            actor_kind = classify_actor_from_name(name)
                        except Exception:
                            actor_kind = 'PLAYER'
                        try:
                            game.apply_silent_aim(cfg=cfg, cam_state=cam_state, target_ent=target_ent, actor_kind=actor_kind)
                        except Exception:
                            pass
                        try:
                            game.update_silent_aim_ammo_speed(cfg=cfg, target_ent=target_ent, actor_kind=actor_kind, local_player_ent=int(local_player_ent), active=True)
                        except Exception:
                            pass
                    else:
                        try:
                            game.update_silent_aim_ammo_speed(cfg=cfg, target_ent=0, actor_kind='PLAYER', local_player_ent=int(local_player_ent) if local_player_ent else 0, active=False)
                        except Exception:
                            pass
                else:
                    try:
                        game.update_silent_aim_ammo_speed(cfg=cfg, target_ent=0, actor_kind='PLAYER', local_player_ent=int(local_player_ent) if local_player_ent else 0, active=False)
                    except Exception:
                        pass
            except Exception:
                pass
        if _pressed_once_vk(VK_F7) and local_player_pos is not None:
            px, _py, pz = local_player_pos
            existing = _get_custom_waypoints_cached()
            wp_index = len(existing) + 1
            name = f'Custom {wp_index}'
            _add_custom_waypoint_from_pos(name, px, pz)
            print(f'[Waypoints] Added custom waypoint {wp_index} at ({px:.1f}, {pz:.1f})')
        if want_items and item_ptrs:
            scene, item_search_labels = build_item_scene(helper=self, cfg=cfg, game=game, cam_state=cam_state, screen_w=screen_w, screen_h=screen_h, item_ptrs=item_ptrs, scene=scene, now=now)
        else:
            try:
                item_search_labels = list(self._item_search_labels_cache)
            except Exception:
                item_search_labels = []
        if self.item_names_dirty and getattr(cfg, 'persist_item_names', True):
            try:
                save_item_names(self.item_name_set)
            except Exception as e:
                print(f'[Items] Failed to persist item names: {e}')
            else:
                self.item_names_dirty = False
        if item_search_labels:
            try:
                update_item_search_items(item_search_labels)
            except Exception:
                pass
            # === PLAYER LIST FOR MENU (full server + SteamIDs) ===
            try:
                if hasattr(game, 'get_player_list_for_menu'):
                    # Use the new full scoreboard-based list (includes distant players + real SteamIDs)
                    scene.player_list_rows = game.get_player_list_for_menu()
                else:
                    # Fallback to old nearby-only rows (if method not yet added)
                    pass
            except Exception as e:
                if getattr(cfg, 'debug_logging', False):
                    esp_log(f"[MENU] Failed to get full player list: {e}")
                # Keep whatever build_actor_scene provided as fallback
                pass

            # Update the menu
            try:
                update_player_list(scene.player_list_rows)
            except Exception:
                pass
        scene = build_waypoint_labels(cfg=cfg, game=game, cam_state=cam_state, screen_w=screen_w, screen_h=screen_h, local_pos=local_player_pos, scene=scene)
        try:
            self.last_actor_count = len(actor_ptrs)
            self.last_item_count = len(item_ptrs)
        except Exception:
            self.last_actor_count = 0
            self.last_item_count = 0
        self.last_scene_build_ms = (time.perf_counter() - start_ts) * 1000.0
        return scene
__all__ = ['ESPMemoryHelper', 'ESPScene', 'load_item_names', 'save_item_names']
