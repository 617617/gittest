---
name: temporal-phase-pre-audit-synthesize
description: CC synthesizes both pre-execution audits and signs the Adopted / Recorded / Out-of-scope verdict. Trigger PRE_AUDIT_SYNTHESIS_R{1,2,3}; BatonNext = BLUEPRINT_REVISION_R<N> or BLUEPRINT_ACCEPTED.
---

# temporal-phase / pre-audit-synthesize (CC lane)

## Trigger
- Baton state: `PRE_AUDIT_SYNTHESIS_R<N>`, with both
  `from-cc/<phase-id>__pre-audit-cc-r<N>.md` and
  `from-codex/<phase-id>__pre-audit-codex-r<N>.md` delivered.

## Reads
- `from-cc/<phase-id>__pre-audit-cc-r<N>.md`
- `from-codex/<phase-id>__pre-audit-codex-r<N>.md`

## Writes
- `from-cc/<phase-id>__pre-audit-synthesis-r<N>.md`
- BatonNext:
  - `BLUEPRINT_REVISION_R<N>` — there are findings to adopt
  - `BLUEPRINT_ACCEPTED` — Adopted is empty and the blueprint is
    acceptable as-is

## Product structure
```text
BatonNext: BLUEPRINT_REVISION_R<N> | BLUEPRINT_ACCEPTED

Adopted:
  - <finding + reporter + repair direction>
Recorded:
  - <finding + reason not to adopt (duplicate / kept for record)>
Out-of-scope:
  - <finding + which later Phase owns it>
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
CC-only. This lane is the closure judge of the pre-execution loop;
Codex must not write this product.

## See also
`ROLES.md` Step 4 + Step 6 · `BATON.schema.md` state
`PRE_AUDIT_SYNTHESIS_R*`
