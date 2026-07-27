from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app_core import (  # noqa: E402
    EvaluationValidationError,
    build_evaluation_record,
    load_jsonl,
    merge_review_updates,
    must_require_human_review,
    normalize_error_tags,
    parse_records_text,
    records_to_jsonl,
    render_single_evaluation_markdown,
    summarize_records,
)


class AppCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sample_records = load_jsonl(
            PROJECT_ROOT / "data" / "sample_evaluations.jsonl"
        )

    def test_normalize_error_tags(self) -> None:
        self.assertEqual(normalize_error_tags([]), ["none"])
        self.assertEqual(
            normalize_error_tags(["none", "unclear", "unclear"]),
            ["unclear"],
        )

    def test_human_review_rules(self) -> None:
        scores = {
            "relevance": 5,
            "factuality": 5,
            "completeness": 5,
            "instruction_following": 5,
            "clarity": 5,
        }
        self.assertFalse(must_require_human_review(scores, ["none"], 0.90))
        self.assertTrue(must_require_human_review(scores, ["unsafe"], 0.90))
        low_factuality = {**scores, "factuality": 2}
        self.assertTrue(
            must_require_human_review(low_factuality, ["hallucination"], 0.90)
        )

    def test_build_record_applies_mandatory_review(self) -> None:
        record = build_evaluation_record(
            case_id="ui-001",
            scores={
                "relevance": 5,
                "factuality": 2,
                "completeness": 4,
                "instruction_following": 5,
                "clarity": 4,
            },
            error_tags=["hallucination"],
            evidence=["The answer contradicts the supplied reference."],
            rationale="A central factual error requires review.",
            confidence=0.92,
            manual_review=False,
            suggested_revision="Correct the unsupported factual claim.",
        )
        self.assertTrue(record["human_review_required"])

    def test_json_and_jsonl_parsing(self) -> None:
        first = self.sample_records[0]
        self.assertEqual(
            parse_records_text(json.dumps(first), ".json")[0]["case_id"],
            first["case_id"],
        )
        jsonl = records_to_jsonl(self.sample_records[:2])
        self.assertEqual(len(parse_records_text(jsonl, ".jsonl")), 2)

    def test_invalid_jsonl_is_rejected(self) -> None:
        with self.assertRaisesRegex(EvaluationValidationError, "line 1"):
            parse_records_text("{not json}", ".jsonl")

    def test_summary_and_markdown_export(self) -> None:
        summary, report = summarize_records(self.sample_records)
        self.assertEqual(summary["total_cases"], 6)
        self.assertIn("LLM Response Evaluation Report", report)

        markdown = render_single_evaluation_markdown(self.sample_records[0])
        self.assertIn("五维评分", markdown)
        self.assertIn(self.sample_records[0]["case_id"], markdown)

    def test_merge_review_updates_preserves_order(self) -> None:
        updated = deepcopy(self.sample_records[0])
        updated["rationale"] = "Reviewed and updated."
        merged = merge_review_updates(
            self.sample_records,
            {updated["case_id"]: updated},
        )
        self.assertEqual(
            [record["case_id"] for record in merged],
            [record["case_id"] for record in self.sample_records],
        )
        self.assertEqual(merged[0]["rationale"], "Reviewed and updated.")


if __name__ == "__main__":
    unittest.main()
