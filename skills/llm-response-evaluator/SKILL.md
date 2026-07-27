---
name: llm-response-evaluator
description: Evaluate one or more LLM answers against user instructions and optional reference material using a transparent quality rubric. Use for model-response review, AI trainer tasks, LLM evaluation, answer quality audits, bad-case labeling, side-by-side answer comparison, or producing structured evaluation JSON for later batch analysis.
---

# LLM Response Evaluator

Evaluate model answers consistently, explain every score with observable evidence, and route uncertain or risky cases to human review.

## Workflow

1. Identify the evaluation input:
   - user request or question;
   - model answer;
   - optional reference answer or source material;
   - optional task-specific constraints.
2. Read [references/rubric.md](references/rubric.md).
3. Score all five dimensions from 1 to 5.
4. Assign only the error tags supported by the answer.
5. Quote or precisely describe the evidence behind the scores. Do not expose private data or secrets.
6. Set `human_review_required` according to the escalation rules below.
7. Return exactly one JSON object that follows [references/output-schema.md](references/output-schema.md).
8. When evaluating multiple answers, write one object per line as JSONL, then run:

```powershell
python scripts/validate_evaluations.py evaluations.jsonl
python scripts/summarize_evaluations.py evaluations.jsonl --json-out summary.json --markdown-out report.md
```

For a source-grounded STEM dataset, follow
[references/stem-case-schema.md](references/stem-case-schema.md), retain the
source filename and PDF page, and run:

```powershell
python scripts/validate_stem_cases.py stem_cases.jsonl
python scripts/build_stem_review_sheet.py stem_cases.jsonl evaluations.jsonl --output review.md
```

## Evaluation Rules

- Judge instruction following against the user's actual request, not personal preference.
- Judge factuality only from supplied references or clearly established facts. Lower confidence when evidence is insufficient.
- Do not invent citations, requirements, or hidden user intent.
- Keep the rationale concise and specific.
- Use `none` only when no other error tag applies.
- Treat the result as decision support, not unquestionable ground truth.
- Label synthetic candidates explicitly and never present them as real model
  benchmark results.
- When demonstrating Prompt A/B without live inference, label every output as
  a simulation fixture and keep the simulation boundary visible in reports.

## Human Review

Set `human_review_required` to `true` when any condition applies:

- `confidence` is below `0.70`;
- `factuality` is 1 or 2;
- `unsafe` or `citation_mismatch` is present;
- supplied sources conflict or are insufficient for a high-stakes conclusion;
- the evaluation may affect medical, legal, financial, employment, or safety decisions.

## Comparison Mode

When comparing answers:

1. Evaluate each answer independently before ranking.
2. Keep the same rubric and reference material for every answer.
3. Compare dimension scores and error tags.
4. Prefer the answer with stronger evidence and fewer material errors, not merely greater length.
5. Report ties when the available evidence does not support a clear winner.

## Boundaries

- Do not claim that this evaluation proves model accuracy or production quality.
- Do not automatically approve high-stakes answers.
- Do not treat style preferences as factual defects.
- Do not use the evaluator to fabricate benchmark gains.
