# Handoff: Request CC Decision On Codex Autopilot

From: Codex
To: CC
Date: 2026-05-21T05:36:00Z
Status: decision requested

## Current State

Codex has received and acknowledged `test-protocol.md`.

Codex has pushed readiness:

```text
blue-k-git-baton-testkit/_coord/from-codex/test-ready.md
blue-k-git-baton-testkit/_coord/from-codex/test-protocol-ack.md
blue-k-git-baton-testkit/_coord/from-codex/test-results/.gitkeep
```

Codex has fetched and read:

```text
blue-k-git-baton-testkit/_coord/from-cc/test-start.md
```

The current `test-start.md` says:

```text
Trigger: the human will run `bk sync -Scenario <name>` and paste the printed
         ChatCommand into the chat window selected by `WindowMatch`.
```

The current `test-protocol.md` also says:

```text
Do not start scenarios on your own.
```

Therefore Codex is currently waiting for the human to paste each scenario's
`bk sync -Scenario <name>` output and `ChatCommand`.

## Decision Needed

The human asked whether Codex should directly continue without manual pasting.
Codex will not reinterpret the current v0.10 protocol by itself because it
explicitly forbids starting scenarios independently.

CC should decide one of the following modes.

## Mode A: Human-Paste Mode

No protocol change.

Codex behavior:

1. Wait for the human to run `bk sync -Scenario <name>`.
2. Wait for the human to paste the full `bk sync` output and `ChatCommand`.
3. Write exactly one result file:

   ```text
   blue-k-git-baton-testkit/_coord/from-codex/test-results/<scenario>.md
   ```

4. Commit and push exactly that result file.
5. Wait for either CC review or the next pasted scenario.

To choose this mode, CC can write:

```text
blue-k-git-baton-testkit/_coord/from-cc/autopilot-decision.md
```

with:

```text
Autopilot: disabled
Reason: keep human-paste v0.10 contract
```

## Mode B: Codex Autopilot Test Runner

CC explicitly authorizes Codex to generate the scenario inputs by running the
simulator wrapper itself, while still not executing any real Blue-K package
work.

Codex behavior:

1. For each authorized scenario, run:

   ```powershell
   powershell -ExecutionPolicy Bypass -File blue-k-git-baton-testkit/scripts/bk.ps1 sync -Scenario <scenario>
   ```

2. Treat that output as the same text the human would have pasted.
3. Produce only chat-text simulation, not real Blue-K work.
4. Write exactly one result file per scenario under:

   ```text
   blue-k-git-baton-testkit/_coord/from-codex/test-results/<scenario>.md
   ```

5. Commit and push one result file per scenario with:

   ```text
   test(v0.10): codex result for <scenario>
   ```

6. After each push, fetch CC review files. If the matching review says FAIL or
   BLOCK, stop and report. If there is no review yet but the scenario result is
   self-evaluated PASS, Codex may continue only if CC's decision file says
   `ContinueWithoutReview: yes`.

Autopilot remains bounded by the original safety rules:

- Do not push to `blue-k/coordination`.
- Do not push to any `blue-k/<task>` work branch.
- Do not call `blue-k-main-runner`, `blue-k-other-runner`,
  `blue-k-other-index`, or `blue-k-consensus` for real.
- Do not run `stage-loop-auto`, `traceable-review`, or `pre-doc-review`.
- Do not write to `docs/mian-k/**`.
- Do not edit `BATON.yaml`.
- Do not run `git push --atomic origin <work> blue-k/coordination`.

To choose this mode, CC should write:

```text
blue-k-git-baton-testkit/_coord/from-cc/autopilot-decision.md
```

with:

```text
Autopilot: enabled
ContinueWithoutReview: no
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
```

If CC wants Codex to continue scenario-to-scenario without waiting for each CC
review file, set:

```text
ContinueWithoutReview: yes
```

That is faster but makes CC review asynchronous.

## Codex Recommendation

Use Mode B only for this testkit walkthrough, because the scenarios are
simulated and the protocol already forbids real Blue-K execution.

Keep Mode A as the default for real project work until a future protocol
version explicitly enables automatic cross-window work.

## Requested CC Response

Please push exactly one of:

```text
blue-k-git-baton-testkit/_coord/from-cc/autopilot-decision.md
```

or an amended:

```text
blue-k-git-baton-testkit/_coord/from-cc/test-start.md
```

that clearly states whether Codex may start scenarios without human-pasted
`ChatCommand` input.

Until then, Codex will keep listening for `_coord/from-cc/` changes and will
not start scenarios independently.
