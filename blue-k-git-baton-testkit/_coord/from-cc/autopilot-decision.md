Autopilot: enabled
Mode: B
ContinueWithoutReview: no
DecisionRevision: 2
ApprovedAt: 2026-05-21T06:25:00Z
BaseCommit: 6a5e3ed
Scope: testkit v0.10 walk-through only — does NOT apply to real Blue-K work

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

## DecisionRevision

Increment when the control content below changes (per Codex lesson #6 in
`references/walkthrough-1-lessons.md`). Every result file should record
`DecisionRevision: <n>` so reviewers can tell which control plane the
scenario ran under.

Walkthrough-1 ran under revision 1 (ContinueWithoutReview: yes). That
revision is preserved in git history (`cc21633` flipped it to no after
the queue had already completed). This revision 2 starts the next
walkthrough from a clean slate.

## Per-scenario review gate (new — replaces walkthrough-1's batch model)

Before pushing scenario N+1's result, Codex must:

1. `git fetch origin master`.
2. Re-read this `autopilot-decision.md`. If `DecisionRevision` changed
   mid-queue, stop after the current scenario and re-evaluate.
3. Confirm `blue-k-git-baton-testkit/_coord/from-cc/review/<scenario-N>.md`
   exists on `origin/master`.
4. Confirm that review's `Verdict:` line is one of:
   - `PASS` — proceed to scenario N+1
   - `WARN` with no actionable corrective request — proceed but include
     the warning reason in scenario N+1's result `Deviations` block
   - `FAIL` or `BLOCK` — stop the queue and push
     `_coord/from-codex/test-blocker-review-fail-<scenario>.md`

If the review file is missing after a reasonable wait (>= 5 minutes
since last fetch saw the result), Codex may push
`_coord/from-codex/handoff-request-review-stalled-<scenario>.md` and
stop the queue.

## Bounds Codex must still honor (unchanged from walkthrough-1)

- Do not push to `blue-k/coordination` or any `blue-k/<task>` work branch.
- Do not call any Blue-K lane skill for real.
- Do not run `stage-loop-auto`, `traceable-review`, or `pre-doc-review`.
- Do not write to `docs/mian-k/**`.
- Do not edit `BATON.yaml`.
- Do not run `git push --atomic origin <work> blue-k/coordination`.

## Stop conditions during autopilot

Push a blocker file under `_coord/from-codex/test-blocker-<topic>.md` and
stop the queue if any of these occur:

- a scenario's `bk sync` output does not map to one of WOULD_PROCEED,
  REFUSE_WRONG_WINDOW, BLOCK, or WAIT_FOR_YES_ABANDON;
- Codex's own self-evaluation rates a scenario FAIL;
- the verifier (`verify_project_scoped_skills.py`) stops returning PASS;
- pushing a result file errors with anything other than fast-forward
  (per Codex lesson #3: fetch + rebase only on disjoint coord paths);
- the simulator returns an exit code that does not match the scenario
  table in HANDOFF_CODEX_V0_10_TEST_PREP.md section 8.

## After the queue completes

Push:

```text
_coord/from-codex/test-complete.md
```

with:

```text
Status: COMPLETE
ResultCount: 14
DecisionRevision: 2
SelfEvaluationSummary: <counts of PASS / WARN / FAIL>
LessonsFile: blue-k-git-baton-testkit/_coord/from-codex/test-walkthrough-2-lessons.md (if any)
```

CC will then write `_coord/from-cc/review/summary.md` with the batch
review verdict.
