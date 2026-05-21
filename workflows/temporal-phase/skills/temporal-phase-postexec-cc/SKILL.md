---
name: temporal-phase-postexec-cc
description: CC independent post-execution review. Trigger POSTEXEC_CC_REVIEW; reads execution report + Codex's subagent review as reference; writes from-cc/<phase-id>__postexec-cc-review.md; BatonNext = POSTEXEC_SYNTHESIS.
---

# temporal-phase / postexec-cc (CC lane)

## Trigger
- Baton state: `POSTEXEC_CC_REVIEW` (after
  `POSTEXEC_SUBAGENT_REVIEW` delivered)

## Reads
- `from-codex/<phase-id>__execution-report.md`
- `from-codex/<phase-id>__postexec-subagent-review.md` (reference only,
  **not** a substitute for independent judgment)

## Writes
- `from-cc/<phase-id>__postexec-cc-review.md`
- BatonNext: `POSTEXEC_SYNTHESIS`

## Product structure
```text
BatonNext: POSTEXEC_SYNTHESIS

ScopeConformance: ...
BlueprintAlignment: ...
MissedRisks: ...           # things Codex's subagents did not cover
BlockersForNextPhase: ...
Recommendation: ACCEPT | FIX_REQUIRED | BLOCKED
```

## CC's review angles (source document §8)
- Does the execution result match the blueprint?
- Did the repair actually solve the Phase goal?
- Are there problems Codex did not cover?
- Is there still a blocker for the next Phase?

## Authority
CC-only. Codex must refuse this lane — independent CC review is the
workflow's check on Codex's own subagent review.

## See also
`ROLES.md` Step 9 · `BATON.schema.md` state `POSTEXEC_CC_REVIEW`
