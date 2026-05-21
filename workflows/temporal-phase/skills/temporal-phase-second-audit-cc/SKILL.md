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

## Authority
CC-only. Codex must refuse — the second audit needs an independent CC
review.

## See also
`ROLES.md` Step 13 · `BATON.schema.md` state `SECOND_AUDIT_CC`
