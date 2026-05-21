---
name: temporal-phase-watch
description: Boot CC's temporal-phase coord watchers. Use at the start of any Claude Code session that participates in the temporal-phase workflow. Pulls origin, verifies registrations, validates baton artifacts, arms a persistent Monitor for new Codex artifacts in workflows/temporal-phase/_coord/from-codex/. Idempotent within a session, and independent from other workflow watchers (multiple workflows can run their watchers in parallel).
---

# temporal-phase-watch — Boot CC's temporal-phase coord watchers

Set up CC's side of the **temporal-phase** workflow preset. Safe to run
multiple times in a session: each step is idempotent. Safe to run
alongside other workflow watchers (e.g., `bk-watch` for the testkit) —
each watcher is self-contained and only touches its own workflow's
coord directory.

## When to invoke

- Start of any Claude Code session that participates in the
  temporal-phase workflow (whether or not other workflows are also
  participating in the same session).
- After anything that may have killed background tasks.
- Any time you want to confirm watchers are armed and the registry is
  consistent.

This skill does **not** check `workflows/_active.md`. That file is
informational only and does not gate watcher startup — multiple
workflows can be enabled simultaneously, each with its own watcher.

## Steps

Follow steps in order. If any step fails, stop and surface — do not arm
watchers against a broken baseline.

### 1. Inspect already-running tasks

Load the `TaskList` tool via `ToolSearch` if not loaded, then list running
tasks. Identify whether this Monitor is already armed:

- description exactly `temporal-phase: new files in _coord/from-codex/`

Record whether it is already running. Do not restart it.

### 2. Pull origin

```bash
git pull origin master
```

Report any new commits. If pull fails (conflict / diverged), stop and
surface — do not start watchers.

### 3. Verify temporal-phase skill registrations

```bash
python scripts/verify_temporal_phase_skills.py
```

Expect `PASS: temporal-phase skills verified`. If it fails, stop — do
not start watchers.

Also run the testkit verifier as a sanity check (it must still pass since
both presets share `.codex/skills.json`):

```bash
python blue-k-git-baton-testkit/scripts/verify_project_scoped_skills.py
```

Expect `PASS: project-scoped Blue-K skills verified`.

### 3.5. Validate runtime baton artifacts

```bash
python scripts/check_baton_artifacts.py
```

Expect `PASS: N baton artifact(s) checked`. This catches malformed
filenames, missing / illegal `BatonNext:` lines, authority violations
(a product landing in the wrong mailbox), and more-than-one open Phase.
If it fails, **stop** — do not arm the monitor against a corrupted
baton state. Surface the FAIL list to the user; fixes typically need
human triage.

### 4. Check baton state (informational, non-blocking)

List the most recent files under origin/master in both mailboxes:

```bash
git ls-tree --name-only origin/master:workflows/temporal-phase/_coord/from-codex 2>/dev/null | grep -v '^\.gitkeep$' | sort
git ls-tree --name-only origin/master:workflows/temporal-phase/_coord/from-cc 2>/dev/null | grep -v '^\.gitkeep$' | sort
```

If either is empty, note "no Phase started yet" but continue — the monitor
will catch new files when they land.

### 5. Arm Monitor — new files in from-codex/ (if not running)

Skip if step 1 already found this Monitor armed. Otherwise start with:

- description: `temporal-phase: new files in _coord/from-codex/`
- persistent: `true`
- timeout_ms: `3600000`
- **Shell: bash (required).** The command uses process substitution
  `<(...)`, which is bash-only. Do not run it under cmd.exe / PowerShell
  / sh — it will fail silently. On Windows hosts, the Monitor tool runs
  via the Bash tool by default; if your harness is different, wrap the
  command with `bash -c '...'`.
- command:

```bash
prev=""; while true; do git fetch -q origin master 2>/dev/null || true; cur=$(git ls-tree --name-only origin/master:workflows/temporal-phase/_coord/from-codex 2>/dev/null | grep -v '^\.gitkeep$' | sort); if [ "$cur" != "$prev" ]; then comm -13 <(echo "$prev") <(echo "$cur") | while IFS= read -r f; do [ -n "$f" ] && echo "NEW_FROM_CODEX: $f"; done; prev="$cur"; fi; sleep 60; done
```

### 6. Report status

Print exactly this block, populated from the steps above:

```text
temporal-phase-watch status:
  OriginHead:                <short SHA from step 2>
  TemporalPhaseVerifier:     <PASS or FAIL summary from step 3>
  TestkitVerifier:           <PASS or FAIL summary from step 3>
  BatonArtifacts:            <PASS / FAIL summary from step 3.5>
  FromCodex mailbox:         <count> files
  FromCC mailbox:            <count> files
  Monitor (from-codex):      <already-running / newly-started / failed>
```

## Event handling — what to do when the Monitor fires

The persistent Monitor armed in step 5 emits lines of the form
`NEW_FROM_CODEX: <filename>` whenever a new artifact lands. CC reacts
per the filename's step-tag:

| Step-tag | Reaction |
|----------|----------|
| `blueprint`, `pre-audit-codex-r<N>`, `postexec-subagent-review`, `postexec-synthesize`, `postexec-fix`, `second-audit-codex`, `second-audit-fix` | Process per the BATON state machine — read the artifact, look up the next lane in HANDOFF §3.1, run that lane. |
| `second-audit-decision` | Read; advance per the decision (YES/NO). |
| `execution-report` | Process per the state machine (POSTEXEC_SUBAGENT_REVIEW is Codex's turn — CC waits). |
| **`close`** | **Run `/temporal-phase-start` Branch C logic.** Read `workflows/_active.md` `ChainMode:`, read the close.md `NextPhasePlan:` block, then apply the Branch C decision tree (auto-advance / confirm / off / hard-stop). This is how Phase chaining actually fires: the Monitor's close.md event triggers the chain decision. |

If you are uncertain what reaction applies, invoke
`/temporal-phase-start` — it consolidates all the diagnostic logic.

## What this skill does NOT do

- It does not write any baton artifact (blueprint / audit / etc.) — those
  are intentional lane-driven choices.
- It does not review artifacts — that happens reactively when the Monitor
  fires.
- It does not start Codex's side — Codex on Host B is responsible for its
  own setup via `workflows/temporal-phase/HANDOFF.md`.
- It does not modify `.claude/settings.json` to auto-invoke this skill on
  session start. The SessionStart hook in `.claude/settings.json` already
  reminds CC to run this when `_active.md` is temporal-phase.

## Failure modes

| Symptom | Required behavior |
|---|---|
| Pull conflict / diverged | Stop. Surface error. Do not arm watcher. |
| Either verifier FAIL | Stop. Surface error. Do not arm watcher. |
| `check_baton_artifacts.py` FAIL | Stop. Surface the list of issues. Do not arm watcher. Fixes typically need human triage. |
| Monitor start error | Surface error and stop. |
| TaskList unavailable | Skip step 1 (deduplication check); start the Monitor unconditionally. |

## Related files

- `workflows/_active.md` — active preset pointer (must be `temporal-phase`).
- `workflows/temporal-phase/HANDOFF.md` — Codex-side entry; CC should read
  it once for context before processing the first artifact.
- `workflows/temporal-phase/_coord/from-codex/` — Codex artifacts watched
  by this skill's Monitor.
- `workflows/temporal-phase/_coord/from-cc/` — CC artifacts CC writes per
  lane.
- `scripts/verify_temporal_phase_skills.py` — registration verifier.
- `scripts/check_baton_artifacts.py` — runtime artifact validator
  (filename / phase-id / step-tag mailbox / `BatonNext:` / open-Phase count).
- `workflows/temporal-phase/ROLES.md` Step Matrix — which lane to invoke
  on each new artifact.
- `workflows/temporal-phase/BATON.schema.md` — state machine.
