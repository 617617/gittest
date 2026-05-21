---
name: temporal-phase-second-audit-decision
description: Codex decides whether to enter the second dual audit. Trigger SECOND_AUDIT_DECISION; writes from-codex/<phase-id>__second-audit-decision.md; BatonNext = SECOND_AUDIT_CC (YES) or PHASE_CLOSING (NO).
---

# temporal-phase / second-audit-decision (Codex lane)

## Trigger
- Baton state: `SECOND_AUDIT_DECISION` (`POSTEXEC_FIX` delivered)

## Reads
- `from-codex/<phase-id>__postexec-fix.md` (repair size + blast radius)

## Decision criteria (source document §10)
- **NO** — fix is small and does not change the Phase's core path →
  `PHASE_CLOSING`
- **YES** — fix is large, or touches the core path / important
  boundaries / critical validation → `SECOND_AUDIT_CC`

## Writes
- `from-codex/<phase-id>__second-audit-decision.md`
- BatonNext: `SECOND_AUDIT_CC` or `PHASE_CLOSING`

## Product structure
```text
BatonNext: SECOND_AUDIT_CC | PHASE_CLOSING

Decision: YES | NO
Rationale:
  - Fix size: <files / lines / modules>
  - Touches core path: <yes/no + reason>
  - Touches critical validation: <yes/no + reason>
```

## Authority
Codex-only.

## See also
`ROLES.md` Step 12 · `BATON.schema.md` state `SECOND_AUDIT_DECISION`
