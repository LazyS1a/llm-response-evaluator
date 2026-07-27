from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = (
    PROJECT_ROOT / "skills" / "llm-response-evaluator" / "scripts"
)
sys.path.insert(0, str(SCRIPTS_DIR))

from build_prompt_simulation import build_simulation  # noqa: E402
from compare_prompt_versions import (  # noqa: E402
    build_comparison,
    render_markdown,
)
from validate_evaluations import load_records  # noqa: E402
from validate_stem_cases import load_cases  # noqa: E402


class PromptSimulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = load_cases(PROJECT_ROOT / "data" / "stem_cases.jsonl")
        cls.v1_evaluations = load_records(
            PROJECT_ROOT / "data" / "stem_draft_evaluations.jsonl"
        )
        cls.outputs, cls.evaluations = build_simulation(
            cls.cases,
            cls.v1_evaluations,
        )

    def test_simulation_builds_paired_outputs(self) -> None:
        self.assertEqual(len(self.outputs), 20)
        self.assertEqual(len(self.evaluations), 20)
        versions = {record["prompt_version"] for record in self.outputs}
        self.assertEqual(
            versions,
            {"v1_question_only", "v2_reference_guided"},
        )

    def test_every_output_is_labeled_as_simulation(self) -> None:
        self.assertTrue(
            all(
                record["answer_origin"] == "simulation_fixture"
                for record in self.outputs
            )
        )
        self.assertTrue(
            all("not an isolated" in record["disclaimer"] for record in self.outputs)
        )

    def test_comparison_matches_expected_fixture_counts(self) -> None:
        comparison = build_comparison(self.evaluations)
        self.assertEqual(
            comparison["v1_question_only"]["material_error_cases"],
            6,
        )
        self.assertEqual(
            comparison["v2_reference_guided"]["material_error_cases"],
            0,
        )
        self.assertEqual(
            comparison["delta_v2_minus_v1"]["human_review_cases"],
            -6,
        )

    def test_report_contains_prominent_boundary(self) -> None:
        report = render_markdown(build_comparison(self.evaluations))
        self.assertIn("流程演示用模拟数据", report)
        self.assertIn("不能说明什么", report)


if __name__ == "__main__":
    unittest.main()
