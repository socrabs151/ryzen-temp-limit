from __future__ import annotations

import time
import tkinter as tk
from collections import deque

WINDOW_SECONDS = 60
LINE_COLOR = "#d6401f"
GRID_COLOR = "#ececec"
TEXT_COLOR = "#888888"


class TemperatureGraph(tk.Canvas):
    def __init__(self, master: tk.Misc, height: int = 96) -> None:
        super().__init__(
            master, height=height, background="#ffffff",
            highlightthickness=1, highlightbackground="#c8c8c8",
        )
        self._samples: deque[tuple[float, float]] = deque()
        self._target = 80
        self.bind("<Configure>", lambda _event: self._draw())

    def add(self, temperature: float, now: float | None = None) -> None:
        moment = time.monotonic() if now is None else now
        self._samples.append((moment, float(temperature)))
        self._prune(moment)
        self._draw()

    def tick(self) -> None:
        self._prune(time.monotonic())
        self._draw()

    def set_target(self, target: int) -> None:
        self._target = int(target)
        self._draw()

    def _prune(self, now: float) -> None:
        cutoff = now - WINDOW_SECONDS
        while self._samples and self._samples[0][0] < cutoff:
            self._samples.popleft()

    def _draw(self) -> None:
        self.delete("all")
        width = self.winfo_width()
        height = self.winfo_height()
        if width < 100 or height < 50:
            return

        left, right = 44, width - 12
        top, bottom = 10, height - 24
        now = time.monotonic()
        values = [value for _moment, value in self._samples]
        low = max(0.0, min([40.0, float(self._target), *values]) - 2)
        high = max([90.0, float(self._target), *values]) + 2
        if high - low < 10:
            high = low + 10

        def y_of(value: float) -> float:
            return bottom - (value - low) / (high - low) * (bottom - top)

        def x_of(moment: float) -> float:
            ratio = (moment - (now - WINDOW_SECONDS)) / WINDOW_SECONDS
            return left + max(0.0, min(1.0, ratio)) * (right - left)

        step = 10
        degree = int(low // step * step)
        while degree <= high:
            if degree >= low:
                y = y_of(degree)
                self.create_line(left, y, right, y, fill=GRID_COLOR)
                self.create_text(
                    left - 6, y, text=str(degree), anchor="e", fill=TEXT_COLOR,
                    font=("Segoe UI", 7),
                )
            degree += step

        target_y = y_of(float(self._target))
        for x in range(left, right, 9):
            self.create_line(x, target_y, min(x + 4, right), target_y, fill=LINE_COLOR)
        self.create_text(
            right - 2, target_y - 2, text=f"{self._target} °C", anchor="se",
            fill=LINE_COLOR, font=("Segoe UI", 7),
        )

        if len(self._samples) >= 2:
            points: list[float] = []
            for moment, value in self._samples:
                points.extend((x_of(moment), y_of(value)))
            self.create_line(*points, fill=LINE_COLOR, width=2)

        if self._samples:
            moment, value = self._samples[-1]
            x, y = x_of(moment), y_of(value)
            self.create_oval(x - 3, y - 3, x + 3, y + 3, fill=LINE_COLOR, outline="")

        self.create_text(left, bottom + 12, text="60 s", anchor="w", fill=TEXT_COLOR, font=("Segoe UI", 7))
        self.create_text(right, bottom + 12, text="now", anchor="e", fill=TEXT_COLOR, font=("Segoe UI", 7))

