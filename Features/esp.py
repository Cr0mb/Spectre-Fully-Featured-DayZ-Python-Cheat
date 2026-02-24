import time
import struct
from typing import List, Tuple, Optional, Dict
import ctypes
from ctypes import wintypes
from Process.esp_config import load_config, ESPConfig, load_custom_waypoints, save_custom_waypoints, get_custom_waypoints_cached, set_custom_waypoints
from Process.memory_helper import ESPMemoryHelper, ESPScene, load_item_names
from menu import process_hotkeys, draw_menu, update_item_search_items
import os, sys
sys.dont_write_bytecode = True
os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')
import re
from functools import lru_cache
from PyQt5 import QtCore, QtGui, QtWidgets, QtOpenGL
user32 = ctypes.windll.user32
VK_F7 = 118
_custom_waypoints_cache = None
def _get_custom_waypoints_cached() -> list[dict]:
    return get_custom_waypoints_cached()
def _add_custom_waypoint_from_pos(name: str, x: float, z: float) -> None:
    wps = list(get_custom_waypoints_cached())
    wps.append({'name': str(name), 'x': float(x), 'z': float(z)})
    set_custom_waypoints(wps)
def _pressed_once_vk(vk: int) -> bool:
    try:
        return user32.GetAsyncKeyState(vk) & 1 != 0
    except Exception:
        return False
def _clamp255(v: int) -> int:
    try:
        return 0 if v < 0 else 255 if v > 255 else int(v)
    except Exception:
        return 255
ITEM_NAME_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dayz_item_names.txt')
_ESP_LOG_PATH = os.path.join(os.environ.get('TEMP', '.'), 'gscript_esp_debug.log')
def _esp_log(msg: str) -> None:
    try:
        ts = time.strftime('%Y-%m-%d %H:%M:%S')
        with open(_ESP_LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(f'[{ts}] {msg}\n')
    except Exception:
        pass
MAX_ACTOR_ESPS_PER_TICK = 256
MAX_ITEM_ESPS_PER_TICK = 256
MAX_SKELETON_ACTORS_PER_TICK = MAX_ACTOR_ESPS_PER_TICK
SKELETON_VISUAL_MAX_DISTANCE = 1000000000.0
ITEM_SEARCH_REFRESH_INTERVAL = 0.75
ITEM_WORLD_REFRESH_INTERVAL = 0.5
SKELETON_VISUAL_MAX_DISTANCE_SQ = SKELETON_VISUAL_MAX_DISTANCE * SKELETON_VISUAL_MAX_DISTANCE
TH32CS_SNAPPROCESS = 2
PROCESS_VM_READ = 16
PROCESS_QUERY_INFORMATION = 1024
LIST_MODULES_ALL = 3
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
psapi = ctypes.WinDLL('Psapi', use_last_error=True)
class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [('dwSize', wintypes.DWORD), ('cntUsage', wintypes.DWORD), ('th32ProcessID', wintypes.DWORD), ('th32DefaultHeapID', ctypes.c_void_p), ('th32ModuleID', wintypes.DWORD), ('cntThreads', wintypes.DWORD), ('th32ParentProcessID', wintypes.DWORD), ('pcPriClassBase', wintypes.LONG), ('dwFlags', wintypes.DWORD), ('szExeFile', wintypes.WCHAR * wintypes.MAX_PATH)]
class MODULEINFO(ctypes.Structure):
    _fields_ = [('lpBaseOfDll', ctypes.c_void_p), ('SizeOfImage', wintypes.DWORD), ('EntryPoint', ctypes.c_void_p)]
kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
kernel32.Process32FirstW.restype = wintypes.BOOL
kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
kernel32.Process32NextW.restype = wintypes.BOOL
kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.CloseHandle.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.ReadProcessMemory.restype = wintypes.BOOL
kernel32.ReadProcessMemory.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, wintypes.LPVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
psapi.EnumProcessModulesEx.restype = wintypes.BOOL
psapi.EnumProcessModulesEx.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_void_p), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.DWORD]
psapi.GetModuleBaseNameW.restype = wintypes.DWORD
psapi.GetModuleBaseNameW.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.LPWSTR, wintypes.DWORD]
psapi.GetModuleInformation.restype = wintypes.BOOL
psapi.GetModuleInformation.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.POINTER(MODULEINFO), wintypes.DWORD]
def get_pid_by_name(exe_name: str) -> int:
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == wintypes.HANDLE(-1).value:
        return 0
    entry = PROCESSENTRY32W()
    entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
    if not kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
        kernel32.CloseHandle(snapshot)
        return 0
    target = exe_name.lower()
    pid = 0
    while True:
        name = entry.szExeFile
        if name.lower() == target:
            pid = entry.th32ProcessID
            break
        if not kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
            break
    kernel32.CloseHandle(snapshot)
    return pid
def get_module_base(handle, module_name: str):
    HMODULE_ARR = ctypes.c_void_p * 1024
    hmods = HMODULE_ARR()
    needed = wintypes.DWORD()
    if not psapi.EnumProcessModulesEx(handle, hmods, ctypes.sizeof(hmods), ctypes.byref(needed), LIST_MODULES_ALL):
        return None
    count = needed.value // ctypes.sizeof(ctypes.c_void_p)
    buf = ctypes.create_unicode_buffer(260)
    module_name_l = module_name.lower()
    for i in range(count):
        mod = hmods[i]
        if not mod:
            continue
        if not psapi.GetModuleBaseNameW(handle, mod, buf, len(buf)):
            continue
        name = buf.value
        if name.lower() == module_name_l:
            info = MODULEINFO()
            if psapi.GetModuleInformation(handle, mod, ctypes.byref(info), ctypes.sizeof(info)):
                return info.lpBaseOfDll
    return None
class MemoryReader:
    def __init__(self, pid: int):
        self.handle = kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
        if not self.handle:
            raise RuntimeError(f'OpenProcess failed for pid={pid}, err={ctypes.get_last_error()}')
    def close(self):
        if self.handle:
            kernel32.CloseHandle(self.handle)
            self.handle = None
    def read(self, address: int, size: int):
        buf = (ctypes.c_ubyte * size)()
        read_size = ctypes.c_size_t(0)
        ok = kernel32.ReadProcessMemory(self.handle, ctypes.c_void_p(address), buf, size, ctypes.byref(read_size))
        if not ok or read_size.value == 0:
            return None
        return bytes(buf[:read_size.value])
    def write(self, address: int, data: bytes) -> bool:
        if not self.handle or not address or (not data):
            return False
        try:
            size = len(data)
            buf = (ctypes.c_ubyte * size).from_buffer_copy(data)
            written = ctypes.c_size_t(0)
            ok = kernel32.WriteProcessMemory(self.handle, ctypes.c_void_p(address), buf, size, ctypes.byref(written))
            return bool(ok and written.value == size)
        except Exception:
            return False
    def read_u64(self, address: int) -> int:
        data = self.read(address, 8)
        if not data or len(data) < 8:
            return 0
        return int.from_bytes(data[:8], 'little', signed=False)
    def read_u32(self, address: int) -> int:
        data = self.read(address, 4)
        if not data or len(data) < 4:
            return 0
        return int.from_bytes(data[:4], 'little', signed=False)
    def read_u8(self, address: int) -> int:
        data = self.read(address, 1)
        if not data:
            return 0
        return int.from_bytes(data[:1], 'little', signed=False) & 255
    def read_wstring(self, address: int, max_chars: int=64) -> str:
        if not address:
            return ''
        max_bytes = max_chars * 2
        data = self.read(address, max_bytes)
        if not data:
            return ''
        end = data.find(b'\x00\x00')
        if end != -1:
            data = data[:end]
        try:
            return data.decode('utf-16-le', errors='ignore')
        except Exception:
            return ''
class MemoryInterface:
    def __init__(self, pid: int, cfg: Optional['ESPConfig']=None):
        self.pid = pid
        self.cfg = cfg
        self.usermode: Optional[MemoryReader] = None
        self._current = None
        self.handle = None
        self._kernel_active = False
        self._init_readers()
    def _init_readers(self):
        """Initialize user-mode memory reader only (kernel driver removed)."""
        try:
            self.usermode = MemoryReader(self.pid)
            self.handle = self.usermode.handle
        except Exception as e:
            print(f'[Mem] User-mode MemoryReader init failed: {e}')
            self.usermode = None
            self.handle = None
            raise RuntimeError('Failed to initialize memory reader.')
        self._current = self.usermode
        self._kernel_active = False
        print('[Mem] Using user-mode RPM.')
    def close(self):
        if self.usermode:
            self.usermode.close()
            self.usermode = None
    def is_kernel_mode_active(self) -> bool:
        # Kernel driver support removed; always False
        return False
    def get_process_base_address(self) -> int:
        # Kernel driver support removed; caller resolves module base via user-mode APIs.
        return 0
    def _reader(self):
        return self._current
    def read(self, address: int, size: int):
        r = self._reader()
        return r.read(address, size) if r else None
    def read_u64(self, address: int) -> int:
        r = self._reader()
        return r.read_u64(address) if r else 0
    def read_u32(self, address: int) -> int:
        r = self._reader()
        return r.read_u32(address) if r else 0
    def read_u8(self, address: int) -> int:
        r = self._reader()
        if not r:
            return 0
        if hasattr(r, 'read_u8'):
            try:
                return int(r.read_u8(address))
            except Exception:
                return 0
        try:
            data = r.read(address, 1)
        except Exception:
            return 0
        if not data:
            return 0
        return int.from_bytes(data[:1], 'little', signed=False) & 255
    def read_u16(self, address: int) -> int:
        r = self._reader()
        return r.read_u16(address) if r else 0
    def read_f32(self, address: int) -> float:
        r = self._reader()
        return r.read_f32(address) if r else 0.0
    def read_vec3(self, address: int) -> Tuple[float, float, float]:
        r = self._reader()
        return r.read_vec3(address) if r else (0.0, 0.0, 0.0)
    def write(self, address: int, data: bytes) -> bool:
        r = self._reader()
        if not r or not hasattr(r, 'write'):
            return False
        try:
            return bool(r.write(address, data))
        except Exception:
            return False
    def write_vec3(self, address: int, vec: Tuple[float, float, float]) -> bool:
        if not address or vec is None:
            return False
        try:
            x, y, z = vec
        except Exception:
            return False
        try:
            data = struct.pack('<fff', float(x), float(y), float(z))
        except Exception:
            return False
        return self.write(address, data)
    def read_wstring(self, address: int, max_chars: int=64) -> str:
        r = self._reader()
        return r.read_wstring(address, max_chars=max_chars) if r else ''
        
class DayZOffsets:
    ENTITY_OBJECTPTR = 404
    OBJECT_CLEANNAMEPTR = 1264
    MODBASE_WORLD = 16035920
    MODBASE_NETWORK = 16114144          # Updated (was 16114064)
    MODBASE_SCRIPTCONTEXT = 15831880
    MODBASE_TICK = 15832008
    WORLD_LOCALPLAYER = 16189504        # Updated to direct global offset from base (was relative 10592)
    WORLD_LOCALOFFSET = 9822546
    WORLD_NEARENTLIST = 3912
    WORLD_FARENTLIST = 4240
    WORLD_SLOWENTLIST = 8208
    WORLD_SLOWENTSIZE = 8
    WORLD_SLOWENTVALIDCOUNT = 8080
    WORLD_BULLETLIST = 3584
    WORLD_CAMERA = 440
    WORLD_EYEACCOM = 10612              # Confirmed same (0x2974)
    WORLD_HOUR = 10616
    WORLD_NOGRASS = 3072
    WORLD_ITEMTABLE_OFFSET = 8288
    WORLD_ITEMTABLE_CAPACITY = WORLD_ITEMTABLE_OFFSET + 8
    WORLD_ITEMTABLE_SIZE = WORLD_ITEMTABLE_OFFSET + 16
    CAMERA_VIEWMATRIX = 8
    CAMERA_VIEWPROJECTION = 208
    CAMERA_VIEWPROJECTION2 = 220
    CAMERA_VIEWPORTMATRIX = 88
    CAMERA_INVERTEDVIEWUP = 20
    CAMERA_INVERTEDVIEWFORWARD = 32
    CAMERA_INVERTEDVIEWTRANSL = 44
    VISUALSTATE_TRANSFORM = 8
    VISUALSTATE_INVERSETRANSFORM = 164
    VISUALSTATE_POSITION = CAMERA_INVERTEDVIEWTRANSL
    HUMAN_VISUALSTATE = 456
    HUMAN_HUMANTYPE = 384
    HUMAN_LODSHAPE = 520
    HUMAN_INVENTORY = 1624
    INVENTORYITEM_ITEMINVENTORY = 1624
    ITEMINVENTORY_CARGOGRID = 328
    ITEMINVENTORY_QUALITY = 404
    CARGOGRID_ITEMLIST = 56
    DAYZPLAYER_SKELETON = 2024
    DAYZINFECTED_SKELETON = 1656
    DAYZPLAYER_NETWORKID = 1764         # Confirmed same (0x6E4)
    DAYZPLAYER_NETWORKCLIENTPTR = 80
    DAYZPLAYER_ISDEAD = 226
    DAYZPLAYER_INVENTORY = HUMAN_INVENTORY
    DAYZPLAYERINV_HANDS = 248
    DAYZPLAYERINV_CLOTHING = 336
    DAYZPLAYERINV_HANDITEMVALID = 432
    WEAPON_WEAPONINDEX = 1712
    WEAPON_WEAPONINFOTABLE = 1720
    WEAPON_MUZZLECOUNT = 1724
    WEAPON_WEAPONINFOSIZE = 1724
    WEAPONINVENTORY_MAGAZINEREF = 336
    MAGAZINE_MAGAZINETYPE = 384
    MAGAZINE_AMMOCOUNT = 1716
    MAGAZINE_BULLETLIST = 3584
    MAGAZINE_BULLETLIST2 = 1448
    AMMOTYPE_INITSPEED = 868
    AMMOTYPE_AIRFRICTION = 948
    SCRIPTCONTEXT_CONSTANTTABLE = 104
    ANIMCLASS_ANIMCOMPONENT = 176
    ANIMCLASS_MATRIXARRAY = 3056
    ANIMCLASS_MATRIXB = 84
    SKELETON_ANIMCLASS1 = 152
    SKELETON_ANIMCLASS2 = 40
    HUMANTYPE_OBJECTNAME = 112
    HUMANTYPE_CATEGORYNAME = 168
    SCOREBOARDIDENTITY_NAME = 248       # Confirmed same (0xF8)
    SCOREBOARDIDENTITY_STEAMID = 160    # Confirmed same (0xA0)
    SCOREBOARDIDENTITY_NETWORKID = 48
    SCOREBOARD_TABLE = 24               # Confirmed same (0x18)
    SCOREBOARD_PLAYERCOUNT = 36         # Confirmed same (0x24)

    # === NEW / UPDATED OFFSETS FROM THREAD (freecam, network, entity, skeleton, weather) ===
    ENTITY_CONDITION = 404              # New (entity health/integrity state, 0x194)
    MODBASE_CAMERA_ACTIVE = 16095768    # New (0xF59A18)
    MODBASE_CAMERA_MODE = 16095624      # New (0xF59988; 3 = debug/freecam)
    MODBASE_FREEDEBUGCAMERA_GETINSTANCE = 4731792  # New (0x483390)
    MODBASE_GLOBAL_FREEDEBUGCAMERAINSTANCE = 15900408  # New (0xF29EF8)
    MODBASE_DEBUGCAMERA_TARGETPOS = 16095728   # New (0xF599F0)
    MODBASE_DEBUGCAMERA_STARTPOS = 16095668    # New (0xF599B4)
    MODBASE_ROTATION_SOURCE1 = 16095696        # New (0xF599D0; right/up rows)
    MODBASE_ROTATION_SOURCE2 = 16095636        # New (0xF59994)
    MODBASE_CAMERA_UPDATE_PATCH = 8896564      # New (0x87C034)
    MODBASE_INPUT_HANDLER_PATCH = 4727840      # New (0x482420)
    SKELETON_BONEMATRIX_STRIDE = 48            # New (0x30 per bone)
    SKELETON_BONEMATRIX_START = 84             # New (0x54 start offset)
    WORLD_WEATHERMANAGER = 29784               # New (0x7458 relative to world)
    WEATHER_TIME = 140                         # New (0x8C, float)
    WEATHER_OVERCAST = 16                      # New (0x10 pointer + 0x10 actual)
    WEATHER_FOG = 24                           # New (0x18 pointer + 0x10 actual)
    WEATHER_RAIN = 32                          # New (0x20 pointer + 0x10 actual)
    WEATHER_SNOWFALL = 40                      # New (0x28 pointer + 0x10 actual)
    
DAYZ_EXE_NAME = 'DayZ_x64.exe'
HEAD_OFFSET_PLAYER = 1.6
HEAD_OFFSET_ZOMBIE = 1.4
QUALITY_RUINED = 4
PLAYER_BONE_IDS = {
    'pelvis': 1, 'spine': 18, 'neck': 22, 'head': 24,
    'left_shoulder': 61, 'left_hand': 66,
    'right_shoulder': 94, 'right_hand': 100,
    'left_upleg': 2, 'left_foot': 7,
    'right_upleg': 10, 'right_foot': 15,
}
INFECTED_BONE_IDS = {
    'pelvis': 1, 'spine': 16, 'neck': 20, 'head': 22,
    'left_shoulder': 24, 'left_hand': 29,
    'right_shoulder': 56, 'right_hand': 62,
    'left_upleg': 2, 'left_foot': 7,
    'right_upleg': 9, 'right_foot': 14,
}
PLAYER_BONE_IDS = {'pelvis': 1, 'spine': 18, 'neck': 22, 'head': 24, 'left_shoulder': 61, 'left_hand': 66, 'right_shoulder': 94, 'right_hand': 100, 'left_upleg': 2, 'left_foot': 7, 'right_upleg': 10, 'right_foot': 15}
INFECTED_BONE_IDS = {'pelvis': 1, 'spine': 16, 'neck': 20, 'head': 22, 'left_shoulder': 24, 'left_hand': 29, 'right_shoulder': 56, 'right_hand': 62, 'left_upleg': 2, 'left_foot': 7, 'right_upleg': 9, 'right_foot': 14}
PLAYER_SKELETON_SEGMENTS = [('pelvis', 'spine'), ('spine', 'neck'), ('neck', 'head'), ('spine', 'left_shoulder'), ('left_shoulder', 'left_hand'), ('spine', 'right_shoulder'), ('right_shoulder', 'right_hand'), ('pelvis', 'left_upleg'), ('left_upleg', 'left_foot'), ('pelvis', 'right_upleg'), ('right_upleg', 'right_foot')]
INFECTED_SKELETON_SEGMENTS = [('pelvis', 'spine'), ('spine', 'neck'), ('neck', 'head'), ('spine', 'left_shoulder'), ('left_shoulder', 'left_hand'), ('spine', 'right_shoulder'), ('right_shoulder', 'right_hand'), ('pelvis', 'left_upleg'), ('left_upleg', 'left_foot'), ('pelvis', 'right_upleg'), ('right_upleg', 'right_foot')]

SKELETON_OFFSET_PLAYER = DayZOffsets.DAYZPLAYER_SKELETON
SKELETON_OFFSET_INFECTED = DayZOffsets.DAYZINFECTED_SKELETON
SKELETON_ANIMCLASS_OFFSET = DayZOffsets.SKELETON_ANIMCLASS1
ANIMCLASS_MATRIXPTR_OFFSET = DayZOffsets.ANIMCLASS_MATRIXARRAY

PLAYER_COLOR = (0, 255, 0)
ZOMBIE_COLOR = (255, 0, 0)
VEHICLE_COLOR = (0, 128, 255)
ANIMAL_COLOR = (255, 165, 0)
PLAYER_COLOR = (0, 255, 0)
ZOMBIE_COLOR = (255, 0, 0)
VEHICLE_COLOR = (0, 128, 255)
ANIMAL_COLOR = (255, 165, 0)
def classify_actor_from_name(name: str) -> str:
    if not name:
        return 'PLAYER'
    n = name.lower().strip()
    if n == 'zombie':
        return 'ZOMBIE'
    if 'treeeffecter' in n or 'areadamagetriggerbase' in n or 'areadamage' in n or ('traptrigger' in n) or ('contaminatedtrigger_dynamic' in n):
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
try:
    user32 = ctypes.windll.user32
except Exception:
    user32 = None
WS_EX_TOPMOST = 8
WS_EX_LAYERED = 524288
WS_EX_TRANSPARENT = 32
_WDA_NONE = 0
_WDA_EXCLUDEFROMCAPTURE = 17
_obs_protection_applied: bool = False
_obs_protection_supported: Optional[bool] = None
_SetWindowDisplayAffinity = None
def _is_obs_protection_enabled(cfg: 'ESPConfig') -> bool:
    for name in ('obs_protection', 'obs_protection_enabled', 'capture_protection'):
        if hasattr(cfg, name):
            try:
                return bool(getattr(cfg, name))
            except Exception:
                return False
    return False
def _ensure_display_affinity_func() -> bool:
    global _SetWindowDisplayAffinity, _obs_protection_supported
    if _obs_protection_supported is False:
        return False
    if user32 is None:
        _obs_protection_supported = False
        return False
    if _SetWindowDisplayAffinity is not None:
        return True
    try:
        func = user32.SetWindowDisplayAffinity
        func.argtypes = [wintypes.HWND, wintypes.DWORD]
        func.restype = wintypes.BOOL
        _SetWindowDisplayAffinity = func
        _obs_protection_supported = True
        return True
    except Exception:
        _SetWindowDisplayAffinity = None
        _obs_protection_supported = False
        return False
def update_obs_protection(hwnd: int, cfg: 'ESPConfig') -> None:
    global _obs_protection_applied, _obs_protection_supported
    if not hwnd:
        return
    if not _ensure_display_affinity_func():
        return
    enabled = _is_obs_protection_enabled(cfg)
    if not enabled and _obs_protection_applied:
        try:
            ok = _SetWindowDisplayAffinity(wintypes.HWND(hwnd), _WDA_NONE)
            if ok:
                _obs_protection_applied = False
                print('[OBS] Capture restored (WDA_NONE).')
            else:
                print('[OBS] Failed to restore capture.')
        except Exception as e:
            print(f'[OBS] Exception disabling OBS protection: {e}')
        return
    if enabled and (not _obs_protection_applied):
        try:
            ok = _SetWindowDisplayAffinity(wintypes.HWND(hwnd), _WDA_EXCLUDEFROMCAPTURE)
            if ok:
                _obs_protection_applied = True
                _obs_protection_supported = True
                print('[OBS] EXCLUDEFROMCAPTURE applied.')
            else:
                _obs_protection_supported = False
                print('[OBS] OBS protection unsupported.')
        except Exception as e:
            _obs_protection_supported = False
            print(f'[OBS] Exception enabling OBS protection: {e}')
class _ESPScene:
    def __init__(self):
        self.actor_crosses: List[Tuple[int, int, str, Tuple[int, int, int]]] = []
        self.actor_heads: List[Tuple[int, int, int, Tuple[int, int, int]]] = []
        self.actor_skeletons: List[Tuple[int, int, int, int, Tuple[int, int, int]]] = []
        self.actor_labels: List[Tuple[int, int, str, Tuple[int, int, int]]] = []
        self.actor_boxes: List[Tuple[int, int, int, int, Tuple[int, int, int]]] = []
        self.item_labels: List[Tuple[int, int, str, Tuple[int, int, int]]] = []
        self.waypoint_labels: List[Tuple[int, int, str, Tuple[int, int, int]]] = []
        self.aimbot_active: bool = False
class ESPOverlay(QtWidgets.QOpenGLWidget):
    def __init__(self, cfg: ESPConfig, game: 'DayZGame', item_name_set: set[str]):
        super().__init__()
        self.cfg = cfg
        self.game = game
        self.item_name_set = item_name_set
        self._memory = ESPMemoryHelper(self.item_name_set)
        self.item_names_dirty = False
        self.last_item_names_flush = time.perf_counter()
        self.scene = _ESPScene()
        self._hwnd: Optional[int] = None
        self._frame_index = 0
        self._last_item_search_refresh = 0.0
        self._item_search_labels_cache: List[str] = []
        self._last_item_world_refresh = 0.0
        self._cached_item_ptrs: List[int] = []
        self._cached_item_positions: dict[int, Tuple[float, float, float]] = {}
        self._item_name_cache: dict[int, str] = {}
        self._pen_cache: dict[Tuple[int, int, int, int, int], QtGui.QPen] = {}
        self._crosshair_pen = QtGui.QPen(QtGui.QColor(255, 255, 255))
        self._crosshair_pen.setWidth(1)
        self._head_pen = QtGui.QPen(QtGui.QColor(255, 255, 255))
        self._head_pen.setWidth(1)
        self._fov_pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 120))
        self._fov_pen.setWidth(1)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint, True)
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        self.setWindowFlag(QtCore.Qt.Tool, True)
        self.text_font = QtGui.QFont('Arial', 7)
        self.text_font.setBold(False)
        screen = QtWidgets.QApplication.primaryScreen()
        geo = screen.geometry()
        self.setGeometry(geo)
        self.screen_w = geo.width()
        self.screen_h = geo.height()
        print(f'[ESP] Overlay (Qt) size: {self.screen_w}x{self.screen_h}')
        self._base_interval_ms = int(1000 / 60)
        self._fast_interval_ms = int(1000 / 90)
        self._slow_interval_ms = int(1000 / 45)
        self._current_interval_ms = self._base_interval_ms
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(self._current_interval_ms)
        self._last_debug_print = 0.0
    def _ensure_hwnd(self) -> int:
        if self._hwnd is None:
            try:
                self._hwnd = int(self.winId())
            except Exception:
                self._hwnd = 0
        return self._hwnd or 0
    def showEvent(self, event):
        super().showEvent(event)
        hwnd = self._ensure_hwnd()
        if hwnd and user32 is not None:
            try:
                GWL_EXSTYLE = -20
                ex = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                ex |= WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST
                user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex)
            except Exception:
                pass
            try:
                update_obs_protection(hwnd, self.cfg)
            except Exception:
                pass
    def set_scene(self, scene: _ESPScene) -> None:
        self.scene = scene
        self.update()
    def _get_pen(self, r: int, g: int, b: int, width: int=1, a: int=255) -> QtGui.QPen:
        key = (_clamp255(r), _clamp255(g), _clamp255(b), _clamp255(a), int(width))
        pen = self._pen_cache.get(key)
        if pen is None:
            color = QtGui.QColor(key[0], key[1], key[2], key[3])
            pen = QtGui.QPen(color)
            pen.setWidth(key[4])
            self._pen_cache[key] = pen
        return pen
        
    def _draw_text(self, painter: QtGui.QPainter, x: int, y: int, text: str, r: int, g: int, b: int) -> None:
            """Draw ESP text using Arial font with a black outline, but avoid shimmer."""

            # Start from the projected position
            base_x = int(round(x))
            base_y = int(round(y)) + 10  # keep your existing vertical offset

            # Optional: snap to a small pixel grid to avoid 1px jitter when moving
            snap = int(getattr(self.cfg, 'esp_text_snap', 2))  # 2px grid by default
            if snap > 1:
                base_x = (base_x // snap) * snap
                base_y = (base_y // snap) * snap

            # Outline thickness from config (default 1)
            outline_thickness = getattr(self.cfg, 'esp_text_outline_thickness', 1)

            # Draw a simpler 4-direction outline instead of 8-way “flower” outline
            if outline_thickness and outline_thickness > 0:
                outline_pen = self._get_pen(0, 0, 0, 1)
                painter.setPen(outline_pen)
                t = int(outline_thickness)

                # Only up / down / left / right → much less flicker
                offsets = [(-t, 0), (t, 0), (0, -t), (0, t)]
                for dx, dy in offsets:
                    painter.drawText(base_x + dx, base_y + dy, text)

            # Foreground colored text
            text_pen = self._get_pen(r, g, b, 1)
            painter.setPen(text_pen)
            painter.drawText(base_x, base_y, text)


    def _draw_center_marker(self, painter: QtGui.QPainter) -> None:
        if not getattr(self.cfg, 'crosshair_enabled', True):
            return
        cx = self.width() // 2
        cy = self.height() // 2
        painter.setPen(self._crosshair_pen)
        painter.drawLine(cx - 10, cy, cx + 10, cy)
        painter.drawLine(cx, cy - 10, cx, cy + 10)
        if self.cfg.esp_enabled:
            text = ''
            r, g, b = (0, 255, 0)
        else:
            text = 'ESP OFF'
            r, g, b = (255, 0, 0)
        if text:
            self._draw_text(painter, cx + 12, cy - 8, text, r, g, b)
    def _draw_aimbot_fov(self, painter: QtGui.QPainter) -> None:
        # Draw FOV circle whenever its visual is enabled, regardless of aimbot mode.
        if not getattr(self.cfg, 'aimbot_draw_fov', True):
            return
        try:
            radius = float(getattr(self.cfg, 'aimbot_fov', 250))
        except Exception:
            radius = 250.0
        if radius <= 0:
            return
        cx = self.width() // 2
        cy = self.height() // 2
        painter.setPen(self._fov_pen)
        r = int(radius)
        painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)
        
    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        try:
            cfg = self.cfg
            s = self.scene

            # Render hints (keep text AA on for readability; geometry AA toggled by cfg)
            fast_drawing = bool(getattr(cfg, "esp_fast_drawing", True))
            painter.setRenderHint(QtGui.QPainter.Antialiasing, not fast_drawing)
            painter.setRenderHint(QtGui.QPainter.TextAntialiasing, True)

            # Clear with transparency
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_Source)
            painter.fillRect(self.rect(), QtCore.Qt.transparent)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)

            # Static overlay elements
            self._draw_center_marker(painter)
            self._draw_aimbot_fov(painter)

            painter.setFont(self.text_font)

            # Menu (already external)
            draw_menu(painter, self._draw_text, 20, 20, cfg)

            # Localize hot methods/values
            get_pen = self._get_pen
            set_pen = painter.setPen
            draw_rect = painter.drawRect
            draw_line = painter.drawLine
            draw_lines = painter.drawLines
            draw_text = self._draw_text
            head_pen = self._head_pen

            # ---------- Boxes ----------
            last_pen = None
            actor_boxes = s.actor_boxes  # local reference
            for left, top, right, bottom, (r, g, b) in actor_boxes:
                pen = get_pen(r, g, b, 1)
                if pen is not last_pen:
                    set_pen(pen)
                    last_pen = pen
                draw_rect(int(left), int(top), int(right - left), int(bottom - top))

            # ---------- Skeletons ----------
            last_pen = None
            for x1, y1, x2, y2, (r, g, b) in s.actor_skeletons:
                pen = get_pen(r, g, b, 1)
                if pen is not last_pen:
                    set_pen(pen)
                    last_pen = pen
                draw_line(int(x1), int(y1), int(x2), int(y2))

            # ---------- Heads ----------
            heads = s.actor_heads
            if heads:
                set_pen(head_pen)
                size = 2
                # Batch when many heads to reduce Python->Qt calls
                if len(heads) >= 16:
                    lines = []
                    append = lines.append
                    QLine = QtCore.QLine
                    for x, y in heads:
                        append(QLine(x - size, y, x + size, y))
                        append(QLine(x, y - size, x, y + size))
                    draw_lines(lines)
                else:
                    for x, y in heads:
                        draw_line(x - size, y, x + size, y)
                        draw_line(x, y - size, x, y + size)

            # ---------- Labels (optimize distance->box snapping) ----------
            bucket_size = 32
            pad = 4
            buckets = None  # lazy-built only if needed and only if box count is large enough

            def _looks_like_meters(t: str) -> bool:
                # Fast check for "123m" or "12.3m" with optional trailing whitespace
                if not t:
                    return False
                if t[-1].isspace():
                    t = t.rstrip()
                    if not t:
                        return False
                if len(t) > 6 or t[-1] != "m":
                    return False
                num = t[:-1]
                if not num:
                    return False
                dot = False
                for ch in num:
                    if ch == ".":
                        if dot:
                            return False
                        dot = True
                    elif not ("0" <= ch <= "9"):
                        return False
                return True

            def _ensure_buckets() -> None:
                nonlocal buckets
                if buckets is not None:
                    return

                # For small counts, the naive scan is usually faster than building an index.
                if len(actor_boxes) < 10:
                    buckets = {}
                    return

                bm = {}
                for left, top, right, bottom, _col in actor_boxes:
                    l = int(left) - pad
                    r = int(right) + pad
                    b0 = l // bucket_size
                    b1 = r // bucket_size
                    entry = (l, r, int(top), int(bottom))
                    for bi in range(b0, b1 + 1):
                        bm.setdefault(bi, []).append(entry)
                buckets = bm

            for x, y, text, (r, g, b) in s.actor_labels:
                # Keep the label-box snapping logic, but avoid O(labels*boxes) for big scenes.
                if actor_boxes and _looks_like_meters(text):
                    if len(actor_boxes) < 10:
                        # Small scene: straight scan is fine
                        xi = int(x)
                        yi = int(y)
                        best_delta = None
                        target_bottom = None
                        for left, top, right, bottom, _col in actor_boxes:
                            if (left - pad) <= xi <= (right + pad):
                                delta = abs(yi - int(top))
                                if best_delta is None or delta < best_delta:
                                    best_delta = delta
                                    target_bottom = bottom
                        if target_bottom is not None:
                            y = int(target_bottom + 300)
                    else:
                        _ensure_buckets()
                        cand = buckets.get(int(x) // bucket_size) if buckets else None
                        if cand:
                            xi = int(x)
                            yi = int(y)
                            best_delta = None
                            target_bottom = None
                            for l, rr, top_i, bottom_i in cand:
                                if l <= xi <= rr:
                                    delta = abs(yi - top_i)
                                    if best_delta is None or delta < best_delta:
                                        best_delta = delta
                                        target_bottom = bottom_i
                            if target_bottom is not None:
                                y = int(target_bottom + 300)

                draw_text(painter, x, y, text, r, g, b)

            for x, y, text, (r, g, b) in s.item_labels:
                if text:
                    draw_text(painter, x, y, text, r, g, b)

            for x, y, text, (r, g, b) in s.waypoint_labels:
                if text:
                    draw_text(painter, x, y, text, r, g, b)

        finally:
            painter.end()

        
    def _tick(self) -> None:
        if not self.cfg:
            return
        self._frame_index = getattr(self, '_frame_index', 0) + 1 & 4294967295
        frame_index = self._frame_index
        process_hotkeys(self.cfg)
        hwnd = self._ensure_hwnd()
        if hwnd:
            update_obs_protection(hwnd, self.cfg)
        world = self.game.get_world_ptr()
        if not world:
            print('[ESP] Lost world pointer, shutting down Qt overlay.')
            QtWidgets.QApplication.quit()
            return
        try:
            mem = getattr(self.game, 'mem', None)
            if mem:
                # No grass toggle (unchanged)
                target = 0.0 if getattr(self.cfg, 'no_grass_enabled', False) else 10.0
                mem.write(int(world) + DayZOffsets.WORLD_NOGRASS, struct.pack('<f', float(target)))
                # World time (sethour) – use configurable slider value when enabled
                try:
                    if getattr(self.cfg, 'sethour', False):
                        hour_val = float(getattr(self.cfg, 'sethour_value', 10.0))
                        # Clamp to a sane range matching the external: 0..10
                        if hour_val < 0.0:
                            hour_val = 0.0
                        if hour_val > 10.0:
                            hour_val = 10.0
                    else:
                        # Neutral-ish fallback so we don't hard-force a weird time
                        hour_val = 1.0
                    mem.write(int(world) + DayZOffsets.WORLD_HOUR, struct.pack('<f', float(hour_val)))
                except Exception:
                    pass
                # Eye accommodation (seteye) – use configurable slider value when enabled
                try:
                    if getattr(self.cfg, 'seteye', False):
                        eye_val = float(getattr(self.cfg, 'seteye_value', 10.0))
                        if eye_val < 0.0:
                            eye_val = 0.0
                        if eye_val > 10.0:
                            eye_val = 10.0
                    else:
                        eye_val = 1.0
                    mem.write(int(world) + DayZOffsets.WORLD_EYEACCOM, struct.pack('<f', float(eye_val)))
                except Exception:
                    pass
        except Exception:
            pass
        cam_ptr = self.game.get_camera_ptr()
        if not cam_ptr:
            self.set_scene(_ESPScene())
            return
        cam_state = self.game.get_camera_state(cam_ptr)
        if not cam_state:
            self.set_scene(_ESPScene())
            return
        scene = self._memory.build_scene(cfg=self.cfg, game=self.game, cam_state=cam_state, screen_w=self.screen_w, screen_h=self.screen_h, frame_index=frame_index, scene_cls=_ESPScene)
        self.set_scene(scene)
        helper = self._memory
        try:
            actor_count = getattr(helper, 'last_actor_count', 0)
            item_count = getattr(helper, 'last_item_count', 0)
            build_ms = getattr(helper, 'last_scene_build_ms', 0.0)
        except Exception:
            actor_count = 0
            item_count = 0
            build_ms = 0.0
        load_score = actor_count + item_count * 0.5
        target_interval = getattr(self, '_base_interval_ms', int(1000 / 60))
        if build_ms < 28.0:
            if load_score >= 300:
                target_interval = getattr(self, '_fast_interval_ms', target_interval)
            elif load_score <= 80:
                target_interval = getattr(self, '_slow_interval_ms', target_interval)
        if hasattr(self, '_timer') and hasattr(self, '_current_interval_ms') and (target_interval != self._current_interval_ms):
            self._current_interval_ms = target_interval
            try:
                self._timer.setInterval(target_interval)
            except Exception:
                pass
NETWORK_MANAGER_OFFSET = DayZOffsets.MODBASE_NETWORK
NETWORK_CLIENT_OFFSET = DayZOffsets.DAYZPLAYER_NETWORKCLIENTPTR
SCOREBOARD_TABLE_OFFSET = 24
SCOREBOARD_PLAYERCOUNT_OFFSET = 36
SCOREBOARD_NETWORKID_OFFSET = DayZOffsets.SCOREBOARDIDENTITY_NETWORKID
SCOREBOARD_STEAMIDPTR_OFFSET = DayZOffsets.SCOREBOARDIDENTITY_STEAMID
SCOREBOARD_NAMEPTR_OFFSET = DayZOffsets.SCOREBOARDIDENTITY_NAME
class DayZGame:
    def __init__(self, exe_name: str=DAYZ_EXE_NAME, config: Optional[ESPConfig]=None):
        self.exe_name = exe_name
        self.config = config
        self.pid: int = 0
        self.mem: Optional[MemoryInterface] = None
        self.mod_base: Optional[int] = None
        self._itemdbg_printed = False
        self._bulletdbg_printed = False
        self._skeleton_debug_count = 0
        self._bone_anim_offset = None
        self._bone_matrix_offset = None
    def attach(self) -> bool:
        self.pid = get_pid_by_name(self.exe_name)
        if not self.pid:
            if self.config and getattr(self.config, 'debug_logging', False):
                _esp_log(f'[DayZ] attach() could not find process {self.exe_name!r}')
            return False
        try:
            self.mem = MemoryInterface(self.pid, self.config)
        except Exception as e:
            print(f'[DayZ] Failed to initialize memory interface: {e}')
            if self.config and getattr(self.config, 'debug_logging', False):
                _esp_log(f'[DayZ] MemoryInterface init failed: {e!r}')
            self.mem = None
            return False
        self.mod_base = 0
        if self.mem.is_kernel_mode_active():
            base_from_driver = self.mem.get_process_base_address()
            if base_from_driver:
                self.mod_base = base_from_driver
        if not self.mod_base and getattr(self.mem, 'handle', None):
            self.mod_base = get_module_base(self.mem.handle, self.exe_name)
        if not self.mod_base:
            print('[DayZ] Failed to get module base')
            if self.config and getattr(self.config, 'debug_logging', False):
                _esp_log('[DayZ] Failed to resolve module base address')
            if self.mem:
                self.mem.close()
                self.mem = None
            return False
        msg = f'[DayZ] Attached pid={self.pid}, base=0x{self.mod_base:X}'
        print(msg)
        if self.config and getattr(self.config, 'debug_logging', False):
            _esp_log(msg)
        return True
    def close(self):
        if self.mem:
            self.mem.close()
            self.mem = None
    def get_world_ptr(self) -> int:
        if not self.mem or self.mod_base is None:
            return 0
        return self.mem.read_u64(self.mod_base + DayZOffsets.MODBASE_WORLD)
    def _read_dynarray_data_count(self, base_addr: int, label: str):
        if not self.mem or not base_addr:
            return (0, 0)
        buf = self.mem.read(base_addr, 12)
        if not buf or len(buf) < 12:
            return (0, 0)
        data, count = struct.unpack_from('<QI', buf, 0)
        if not data or count <= 0 or count > 200000:
            return (0, 0)
        return (data, count)
    def _read_entity_ptrs_from_array(self, data: int, count: int, label: str):
        ents: List[int] = []
        if not self.mem or not data or count <= 0:
            return ents
        buf = self.mem.read(data, count * 8)
        if not buf:
            return ents
        for i in range(count):
            ptr = struct.unpack_from('<Q', buf, i * 8)[0]
            if ptr:
                ents.append(ptr)
        return ents
    def _read_entity_array_any(self, world: int, offset: int, label: str):
        ents: List[int] = []
        if not self.mem or not world:
            return ents
        member = world + offset
        qword = self.mem.read_u64(member)
        data, count = self._read_dynarray_data_count(qword, label + ' A')
        if data and count:
            ents = self._read_entity_ptrs_from_array(data, count, label + ' A')
            if ents:
                return ents
        data, count = self._read_dynarray_data_count(member, label + ' B')
        if data and count:
            ents = self._read_entity_ptrs_from_array(data, count, label + ' B')
            if ents:
                return ents
        return []
    def _read_item_table_entities(self, world: int) -> List[int]:
        if not self.mem:
            return []
        item_header = world + DayZOffsets.WORLD_ITEMTABLE_OFFSET
        item_table = self.mem.read_u64(item_header + 0)
        if not item_table:
            return []
        capacity = self.mem.read_u32(world + DayZOffsets.WORLD_ITEMTABLE_CAPACITY)
        size = self.mem.read_u32(world + DayZOffsets.WORLD_ITEMTABLE_SIZE)
        max_entries = 0
        if 0 < capacity <= 4096:
            max_entries = capacity
        elif 0 < size <= 4096:
            max_entries = size
        else:
            return []
        if not self._itemdbg_printed:
            self._itemdbg_printed = True
            print('\n========== ItemTable Debug ==========')
            print(f'[ITEMDBG] World pointer           : 0x{world:016X}')
            print(f'[ITEMDBG] World + ItemTableOffset : 0x{item_header:016X}')
            print(f'[ITEMDBG] *(world+off) (tablePtr) : 0x{item_table:016X}')
            print(f'[ITEMDBG] [world+off+0x8].u32     : {capacity}  <-- capacity')
            print(f'[ITEMDBG] [world+off+0x10].u32    : {size}      <-- size (used slots)')
        entry_size = 24
        total_bytes = max_entries * entry_size
        raw = self.mem.read(item_table, total_bytes)
        if not raw or len(raw) < entry_size:
            return []
        ents: List[int] = []
        for i in range(max_entries):
            off = i * entry_size
            if off + 12 > len(raw):
                break
            flag = struct.unpack_from('<I', raw, off)[0]
            if flag != 1:
                continue
            ent = struct.unpack_from('<Q', raw, off + 8)[0]
            if not ent:
                continue
            ents.append(ent)
        return ents
    def get_bullet_entity_ptrs(self, debug: bool=False) -> List[int]:
        if not self.mem:
            return []
        world = self.get_world_ptr()
        if not world:
            return []
        if debug and (not self._bulletdbg_printed):
            self._bulletdbg_printed = True
            header = world + DayZOffsets.WORLD_BULLETLIST
            qword = self.mem.read_u64(header)
            data_a, count_a = self._read_dynarray_data_count(qword, 'BulletList A')
            data_b, count_b = self._read_dynarray_data_count(header, 'BulletList B')
            print('\n========== BulletList Debug ==========')
            print(f'[SAIMDBG] World pointer           : 0x{world:016X}')
            print(f'[SAIMDBG] World + BulletListOff  : 0x{header:016X}')
            print(f'[SAIMDBG] [header].u64 (qword)   : 0x{qword:016X}')
            print(f'[SAIMDBG] DynArray A data,count  : 0x{data_a:016X}, {count_a}')
            print(f'[SAIMDBG] DynArray B data,count  : 0x{data_b:016X}, {count_b}')
        ents = self._read_entity_array_any(world, DayZOffsets.WORLD_BULLETLIST, 'BulletList')
        return ents
    def get_actor_entity_ptrs(self) -> List[int]:
        world = self.get_world_ptr()
        if not world:
            return []
        near_e = self._read_entity_array_any(world, DayZOffsets.WORLD_NEARENTLIST, 'Near')
        far_e = self._read_entity_array_any(world, DayZOffsets.WORLD_FARENTLIST, 'Far')
        seen: set[int] = set()
        merged: List[int] = []
        for ent in near_e:
            if ent and ent not in seen:
                seen.add(ent)
                merged.append(ent)
        for ent in far_e:
            if ent and ent not in seen:
                seen.add(ent)
                merged.append(ent)
        slow_off = getattr(DayZOffsets, 'WORLD_SLOWENTLIST', None)
        if slow_off:
            try:
                slow_e = self._read_entity_array_any(world, slow_off, 'Slow')
            except Exception:
                slow_e = []
            if slow_e:
                max_slow_corpses = 64
                added = 0
                for ent in slow_e:
                    if not ent or ent in seen:
                        continue
                    try:
                        if not self.is_corpse(ent):
                            continue
                    except Exception:
                        continue
                    seen.add(ent)
                    merged.append(ent)
                    added += 1
                    if added >= max_slow_corpses:
                        break
        return merged
    def get_item_entity_ptrs(self) -> List[int]:
        world = self.get_world_ptr()
        if not world:
            return []
        return self._read_item_table_entities(world)
    def get_entity_position(self, ent: int):
        if not self.mem or not ent:
            return None
        vis = self.mem.read_u64(ent + DayZOffsets.HUMAN_VISUALSTATE)
        if not vis:
            return None
        raw = self.mem.read(vis + 44, 12)
        if not raw or len(raw) < 12:
            return None
        return struct.unpack('<fff', raw)
    def get_entity_quality(self, ent: int) -> int:
        if not self.mem or not ent:
            return 0
        try:
            off = getattr(DayZOffsets, 'ITEMINVENTORY_QUALITY', 404)
            return int(self.mem.read_u32(ent + off))
        except Exception:
            return 0
    def is_entity_dead_flag(self, ent: int) -> bool:
        if not self.mem or not ent:
            return False
        try:
            off = getattr(DayZOffsets, 'DAYZPLAYER_ISDEAD', 226)
            value = int(self.mem.read_u8(ent + off))
        except Exception:
            return False
        return bool(value & 255)
    def is_dead(self, ent: int) -> bool:
        try:
            return self.is_entity_dead_flag(ent)
        except Exception:
            return False
    def is_corpse(self, ent: int) -> bool:
        try:
            if not self.is_entity_dead_flag(ent):
                return False
            quality = self.get_entity_quality(ent)
            return quality == QUALITY_RUINED
        except Exception:
            return False
    def _read_string_struct_char(self, struct_ptr: int, max_bytes: int=256) -> str:
        if not self.mem or not struct_ptr:
            return ''
        size = self.mem.read_u32(struct_ptr + 8)
        if size <= 0 or size > max_bytes:
            return ''
        raw = self.mem.read(struct_ptr + 16, size)
        if not raw:
            return ''
        raw = raw.split(b'\x00', 1)[0]
        if not raw:
            return ''
        try:
            text = raw.decode('utf-8', errors='ignore').strip()
        except Exception:
            try:
                text = raw.decode('ascii', errors='ignore').strip()
            except Exception:
                return ''
        return text
    def _read_string_struct_wide(self, struct_ptr: int, max_chars: int=64) -> str:
        if not self.mem or not struct_ptr:
            return ''
        size = self.mem.read_u32(struct_ptr + 8)
        if size <= 0 or size > max_chars:
            return ''
        raw = self.mem.read(struct_ptr + 16, size * 2)
        if not raw:
            return ''
        raw = raw.split(b'\x00\x00', 1)[0]
        if not raw:
            return ''
        try:
            return raw.decode('utf-16-le', errors='ignore').strip()
        except Exception:
            return ''
    def _get_entity_cleanname(self, ent: int) -> str:
        if not self.mem or not ent:
            return ''
        obj = self.mem.read_u64(ent + DayZOffsets.ENTITY_OBJECTPTR)
        if not obj:
            return ''
        clean_ptr = self.mem.read_u64(obj + DayZOffsets.OBJECT_CLEANNAMEPTR)
        if not clean_ptr:
            return ''
        text = self._read_string_struct_char(clean_ptr, max_bytes=256)
        if text:
            return text
        text = self._read_string_struct_wide(clean_ptr, max_chars=64)
        if text:
            return text
        return ''
    def _get_entity_humantype_structname(self, ent: int) -> str:
        if not self.mem or not ent:
            return ''
        human_type = self.mem.read_u64(ent + DayZOffsets.HUMAN_HUMANTYPE)
        if not human_type:
            return ''
        name_struct = self.mem.read_u64(human_type + DayZOffsets.HUMANTYPE_OBJECTNAME)
        if not name_struct:
            return ''
        text = self._read_string_struct_char(name_struct, max_bytes=256)
        if text:
            return text
        text = self._read_string_struct_wide(name_struct, max_chars=64)
        if text:
            return text
        return ''
    def _get_entity_humantype_wstring(self, ent: int) -> str:
        if not self.mem or not ent:
            return ''
        human_type = self.mem.read_u64(ent + DayZOffsets.HUMAN_HUMANTYPE)
        if not human_type:
            return ''
        name_ptr = self.mem.read_u64(human_type + DayZOffsets.HUMANTYPE_OBJECTNAME)
        if not name_ptr:
            return ''
        name = self.mem.read_wstring(name_ptr, max_chars=64)
        if not name:
            return ''
        return name.strip()
    def get_entity_name(self, ent: int) -> str:
        name = self._get_entity_cleanname(ent)
        if not name:
            name = self._get_entity_humantype_structname(ent)
        if not name:
            name = self._get_entity_humantype_wstring(ent)
        if not name:
            return ''
        if name.startswith('ZmbM') or name.startswith('ZmbF'):
            return 'zombie'
        return name.strip()
    def _get_network_client_base(self) -> int:
        if not self.mem or self.mod_base is None:
            return 0
        try:
            net_mgr = self.mem.read_u64(self.mod_base + NETWORK_MANAGER_OFFSET)
            if not net_mgr:
                return 0
            net_client = self.mem.read_u64(net_mgr + NETWORK_CLIENT_OFFSET)
            return net_client or 0
        except Exception:
            return 0
    def _read_scoreboard_players_raw(self, max_players: int=128) -> List[dict]:
        if not self.mem:
            return []
        net_client = self._get_network_client_base()
        if not net_client:
            return []
        try:
            table = self.mem.read_u64(net_client + SCOREBOARD_TABLE_OFFSET)
            count = int(self.mem.read_u32(net_client + SCOREBOARD_PLAYERCOUNT_OFFSET))
        except Exception:
            return []
        if not table or count <= 0:
            return []
        if count > max_players:
            count = max_players
        try:
            raw = self.mem.read(table, count * 8)
        except Exception:
            raw = None
        if not raw:
            return []
        rows: List[dict] = []
        for i in range(count):
            off = i * 8
            if off + 8 > len(raw):
                break
            entry_ptr = struct.unpack_from('<Q', raw, off)[0]
            if not entry_ptr:
                continue
            try:
                steam_class = self.mem.read_u64(entry_ptr + SCOREBOARD_STEAMIDPTR_OFFSET)
                name_class = self.mem.read_u64(entry_ptr + SCOREBOARD_NAMEPTR_OFFSET)
                network_id = int(self.mem.read_u32(entry_ptr + SCOREBOARD_NETWORKID_OFFSET))
                if not isinstance(network_id, int) or network_id <= 1:
                    continue
            except Exception:
                continue
            def _read_score_text(cls_ptr: int, max_bytes: int=64) -> str:
                if not self.mem or not cls_ptr:
                    return ''
                try:
                    buf = self.mem.read(cls_ptr + 16, max_bytes)
                except Exception:
                    return ''
                if not buf:
                    return ''
                buf = buf.split(b'\x00', 1)[0]
                if not buf:
                    return ''
                try:
                    return buf.decode('utf-8', errors='ignore').strip()
                except Exception:
                    try:
                        return buf.decode('ascii', errors='ignore').strip()
                    except Exception:
                        return ''
            steam_id = _read_score_text(steam_class)
            name = _read_score_text(name_class)
            if not steam_id and (not name):
                continue
            rows.append({'network_id': network_id, 'name': name or '', 'steam_id': steam_id or ''})
        return rows
    def _refresh_scoreboard_cache(self, max_age: float=0.25) -> None:
        now = time.perf_counter()
        last = getattr(self, '_last_scoreboard_refresh', 0.0)
        if now - last < max_age:
            return
        rows = self._read_scoreboard_players_raw()
        by_nid: Dict[int, dict] = {}
        for row in rows:
            nid = row.get('network_id')
            if isinstance(nid, int) and nid > 0:
                by_nid[nid] = row
        self._last_scoreboard_refresh = now
        self._scoreboard_rows = rows
        self._scoreboard_by_nid = by_nid
    def get_scoreboard_players(self) -> List[dict]:
        self._refresh_scoreboard_cache()
        rows = getattr(self, '_scoreboard_rows', None) or []
        return list(rows)
    def get_entity_network_id(self, ent: int) -> int:
        if not self.mem or not ent:
            return 0
        for attr in ('DAYZPLAYER_NETWORKID', 'PLAYER_NETWORKID', 'PLAYER_NETWORK_ID'):
            off = getattr(DayZOffsets, attr, None)
            if isinstance(off, int) and off > 0:
                try:
                    return int(self.mem.read_u32(ent + off))
                except Exception:
                    pass
        sb_ident_off = getattr(DayZOffsets, 'DAYZPLAYER_SCOREBOARDIDENTITY', None) or getattr(DayZOffsets, 'PLAYER_SCOREBOARDIDENTITY', None)
        sb_nid_off = getattr(DayZOffsets, 'SCOREBOARDIDENTITY_NETWORKID', None)
        if isinstance(sb_ident_off, int) and sb_ident_off > 0:
            try:
                sb_ptr = self.mem.read_u64(ent + sb_ident_off)
            except Exception:
                sb_ptr = 0
            if sb_ptr and isinstance(sb_nid_off, int) and (sb_nid_off >= 0):
                try:
                    return int(self.mem.read_u32(sb_ptr + sb_nid_off))
                except Exception:
                    return 0
        return 0
    def get_entity_steam_id(self, ent: int) -> str:
        if not self.mem or not ent:
            return ''
        try:
            self._refresh_scoreboard_cache()
        except Exception:
            pass
        nid = self.get_entity_network_id(ent)
        if not nid:
            return ''
        by_nid = getattr(self, '_scoreboard_by_nid', None) or {}
        row = by_nid.get(nid)
        if not row:
            return ''
        steam_id = row.get('steam_id') or ''
        return steam_id.strip()
    def is_friend_entity(self, ent: int) -> bool:
        cfg = self.config
        if not cfg or not hasattr(cfg, 'friend_steam_ids'):
            return False
        steam_ids = getattr(cfg, 'friend_steam_ids', None) or []
        if not steam_ids:
            return False
        steam_id = self.get_entity_steam_id(ent)
        if not steam_id:
            return False
        try:
            ids_set = set(steam_ids)
        except Exception:
            ids_set = set((str(s) for s in steam_ids if s))
        return steam_id in ids_set
    def get_camera_ptr(self) -> int:
        if not self.mem:
            return 0
        world = self.get_world_ptr()
        if not world:
            return 0
        return self.mem.read_u64(world + DayZOffsets.WORLD_CAMERA)
    def _read_vec3(self, base: int, offset: int):
        if not self.mem or not base:
            return None
        raw = self.mem.read(base + offset, 12)
        if not raw or len(raw) < 12:
            return None
        return struct.unpack('<fff', raw)
    def get_camera_state(self, cam_ptr: int):
        if not self.mem or not cam_ptr:
            return None
        cam_pos = self._read_vec3(cam_ptr, DayZOffsets.CAMERA_INVERTEDVIEWTRANSL)
        right = self._read_vec3(cam_ptr, DayZOffsets.CAMERA_VIEWMATRIX)
        up = self._read_vec3(cam_ptr, DayZOffsets.CAMERA_INVERTEDVIEWUP)
        forward = self._read_vec3(cam_ptr, DayZOffsets.CAMERA_INVERTEDVIEWFORWARD)
        viewport = self._read_vec3(cam_ptr, DayZOffsets.CAMERA_VIEWPORTMATRIX)
        proj_d1 = self._read_vec3(cam_ptr, DayZOffsets.CAMERA_VIEWPROJECTION)
        proj_d2 = self._read_vec3(cam_ptr, DayZOffsets.CAMERA_VIEWPROJECTION2)
        if not all([cam_pos, right, up, forward, viewport, proj_d1, proj_d2]):
            return None
        return (cam_pos, right, up, forward, viewport, proj_d1, proj_d2)
    def world_to_screen_state(self, pos, cam_state):
        cam_pos, right, up, forward, viewport, proj_d1, proj_d2 = cam_state
        temp_x = pos[0] - cam_pos[0]
        temp_y = pos[1] - cam_pos[1]
        temp_z = pos[2] - cam_pos[2]
        x = temp_x * right[0] + temp_y * right[1] + temp_z * right[2]
        y = temp_x * up[0] + temp_y * up[1] + temp_z * up[2]
        z = temp_x * forward[0] + temp_y * forward[1] + temp_z * forward[2]
        if z < 0.1:
            return None
        screen_x = viewport[0] * (1.0 + x / proj_d1[0] / z)
        screen_y = viewport[1] * (1.0 - y / proj_d2[1] / z)
        return (screen_x, screen_y, z)
    def _resolve_bone_offsets(self, skeleton: int, vis_state: int, pivot: int):
        if not self.mem or not skeleton or (not vis_state):
            return False
        anim_candidates = [176, 168, 152]
        matrix_candidates = [3056, 3048, 3032, 2880, 2864]
        for a_off in anim_candidates:
            anim_class = self.mem.read_u64(skeleton + a_off)
            if not anim_class:
                continue
            for m_off in matrix_candidates:
                matrix_class = self.mem.read_u64(anim_class + m_off)
                if not matrix_class:
                    continue
                try:
                    buf = self.mem.read(matrix_class + pivot * (12 * 4), 36 * 4)
                except Exception:
                    buf = b''
                if not buf or len(buf) < 36 * 4:
                    continue
                self._bone_anim_offset = a_off
                self._bone_matrix_offset = m_off
                print('========== Skeleton Debug ==========')
                print(f'[SKELETON_DEBUG] RESOLVED anim_offset=0x{a_off:X} matrix_offset=0x{m_off:X}')
                print(f'[SKELETON_DEBUG] skeleton=0x{skeleton:016X} vis_state=0x{vis_state:016X} pivot={pivot}')
                print(f'[SKELETON_DEBUG] anim_class=0x{anim_class:016X} matrix_class=0x{matrix_class:016X}')
                return True
        print('========== Skeleton Debug ==========')
        print(f'[SKELETON_DEBUG] FAILED to resolve anim/matrix offsets for skeleton=0x{skeleton:016X}')
        return False
    def _get_bone_position_ws(self, skeleton: int, vis_state: int, pivot: int):
        if not self.mem or not skeleton or (not vis_state) or (pivot is None):
            return None
        debug = getattr(self, '_skeleton_debug_count', 0) < 80
        if self._bone_anim_offset is None or self._bone_matrix_offset is None:
            if not self._resolve_bone_offsets(skeleton, vis_state, pivot):
                if debug:
                    self._skeleton_debug_count = getattr(self, '_skeleton_debug_count', 0) + 1
                    print('========== Skeleton Debug ==========')
                    print(f'[SKELETON_DEBUG] Could not resolve offsets, pivot={pivot}')
                return None
        anim_class = self.mem.read_u64(skeleton + self._bone_anim_offset)
        if not anim_class:
            if debug:
                self._skeleton_debug_count = getattr(self, '_skeleton_debug_count', 0) + 1
                print('========== Skeleton Debug ==========')
                print(f'[SKELETON_DEBUG] skeleton=0x{skeleton:016X} vis_state=0x{vis_state:016X} pivot={pivot}')
                print('[SKELETON_DEBUG] anim_class INVALID after resolve')
            return None
        matrix_class = self.mem.read_u64(anim_class + self._bone_matrix_offset)
        if not matrix_class:
            if debug:
                self._skeleton_debug_count = getattr(self, '_skeleton_debug_count', 0) + 1
                print('========== Skeleton Debug ==========')
                print(f'[SKELETON_DEBUG] skeleton=0x{skeleton:016X} vis_state=0x{vis_state:016X} pivot={pivot}')
                print(f'[SKELETON_DEBUG] anim_class=0x{anim_class:016X}')
                print('[SKELETON_DEBUG] matrix_class INVALID after resolve')
            return None
        try:
            buf = self.mem.read(matrix_class + pivot * (12 * 4), 36 * 4)
            if not buf or len(buf) < 36 * 4:
                if debug:
                    self._skeleton_debug_count = getattr(self, '_skeleton_debug_count', 0) + 1
                    print('========== Skeleton Debug ==========')
                    print(f'[SKELETON_DEBUG] skeleton=0x{skeleton:016X} vis_state=0x{vis_state:016X} pivot={pivot}')
                    print(f'[SKELETON_DEBUG] anim_class=0x{anim_class:016X} matrix_class=0x{matrix_class:016X}')
                    print('[SKELETON_DEBUG] matrix bone read FAILED after resolve')
                return None
            v8 = struct.unpack('<36f', buf)
            m1_buf = self.mem.read(vis_state + 8, 12 * 4)
            if not m1_buf or len(m1_buf) < 12 * 4:
                if debug:
                    self._skeleton_debug_count = getattr(self, '_skeleton_debug_count', 0) + 1
                    print('========== Skeleton Debug ==========')
                    print(f'[SKELETON_DEBUG] vis_state=0x{vis_state:016X} pivot={pivot}')
                    print('[SKELETON_DEBUG] visual matrix read FAILED (m1_buf empty/short)')
                return None
            m1 = struct.unpack('<12f', m1_buf)
        except Exception as e:
            if debug:
                self._skeleton_debug_count = getattr(self, '_skeleton_debug_count', 0) + 1
                print('========== Skeleton Debug ==========')
                print(f'[SKELETON_DEBUG] skeleton=0x{skeleton:016X} vis_state=0x{vis_state:016X} pivot={pivot}')
                print(f'[SKELETON_DEBUG] EXCEPTION in _get_bone_position_ws: {e!r}')
            return None
        z = v8[10] * m1[5] + v8[9] * m1[2] + v8[11] * m1[8] + m1[11]
        y = v8[10] * m1[4] + v8[9] * m1[1] + v8[11] * m1[7] + m1[10]
        x = v8[10] * m1[3] + v8[9] * m1[0] + v8[11] * m1[6] + m1[9]
        return (x, y, z)
    def _get_entity_skeleton_and_vis(self, ent: int, actor_kind: str):
        if not self.mem or not ent:
            return (0, 0)
        vis_state = self.mem.read_u64(ent + DayZOffsets.HUMAN_VISUALSTATE)
        if actor_kind == 'ZOMBIE':
            skeleton = self.mem.read_u64(ent + SKELETON_OFFSET_INFECTED)
        else:
            skeleton = self.mem.read_u64(ent + SKELETON_OFFSET_PLAYER)
        return (skeleton or 0, vis_state or 0)
    def get_bone_position_ws_for_entity(self, ent: int, actor_kind: str, bone_name: str):
        if actor_kind == 'ZOMBIE':
            table = INFECTED_BONE_IDS
        else:
            table = PLAYER_BONE_IDS
        pivot = table.get(bone_name)
        if pivot is None:
            return None
        skeleton, vis_state = self._get_entity_skeleton_and_vis(ent, actor_kind)
        if not skeleton or not vis_state:
            return None
        return self._get_bone_position_ws(skeleton, vis_state, pivot)
    def build_skeleton_2d(self, ent, actor_kind, cam_state, screen_w: int, screen_h: int):
        if actor_kind == 'ZOMBIE':
            bone_ids = INFECTED_BONE_IDS
            segments_def = INFECTED_SKELETON_SEGMENTS
        elif actor_kind == 'PLAYER':
            bone_ids = PLAYER_BONE_IDS
            segments_def = PLAYER_SKELETON_SEGMENTS
        else:
            return ({}, [])
        skeleton, vis_state = self._get_entity_skeleton_and_vis(ent, actor_kind)
        if not skeleton or not vis_state:
            if getattr(self, '_skeleton_debug_count', 0) < 10:
                self._skeleton_debug_count = getattr(self, '_skeleton_debug_count', 0) + 1
                print('========== Skeleton Debug ==========')
                print(f'[SKELETON_DEBUG] ent=0x{ent:016X} kind={actor_kind} skeleton=0x{skeleton:016X} vis_state=0x{vis_state:016X}')
                print('[SKELETON_DEBUG] skeleton/vis_state missing, skipping entity.')
            return (None, [])
        needed_bones = set()
        for a, b in segments_def:
            needed_bones.add(a)
            needed_bones.add(b)
        needed_bones.add('head')
        world_bones = {}
        debug = False
        for name in needed_bones:
            pivot = bone_ids.get(name)
            if pivot is None:
                continue
            pos = self._get_bone_position_ws(skeleton, vis_state, pivot)
            if not pos:
                if debug and name in ('pelvis', 'spine', 'neck', 'head'):
                    self._skeleton_debug_count = getattr(self, '_skeleton_debug_count', 0) + 1
                    print('========== Skeleton Debug ==========')
                    print(f'[SKELETON_DEBUG] ent=0x{ent:016X} kind={actor_kind}')
                    print(f'[SKELETON_DEBUG] skeleton=0x{skeleton:016X} vis_state=0x{vis_state:016X}')
                    print(f"[SKELETON_DEBUG] bone '{name}' pivot={pivot} -> FAILED")
                continue
            world_bones[name] = pos
            if debug and name in ('pelvis', 'spine', 'neck', 'head'):
                self._skeleton_debug_count = getattr(self, '_skeleton_debug_count', 0) + 1
                print('========== Skeleton Debug ==========')
                print(f'[SKELETON_DEBUG] ent=0x{ent:016X} kind={actor_kind}')
                print(f'[SKELETON_DEBUG] skeleton=0x{skeleton:016X} vis_state=0x{vis_state:016X}')
                print(f"[SKELETON_DEBUG] bone '{name}' pivot={pivot} -> WS {pos}")
        if not world_bones:
            return ({}, [])
        screen_bones = {}
        for name, pos in world_bones.items():
            w2s = self.world_to_screen_state(pos, cam_state)
            if not w2s:
                continue
            sx_raw, sy_raw, _ = w2s
            sx = int(max(0, min(screen_w - 1, sx_raw)))
            sy = int(max(0, min(screen_h - 1, sy_raw)))
            screen_bones[name] = (sx, sy)
        head_2d = screen_bones.get('head')
        chest_2d = screen_bones.get('spine3') or screen_bones.get('spine2') or screen_bones.get('spine1') or head_2d
        segments = []
        for a, b in segments_def:
            pa = screen_bones.get(a)
            pb = screen_bones.get(b)
            if not pa or not pb:
                continue
            ax, ay = pa
            bx, by = pb
            segments.append((ax, ay, bx, by))
        keypoints = {'head': head_2d, 'chest': chest_2d}
        return (keypoints, segments)
def run_esp(config: Optional[ESPConfig]=None):
    cfg = config if config is not None else load_config()
    if not hasattr(cfg, 'draw_actors'):
        cfg.draw_actors = True
    if not hasattr(cfg, 'draw_items'):
        cfg.draw_items = False
    if not hasattr(cfg, 'draw_players'):
        cfg.draw_players = getattr(cfg, 'draw_actors', True)
    if not hasattr(cfg, 'draw_zombies'):
        cfg.draw_zombies = getattr(cfg, 'draw_actors', True)
    if not hasattr(cfg, 'draw_player_text'):
        cfg.draw_player_text = True
    if not hasattr(cfg, 'draw_zombie_text'):
        cfg.draw_zombie_text = True
    if not hasattr(cfg, 'draw_player_head_cross'):
        cfg.draw_player_head_cross = True
    if not hasattr(cfg, 'draw_zombie_head_cross'):
        cfg.draw_zombie_head_cross = True
    if not hasattr(cfg, 'no_grass_enabled'):
        cfg.no_grass_enabled = False
    item_name_set = load_item_names()
    game = DayZGame(config=cfg)
    while True:
        if game.attach():
            print(f'[ESP] Attached to {DAYZ_EXE_NAME}, initializing ESP (Qt overlay)...')
            break
        time.sleep(0.5)
    print('[ESP] Waiting for World pointer (load into a game/server)...')
    world = 0
    while True:
        world = game.get_world_ptr()
        if world:
            break
        if not game.pid or not game.mem:
            print('[ESP] Lost process while waiting for world, exiting.')
            game.close()
            return
        time.sleep(0.5)
    if not world:
        print('[ESP] Stopped while waiting for world pointer.')
        game.close()
        return
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    overlay = ESPOverlay(cfg, game, item_name_set)
    overlay.show()
    try:
        app.exec_()
    finally:
        game.close()
        print('[ESP] Qt overlay shutdown complete.')
def _dayzgame_get_ammo_type_for_player(self, local_player_ent: int, debug: bool=False) -> int:
    mem = getattr(self, 'mem', None)
    if not mem or not local_player_ent:
        if debug:
            print('[SAIMDBG] _get_ammo_type_for_player: no mem or local_player_ent=0')
        return 0
    inv_off = getattr(DayZOffsets, 'DAYZPLAYER_INVENTORY', DayZOffsets.HUMAN_INVENTORY)
    OFF_AMMO_TYPE1 = 1712
    OFF_AMMO_TYPE2 = 32
    inventory = 0
    hands = 0
    ammo_type1 = 0
    ammo_type2 = 0
    try:
        inventory = mem.read_u64(int(local_player_ent) + inv_off)
        if not inventory:
            if debug:
                print(f'[SAIMDBG] _get_ammo_type_for_player: inventory=0 (local=0x{int(local_player_ent):016X}, inv_off=0x{inv_off:X})')
            return 0
        hands = mem.read_u64(inventory + 432)
        if not hands:
            if debug:
                print(f'[SAIMDBG] _get_ammo_type_for_player: hands=0 (inventory=0x{int(inventory):016X})')
            return 0
        ammo_type1 = mem.read_u64(hands + OFF_AMMO_TYPE1)
        if not ammo_type1:
            if debug:
                print(f'[SAIMDBG] _get_ammo_type_for_player: AmmoType1=0 (hands=0x{int(hands):016X}, off=0x{OFF_AMMO_TYPE1:X})')
            return 0
        ammo_type2 = mem.read_u64(ammo_type1 + OFF_AMMO_TYPE2)
        if not ammo_type2:
            if debug:
                print(f'[SAIMDBG] _get_ammo_type_for_player: no AmmoType pointer.\n  local_player_ent = 0x{int(local_player_ent):016X}\n  inventory        = 0x{int(inventory):016X}\n  hands/weapon     = 0x{int(hands):016X}\n  ammo_type1       = 0x{int(ammo_type1):016X}\n  ammo_type2@+0x20 = 0x0000000000000000')
            return 0
        if debug:
            print(f'[SAIMDBG] _get_ammo_type_for_player OK:\n  local_player_ent = 0x{int(local_player_ent):016X}\n  inventory        = 0x{int(inventory):016X}\n  hands/weapon     = 0x{int(hands):016X}\n  ammo_type1       = 0x{int(ammo_type1):016X}\n  ammo_type2       = 0x{int(ammo_type2):016X}')
        return int(ammo_type2)
    except Exception as e:
        if debug:
            print(f'[SAIMDBG] _get_ammo_type_for_player: exception {e}')
            print(f'  partial chain: inv=0x{int(inventory or 0):016X} hands=0x{int(hands or 0):016X} ammo_type1=0x{int(ammo_type1 or 0):016X}')
        return 0
def _dayzgame_apply_silent_aim(self, *, cfg: ESPConfig, cam_state, target_ent: int, actor_kind: str) -> None:
    mem = getattr(self, 'mem', None)
    if not mem:
        return
    if not target_ent:
        return
    ent = int(target_ent)
    actor_kind = actor_kind or 'PLAYER'
    debug = bool(getattr(cfg, 'silent_aim_debug', False))
    bone_name = 'head'
    try:
        use_head = getattr(cfg, 'aimbot_bone_head', True)
        use_chest = getattr(cfg, 'aimbot_bone_chest', False)
    except Exception:
        use_head, use_chest = (True, False)
    if use_chest and (not use_head):
        bone_name = 'chest'
    aim_ws = None
    try:
        aim_ws = self.get_bone_position_ws_for_entity(ent, actor_kind, bone_name)
    except Exception:
        aim_ws = None
    if not aim_ws:
        pos = self.get_entity_position(ent)
        if not pos:
            if debug:
                print(f'[SAIMDBG] Silent aim: no position for ent=0x{ent:016X}')
            return
        try:
            head_offset = HEAD_OFFSET_ZOMBIE if actor_kind == 'ZOMBIE' else HEAD_OFFSET_PLAYER
        except NameError:
            head_offset = 1.6 if actor_kind != 'ZOMBIE' else 1.5
        aim_ws = (pos[0], pos[1] + head_offset, pos[2])
    cam_pos = None
    if cam_state:
        try:
            cam_pos = cam_state[0]
        except Exception:
            cam_pos = None
    if cam_pos is None:
        try:
            cs = self.get_camera_state()
            if cs:
                cam_pos = cs[0]
        except Exception:
            cam_pos = None
    if cam_pos is None:
        try:
            from Process.ent_esp import get_local_player_entity
        except Exception:
            get_local_player_entity = None
        if get_local_player_entity:
            try:
                local_ent = get_local_player_entity(self)
            except Exception:
                local_ent = 0
        else:
            local_ent = 0
        if local_ent:
            lp = self.get_entity_position(local_ent)
        else:
            lp = None
        if lp:
            cam_pos = lp
    if cam_pos is None:
        if debug:
            print('[SAIMDBG] Silent aim: no camera position; skipping bullet teleport.')
        return

    # Limit magic bullet / silent aim to a maximum distance from the camera (in meters)
    try:
        max_dist = float(getattr(cfg, 'magic_bullet_max_distance', 0.0) or 0.0)
    except Exception:
        max_dist = 0.0
    if max_dist > 0.0:
        try:
            dx = float(aim_ws[0]) - float(cam_pos[0])
            dy = float(aim_ws[1]) - float(cam_pos[1])
            dz = float(aim_ws[2]) - float(cam_pos[2])
            dist_sq = dx * dx + dy * dy + dz * dz
        except Exception:
            dist_sq = 0.0
        if dist_sq > (max_dist * max_dist):
            if debug:
                print(f'[SAIMDBG] Silent aim: target beyond max distance {max_dist:.1f}m; skipping.')
            return
    bullet_ents = self.get_bullet_entity_ptrs(debug=debug)
    if not bullet_ents:
        if debug:
            print('[SAIMDBG] No bullets in WORLD_BULLETLIST this tick.')
        return
    best_bullet = 0
    best_dist2 = float('inf')
    for b in bullet_ents:
        b_pos = self.get_entity_position(b)
        if not b_pos:
            continue
        dx = float(b_pos[0]) - float(cam_pos[0])
        dy = float(b_pos[1]) - float(cam_pos[1])
        dz = float(b_pos[2]) - float(cam_pos[2])
        dist2 = dx * dx + dy * dy + dz * dz
        if dist2 < best_dist2:
            best_dist2 = dist2
            best_bullet = b
    if not best_bullet:
        if debug:
            print('[SAIMDBG] Could not resolve a local bullet entity.')
        return
    vis_state = mem.read_u64(int(best_bullet) + DayZOffsets.HUMAN_VISUALSTATE)
    if not vis_state:
        if debug:
            print(f'[SAIMDBG] Bullet 0x{int(best_bullet):016X} has no VisualState.')
        return
    target_addr = vis_state + DayZOffsets.VISUALSTATE_POSITION
    old_pos = mem.read_vec3(target_addr)
    ok = mem.write_vec3(target_addr, aim_ws)
    sx = sy = depth = 0.0
    try:
        proj = self.world_to_screen_state(aim_ws, (cam_pos, None, None, None))
    except Exception:
        proj = None
    if proj:
        try:
            sx, sy, depth = (float(proj[0]), float(proj[1]), float(proj[2]))
        except Exception:
            pass
    if debug:
        print('\n[SAIMDBG] Silent aim applied')
        print(f'  target_ent = 0x{ent:016X} kind={actor_kind}')
        print(f'  screen     = ({sx:.1f}, {sy:.1f}) depth={depth:.2f}')
        print(f'  bullet_ent = 0x{int(best_bullet):016X} vis=0x{int(vis_state):016X}')
        print(f'  old_pos    = {old_pos}')
        print(f'  new_pos    = {aim_ws}')
        print(f'  cam_dist2  = {best_dist2:.3f}')
        print(f'  write_ok   = {ok}')
def _dayzgame_update_silent_aim_ammo_speed(self, *, cfg: ESPConfig, target_ent: int, actor_kind: str, local_player_ent: int, active: bool) -> None:
    mem = getattr(self, 'mem', None)
    if not mem:
        return
    debug = bool(getattr(cfg, 'silent_aim_debug', False))
    if not hasattr(self, '_silent_ammo_cached'):
        self._silent_ammo_cached = False
        self._silent_ammo_type_ptr = 0
        self._silent_ammo_orig_speed = 0.0
    if not active or not target_ent or (not local_player_ent):
        if self._silent_ammo_cached and self._silent_ammo_type_ptr:
            try:
                mem.write(int(self._silent_ammo_type_ptr) + DayZOffsets.AMMOTYPE_INITSPEED, struct.pack('<f', float(self._silent_ammo_orig_speed)))
                if debug:
                    print(f'[SAIMDBG] Restored AmmoType::InitSpeed 0x{int(self._silent_ammo_type_ptr):016X} -> {float(self._silent_ammo_orig_speed):.3f}')
            except Exception as e:
                if debug:
                    print(f'[SAIMDBG] Failed to restore InitSpeed: {e}')
        self._silent_ammo_cached = False
        self._silent_ammo_type_ptr = 0
        self._silent_ammo_orig_speed = 0.0
        return
    ammo_type = _dayzgame_get_ammo_type_for_player(self, int(local_player_ent), debug=debug)
    if not ammo_type:
        if self._silent_ammo_cached and self._silent_ammo_type_ptr:
            try:
                mem.write(int(self._silent_ammo_type_ptr) + DayZOffsets.AMMOTYPE_INITSPEED, struct.pack('<f', float(self._silent_ammo_orig_speed)))
            except Exception:
                pass
        self._silent_ammo_cached = False
        self._silent_ammo_type_ptr = 0
        self._silent_ammo_orig_speed = 0.0
        return
    if not self._silent_ammo_cached or self._silent_ammo_type_ptr != ammo_type:
        try:
            orig_speed = mem.read_f32(int(ammo_type) + DayZOffsets.AMMOTYPE_INITSPEED)
        except Exception:
            orig_speed = 0.0
        self._silent_ammo_type_ptr = int(ammo_type)
        self._silent_ammo_orig_speed = float(orig_speed or 0.0)
        self._silent_ammo_cached = True
        if debug:
            print(f'[SAIMDBG] Cached AmmoType::InitSpeed ammo=0x{int(ammo_type):016X} orig={float(orig_speed or 0.0):.3f}')
    target_pos = self.get_entity_position(int(target_ent))
    local_pos = self.get_entity_position(int(local_player_ent))
    if not target_pos or not local_pos:
        return
    dx = float(target_pos[0]) - float(local_pos[0])
    dy = float(target_pos[1]) - float(local_pos[1])
    dz = float(target_pos[2]) - float(local_pos[2])
    distance = (dx * dx + dy * dy + dz * dz) ** 0.5
    new_speed = float(distance * 100.0)
    orig = float(self._silent_ammo_orig_speed) if self._silent_ammo_orig_speed > 0.0 else new_speed
    try:
        max_factor = float(getattr(cfg, 'silent_aim_speed_max_factor', 6.0))
    except Exception:
        max_factor = 6.0
    hard_max = orig * max_factor if max_factor > 0.0 else 0.0
    if hard_max > 0.0 and new_speed > hard_max:
        new_speed = hard_max
    ok = False
    try:
        ok = bool(mem.write(int(ammo_type) + DayZOffsets.AMMOTYPE_INITSPEED, struct.pack('<f', float(new_speed))))
    except Exception:
        ok = False
    if debug:
        print(f'[SAIMDBG] InitSpeed tweak ammo=0x{int(ammo_type):016X} dist={distance:.2f}m orig={orig:.3f} new={new_speed:.3f} ok={ok}')
DayZGame._get_ammo_type_for_player = _dayzgame_get_ammo_type_for_player
DayZGame.apply_silent_aim = _dayzgame_apply_silent_aim
DayZGame.update_silent_aim_ammo_speed = _dayzgame_update_silent_aim_ammo_speed