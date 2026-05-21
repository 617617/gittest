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
  NextPhaseId:       <phase-NN (the next phase-id you propose) | omit-if-chain-stops>
  NextPhaseGoal:     <one or two sentences describing the next Phase's intent>
  NextSourceAnchor:  <optional pointer into the source workflow doc | N/A>
  StopReason:        <required only if NextPhaseId is omitted; e.g. "roadmap complete" / "blocking risk needs human triage">
```

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
