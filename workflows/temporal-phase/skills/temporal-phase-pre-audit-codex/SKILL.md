---
name: temporal-phase-pre-audit-codex
description: Codex-side pre-execution audit. Trigger PRE_AUDIT_R{1,2,3}; reads the current blueprint; writes from-codex/<phase-id>__pre-audit-codex-r<N>.md; BatonNext = PRE_AUDIT_SYNTHESIS_R<N>.
---

# temporal-phase / pre-audit-codex (Codex lane)

## Trigger
- Baton state: `PRE_AUDIT_R1` / `PRE_AUDIT_R2` / `PRE_AUDIT_R3`, with
  this round's Codex half not yet delivered.

## Reads
- R1: `from-codex/<phase-id>__blueprint.md`
- R2/R3: `from-cc/<phase-id>__blueprint-revision-r<N-1>.md` (the
  previous round's revision)

## Writes
- `from-codex/<phase-id>__pre-audit-codex-r<N>.md`
- First line `BatonNext: PRE_AUDIT_SYNTHESIS_R<N>`

## Product structure
```text
BatonNext: PRE_AUDIT_SYNTHESIS_R<N>

Findings: ...
Risks: ...
Open Questions: ...
Recommendation: ACCEPT | REVISE | ABANDON
```

Fully symmetric to `pre-audit-cc`. Codex audits from a code- and
execution-feasibility angle; CC audits from scope and closure-loop
angles.

## Authority
Codex-only.

## See also
`ROLES.md` Step 3 · `BATON.schema.md` state `PRE_AUDIT_R*`
