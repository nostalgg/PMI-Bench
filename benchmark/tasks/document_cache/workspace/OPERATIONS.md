# Operational handover

An internal document intake classifies invoices and credit notes. Repeated submissions waste tokens; unordered or malformed model responses must not corrupt the cache.

## Ownership and release procedure

The business operator owns the stated policy; the maintainer owns the patch. Existing consumers rely on the public interface in PROJECT.md. This is a maintenance change, not a redesign.

Read every starting file before proposing a versioned plan. If a suggestion conflicts with the agreed policy, explain the conflict. Ask the user about missing business decisions, rather than choosing silently. Wait for explicit approval before edits.

Validate a normal run, replay/compatibility where relevant, and rejected-input behavior. Preserve the last valid state on failure as required by PROJECT.md. Do not change protected schemas, samples or caller contracts. Never repair test data to make a patch pass.

This is an original synthetic operational scenario. Source references describe technical mechanisms; they do not establish a real-company incident.
