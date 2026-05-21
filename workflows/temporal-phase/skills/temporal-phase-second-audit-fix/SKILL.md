---
name: temporal-phase-second-audit-fix
description: Codex final fix after the second dual audit. Trigger SECOND_AUDIT_FIX; writes from-codex/<phase-id>__second-audit-fix.md; BatonNext = PHASE_CLOSING (pass) or BLOCKED_POSTEXEC (still blocked, no further loop).
---

# temporal-phase / second-audit-fix (Codex lane)

## Trigger
- Baton state: `SECOND_AUDIT_FIX` (both second-audit sides delivered)

## Reads
- `from-cc/<phase-id>__second-audit-cc.md`
- `from-codex/<phase-id>__second-audit-codex.md`

## Writes
- `from-codex/<phase-id>__second-audit-fix.md`
- Includes: final fix + validation conclusion
- BatonNext:
  - `PHASE_CLOSING` — fix passes, ready to close
  - `BLOCKED_POSTEXEC` — still blocked (terminal, **no further loop**)

## Second dual audit is one-shot (invariant §3)
After `SECOND_AUDIT_FIX` you **cannot** loop back to
`SECOND_AUDIT_DECISION`. Source document §10: "The second dual audit
handles risk confirmation after a large repair; it must not loop
indefinitely."

## Product structure
```text
BatonNext: PHASE_CLOSING | BLOCKED_POSTEXEC

FinalFixes:
  - <finding → change → temporal@<sha>>
ReValidation: ...
FinalConclusion: PASS | BLOCKED
```

## Authority
Codex-only.

## See also
`ROLES.md` Step 15 · `BATON.schema.md` state `SECOND_AUDIT_FIX` ·
invariant §3
