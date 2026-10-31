from __future__ import annotations

import ctypes
import os

ERROR_ALREADY_EXISTS = 183
DEFAULT_NAME = "Local\\RyzenTempLimit.Gui"


class SingleInstance:
    def __init__(self, name: str = DEFAULT_NAME) -> None:
        self.handle: int | None = None
        self.already_running = False
        if os.name != "nt":
            return
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.restype = ctypes.c_void_p
        kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
        self.handle = kernel32.CreateMutexW(None, False, name)
        self.already_running = ctypes.get_last_error() == ERROR_ALREADY_EXISTS

    def release(self) -> None:
        if self.handle:
            ctypes.windll.kernel32.CloseHandle(ctypes.c_void_p(self.handle))
            self.handle = None
