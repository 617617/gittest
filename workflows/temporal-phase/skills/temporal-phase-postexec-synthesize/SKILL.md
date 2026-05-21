---
name: temporal-phase-postexec-synthesize
description: Codex synthesizes both post-execution reviews and signs Adopted / Recorded / Out-of-scope. Trigger POSTEXEC_SYNTHESIS; BatonNext = POSTEXEC_FIX or PHASE_CLOSING.
---

# temporal-phase / postexec-synthesize (Codex lane)

## Trigger
- Baton state: `POSTEXEC_SYNTHESIS` (subagent review + CC review both
  delivered)

## Reads
- `from-codex/<phase-id>__postexec-subagent-review.md`
- `from-cc/<phase-id>__postexec-cc-review.md`

## Writes
- `from-codex/<phase-id>__postexec-synthesis.md`
- BatonNext:
  - `POSTEXEC_FIX` — Adopted is non-empty, repair is needed
  - `PHASE_CLOSING` — Adopted is empty, go straight to close

## Product structure
```text
BatonNext: POSTEXEC_FIX | PHASE_CLOSING

Adopted:
  - <finding + reporter (subagent / CC) + repair direction>
Recorded:
  - <finding + reason (invalid / duplicate but kept for record)>
Out-of-scope:
  - <finding + which later Phase owns it>
```

Source document §9 emphasizes: "invalid, duplicate, out-of-scope, or
later-Phase findings must each have an explicit disposition recorded to
avoid future re-debate."

## Authority
Codex-only.

## See also
`ROLES.md` Step 10 · `BATON.schema.md` state `POSTEXEC_SYNTHESIS`
