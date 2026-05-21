# Codex Autopilot Walkthrough Lessons

Date: 2026-05-21
Scope: Blue-K Git baton testkit v0.10 walkthrough only

## Summary

The walkthrough proved more than the scenario table. The useful findings are
the control-plane edge cases that appeared while CC and Codex were both pushing
through Git.

Current result count:

- Scenario result files pushed: 14
- SelfEvaluation PASS: 13
- SelfEvaluation WARN: 1
- SelfEvaluation FAIL: 0

## Issues Found And Resolutions

### 1. Codex listener was polling, not truly push-triggered

Observed:

- CC pushed `autopilot-decision.md`.
- Codex did not notice instantly.
- The heartbeat listener only checked on its timer, so the human noticed the
  missing responsiveness first.

Impact:

- The Git-only loop was functionally correct but not fully ergonomic.
- "Listening" was too easy to confuse with webhook-level realtime behavior.

Resolution during test:

- Codex manually fetched, detected `3bd7555`, fast-forwarded, and read
  `blue-k-git-baton-testkit/_coord/from-cc/autopilot-decision.md`.
- The heartbeat interval was tightened from 2 minutes to 1 minute and updated
  to watch `autopilot-decision.md`, `review/*.md`, `summary.md`, and blockers.

Recommended workflow fix:

- Rename this capability from "listener" to "polling watcher" unless a real
  webhook or filesystem event bridge exists.
- For fast tests, provide a `/bk-watch` or equivalent command on each side that
  starts an explicit watcher loop.
- The watcher should persist a last-seen remote commit so it can report only
  new actionable changes.

### 2. v0.10 human-paste protocol conflicted with desired autopilot

Observed:

- `test-protocol.md` said "Do not start scenarios on your own."
- `test-start.md` said the human would run `bk sync -Scenario <name>` and paste
  the `ChatCommand`.
- The human expected full automation.

Impact:

- Codex correctly refused to reinterpret the protocol.
- This created a useful pause but also showed that the protocol needed an
  explicit testkit-only autopilot switch.

Resolution during test:

- Codex pushed:

  ```text
  blue-k-git-baton-testkit/_coord/from-codex/handoff-request-autopilot-decision.md
  ```

- CC responded with:

  ```text
  blue-k-git-baton-testkit/_coord/from-cc/autopilot-decision.md
  ```

  containing `Autopilot: enabled`, `Mode: B`, and
  `ContinueWithoutReview: yes`.

Recommended workflow fix:

- Keep v0.10 real work human-gated.
- Add a testkit-only autopilot control file:

  ```text
  blue-k-git-baton-testkit/_coord/from-cc/autopilot-decision.md
  ```

- Require it to include:

  ```text
  Autopilot: enabled|disabled
  ContinueWithoutReview: yes|no
  ScenarioQueue:
  - ...
  ```

### 3. Concurrent CC push rejected Codex's first result push

Observed:

- Codex generated and committed `ready_codex_main`.
- Before Codex pushed, CC pushed additional watcher support:

  ```text
  .claude/skills/bk-watch/SKILL.md
  ```

- Codex push was rejected with `fetch first`.

Impact:

- This is the exact Git-only concurrency edge the workflow must handle.
- It confirmed that naive "commit then push" is not enough when both sides are
  active.

Resolution during test:

- Codex fetched origin.
- Verified the remote change did not overlap with the local result file.
- Rebasing the one local result commit onto `origin/master` succeeded.
- Codex pushed the rebased result successfully.

Recommended workflow fix:

- Before every result push:

  ```text
  git fetch origin master
  git status --short --branch
  ```

- If local is behind only, fast-forward before working.
- If local is ahead and behind, inspect remote file paths.
- Rebase only when local and remote touched disjoint coordination files.
- Never force-push.
- If paths overlap, stop and write a blocker under `_coord/from-codex/`.

### 4. Scenario table disagreement around takeover behavior

Observed:

- `test-protocol.md` scenario table expected
  `stale_lease_takeover_required` to produce `WAIT_FOR_YES_ABANDON`.
- `HANDOFF_CODEX_V0_10_TEST_PREP.md` section 8 says:

  ```text
  If ChatTarget is CC, refuse as wrong-window; if ChatTarget is Codex, show
  takeover evidence and wait for yes, abandon.
  ```

- The simulator output for this scenario says:

  ```text
  ChatTarget: CC chat
  ChatCommand: /bk takeover
  ```

Impact:

- Both readings are defensible unless the target window is considered.
- For Codex, the safer behavior is Rule 2 wrong-window refusal.

Resolution during test:

- Codex wrote:

  ```text
  Outcome: REFUSE_WRONG_WINDOW
  SelfEvaluation: WARN
  ```

- The result records the cross-document tension instead of hiding it.

Recommended workflow fix:

- Amend `test-protocol.md` row 8 to match the newer section-8 rule:

  ```text
  stale_lease_takeover_required | REFUSE_WRONG_WINDOW for Codex when ChatTarget is CC; WAIT_FOR_YES_ABANDON only in the selected takeover chat.
  ```

### 5. Result files alone are not enough; lessons need a first-class artifact

Observed:

- The 14 result files validate scenario behavior.
- They do not, by themselves, preserve process failures like listener latency or
  push rejection recovery.

Impact:

- Without a lessons artifact, the most important workflow improvements would
  stay buried in chat history.

Resolution during test:

- Codex wrote this file as a first-class coordination artifact.

Recommended workflow fix:

- Every full walkthrough should end with:

  ```text
  _coord/from-codex/test-autopilot-lessons.md
  _coord/from-codex/test-complete.md
  ```

- CC should include those in its final review summary.

### 6. Control-plane amendments can arrive after the local runner has already acted

Observed:

- Codex ran the Mode B queue under the first `autopilot-decision.md`, which
  said:

  ```text
  ContinueWithoutReview: yes
  ```

- After all 14 result files had already been pushed, Codex fetched a newer CC
  amendment:

  ```text
  ContinueWithoutReview: no
  ```

- The amendment said per-scenario review gating should apply, while preserving
  already-pushed results.

Impact:

- Even when file paths do not conflict, control-plane semantics can change
  while an autopilot runner is active.
- A runner that only fetches between pushes may still be too coarse if a
  long-running local loop can produce multiple commits before noticing an
  amendment.

Resolution during test:

- Codex rebased its completion commit on top of the amended CC decision.
- This lessons file records that the amendment arrived after the queue had
  already completed locally and after the result commits were already pushed.

Recommended workflow fix:

- Autopilot runners should fetch and re-read
  `_coord/from-cc/autopilot-decision.md` before every scenario, not only before
  every push.
- The decision file should carry a monotonic field such as:

  ```text
  DecisionRevision: 1
  ```

- Result files should record the `DecisionRevision` they executed under.
- If `ContinueWithoutReview` flips to `no`, the runner must stop after the
  current scenario unless all remaining scenarios already have matching CC
  review approvals.

## Proposed Next Protocol Improvements

1. Add `WatcherKind: polling|webhook|manual` to readiness files.
2. Add `LastSeenRemoteCommit` to watcher state.
3. Add an explicit `Autopilot` section to `test-start.md`.
4. Require every pusher to fetch before pushing result files.
5. Add a standard conflict response:

   ```text
   _coord/from-codex/test-blocker-push-race.md
   ```

6. Split real-work v0.10 from testkit autopilot mode in the docs so the
   safety model stays clear.
7. Add `DecisionRevision` to autopilot control files and require each result
   file to record it.

## Final Codex Position

Mode B is suitable for this simulated testkit walkthrough.

It should not be treated as authorization for real Blue-K work. Real work still
requires the v0.10 human-gated `bk sync` -> selected chat command loop unless a
future protocol explicitly changes that boundary.
