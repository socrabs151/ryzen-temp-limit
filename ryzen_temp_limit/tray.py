from __future__ import annotations

from pathlib import Path
from typing import Any, cast

try:
    import pystray as _pystray
    from PIL import Image as _image
except Exception:  # pragma: no cover - optional dependency
    _pystray = None  # type: ignore[assignment]
    _image = None  # type: ignore[assignment]

AVAILABLE = _pystray is not None


class Tray:
    def __init__(self, app, image_path: Path | None) -> None:
        self.app = app
        self.image_path = image_path
        self.icon: Any = None
        self.active = False

    def start(self) -> bool:
        if not AVAILABLE:
            return False
        module = cast(Any, _pystray)
        menu = module.Menu(
            module.MenuItem("Show window", lambda: self._act("show"), default=True),
            module.MenuItem("Apply limit", lambda: self._act("apply")),
            module.MenuItem("Restore", lambda: self._act("restore")),
            module.MenuItem("Pause", lambda: self._act("pause")),
            module.Menu.SEPARATOR,
            module.MenuItem("Check for updates", lambda: self._act("check")),
            module.MenuItem("Exit", lambda: self._act("exit")),
        )
        self.icon = module.Icon("RyzenTempLimit", self._image(), "Ryzen Temp Limit", menu)
        self.icon.run_detached()
        self.active = True
        return True

    def _image(self) -> Any:
        image_module = cast(Any, _image)
        if self.image_path is not None and self.image_path.exists():
            return image_module.open(self.image_path).convert("RGBA")
        return image_module.new("RGBA", (64, 64), (214, 65, 31, 255))

    def _act(self, name: str) -> None:
        self.app._post(self.app._tray_action, name)

    def update(self, temperature: float | None, limit: int) -> None:
        if self.icon is None:
            return
        if temperature is None:
            text = f"Ryzen Temp Limit — limit {limit} °C"
        else:
            text = f"Ryzen Temp Limit — {temperature:.1f} °C (limit {limit} °C)"
        try:
            self.icon.title = text
        except Exception:
            pass

    def notify(self, title: str, message: str) -> None:
        if self.icon is None:
            return
        try:
            self.icon.notify(message, title)
        except Exception:
            pass

    def stop(self) -> None:
        if self.icon is not None:
            try:
                self.icon.stop()
            except Exception:
                pass
            self.icon = None
        self.active = False

