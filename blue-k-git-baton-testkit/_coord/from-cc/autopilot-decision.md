Autopilot: enabled
ContinueWithoutReview: no
Mode: B
Scope: testkit v0.10 walk-through only — does NOT apply to real Blue-K work
ApprovedAt: 2026-05-21T05:45:00Z
AmendedAt: 2026-05-21T06:00:00Z
AmendmentReason: user flagged that pushing the next scenario before
  receiving CC review defeats the peer-review value of the dual-AI test.
  Switching to per-scenario gating: Codex must wait for
  `_coord/from-cc/review/<scenario>.md` to land before pushing the next
  result. Already-pushed results (ready_codex_main, ready_cc_planner,
  role_mismatch, audit_report_blocks_runner, atomic_unavailable,
  active_lease_other_holder, stale_lease_resume_original,
  stale_lease_takeover_required) stay valid — CC will review them
  individually; Codex does not need to re-run them.

ScenarioQueue:
- ready_codex_main
- ready_cc_planner
- role_mismatch
- audit_report_blocks_runner
- atomic_unavailable
- active_lease_other_holder
- stale_lease_resume_original
- stale_lease_takeover_required
- lower_gate_block_cannot_be_accepted
- review_pending_finalize_only
- fix_required_routes_runner_fix
- superseded_topic_after_code_fix
- docs_only_freeze_violation
- dependency_fix_target_prereq

## Rationale

Codex correctly stopped to ask. Authorizing Mode B because:

1. The v0.10 contract behavior tested (self-announce, wrong-window refusal,
   block-on-precondition, closing line) does not depend on who feeds the
   ChatCommand. Codex's window-mismatch logic triggers off `ChatTarget` in
   the bk sync output, not off the identity of the typist.

2. REFUSE_WRONG_WINDOW scenarios stay valid: when Codex runs
   `bk.ps1 sync -Scenario ready_cc_planner` itself, the output will say
   `ChatTarget: CC chat`. Codex pasting that into a Codex window (its own)
   is still a wrong-window case — refuse per Rule 2.

3. ContinueWithoutReview: yes lets Codex walk all 14 scenarios in one pass.
   CC reviews the batch afterward. This is acceptable in a testkit context
   because every result file is self-contained, has a fixed format, and the
   expected outcome per scenario is already specified in test-protocol.md.

4. This permission is scoped to the testkit walk-through only. The v0.10
   normative rule "human pastes ChatCommand into the WindowMatch chat"
   stays in force for real Blue-K work. A future v0.11 would be where any
   broader autopilot enables.

## Bounds Codex must still honor (unchanged)

- Do not push to `blue-k/coordination` or any `blue-k/<task>` work branch.
- Do not call any Blue-K lane skill for real.
- Do not run `stage-loop-auto`, `traceable-review`, or `pre-doc-review`.
- Do not write to `docs/mian-k/**`.
- Do not edit `BATON.yaml`.
- Do not run `git push --atomic origin <work> blue-k/coordination`.

## Stop conditions during autopilot

Codex must stop and push a blocker file under
`_coord/from-codex/test-blocker-<topic>.md` if any of these occur:

- a scenario's `bk sync` output does not map to one of WOULD_PROCEED,
  REFUSE_WRONG_WINDOW, BLOCK, or WAIT_FOR_YES_ABANDON;
- Codex's own self-evaluation rates a scenario FAIL;
- the verifier (`verify_project_scoped_skills.py`) stops returning PASS at
  any point;
- pushing a result file produces an error other than a clean fast-forward;
- the simulator returns an exit code that does not match the scenario
  table in HANDOFF_CODEX_V0_10_TEST_PREP.md section 8.

## After the queue completes

Once Codex has pushed all 14 result files, push:

```text
_coord/from-codex/test-complete.md
```

with:

```text
Status: COMPLETE
ResultCount: 14
SelfEvaluationSummary: <counts of PASS / WARN / FAIL>
```

CC will then write `_coord/from-cc/review/summary.md` with the batch
review verdict.
