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

## Push procedure

Same shape as `/temporal-phase-start` Branch A (commit-before-rebase):

1. Run `python scripts/check_baton_artifacts.py` — must PASS against
   the working tree. On FAIL, `rm` the new file and stop.
2. `git add` the new product file.
3. `git commit -m "<step-tag>(<phase-id>): <brief>"`.
4. `git pull --rebase origin master` (tree is clean because step 3
   committed).
5. `git push origin master`.

If the rebase produces conflicts or the push is rejected, surface and
stop — do not auto-resolve.

## Authority
CC-only. Codex must refuse this lane — independent CC review is the
workflow's check on Codex's own subagent review.

## See also
`ROLES.md` Step 9 · `BATON.schema.md` state `POSTEXEC_CC_REVIEW`
