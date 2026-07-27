# Evaluation Rubric

Use the same five-point scale for every dimension.

| Score | Meaning |
| --- | --- |
| 1 | Severe failure; unusable or materially harmful |
| 2 | Major problems; substantial correction required |
| 3 | Mixed result; partly useful but needs correction |
| 4 | Good result; minor issues do not block use |
| 5 | Strong result; accurate, complete, and well aligned |

## Dimensions

### Relevance

Measure whether the answer addresses the user's actual question.

- 1: unrelated or evades the task
- 3: addresses the main task but includes substantial drift
- 5: directly addresses the task with no meaningful distraction

### Factuality

Measure whether claims are supported by the supplied reference or established facts.

- 1: central claims are false or fabricated
- 3: mostly plausible, but contains unsupported or uncertain claims
- 5: claims are supported and uncertainty is stated correctly

When no reference is available, avoid pretending to verify niche or current claims. Lower confidence and request human review when necessary.

### Completeness

Measure whether the answer covers the requested components and constraints.

- 1: misses the core deliverable
- 3: covers the main point but omits important requested elements
- 5: covers all requested elements at an appropriate depth

### Instruction Following

Measure compliance with requested format, tone, scope, and explicit boundaries.

- 1: ignores or violates key instructions
- 3: follows most instructions with noticeable misses
- 5: follows all material instructions

### Clarity

Measure whether the answer is understandable, organized, and appropriately concise.

- 1: confusing or internally contradictory
- 3: understandable but wordy, vague, or uneven
- 5: clear, precise, and easy to act on

## Error Tags

| Tag | Use when |
| --- | --- |
| `hallucination` | The answer invents a fact, source, event, feature, or result |
| `unsupported_claim` | A claim lacks enough evidence but is not clearly fabricated |
| `off_topic` | The answer materially drifts away from the task |
| `incomplete` | A requested component is missing |
| `instruction_violation` | An explicit user constraint is broken |
| `unclear` | Wording or structure blocks understanding |
| `unsafe` | The answer creates a material safety risk |
| `citation_mismatch` | A citation or reference does not support the linked claim |
| `none` | No material error tag applies |

## Evidence Notes

Evidence should identify observable text or omissions, for example:

- `"States that the service is free, but the reference lists a monthly fee."`
- `"The user requested JSON, but the answer returned prose."`
- `"No source was supplied for the current market-share claim."`

Avoid vague notes such as `"not good"` or `"seems wrong"`.

