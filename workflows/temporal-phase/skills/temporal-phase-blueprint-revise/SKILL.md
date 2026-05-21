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
CC-only. Codex must refuse this lane — blueprint repair belongs to the
CC synthesis loop.

## See also
`ROLES.md` Step 5 · `BATON.schema.md` state `BLUEPRINT_REVISION_R*`
