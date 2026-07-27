# STEM Case Schema

Each line in `data/stem_cases.jsonl` is one source-grounded evaluation case.

| Field | Type | Notes |
| --- | --- | --- |
| `case_id` | string | Unique identifier beginning with `stem-` |
| `domain` | string | Subject area used for coverage analysis |
| `difficulty` | string | `basic`, `intermediate`, or `advanced` |
| `prompt` | string | The task shown to the model |
| `reference_answer` | string | Paraphrased source-grounded answer |
| `key_points` | array | Observable points expected in a strong answer |
| `sources` | array | Source filename, one or more PDF pages, and a locator note |
| `candidate_answer` | string | Answer to evaluate |
| `answer_origin` | string | `synthetic_fixture` or `real_model_output` |
| `review_status` | string | `pending_human_review` or `human_reviewed` |

The local course PDFs are not redistributed with the repository. Source
filenames and page numbers are retained for traceability. Synthetic fixtures
exercise the evaluation workflow but are not evidence of real model quality.
