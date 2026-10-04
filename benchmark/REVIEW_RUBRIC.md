# Human review rubric — accepted maintenance patches

Apply after correctness and scope acceptance; never compensate for a failed constraint
with a subjective style score. Reviewer identity/date, patch hash, scenario and variant
must be recorded. Use two reviewers for publishable comparisons when possible; record
agreement and resolve disagreements with concrete examples.

| Dimension | 0 | 1 | 2 |
| --- | --- | --- | --- |
| Scope and compatibility | Unnecessary redesign or broken consumer | Preserved consumer with avoidable change | Focused fix consistent with caller contracts |
| Readability | Hard to follow control/data flow | Understandable with some avoidable complexity | Clear names and direct control flow |
| Duplication and abstraction | Repeated logic or speculative frameworks | Some justified abstraction plus excess | Just enough reusable structure for the task |
| Failure behavior | Accepted tests pass but failure reasoning unclear | Behavior mostly explicit | Validation, ownership and rollback are easy to inspect |
| Business alignment | Unstated assumptions or misleading explanation | Assumptions stated but weakly justified | Decisions connected to documented business invariants |

Attach explanation/evidence for each dimension. Leave unknown rather than inventing
review. Do not reduce these judgments to an automated universal quality score.

Record lines/files changed as context, never reward short code by itself. More lines
may be necessary for validation, compatibility or recovery. Reference solutions are
examples, not canonical style targets; alternative implementations can be accepted.
A model's confident agreement with a user suggestion is not correctness evidence.
