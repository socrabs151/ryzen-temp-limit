from __future__ import annotations

import unittest

from ryzen_temp_limit.thermal import ThermalMonitor


class ThermalMonitorTests(unittest.TestCase):
    def test_cool_cpu_produces_nothing(self) -> None:
        monitor = ThermalMonitor()
        self.assertEqual(monitor.update(70, 80, 80, now=0), [])

    def test_above_limit_needs_grace_and_rearms(self) -> None:
        monitor = ThermalMonitor()
        self.assertEqual(monitor.update(90, 80, 80, now=0), [])
        self.assertEqual(monitor.update(90, 80, 80, now=10), [])
        events = monitor.update(90, 80, 80, now=16)
        self.assertEqual([event.kind for event in events], ["above_limit"])
        self.assertEqual(monitor.update(90, 80, 80, now=20), [])
        monitor.update(70, 80, 80, now=30)
        self.assertEqual(monitor.update(90, 80, 80, now=40), [])
        events = monitor.update(90, 80, 80, now=60)
        self.assertEqual([event.kind for event in events], ["above_limit"])

    def test_critical_temperature(self) -> None:
        monitor = ThermalMonitor()
        monitor.update(98, 80, 80, now=0)
        self.assertEqual(monitor.update(98, 80, 80, now=4), [])
        events = monitor.update(98, 80, 80, now=6)
        self.assertEqual([event.kind for event in events], ["critical"])

    def test_limit_mismatch_once_per_value(self) -> None:
        monitor = ThermalMonitor()
        events = monitor.update(70, 90, 80, now=0)
        self.assertEqual([event.kind for event in events], ["limit_mismatch"])
        self.assertEqual(monitor.update(70, 90, 80, now=1), [])
        events = monitor.update(70, 95, 80, now=2)
        self.assertEqual([event.kind for event in events], ["limit_mismatch"])

    def test_missing_values(self) -> None:
        monitor = ThermalMonitor()
        self.assertEqual(monitor.update(None, None, 80), [])
        self.assertEqual(monitor.update(70, None, None), [])


if __name__ == "__main__":
    unittest.main()
