---
name: temporal-phase-second-audit-cc
description: CC second dual audit. Trigger SECOND_AUDIT_CC (entered when second-audit-decision=YES); writes from-cc/<phase-id>__second-audit-cc.md; BatonNext = SECOND_AUDIT_CODEX.
---

# temporal-phase / second-audit-cc (CC lane)

## Trigger
- Baton state: `SECOND_AUDIT_CC` (after
  `second-audit-decision.md` marked YES)

## Reads
- `from-codex/<phase-id>__postexec-fix.md`
- `from-codex/<phase-id>__postexec-synthesis.md` (reference the original
  synthesis)

## Writes
- `from-cc/<phase-id>__second-audit-cc.md`
- BatonNext: `SECOND_AUDIT_CODEX`

## Product structure
```text
BatonNext: SECOND_AUDIT_CODEX

FixSufficiency: ...        # does the fix sufficiently cover Adopted
RegressionRisk: ...        # did the fix introduce regressions
RemainingBlockers: ...
Recommendation: ACCEPT | FIX_REQUIRED | BLOCKED
```

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
CC-only. Codex must refuse — the second audit needs an independent CC
review.

## See also
`ROLES.md` Step 13 · `BATON.schema.md` state `SECOND_AUDIT_CC`
