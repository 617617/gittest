---
name: temporal-phase-start
description: One-command orchestrator for the temporal-phase workflow. Use whenever the user wants to start a new Phase, resume an in-progress Phase, or check "where are we" — this skill diagnoses the current baton state and routes to the right branch (fresh start / in progress / closing & chaining). Designed so the user only has to remember `/temporal-phase-start`.
---

# temporal-phase-start — One-command orchestrator

Single CC-side entry point into the `temporal-phase` workflow. Runs a
short diagnosis, then routes to the right branch's reference doc for
the procedure. Detailed branch procedures live under `references/` so
the SKILL.md stays a thin dispatcher.

## Required reading (load these before acting)

This skill's load-bearing detail is split across `references/`.
**The SKILL.md alone is not sufficient for correct execution** — the
3 branch procedure files contain commands, recovery paths, and
collision logic that the dispatcher only summarizes.

After Step 3 (diagnose state) routes you to a branch, read the
matching reference completely before doing anything in that branch:

- `references/branch-a-fresh-start.md` — fresh-start path (no Phase
  open yet): kickoff write + commit-before-rebase + cleanup.
- `references/branch-b-in-progress.md` — open-Phase path: status
  block + lane lookup + paste-to-Codex message.
- `references/branch-c-chain-decision.md` — close + chain-mode
  decision tree + atomic chain advance + recovery.

## When to invoke

- The user wants to start the first Phase.
- The user wants to start the next Phase (after a previous Phase
  closed).
- The user wants to resume / check status of an in-progress Phase.
- Any time the user types `/temporal-phase-start`.

If the user has not yet invoked `/temporal-phase-watch` in this
session, this skill invokes it automatically as the first step.

## Steps

### 1. Ensure the watcher is armed

Check whether the persistent Monitor with description
`temporal-phase: new files in _coord/from-codex/` is running.

- If TaskList shows it: skip.
- If not: invoke `/temporal-phase-watch` first. Fail-stop on its
  failure.

### 2. Run the verifiers + the artifact checker

```bash
python scripts/verify_temporal_phase_skills.py
python scripts/check_baton_artifacts.py
python scripts/check_refs_consistency.py
python blue-k-git-baton-testkit/scripts/verify_project_scoped_skills.py
```

If any FAIL: surface the FAIL output and stop. Fixes typically need
human triage.

### 3. Diagnose the current baton state

Read the latest artifact across both mailboxes:

```bash
git ls-tree --name-only origin/master:workflows/temporal-phase/_coord/from-codex 2>/dev/null | grep -v '^\.gitkeep$' | sort
git ls-tree --name-only origin/master:workflows/temporal-phase/_coord/from-cc   2>/dev/null | grep -v '^\.gitkeep$' | sort
```

Identify the most recent artifact and read its first non-empty line to
extract `BatonNext: <STATE>`. Also identify the open Phase ID (if any).
A Phase is "open" if it has artifacts in either mailbox without a
matching `<phase-id>__close.md`.

### 4. Route to the right branch — read the matching reference

| Diagnosis | Branch | Reference (read this file, follow it) |
|---|---|---|
| Both mailboxes empty of phase artifacts | A — fresh start | `references/branch-a-fresh-start.md` |
| Open Phase exists, latest artifact is not `__close.md` | B — in progress | `references/branch-b-in-progress.md` |
| Latest artifact is `<phase-id>__close.md` | C — closing & chaining | `references/branch-c-chain-decision.md` |

Each reference file is self-contained: it walks the AI step-by-step
through that branch's procedure, including any inline shell commands,
collision checks, push order, recovery on FAIL, and the final report
to print.

### 5. Final summary

After the branch's procedure completes, always print one summary line
so the user (and the next session) can see what happened:

```text
temporal-phase-start: <branch A/B/C> -- <one-line summary of what was emitted or pushed>
```

## What this skill does NOT do

- It does NOT write any baton artifact itself. The branch references
  drive any writes; lane skills (e.g., `temporal-phase-blueprint`) own
  their own artifacts.
- It does NOT pick phase-ids or Phase goals — those come from the
  user.
- It does NOT push or pull anything beyond what `/temporal-phase-watch`
  does. All git operations are scoped inside the branch procedures.

## Failure modes

| Symptom | Required behavior |
|---|---|
| Watcher won't arm | Surface failure. Do not continue. |
| Any verifier / checker FAIL | Surface FAIL output. Do not run any branch. |
| More than one open Phase | Artifact checker FAILs; surface and stop. |
| Cannot read mailboxes | Surface error. |
| Branch reference file missing | Should never happen; if so, file an `issue/` and stop. |

## Related files

- `references/branch-a-fresh-start.md` — Branch A procedure.
- `references/branch-b-in-progress.md` — Branch B procedure.
- `references/branch-c-chain-decision.md` — Branch C decision tree +
  atomic chain advance + recovery.
- `.claude/skills/temporal-phase-watch/SKILL.md` — watcher (auto-invoked
  by step 1).
- `workflows/temporal-phase/HANDOFF.md` — Codex-side entry.
- `workflows/temporal-phase/CHARTER.md` — phase-id rules,
  ChainMode policy.
- `scripts/verify_temporal_phase_skills.py`,
  `scripts/check_baton_artifacts.py`,
  `scripts/verify_cross_repo_refs.py`,
  `scripts/archive_phase.py`.
