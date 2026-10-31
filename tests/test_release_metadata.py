from __future__ import annotations

import unittest

from ryzen_temp_limit import release_notes, version_info

CHANGELOG = """# Changelog

## 0.3.4

- First item.
- Second item.

## 0.3.3

- Old item.
"""


class ReleaseNotesTests(unittest.TestCase):
    def test_section(self) -> None:
        body = release_notes.section(CHANGELOG, "v0.3.4")
        self.assertIn("First item.", body)
        self.assertIn("Second item.", body)
        self.assertNotIn("Old item.", body)

    def test_render_includes_policy(self) -> None:
        text = release_notes.render(CHANGELOG, "v0.3.4")
        self.assertTrue(text.startswith("# Ryzen Temp Limit v0.3.4"))
        self.assertIn("SignPath Foundation", text)

    def test_missing_section(self) -> None:
        text = release_notes.render(CHANGELOG, "v9.9.9")
        self.assertIn("See CHANGELOG.md", text)


class VersionInfoTests(unittest.TestCase):
    def test_render(self) -> None:
        text = version_info.render("0.3.4")
        self.assertIn("filevers=(0, 3, 4, 0)", text)
        self.assertIn("StringStruct('FileVersion', '0.3.4')", text)
        self.assertIn("StringStruct('CompanyName', 'socrabs151')", text)
        self.assertIn("OriginalFilename", text)


if __name__ == "__main__":
    unittest.main()
