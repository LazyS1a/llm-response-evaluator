from __future__ import annotations

from pathlib import Path
import re
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ReleaseMetadataTests(unittest.TestCase):
    def test_version_is_consistent_across_release_files(self) -> None:
        version = (PROJECT_ROOT / "VERSION").read_text(encoding="utf-8").strip()
        changelog = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        self.assertIn(f"## [{version}]", changelog)
        self.assertIn(f"version-v{version}", readme)


if __name__ == "__main__":
    unittest.main()
