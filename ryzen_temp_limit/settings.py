from __future__ import annotations

import json
import os
import platform
import tempfile
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from . import APP_NAME, DEFAULT_INTERVAL_MIN, DEFAULT_TEMP, MAX_TEMP, MIN_TEMP

CONFIG_FILE = "settings.json"


@dataclass(frozen=True)
class Settings:
    temp: int = DEFAULT_TEMP
    interval_min: int = DEFAULT_INTERVAL_MIN
    autostart: bool = False

    def normalized(self) -> "Settings":
        temp = max(MIN_TEMP, min(MAX_TEMP, int(self.temp)))
        interval = max(1, min(120, int(self.interval_min)))
        return replace(self, temp=temp, interval_min=interval, autostart=bool(self.autostart))


def data_dir() -> Path:
    override = os.environ.get("RYZEN_TEMP_LIMIT_DIR")
    if override:
        path = Path(override)
        path.mkdir(parents=True, exist_ok=True)
        return path

    candidates: list[Path] = []
    if platform.system() == "Windows":
        base = os.environ.get("PROGRAMDATA") or os.environ.get("APPDATA")
        if base:
            candidates.append(Path(base) / APP_NAME.replace(" ", ""))
        appdata = os.environ.get("APPDATA")
        if appdata:
            candidates.append(Path(appdata) / APP_NAME.replace(" ", ""))
    else:
        candidates.append(Path.home() / ".config" / APP_NAME.replace(" ", "").lower())
    candidates.append(Path(tempfile.gettempdir()) / APP_NAME.replace(" ", ""))

    for path in candidates:
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".write-test"
            probe.write_text("", encoding="utf-8")
            probe.unlink()
            return path
        except OSError:
            continue
    raise OSError("No writable directory for application data")


def config_path() -> Path:
    return data_dir() / CONFIG_FILE


def load() -> Settings:
    path = config_path()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Settings()
    if not isinstance(raw, dict):
        return Settings()
    return Settings(
        temp=raw.get("temp", DEFAULT_TEMP),
        interval_min=raw.get("interval_min", DEFAULT_INTERVAL_MIN),
        autostart=raw.get("autostart", False),
    ).normalized()


def save(settings: Settings) -> None:
    settings = settings.normalized()
    path = config_path()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
    tmp.replace(path)
