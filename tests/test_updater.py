from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from ryzen_temp_limit import updater


class VersionTests(unittest.TestCase):
    def test_parse_version(self) -> None:
        self.assertEqual(updater.parse_version("v0.2.0"), (0, 2, 0))
        self.assertEqual(updater.parse_version("1.10"), (1, 10))
        self.assertEqual(updater.parse_version("release-2026.1"), (2026, 1))
        self.assertEqual(updater.parse_version("nonsense"), (0,))

    def test_is_newer(self) -> None:
        self.assertTrue(updater.is_newer("0.2.0", "0.1.9"))
        self.assertTrue(updater.is_newer("v0.10.0", "0.9.9"))
        self.assertFalse(updater.is_newer("0.2.0", "0.2.0"))
        self.assertFalse(updater.is_newer("0.1.9", "0.2.0"))
        self.assertFalse(updater.is_newer("0.2", "0.2.0"))
        self.assertTrue(updater.is_newer("0.2.1", "0.2"))


class AssetTests(unittest.TestCase):
    def _release(self, **assets: str) -> updater.Release:
        return updater.Release(version="0.2.0", tag="v0.2.0", page_url="", assets=assets)

    def test_pick_asset(self) -> None:
        release = self._release(
            **{
                updater.ONEDIR_ASSET: "https://example/onedir.zip",
                updater.ONEFILE_ASSET: "https://example/onefile.exe",
            }
        )
        self.assertEqual(updater.pick_asset(release, "onedir"), "https://example/onedir.zip")
        self.assertEqual(updater.pick_asset(release, "onefile"), "https://example/onefile.exe")

    def test_pick_asset_missing(self) -> None:
        with self.assertRaises(updater.UpdateError):
            updater.pick_asset(self._release(), "onedir")

    def test_parse_sums(self) -> None:
        text = (
            "abc123  RyzenTempLimit-win64.zip\n"
            "DEF456 *RyzenTempLimit-onefile.exe\n"
            "malformed line here\n"
        )
        sums = updater.parse_sums(text)
        self.assertEqual(sums["RyzenTempLimit-win64.zip"], "abc123")
        self.assertEqual(sums["RyzenTempLimit-onefile.exe"], "def456")
        self.assertEqual(len(sums), 2)

    def test_source_checkout_is_not_frozen(self) -> None:
        self.assertIsNone(updater.frozen_mode())

    def test_render_updater_script(self) -> None:
        script = updater.render_updater_script(
            pid=1234,
            mode="onedir",
            source=Path(r"C:\stage"),
            target=Path(r"C:\app"),
            exe=Path(r"C:\app\RyzenTempLimit.exe"),
            new_exe=None,
            workdir=Path(r"C:\work"),
        )
        self.assertIn("1234", script)
        self.assertIn("robocopy 'C:\\stage' 'C:\\app'", script)
        self.assertIn("Start-Process -FilePath 'C:\\app\\RyzenTempLimit.exe'", script)
        self.assertNotIn("@PID@", script)
        self.assertNotIn("@LOG@", script)
        self.assertNotIn("@EXE@", script)

    def test_render_updater_script_single_file(self) -> None:
        script = updater.render_updater_script(
            pid=99,
            mode="onefile",
            source=None,
            target=Path(r"C:\app"),
            exe=Path(r"C:\app\RyzenTempLimit.exe"),
            new_exe=Path(r"C:\work\new.exe"),
            workdir=Path(r"C:\work"),
        )
        self.assertIn("if ($true)", script)
        self.assertIn("Copy-Item -LiteralPath 'C:\\work\\new.exe'", script)

    def test_update_root_uses_local_appdata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            previous = os.environ.get("LOCALAPPDATA")
            os.environ["LOCALAPPDATA"] = temporary
            try:
                root = updater.update_root()
            finally:
                if previous is None:
                    os.environ.pop("LOCALAPPDATA", None)
                else:
                    os.environ["LOCALAPPDATA"] = previous
            self.assertEqual(root, Path(temporary) / "RyzenTempLimit" / "update")


if __name__ == "__main__":
    unittest.main()
