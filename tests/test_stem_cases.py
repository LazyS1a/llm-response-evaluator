from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = (
    PROJECT_ROOT / "skills" / "llm-response-evaluator" / "scripts"
)
sys.path.insert(0, str(SCRIPTS_DIR))

from build_stem_review_sheet import render_review_sheet  # noqa: E402
from mark_stem_review import mark_cases  # noqa: E402
from validate_evaluations import load_records, validate_records  # noqa: E402
from validate_stem_cases import (  # noqa: E402
    StemCaseValidationError,
    coverage,
    load_cases,
    validate_case,
    validate_cases,
)


class StemCaseValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = load_cases(PROJECT_ROOT / "data" / "stem_cases.jsonl")

    def test_stem_dataset_is_valid(self) -> None:
        validate_cases(self.cases)
        self.assertEqual(len(self.cases), 10)

    def test_dataset_covers_all_six_domains(self) -> None:
        result = coverage(self.cases)
        self.assertEqual(len(result["domains"]), 6)
        self.assertEqual(result["answer_origin"], {"synthetic_fixture": 10})

    def test_source_pages_must_be_sorted(self) -> None:
        case = deepcopy(self.cases[0])
        case["sources"][0]["pages"] = [9, 8]
        with self.assertRaisesRegex(StemCaseValidationError, "unique and sorted"):
            validate_case(case)

    def test_empty_key_points_are_rejected(self) -> None:
        case = deepcopy(self.cases[0])
        case["key_points"] = []
        with self.assertRaisesRegex(StemCaseValidationError, "at least two"):
            validate_case(case)

    def test_selected_cases_can_be_marked_reviewed(self) -> None:
        cases = deepcopy(self.cases)
        mark_cases(cases, {"stem-001", "stem-002"}, "human_reviewed")
        status_by_id = {
            case["case_id"]: case["review_status"] for case in cases
        }
        self.assertEqual(status_by_id["stem-001"], "human_reviewed")
        self.assertEqual(status_by_id["stem-002"], "human_reviewed")

    def test_unknown_review_case_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown case IDs"):
            mark_cases(deepcopy(self.cases), {"stem-999"}, "human_reviewed")


class StemReviewSheetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = load_cases(PROJECT_ROOT / "data" / "stem_cases.jsonl")
        cls.evaluations = load_records(
            PROJECT_ROOT / "data" / "stem_draft_evaluations.jsonl"
        )

    def test_draft_evaluations_are_valid(self) -> None:
        validate_records(self.evaluations)
        self.assertEqual(len(self.evaluations), 10)

    def test_review_sheet_contains_every_case(self) -> None:
        sheet = render_review_sheet(self.cases, self.evaluations)
        for case in self.cases:
            self.assertIn(case["case_id"], sheet)
        self.assertIn("合成样例", sheet)
        self.assertIn("人工意见", sheet)

    def test_reviewed_case_is_checked_in_sheet(self) -> None:
        cases = deepcopy(self.cases)
        mark_cases(cases, {"stem-001"}, "human_reviewed")
        sheet = render_review_sheet(cases, self.evaluations)
        first_case = sheet.split("## stem-002", maxsplit=1)[0]
        self.assertIn("- [x] 接受参考答案与关键点", first_case)
        self.assertIn("已复核通过", first_case)


if __name__ == "__main__":
    unittest.main()
