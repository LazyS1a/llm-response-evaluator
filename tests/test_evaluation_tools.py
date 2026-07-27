from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = (
    PROJECT_ROOT / "skills" / "llm-response-evaluator" / "scripts"
)
sys.path.insert(0, str(SCRIPTS_DIR))

from summarize_evaluations import build_summary, render_markdown  # noqa: E402
from validate_evaluations import (  # noqa: E402
    EvaluationValidationError,
    load_records,
    validate_record,
    validate_records,
)


class EvaluationValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sample_path = PROJECT_ROOT / "data" / "sample_evaluations.jsonl"
        cls.records = load_records(cls.sample_path)

    def test_sample_dataset_is_valid(self) -> None:
        validate_records(self.records)
        self.assertEqual(len(self.records), 6)

    def test_none_cannot_be_combined_with_another_tag(self) -> None:
        record = deepcopy(self.records[0])
        record["error_tags"] = ["none", "unclear"]
        with self.assertRaisesRegex(EvaluationValidationError, "cannot be combined"):
            validate_record(record)

    def test_low_factuality_requires_human_review(self) -> None:
        record = deepcopy(self.records[2])
        record["human_review_required"] = False
        with self.assertRaisesRegex(EvaluationValidationError, "must be true"):
            validate_record(record)

    def test_duplicate_case_id_is_rejected(self) -> None:
        duplicate = deepcopy(self.records[0])
        with self.assertRaisesRegex(EvaluationValidationError, "duplicate case_id"):
            validate_records([self.records[0], duplicate])

    def test_boolean_score_is_rejected(self) -> None:
        record = deepcopy(self.records[0])
        record["scores"]["clarity"] = True
        with self.assertRaisesRegex(EvaluationValidationError, "integer from 1 to 5"):
            validate_record(record)


class EvaluationSummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sample_path = PROJECT_ROOT / "data" / "sample_evaluations.jsonl"
        cls.records = load_records(sample_path)

    def test_summary_counts(self) -> None:
        summary = build_summary(self.records, pass_threshold=4.0)
        self.assertEqual(summary["total_cases"], 6)
        self.assertEqual(summary["human_review_cases"], 3)
        self.assertEqual(summary["error_tag_counts"]["unsupported_claim"], 2)
        self.assertEqual(summary["lowest_scoring_cases"][0]["case_id"], "case-006")

    def test_markdown_report_contains_sections(self) -> None:
        report = render_markdown(build_summary(self.records))
        self.assertIn("# LLM Response Evaluation Report", report)
        self.assertIn("## Dimension Averages", report)
        self.assertIn("## Lowest-Scoring Cases", report)

    def test_summary_is_json_serializable(self) -> None:
        json.dumps(build_summary(self.records))


if __name__ == "__main__":
    unittest.main()
