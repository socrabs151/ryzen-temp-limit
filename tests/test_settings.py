from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from ryzen_temp_limit import settings as store


class SettingsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["RYZEN_TEMP_LIMIT_DIR"] = self._tmp.name

    def tearDown(self) -> None:
        os.environ.pop("RYZEN_TEMP_LIMIT_DIR", None)
        self._tmp.cleanup()

    def test_defaults(self) -> None:
        self.assertEqual(store.load(), store.Settings())

    def test_roundtrip(self) -> None:
        store.save(store.Settings(temp=90, interval_min=10, autostart=True))
        self.assertEqual(store.load(), store.Settings(temp=90, interval_min=10, autostart=True))

    def test_out_of_range_is_clamped(self) -> None:
        normalized = store.Settings(temp=500, interval_min=0).normalized()
        self.assertEqual(normalized.temp, store.MAX_TEMP)
        self.assertEqual(normalized.interval_min, 1)

    def test_corrupt_file_falls_back(self) -> None:
        store.config_path().write_text("{not json", encoding="utf-8")
        self.assertEqual(store.load(), store.Settings())

    def test_partial_file(self) -> None:
        store.config_path().write_text('{"temp": 75}', encoding="utf-8")
        loaded = store.load()
        self.assertEqual(loaded.temp, 75)
        self.assertEqual(loaded.interval_min, store.DEFAULT_INTERVAL_MIN)
        self.assertFalse(loaded.autostart)

    def test_migrates_settings_from_programdata(self) -> None:
        previous = {key: os.environ.get(key) for key in ("RYZEN_TEMP_LIMIT_DIR", "LOCALAPPDATA", "PROGRAMDATA")}
        os.environ.pop("RYZEN_TEMP_LIMIT_DIR", None)
        with tempfile.TemporaryDirectory() as local, tempfile.TemporaryDirectory() as programdata:
            os.environ["LOCALAPPDATA"] = local
            os.environ["PROGRAMDATA"] = programdata
            try:
                legacy = Path(programdata) / "RyzenTempLimit" / "settings.json"
                legacy.parent.mkdir(parents=True)
                legacy.write_text('{"temp": 77, "interval_min": 15, "autostart": true}', encoding="utf-8")

                loaded = store.load()

                self.assertEqual(loaded.temp, 77)
                self.assertEqual(loaded.interval_min, 15)
                self.assertTrue(loaded.autostart)
                self.assertTrue((Path(local) / "RyzenTempLimit" / "settings.json").is_file())
            finally:
                for key, value in previous.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
