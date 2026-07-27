from __future__ import annotations

from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class StreamlitAppSmokeTests(unittest.TestCase):
    def test_app_starts_without_runtime_exceptions(self) -> None:
        app = AppTest.from_file(PROJECT_ROOT / "streamlit_app.py")
        app.run(timeout=15)
        self.assertEqual(list(app.exception), [])
        self.assertEqual(app.title[0].value, "EvalFlow")
        self.assertEqual(
            [tab.label for tab in app.tabs],
            ["单条评测", "批量分析", "人工复核"],
        )


if __name__ == "__main__":
    unittest.main()
