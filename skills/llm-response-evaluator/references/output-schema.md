# Output Schema

Return one JSON object per evaluated answer.

```json
{
  "case_id": "case-001",
  "scores": {
    "relevance": 5,
    "factuality": 4,
    "completeness": 4,
    "instruction_following": 5,
    "clarity": 5
  },
  "error_tags": ["unsupported_claim"],
  "evidence": [
    "The answer gives the requested steps but does not support one current product claim."
  ],
  "rationale": "The response is useful and well structured, with one unsupported statement.",
  "confidence": 0.82,
  "human_review_required": false,
  "suggested_revision": "Remove the unsupported product claim or add a verified source."
}
```

## Required Fields

| Field | Type | Constraint |
| --- | --- | --- |
| `case_id` | string | non-empty and unique within a batch |
| `scores` | object | contains all five dimensions |
| each score | integer | 1 through 5 |
| `error_tags` | array of strings | contains only defined tags |
| `evidence` | array of strings | at least one specific observation |
| `rationale` | string | non-empty |
| `confidence` | number | 0.0 through 1.0 |
| `human_review_required` | boolean | follows escalation rules |
| `suggested_revision` | string | non-empty; use `"No material revision needed."` when applicable |

`none` cannot appear with another error tag.

