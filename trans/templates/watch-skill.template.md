---
name: <preset>-watch
description: Boot CC's <preset> coord watchers. Use at the start of any Claude Code session that participates in the <preset> workflow. Pulls origin, verifies registrations, validates baton artifacts, arms a persistent Monitor for new artifacts in workflows/<preset>/_coord/from-codex/. Idempotent within a session, and independent from other workflow watchers (multiple workflows can run their watchers in parallel).
---

# <preset>-watch — Boot CC's <preset> coord watchers

Set up CC's side of the **<preset>** workflow preset. Safe to run
multiple times in a session: each step is idempotent. Safe to run
alongside other workflow watchers — each watcher only touches its own
workflow's coord directory.

## When to invoke

- Start of any Claude Code session that participates in the <preset>
  workflow.
- After anything that may have killed background tasks.
- Any time you want to confirm watchers are armed and the registry is
  consistent.

This skill does **not** check `workflows/_active.md`. That file is
informational only.

## Steps

### 1. Inspect already-running tasks

Load `TaskList` via `ToolSearch` if not loaded. Identify whether this
Monitor is already armed:

- description exactly `<preset>: new files in _coord/from-codex/`

### 2. Pull origin

```bash
git pull origin master
```

If pull fails (conflict / diverged), stop and surface.

### 3. Verify <preset> skill registrations

```bash
python scripts/verify_<preset>_skills.py
```

Expect `PASS: <preset> skills verified`. Fail-stop on FAIL.

Also run any other presets' verifiers (e.g., the testkit's) as a
sanity check since `.codex/skills.json` is shared.

### 3.5. Validate runtime baton artifacts

```bash
python scripts/check_baton_artifacts.py
```

Expect `PASS: N baton artifact(s) checked`. Fail-stop on FAIL.

### 4. Check baton state (informational)

```bash
git ls-tree --name-only origin/master:workflows/<preset>/_coord/from-codex 2>/dev/null | grep -v '^\.gitkeep$' | sort
git ls-tree --name-only origin/master:workflows/<preset>/_coord/from-cc   2>/dev/null | grep -v '^\.gitkeep$' | sort
```

### 5. Arm Monitor — new files in from-codex/

Skip if step 1 already found this Monitor armed. Otherwise start with:

- description: `<preset>: new files in _coord/from-codex/`
- persistent: `true`
- timeout_ms: `3600000`
- **Shell: bash (required)** (process substitution is bash-only).
- command:

```bash
prev=""; while true; do git fetch -q origin master 2>/dev/null || true; cur=$(git ls-tree --name-only origin/master:workflows/<preset>/_coord/from-codex 2>/dev/null | grep -v '^\.gitkeep$' | sort); if [ "$cur" != "$prev" ]; then comm -13 <(echo "$prev") <(echo "$cur") | while IFS= read -r f; do [ -n "$f" ] && echo "NEW_FROM_CODEX: $f"; done; prev="$cur"; fi; sleep 60; done
```

### 6. Report status

```text
<preset>-watch status:
  OriginHead:                <short SHA from step 2>
  <Preset>Verifier:          <PASS/FAIL>
  OtherPresetVerifiers:      <PASS/FAIL>
  BatonArtifacts:            <PASS/FAIL>
  FromCodex mailbox:         <count> files
  FromCC mailbox:            <count> files
  Monitor (from-codex):      <already-running / newly-started / failed>
```

## What this skill does NOT do

- Does not write baton artifacts.
- Does not review artifacts (that happens reactively when the Monitor
  fires).
- Does not start the other side.

## Failure modes

| Symptom | Required behavior |
|---|---|
| Pull conflict / diverged | Stop. Surface error. Do not arm watcher. |
| Either verifier FAIL | Stop. Surface error. Do not arm watcher. |
| `check_baton_artifacts.py` FAIL | Stop. Surface the list. Do not arm watcher. |
| Monitor start error | Surface error and stop. |
| `TaskList` unavailable | Skip step 1; start the Monitor unconditionally. |

## Related files

- `workflows/<preset>/HANDOFF.md` — other side's entry.
- `workflows/<preset>/_coord/from-codex/` — Codex artifacts watched.
- `workflows/<preset>/_coord/from-cc/` — CC artifacts CC writes.
- `scripts/verify_<preset>_skills.py` — registration verifier.
- `scripts/check_baton_artifacts.py` — runtime artifact validator.
