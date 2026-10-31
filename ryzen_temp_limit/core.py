from __future__ import annotations

import logging
import platform
import subprocess
import sys
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from typing import Any

from . import APP_NAME
from .settings import data_dir

IS_WINDOWS = platform.system() == "Windows"
SMU_OK = 1


class CoreError(RuntimeError):
    pass


@dataclass(frozen=True)
class Cpu:
    name: str
    family: str
    kind: str
    supported: bool


@dataclass(frozen=True)
class Live:
    tctl: float | None = None
    limit: float | None = None
    load: float | None = None
    socket_power: float | None = None
    gfx_clk: float | None = None


_cpu: Cpu | None = None
_backend: str | None = None


def _zenmaster() -> Any:
    try:
        import zenmaster
    except ImportError as exc:
        raise CoreError(
            "The 'zenmaster' package is missing. Install it with: pip install zenmaster"
        ) from exc
    return zenmaster


def _run_quiet(args: list[str]) -> None:
    flags = 0
    if IS_WINDOWS:
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        subprocess.run(args, capture_output=True, timeout=15, creationflags=flags)
    except (OSError, subprocess.SubprocessError):
        pass


def start_pawnio_service() -> None:
    if IS_WINDOWS:
        _run_quiet(["sc", "start", "PawnIO"])


def pawnio_version() -> str | None:
    if not IS_WINDOWS:
        return None
    try:
        status = _zenmaster().module_status()
    except Exception:
        return None
    return status.version if status.ok else None


def ensure_backend() -> str:
    global _backend
    if _backend is not None:
        return _backend
    zm = _zenmaster()
    try:
        _backend = zm.init()
        return _backend
    except Exception as first:
        start_pawnio_service()
        try:
            _backend = zm.init()
            return _backend
        except Exception:
            raise CoreError(str(first)) from first


def cpu() -> Cpu:
    global _cpu
    if _cpu is None:
        info = _zenmaster().detect()
        _cpu = Cpu(
            name=info.name,
            family=info.family,
            kind=info.type,
            supported=info.type in ("Amd_Apu", "Amd_Desktop_Cpu"),
        )
    return _cpu


def _value(container: Any, name: str) -> float | None:
    value = getattr(container, name, None)
    if value is None and isinstance(container, dict):
        value = container.get(name)
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if value != value:
        return None
    return value


def _read_table() -> tuple[bytes, int]:
    zm = _zenmaster()
    ensure_backend()
    full = zm.read_pm_table_full(cpu().family)
    if not full:
        raise CoreError("Unable to read the PM table")
    return full


def _limit_from_table(zm: Any, data: bytes, version: int) -> float | None:
    for _label, value, flag in zm.table.read_table(data, version):
        if flag == "tctl-temp":
            return float(value)
    return None


def read_limit() -> float | None:
    data, version = _read_table()
    return _limit_from_table(_zenmaster(), data, version)


def read_live() -> Live:
    zm = _zenmaster()
    data, version = _read_table()
    sensors = zm.sensors.read_sensors(data, version)
    return Live(
        tctl=_value(sensors, "tctl_temp"),
        limit=_limit_from_table(zm, data, version),
        load=_value(sensors, "cclk_busy"),
        socket_power=_value(sensors, "socket_power"),
        gfx_clk=_value(sensors, "gfx_clk"),
    )


def apply_temp(temp: int) -> str:
    zm = _zenmaster()
    info = cpu()
    if not info.supported:
        raise CoreError(f"{info.name} is not supported by zenmaster")
    ensure_backend()
    results, _rejected = zm.apply(f"--tctl-temp={int(temp)}", info.family)
    accepted = [r for r in results if r["status"] == SMU_OK]
    if not accepted:
        reason = next((r["error"] for r in results if r["error"]), None)
        raise CoreError(reason or "SMU rejected the temperature limit")
    return f"Limit set to {int(temp)} °C"


def _logger() -> logging.Logger:
    logger = logging.getLogger("ryzen_temp_limit")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    try:
        handler = RotatingFileHandler(
            data_dir() / "app.log", maxBytes=256 * 1024, backupCount=2, encoding="utf-8"
        )
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    except OSError:
        pass
    if not getattr(sys, "frozen", False) and sys.stderr is not None:
        stream = logging.StreamHandler()
        stream.setFormatter(logging.Formatter("%(asctime)s %(message)s", "%H:%M:%S"))
        logger.addHandler(stream)
    return logger


log = _logger()


def log_path() -> str:
    return str(data_dir() / "app.log")
