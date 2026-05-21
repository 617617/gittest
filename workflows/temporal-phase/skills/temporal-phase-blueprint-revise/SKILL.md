---
name: temporal-phase-blueprint-revise
description: CC repairs the Phase blueprint per the synthesis. Trigger BLUEPRINT_REVISION_R{1,2,3}; writes from-cc/<phase-id>__blueprint-revision-r<N>.md; BatonNext = BLUEPRINT_ACCEPTED or PRE_AUDIT_R<N+1> or BLOCKED_BLUEPRINT (when R3 still blocks).
---

# temporal-phase / blueprint-revise (CC lane)

## Trigger
- Baton state: `BLUEPRINT_REVISION_R<N>` (N ∈ {1,2,3})

## Reads
- Current blueprint (R1 original; or the previous round's revision)
- The Adopted section of
  `from-cc/<phase-id>__pre-audit-synthesis-r<N>.md`

## Writes
- `from-cc/<phase-id>__blueprint-revision-r<N>.md`
- Includes: diff summary / actual changes / residual-risk assessment
- BatonNext:
  - `BLUEPRINT_ACCEPTED` — acceptable after the repair
  - `PRE_AUDIT_R<N+1>` — needs another round (only when N<3)
  - `BLOCKED_BLUEPRINT` — N=3 and blockers remain (terminal)

## Three-round cap
BATON.schema invariant §1: there is no `R4`. When N=3 and the result is
not acceptable, you **must** write `BLOCKED_BLUEPRINT`.

## Authority
CC-only. Codex must refuse this lane — blueprint repair belongs to the
CC synthesis loop.

## See also
`ROLES.md` Step 5 · `BATON.schema.md` state `BLUEPRINT_REVISION_R*`
