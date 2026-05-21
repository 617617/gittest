---
name: bk-watch
description: Boot CC's Blue-K v0.10 testkit watchers. Use at the start of any Claude Code session that will participate in the v0.10 walkthrough, or any time you want to confirm watchers are armed. Pulls origin, runs the project-scoped skill verifier, and arms two persistent Monitors for Codex result files and coordination messages. Idempotent within a session — skips Monitors that are already running.
---

# bk-watch — Boot Blue-K v0.10 Test Watchers

Set up CC's side of the Blue-K v0.10 testkit walkthrough. Safe to run
multiple times in the same session: each step is idempotent.

## When to invoke

- Start of a new Claude Code session that resumes the v0.10 walkthrough.
- After anything that may have killed background tasks.
- Any time you want to confirm watchers are armed and Codex is ready.

## Steps

Follow these steps in order. If any step fails, stop and surface the error
before continuing — do not start watchers against a broken baseline.

### 1. Inspect already-running tasks

Load the `TaskList` tool via `ToolSearch` if not loaded, then list running
tasks. Identify whether either of these Monitors is already armed:

- description exactly `v0.10 test results landing in _coord/from-codex/test-results/`
- description exactly `New coord files in _coord/from-codex/ (excluding test-results/)`

Record which are already running. Do not restart them.

### 2. Pull origin

```bash
git pull origin master
```

Report any new commits since the last fetch. If pull fails (conflict,
diverged), stop and surface — do not start watchers.

### 3. Verify project-scoped skills

```bash
python blue-k-git-baton-testkit/scripts/verify_project_scoped_skills.py
```

Expect `PASS: project-scoped Blue-K skills verified`. If it fails, stop —
do not start watchers.

### 4. Check Codex readiness

Read `blue-k-git-baton-testkit/_coord/from-codex/test-ready.md`. Capture:

- `Status:` line
- `Verifier:` line

If the file is missing, note "Codex not yet ready" but continue — watchers
can still arm; they will catch readiness when it lands.

### 5. Arm Monitor #1 — test results (if not running)

Skip if step 1 already found this Monitor armed. Otherwise start with:

- description: `v0.10 test results landing in _coord/from-codex/test-results/`
- persistent: `true`
- timeout_ms: `3600000`
- command:

```bash
prev=""; while true; do git fetch -q origin master 2>/dev/null || true; cur=$(git ls-tree --name-only origin/master:blue-k-git-baton-testkit/_coord/from-codex/test-results 2>/dev/null | grep -v '^\.gitkeep$' | sort); if [ "$cur" != "$prev" ]; then comm -13 <(echo "$prev") <(echo "$cur") | while IFS= read -r f; do [ -n "$f" ] && echo "NEW_RESULT: $f"; done; prev="$cur"; fi; sleep 60; done
```

### 6. Arm Monitor #2 — coord top-level (if not running)

Skip if step 1 already found this Monitor armed. Otherwise start with:

- description: `New coord files in _coord/from-codex/ (excluding test-results/)`
- persistent: `true`
- timeout_ms: `3600000`
- command:

```bash
git fetch -q origin master 2>/dev/null || true; prev=$(git ls-tree --name-only origin/master:blue-k-git-baton-testkit/_coord/from-codex 2>/dev/null | grep -v '^test-results$' | sort); while true; do sleep 60; git fetch -q origin master 2>/dev/null || true; cur=$(git ls-tree --name-only origin/master:blue-k-git-baton-testkit/_coord/from-codex 2>/dev/null | grep -v '^test-results$' | sort); if [ "$cur" != "$prev" ]; then comm -13 <(echo "$prev") <(echo "$cur") | while IFS= read -r f; do [ -n "$f" ] && echo "NEW_COORD_FILE: $f"; done; prev="$cur"; fi; done
```

### 7. Report status

Print exactly this block, populated from the steps above:

```text
bk-watch status:
  OriginHead:        <short SHA from step 2>
  Verifier:          <PASS or FAIL summary from step 3>
  CodexReady:        <yes / no / no-file>
  Monitor #1:        <already-running / newly-started / failed>
  Monitor #2:        <already-running / newly-started / failed>
```

## What this skill does NOT do

- It does not write `test-start.md`, `autopilot-decision.md`, or any other
  decision file — those are intentional CC-driven choices.
- It does not review test results — reviewing happens reactively when
  Monitor #1 fires.
- It does not start Codex's side — Codex registers and arms itself.
- It does not modify `.claude/settings.json` to auto-invoke this skill on
  session start. Suggest that as a follow-up if you want true auto-boot.

## Failure modes

| Symptom | Required behavior |
|---|---|
| Pull conflict / diverged | Stop. Surface error. Do not arm watchers. |
| Verifier FAIL | Stop. Surface error. Do not arm watchers. |
| Monitor start error | Surface error. Continue if the other Monitor can still arm. |
| TaskList unavailable | Skip step 1 (deduplication check); always start both Monitors. Accept duplicate Monitors as the cost of being unable to introspect. |

## Related files

- `blue-k-git-baton-testkit/_coord/from-codex/test-ready.md` — Codex
  readiness signal.
- `blue-k-git-baton-testkit/_coord/from-codex/test-results/` — Codex result
  files, watched by Monitor #1.
- `blue-k-git-baton-testkit/_coord/from-codex/` (top level) — Codex
  coordination messages, watched by Monitor #2.
- `blue-k-git-baton-testkit/_coord/from-cc/test-protocol.md` — the rules
  Codex is following.
- `blue-k-git-baton-testkit/_coord/from-cc/autopilot-decision.md` — current
  test mode.
