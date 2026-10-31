from __future__ import annotations

import ctypes
import os
import subprocess
import sys

from . import APP_NAME


def is_admin() -> bool:
    if os.name != "nt":
        return True
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _pythonw() -> str:
    exe = sys.executable
    if exe.lower().endswith("python.exe"):
        candidate = exe[:-len("python.exe")] + "pythonw.exe"
        if os.path.exists(candidate):
            return candidate
    return exe


def relaunch_as_admin(extra_args: list[str] | None = None) -> bool:
    if os.name != "nt":
        return False
    args = list(extra_args or [])
    if getattr(sys, "frozen", False):
        target = sys.executable
        params = subprocess.list2cmdline(args)
    else:
        target = _pythonw()
        params = subprocess.list2cmdline(["-m", "ryzen_temp_limit", *args])
    result = ctypes.windll.shell32.ShellExecuteW(None, "runas", target, params, os.getcwd(), 1)
    return result > 32


def message_box(title: str, text: str, error: bool = False) -> None:
    flags = 0x10 if error else 0x40
    try:
        ctypes.windll.user32.MessageBoxW(None, text, title or APP_NAME, flags)
    except Exception:
        print(f"{title}: {text}", file=sys.stderr)
