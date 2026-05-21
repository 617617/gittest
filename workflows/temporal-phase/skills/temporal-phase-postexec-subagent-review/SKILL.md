---
name: temporal-phase-postexec-subagent-review
description: Codex launches multiple subagents for an integrated review of the execution result. Trigger POSTEXEC_SUBAGENT_REVIEW; writes from-codex/<phase-id>__postexec-subagent-review.md; BatonNext = POSTEXEC_CC_REVIEW.
---

# temporal-phase / postexec-subagent-review (Codex lane)

## Trigger
- Baton state: `POSTEXEC_SUBAGENT_REVIEW` (after `EXECUTION_REPORTED`)

## Reads
- `from-codex/<phase-id>__execution-report.md`
- Actual work-repo diff via a `temporal@<base>..<head>` range

## Subagent angles (source document §7, one angle per subagent)
- Did execution stay within the blueprint scope?
- Are the changes within project boundaries?
- Are tests / validation sufficient?
- Are evidence artifacts complete?
- Are there omissions, regression risks, inconsistencies?
- Is supplementary repair needed?

## Writes
- `from-codex/<phase-id>__postexec-subagent-review.md`
- Merge multiple subagents' conclusions into a single file, tagging each
  finding with its reporter and weight
- BatonNext: `POSTEXEC_CC_REVIEW` (hand off to CC for independent
  review)

## Subagents ≠ decision-makers
Source document §7: subagents only emit opinions. The main driver still
makes the final disposition (synthesis happens later in the
`postexec-synthesize` lane).

## Authority
Codex-only.

## See also
`ROLES.md` Step 8 · `BATON.schema.md` state `POSTEXEC_SUBAGENT_REVIEW`
