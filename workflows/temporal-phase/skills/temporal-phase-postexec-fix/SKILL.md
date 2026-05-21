---
name: temporal-phase-postexec-fix
description: Codex absorbs the synthesized Adopted findings and applies the fix. Trigger POSTEXEC_FIX; writes from-codex/<phase-id>__postexec-fix.md (actual changes + validation + disposition); BatonNext = SECOND_AUDIT_DECISION.
---

# temporal-phase / postexec-fix (Codex lane)

## Trigger
- Baton state: `POSTEXEC_FIX` (`postexec-synthesis.md` marked Adopted
  non-empty)

## Reads
- The Adopted section of
  `from-codex/<phase-id>__postexec-synthesis.md`

## Writes
- `from-codex/<phase-id>__postexec-fix.md`
- Includes: actual changes (work-repo commit list), re-validation
  results, disposition
- BatonNext: `SECOND_AUDIT_DECISION`

## Product structure
```text
BatonNext: SECOND_AUDIT_DECISION

Fixes:
  - <Adopted finding → concrete change → temporal@<sha>>
ReValidation: ...
Conclusions:
  - <disposition for each Adopted finding>
```

## Authority
Codex-only.

## See also
`ROLES.md` Step 11 · `BATON.schema.md` state `POSTEXEC_FIX`
