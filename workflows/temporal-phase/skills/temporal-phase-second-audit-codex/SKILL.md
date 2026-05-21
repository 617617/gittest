---
name: temporal-phase-second-audit-codex
description: Codex second dual audit. Trigger SECOND_AUDIT_CODEX; Codex uses subagents to audit the fix once more; writes from-codex/<phase-id>__second-audit-codex.md; BatonNext = SECOND_AUDIT_FIX.
---

# temporal-phase / second-audit-codex (Codex lane)

## Trigger
- Baton state: `SECOND_AUDIT_CODEX` (CC second audit delivered)

## Reads
- `from-codex/<phase-id>__postexec-fix.md`
- `from-cc/<phase-id>__second-audit-cc.md`

## Procedure
Use subagents to audit the fix once more. Angles are similar to
`postexec-subagent-review`, but with the emphasis on "did this fix
introduce new risk or regression?"

## Writes
- `from-codex/<phase-id>__second-audit-codex.md`
- BatonNext: `SECOND_AUDIT_FIX`

## Product structure
```text
BatonNext: SECOND_AUDIT_FIX

FixCoverage: ...           # does the fix cover Adopted
NewRisks: ...              # new risks introduced by the fix
RegressionSignals: ...
Recommendation: ACCEPT | FIX_REQUIRED | BLOCKED
```

## Authority
Codex-only.

## See also
`ROLES.md` Step 14 · `BATON.schema.md` state `SECOND_AUDIT_CODEX`
