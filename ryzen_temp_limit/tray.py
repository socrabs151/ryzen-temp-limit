from __future__ import annotations

from pathlib import Path

try:
    import pystray
    from PIL import Image
except Exception:  # pragma: no cover - optional dependency
    pystray = None
    Image = None


class Tray:
    def __init__(self, app, image_path: Path | None) -> None:
        self.app = app
        self.image_path = image_path
        self.icon = None
        self.active = False

    def start(self) -> bool:
        if pystray is None:
            return False
        menu = pystray.Menu(
            pystray.MenuItem("Show window", lambda: self._act("show"), default=True),
            pystray.MenuItem("Apply limit", lambda: self._act("apply")),
            pystray.MenuItem("Restore", lambda: self._act("restore")),
            pystray.MenuItem("Pause", lambda: self._act("pause")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Check for updates", lambda: self._act("check")),
            pystray.MenuItem("Exit", lambda: self._act("exit")),
        )
        self.icon = pystray.Icon("RyzenTempLimit", self._image(), "Ryzen Temp Limit", menu)
        self.icon.run_detached()
        self.active = True
        return True

    def _image(self):
        if self.image_path is not None and self.image_path.exists():
            return Image.open(self.image_path).convert("RGBA")
        return Image.new("RGBA", (64, 64), (214, 65, 31, 255))

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

    def stop(self) -> None:
        if self.icon is not None:
            try:
                self.icon.stop()
            except Exception:
                pass
            self.icon = None
        self.active = False
