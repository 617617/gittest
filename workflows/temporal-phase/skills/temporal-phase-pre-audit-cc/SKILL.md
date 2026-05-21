---
name: temporal-phase-pre-audit-cc
description: CC-side pre-execution audit. Trigger PRE_AUDIT_R{1,2,3}; reads the current blueprint; writes from-cc/<phase-id>__pre-audit-cc-r<N>.md; the synthesis lane advances the state after this round's Codex half also lands.
---

# temporal-phase / pre-audit-cc (CC lane)

## Trigger
- Baton state: `PRE_AUDIT_R1` / `PRE_AUDIT_R2` / `PRE_AUDIT_R3`, with
  this round's CC half not yet delivered.

## Reads
- R1: `from-codex/<phase-id>__blueprint.md`
- R2/R3: `from-cc/<phase-id>__blueprint-revision-r<N-1>.md`

## Writes
- `from-cc/<phase-id>__pre-audit-cc-r<N>.md`
- First line `BatonNext: PRE_AUDIT_SYNTHESIS_R<N>` (declares that the
  baton is waiting for synthesis; the actual transition is driven by the
  `pre-audit-synthesize` lane).

## Product structure
```text
BatonNext: PRE_AUDIT_SYNTHESIS_R<N>

Findings: ...
Risks: ...
Open Questions: ...
Recommendation: ACCEPT | REVISE | ABANDON
```

CC focuses on: scope compliance, `AllowedFiles` reasonableness,
validation executability, alignment with source document §11 completion
criteria.

## Authority
CC-only. Codex must refuse — this is not a Codex lane and writing into
`from-cc/` from Codex is an authority violation.

## See also
`ROLES.md` Step 2 · `BATON.schema.md` state `PRE_AUDIT_R*`
