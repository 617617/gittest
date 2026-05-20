---
description: Blue-K Git baton chat entry. Use when the user types /bk work or asks Claude to execute the current BATON assignment after bk sync has selected this Claude window.
disable-model-invocation: true
allowed-tools:
  - Bash(git *)
  - Bash(powershell -ExecutionPolicy Bypass -File scripts/blue_k_baton/bk.ps1 *)
  - Read
  - Grep
  - Glob
  - Edit
  - Write
---

# Blue-K Baton Work

This skill handles `/bk work`.

If the user did not pass `work` as the first argument, stop and say:

```text
Use /bk work for execution. Use shell bk sync for synchronization.
```

## Non-Negotiable Rules

- Run shell `bk sync` or the equivalent safe-sync gate before any work.
- Do not start unless local HEAD, origin work branch, and BATON.WorkBranchHead match.
- Do not start unless the worktree is clean.
- Do not execute from the wrong owner role/window.
- Acquire the coordination lease through compare-and-swap before changing business state.
- Run exactly one BATON assignment, then push a safe point and hand off.
- Do not select runner packages in this wrapper.
- Do not write progress tables in this wrapper.
- Do not run stage-loop-auto in this wrapper.
- Do not override plan-audit, traceable-review, code-graph, or package-gate BLOCK.

## Dispatch

Dispatch by BATON lane:

- `blue-k-planner`: call the existing Blue-K planner workflow; requires durable human authorization.
- `blue-k-plan-audit`: call the existing Blue-K plan audit workflow.
- `blue-k-main-runner`: call the existing Blue-K main runner. The runner selects/resumes from `docs/mian-k/MAIN_PACKAGE_PROGRESS.md`.
- `blue-k-other-runner`: call the existing Blue-K other runner. The runner selects/resumes from `docs/mian-k/OTHER_MIN_PACKAGE_PROGRESS.md`.
- `blue-k-consensus`: run the consensus lane only under `docs/mian-k/_consensus/<topic-id>/`.

## Required Consensus Gates

- Every plan output must pass plan consensus before runner execution.
- Every code/package output must pass code consensus before runner finalization.
- `review_pending + accepted consensus` means finalize the current row only, then stop.
- `fix_required` means route back to the runner-owned fix lane.
- Superseded, cancelled, subject-mismatch, hash-mismatch, docs-only-freeze violation, or lower-gate BLOCK must stop.

## Finish

After one safe assignment:

1. Update/preserve the runner-owned checkpoint artifacts.
2. Push work branch plus coordination branch atomically where supported.
3. Print the next `bk sync` instruction for the human.
4. Stop. Do not chain into the next package.