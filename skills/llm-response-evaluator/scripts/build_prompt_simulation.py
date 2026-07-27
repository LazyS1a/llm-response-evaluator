#!/usr/bin/env python3
"""Build a transparent simulated Prompt V1/V2 experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from validate_evaluations import load_records, validate_records
from validate_stem_cases import load_cases, validate_cases


DISCLAIMER = (
    "Simulation fixture assembled from authored candidate and reference answers; "
    "not an isolated or live model inference."
)


def build_simulation(
    cases: list[dict],
    v1_evaluations: list[dict],
) -> tuple[list[dict], list[dict]]:
    evaluation_by_id = {
        evaluation["case_id"]: evaluation for evaluation in v1_evaluations
    }
    if set(evaluation_by_id) != {case["case_id"] for case in cases}:
        raise ValueError("case IDs do not match between cases and V1 evaluations")

    outputs: list[dict] = []
    evaluations: list[dict] = []
    for case in cases:
        base_id = case["case_id"]
        outputs.extend(
            [
                {
                    "experiment_id": "simulated-prompt-ab-001",
                    "case_id": base_id,
                    "prompt_version": "v1_question_only",
                    "model_label": "Codex simulation fixture",
                    "answer": case["candidate_answer"],
                    "answer_origin": "simulation_fixture",
                    "disclaimer": DISCLAIMER,
                },
                {
                    "experiment_id": "simulated-prompt-ab-001",
                    "case_id": base_id,
                    "prompt_version": "v2_reference_guided",
                    "model_label": "Codex simulation fixture",
                    "answer": case["reference_answer"],
                    "answer_origin": "simulation_fixture",
                    "disclaimer": DISCLAIMER,
                },
            ]
        )

        v1_evaluation = dict(evaluation_by_id[base_id])
        v1_evaluation["case_id"] = f"{base_id}-v1"
        evaluations.append(v1_evaluation)
        evaluations.append(
            {
                "case_id": f"{base_id}-v2",
                "scores": {
                    "relevance": 5,
                    "factuality": 5,
                    "completeness": 5,
                    "instruction_following": 5,
                    "clarity": 5,
                },
                "error_tags": ["none"],
                "evidence": [
                    "模拟 V2 使用已人工复核的参考答案，覆盖该题关键点且没有引入资料外结论。"
                ],
                "rationale": "在模拟流程中，参考资料约束后的答案与人工复核真值一致。",
                "confidence": 0.99,
                "human_review_required": False,
                "suggested_revision": "No material revision needed.",
            }
        )

    validate_records(evaluations)
    return outputs, evaluations


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(
        json.dumps(record, ensure_ascii=False, separators=(",", ":"))
        for record in records
    )
    path.write_text(content + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cases", type=Path)
    parser.add_argument("v1_evaluations", type=Path)
    parser.add_argument("--outputs-out", type=Path, required=True)
    parser.add_argument("--evaluations-out", type=Path, required=True)
    args = parser.parse_args()

    try:
        cases = load_cases(args.cases)
        validate_cases(cases)
        v1_evaluations = load_records(args.v1_evaluations)
        validate_records(v1_evaluations)
        outputs, evaluations = build_simulation(cases, v1_evaluations)
        write_jsonl(args.outputs_out, outputs)
        write_jsonl(args.evaluations_out, evaluations)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"build failed: {exc}\n")

    print(
        f"wrote {len(outputs)} simulated output(s) and "
        f"{len(evaluations)} evaluation(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
