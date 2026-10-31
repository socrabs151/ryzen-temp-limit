from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(frozen=True)
class ThermalEvent:
    kind: str
    message: str


class ThermalMonitor:
    """Read-only checks. It never changes the SMU limit by itself."""

    def __init__(
        self,
        over: float = 7.0,
        grace: float = 15.0,
        critical: float = 97.0,
        critical_grace: float = 5.0,
    ) -> None:
        self.over = over
        self.grace = grace
        self.critical = critical
        self.critical_grace = critical_grace
        self._hot_since: float | None = None
        self._hot_warned = False
        self._critical_since: float | None = None
        self._critical_warned = False
        self._mismatched: set[int] = set()

    def update(
        self,
        temperature: float | None,
        limit: float | None,
        target: float | None,
        now: float | None = None,
    ) -> list[ThermalEvent]:
        if temperature is None or target is None:
            return []
        current = time.monotonic() if now is None else now
        events: list[ThermalEvent] = []

        if limit is not None and abs(float(limit) - float(target)) > 1.5:
            key = int(round(float(limit)))
            if key not in self._mismatched:
                self._mismatched.add(key)
                events.append(
                    ThermalEvent(
                        "limit_mismatch",
                        f"SMU limit is {float(limit):.0f} °C, expected {float(target):.0f} °C"
                        " — press Apply or Repair task.",
                    )
                )

        if temperature >= float(target) + self.over:
            if self._hot_since is None:
                self._hot_since = current
            if current - self._hot_since >= self.grace and not self._hot_warned:
                self._hot_warned = True
                events.append(
                    ThermalEvent(
                        "above_limit",
                        f"CPU is {temperature:.0f} °C, above the {float(target):.0f} °C ceiling;"
                        " the firmware may be ignoring the limit.",
                    )
                )
        else:
            self._hot_since = None
            if temperature < float(target) - 2:
                self._hot_warned = False

        if temperature >= self.critical:
            if self._critical_since is None:
                self._critical_since = current
            if current - self._critical_since >= self.critical_grace and not self._critical_warned:
                self._critical_warned = True
                events.append(
                    ThermalEvent("critical", f"CPU temperature reached {temperature:.0f} °C.")
                )
        else:
            self._critical_since = None
            if temperature < self.critical - 5:
                self._critical_warned = False

        return events
