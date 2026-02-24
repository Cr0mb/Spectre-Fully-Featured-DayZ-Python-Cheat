import os, sys
sys.dont_write_bytecode = True
os.environ.setdefault('PYTHONDONTWRITEBYTECODE', '1')
import time
import traceback
import ctypes
from Process.esp_config import load_config
from Features.esp import run_esp
_LOG_PATH = os.path.join(os.environ.get('TEMP', '.'), 'gscript_bootstrap.log')
def _log(msg: str) -> None:
    try:
        ts = time.strftime('%Y-%m-%d %H:%M:%S')
        os.makedirs(os.path.dirname(_LOG_PATH), exist_ok=True)
        with open(_LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(f'[{ts}] {msg}\n')
    except Exception:
        pass
def _show_msgbox(title: str, message: str) -> None:
    try:
        MB_ICONERROR = 16
        MB_OK = 0
        user32 = ctypes.windll.user32
        user32.MessageBoxW(0, str(message), str(title), MB_ICONERROR | MB_OK)
    except Exception:
        print(f'{title}: {message}')
def _ensure_dpi_awareness() -> None:
    try:
        shcore = ctypes.windll.shcore
        PROCESS_PER_MONITOR_DPI_AWARE = 2
        shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
def main() -> None:
    _ensure_dpi_awareness()
    if os.name == 'nt' and ctypes.sizeof(ctypes.c_void_p) != 8:
        msg = 'This build of the DayZ ESP must be run with 64-bit Python.\n\nPlease install the 64-bit version of Python 3 and try again.'
        _log('Wrong Python bitness detected; aborting.')
        _show_msgbox('Invalid Python build', msg)
        return
    _log('Starting DayZ ESP bootstrap (main.py).')
    try:
        cfg = load_config()
    except Exception as exc:
        _log(f'Failed to load config: {exc}')
        cfg = None
    try:
        run_esp(cfg)
    except Exception as exc:
        tb = traceback.format_exc()
        _log('Exception from run_esp:\n' + tb)
        _show_msgbox('ESP crashed', f'The overlay crashed.\n\nA crash log was written to:\n{_LOG_PATH}\n\n{exc}')
        raise
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        tb = traceback.format_exc()
        _log('FATAL EXCEPTION:\n' + tb)
        print(tb)
        _show_msgbox('Crash', f'A fatal error occurred.\n\nLog: {_LOG_PATH}\n\n{e}')
        try:
            input('Press Enter to exit...')
        except Exception:
            pass
        raise
