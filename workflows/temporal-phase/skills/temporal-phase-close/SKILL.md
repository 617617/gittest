---
name: temporal-phase-close
description: Codex closes the Phase. Trigger PHASE_CLOSING; checks every completion criterion in CHARTER; writes from-codex/<phase-id>__close.md; BatonNext = COMPLETED or BLOCKED_POSTEXEC.
---

# temporal-phase / close (Codex lane)

## Trigger
- Baton state: `PHASE_CLOSING` (entered from `POSTEXEC_SYNTHESIS` with
  Adopted empty, or `POSTEXEC_FIX → SECOND_AUDIT_DECISION=NO`, or
  `SECOND_AUDIT_FIX=PASS`)

## Required: check the completion criteria (invariant §2)
Walk every item in
`workflows/temporal-phase/CHARTER.md` "Completion criteria" section and
tag each **satisfied / not satisfied**. Any item not satisfied →
`BLOCKED_POSTEXEC`; `COMPLETED` is not allowed.

## Reads
- All products of this Phase (blueprint, audits, execution report,
  synthesis, fix, second-dual-audit results)
- The "Completion criteria" section of `CHARTER.md`

## Writes
- `from-codex/<phase-id>__close.md`
- BatonNext: `COMPLETED` or `BLOCKED_POSTEXEC`

## Product structure

The `CompletionCriteria` block uses the same `CC-NN` IDs and verbatim
text as `CHARTER.md` §"Completion criteria". The verifier cross-checks
that the same set of IDs appears in both files.

```text
BatonNext: COMPLETED | BLOCKED_POSTEXEC

CompletionCriteria:
  - CC-01 Blueprint passed pre-execution audit:                                [PASS|FAIL] <evidence>
  - CC-02 Execution did not exceed scope, or any deviation was explicitly
          recorded and re-confirmed:                                           [PASS|FAIL] <evidence>
  - CC-03 Codex completed execution and produced the execution report:         [PASS|FAIL] <evidence>
  - CC-04 Codex subagents completed the post-execution review:                 [PASS|FAIL] <evidence>
  - CC-05 CC completed the independent post-execution review:                  [PASS|FAIL] <evidence>
  - CC-06 Codex synthesized both sides and absorbed the valid findings:        [PASS|FAIL] <evidence>
  - CC-07 Required repairs and re-validation are complete:                    [PASS|FAIL|N/A] <evidence>
  - CC-08 If large/high-risk repair happened, one extra dual-audit + repair
          cycle has completed:                                                [PASS|FAIL|N/A] <evidence>
  - CC-09 Blockers cleared; remaining risks have explicit recording and
          follow-up ownership:                                                 [PASS|FAIL] <evidence>

ResidualRisks:
  - <residual risk + follow-up ownership (next Phase / separate ticket / accepted)>

NextPhasePlan:
  NextPhaseId:       <DERIVED from queue+INDEX per §"Derivation rule" below — or omit if chain explicitly stops>
  NextPhaseGoal:     <DERIVED from queue Notes column + relevant Phase design doc>
  NextSourceAnchor:  <DERIVED from the relevant Phase design doc path>
  StopReason:        <required only if NextPhaseId is omitted; e.g. "roadmap complete" / "blocking risk needs human triage">
```

## Derivation rule for NextPhasePlan (mandatory unless chain stops)

The next-Phase pick is **not user input**; it is **read off** the
work-repo roadmap. Codex executing this lane MUST:

1. Read
   `temporal:docs/skill-temporal-reorchestration/stage-loop-auto-packages/INDEX.md`
   §"Planned but not generated successor package candidates"
   (ordered list).
2. Read
   `temporal:docs/skill-temporal-reorchestration/current/execution/STAGE_LOOP_AUTO_EXECUTION_QUEUE_ZH_2026-05-16.md`
   §"Current Cursor" for any explicit "next package" override.
3. Select the FIRST candidate in the ordered list whose package has
   not yet been completed (cross-check against
   `stage-loop-auto-packages/history/` archive).
4. **`NextPhaseId`** is that candidate's package id (e.g.,
   `phase-12-exploration-pilot` resolves to `phase-12-exploration-pilot`
   for the work repo; the **coord-side phase-id is the matching short
   form** — typically `phase-12`, `phase-13A`, `phase-14-5`, etc.
   Strip the trailing slug to get the coord id).
5. **`NextPhaseGoal`** is derived from the queue's Notes column for
   that candidate plus a one-line summary from the relevant Phase
   design doc (e.g., `current/PHASE_*.md`).
6. **`NextSourceAnchor`** points at the Phase design doc you used in
   step 5.

Sidecar precedence (Phase R):
- Phase R is sidecar (R0 = `BACKFILL_PHASE_R1_R4`). It does NOT block
  mainline closure of Phases preceding 13A.
- If just-closed Phase ∈ {Phase 12, Phase 13A onwards} AND Phase R
  has NOT yet been generated/completed, NextPhaseId derivation must
  account for it. Conservative rule: if just-closed is `phase-12`
  and phase-r is still pending, NextPhaseId may still be `phase-13A`
  per the queue, **but** the matching Goal must flag the Phase R
  dependency for the user. Most explicit path: do Phase R before
  Phase 12 (the queue's current default after Phase 11 close).
- If just-closed Phase = `phase-r`, NextPhaseId is the next mainline
  candidate (typically `phase-12`).

Chain stops only when:
- The just-closed Phase is `BLOCKED_*` (BLOCKED close stops chain
  regardless).
- The candidate list is exhausted (final Phase in the roadmap, e.g.
  `phase-16`).
- The queue/INDEX explicitly marks the next candidate as not yet
  ready for generation (e.g., `R0_DECIDED_NOT_GENERATED` without
  user's explicit go).

In each stop case, set `StopReason:` accordingly and omit
`NextPhaseId`.

`CC-07` and `CC-08` may be `N/A` when the corresponding step was
bypassed (Adopted set was empty for `CC-07`; second-audit-decision was
NO for `CC-08`). When `N/A`, cite the synthesis / decision file that
justifies the bypass.

## NextPhasePlan — when to include / when to omit

The `NextPhasePlan` block is the **chain-mode hand-off** to the next
Phase. `temporal-phase-start` on the CC side parses it after the close
lands and decides whether to auto-advance, prompt for confirmation, or
do nothing, per `workflows/_active.md` `ChainMode:` (see CHARTER
§"Chain mode and auto-advance"). Rules:

- **`BatonNext: COMPLETED`** — `NextPhasePlan` is **optional**:
  - Include `NextPhaseId` + `NextPhaseGoal` + (optionally)
    `NextSourceAnchor` when there is a sensible next Phase per the
    blueprint / source-doc roadmap.
  - Omit `NextPhaseId` (and fill `StopReason:`) when this is the last
    Phase or the next move requires human design (e.g., the source-doc
    roadmap ended).
- **`BatonNext: BLOCKED_POSTEXEC`** — `NextPhasePlan` **must omit
  `NextPhaseId`** and include `StopReason: blocked`. A blocked Phase
  never auto-advances.

`NextPhaseId` must match `^phase-[a-zA-Z0-9][a-zA-Z0-9\-]*$` and **must not** collide with
any phase-id that already has artifacts in the live mailboxes or
archive. The chain logic and `check_baton_artifacts.py` enforce
this.

## Authority
Codex-only.

## See also
`ROLES.md` Step 16 · `BATON.schema.md` state `PHASE_CLOSING` ·
invariant §2
