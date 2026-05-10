"""
Run this ONCE to install the tracker into Windows startup.
After running, the tracker will launch automatically every time you log in.
"""

import os
import sys
import winreg
from pathlib import Path

SCRIPT    = Path(__file__).parent / 'tracker.pyw'
PYTHONW   = Path(sys.executable).parent / 'pythonw.exe'
REG_PATH  = r'Software\Microsoft\Windows\CurrentVersion\Run'
APP_NAME  = 'LifetimeTracker'


def install():
    if not SCRIPT.exists():
        print(f'ERROR: tracker.pyw not found at {SCRIPT}')
        input('Press Enter to exit...')
        return

    if not PYTHONW.exists():
        print(f'ERROR: pythonw.exe not found at {PYTHONW}')
        print('Make sure you run this with a standard Python installation.')
        input('Press Enter to exit...')
        return

    cmd = f'"{PYTHONW}" "{SCRIPT}"'
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0,
                            winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
        print('SUCCESS — Lifetime App Tracker added to Windows startup.')
        print()
        print(f'  Startup command : {cmd}')
        print(f'  Data will save  : {os.environ["APPDATA"]}\\LifetimeTracker\\app_usage.json')
        print(f'  Logs            : {os.environ["APPDATA"]}\\LifetimeTracker\\tracker.log')
        print()
        print('The tracker will start automatically next time you log in.')
        print('To start it right now, just double-click tracker.pyw.')
    except Exception as e:
        print(f'ERROR writing to registry: {e}')

    input('Press Enter to exit...')


def uninstall():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0,
                            winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, APP_NAME)
        print('Removed from startup. Your data file is untouched.')
    except FileNotFoundError:
        print('Was not in startup.')
    except Exception as e:
        print(f'ERROR: {e}')
    input('Press Enter to exit...')


if __name__ == '__main__':
    if '--uninstall' in sys.argv:
        uninstall()
    else:
        install()
