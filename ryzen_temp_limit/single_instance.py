from __future__ import annotations

import ctypes
import os
import threading
from collections.abc import Callable

ERROR_ALREADY_EXISTS = 183
DEFAULT_NAME = "Local\\RyzenTempLimit.Gui"
ACTIVATION_EVENT = "Local\\RyzenTempLimit.Activate"


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


def signal_activation(name: str = ACTIVATION_EVENT) -> bool:
    if os.name != "nt":
        return False
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenEventW.restype = ctypes.c_void_p
    kernel32.OpenEventW.argtypes = [ctypes.c_uint32, ctypes.c_bool, ctypes.c_wchar_p]
    kernel32.SetEvent.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel32.OpenEventW(0x0002, False, name)
    if not handle:
        return False
    try:
        return bool(kernel32.SetEvent(ctypes.c_void_p(handle)))
    finally:
        kernel32.CloseHandle(ctypes.c_void_p(handle))


class ActivationServer:
    def __init__(self, callback: Callable[[], None], name: str = ACTIVATION_EVENT) -> None:
        self.callback = callback
        self.handle: int | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        if os.name != "nt":
            return
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateEventW.restype = ctypes.c_void_p
        kernel32.CreateEventW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_bool, ctypes.c_wchar_p]
        self.handle = kernel32.CreateEventW(None, False, False, name)

    def start(self) -> None:
        if not self.handle:
            return
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        kernel32 = ctypes.windll.kernel32
        while not self._stop.is_set():
            result = kernel32.WaitForSingleObject(ctypes.c_void_p(self.handle), 500)
            if result == 0:
                try:
                    self.callback()
                except Exception:
                    pass

    def stop(self) -> None:
        self._stop.set()
        if self.handle:
            ctypes.windll.kernel32.CloseHandle(ctypes.c_void_p(self.handle))
            self.handle = None
