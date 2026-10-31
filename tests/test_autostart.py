from __future__ import annotations

import unittest

from ryzen_temp_limit import autostart
from ryzen_temp_limit.settings import Settings


class TaskXmlTests(unittest.TestCase):
    def test_task_runs_as_current_user(self) -> None:
        xml = autostart.build_xml(
            Settings(temp=80, interval_min=10),
            user="DOMAIN\\tester",
            start="2026-01-01T00:00:00",
        )
        self.assertIn("<LogonTrigger>", xml)
        self.assertIn("<LogonType>InteractiveToken</LogonType>", xml)
        self.assertIn("<RunLevel>HighestAvailable</RunLevel>", xml)
        self.assertIn("DOMAIN\\tester", xml)
        self.assertNotIn("S-1-5-18", xml)
        self.assertIn("<Interval>PT10M</Interval>", xml)
        self.assertIn("2026-01-01T00:00:00", xml)
        self.assertIn("--apply-only", xml)

    def test_interval_is_never_zero(self) -> None:
        xml = autostart.build_xml(Settings(interval_min=0), user="u", start="2026-01-01T00:00:00")
        self.assertIn("<Interval>PT1M</Interval>", xml)


if __name__ == "__main__":
    unittest.main()
