# Sort + tiebreak rules: "most recent artifact"

Used by Step 3 of `temporal-phase-codex-sync` to decide which mailbox
artifact across `from-cc/` and `from-codex/` represents the current
baton state. Skip `_coord/archive/<phase-id>/` directories — those are
closed Phases.

## Rules (in priority order)

1. **Single-artifact case.** If only one non-`.gitkeep` artifact
   exists across both mailboxes, that is the most recent — no
   tiebreak needed.

2. **Sort by `phase-id`, then by step-tag.** If multiple artifacts
   exist, sort by `phase-id` first (highest wins; there should
   normally be only one open phase-id), then by step-tag using the
   baton transition order in `BATON.schema.md` — later states sort
   later. Round-numbered tags (`pre-audit-codex-r2`) sort after
   lower-round tags (`pre-audit-codex-r1`).

3. **Git commit order fallback.** If still ambiguous, fall back to
   git commit order:

   ```bash
   git log --format='%H %s' workflows/temporal-phase/_coord/
   ```

Read the chosen artifact's first line `BatonNext: <STATE>`. That is
the current baton state.

## Special case — first artifact for a Phase ever

The most recent artifact is `from-cc/<phase-id>__kickoff.md`. Its
`BatonNext:` is `DRAFTING_BLUEPRINT`. That is your trigger to enter
the blueprint lane
(`workflows/temporal-phase/skills/temporal-phase-blueprint/SKILL.md`).
Read the kickoff completely for `PhaseId:`, `Goal:`, `SourceAnchor:`,
`PreviousPhaseClose:`, then proceed.
