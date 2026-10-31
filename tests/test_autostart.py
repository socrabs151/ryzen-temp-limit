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


class TaskInfoTests(unittest.TestCase):
    def test_parse_installed(self) -> None:
        info = autostart.parse_task_info(
            '{"installed":true,"state":"Ready","lastRun":"2026-11-01 00:41:48",'
            '"lastResult":0,"nextRun":"2026-11-01 00:46:47"}'
        )
        self.assertTrue(info.installed)
        self.assertEqual(info.state, "Ready")
        self.assertEqual(info.last_run, "2026-11-01 00:41:48")
        self.assertEqual(info.last_result, 0)
        self.assertEqual(info.next_run, "2026-11-01 00:46:47")

    def test_parse_not_installed(self) -> None:
        self.assertFalse(autostart.parse_task_info('{"installed":false}').installed)

    def test_parse_garbage(self) -> None:
        self.assertFalse(autostart.parse_task_info("not json").installed)


if __name__ == "__main__":
    unittest.main()
