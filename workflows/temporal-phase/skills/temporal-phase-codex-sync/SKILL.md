---
name: temporal-phase-codex-sync
description: Codex-side sync routine for the temporal-phase workflow. Run on Codex CLI startup on Host B, and any time the user types `/temporal-phase-codex-sync`. Pulls origin, runs the verifiers, scans the from-cc/ mailbox for any product awaiting a Codex response (kickoff or other CC artifact), and reports the exact next action. Operational skill -- does not produce a baton artifact itself.
---

# temporal-phase-codex-sync (Codex operational skill)

Codex's mirror of CC's `/temporal-phase-watch` + `/temporal-phase-start`
combined into one operational entry. Run it whenever Codex on Host B
boots (or whenever the user wants a "where are we" status from the
Codex side). It does not produce a baton artifact; it only inspects
mailbox state and tells Codex which lane to enter next.

## Trigger
- Codex CLI session start on Host B.
- User asks Codex "sync" / "check mailbox" / "what's next".
- Any time you suspect a missed push from CC.

This is **operational**, not part of the state machine.

## Reads
- The current `from-cc/` and `from-codex/` mailbox listings under
  `workflows/temporal-phase/_coord/`.
- All lane SKILLs under `workflows/temporal-phase/skills/` (lookup
  per state).
- `workflows/temporal-phase/BATON.schema.md` for state enumeration and
  transitions.
- `workflows/temporal-phase/HANDOFF.md` §3.1 state→lane table.

## Writes
None. This skill is informational only. It does not write
`BatonNext:` artifacts; the usual `BatonNext: <STATE>` first-line rule
does not apply here. Lane skills (e.g., `temporal-phase-blueprint`,
`temporal-phase-execute`) own all artifact-writing.

## Steps

### 1. Sync repo
Resolve your coord-repo path via `PATHS.md` (Host B row → coord repo
column), then `git pull origin master`. If pull fails (conflict /
diverged), stop and surface — do not act on a stale baseline.

### 2. Verify registrations + artifacts
Run both verifiers; both must PASS before you act on the baton state.
On FAIL, surface the errors and stop.

```bash
python scripts/verify_temporal_phase_skills.py
python scripts/check_baton_artifacts.py
```

### 3. Diagnose what is pending
List the two mailboxes (`from-cc/` and `from-codex/` under
`workflows/temporal-phase/_coord/`). Identify the **most recent
artifact across both mailboxes** and read its first-line
`BatonNext: <STATE>` — that is the current baton state.

See `references/sort-tiebreak.md` for the full ordering rules
(single-artifact case, phase-id + step-tag sort, git-commit-order
fallback) and the "first artifact for a Phase ever" kickoff case.

### 4. Decide your next action
Cross-reference the state against the table in
`workflows/temporal-phase/HANDOFF.md` §3.1.

- If the next driver is **Codex**: open the corresponding lane SKILL
  under `workflows/temporal-phase/skills/<lane>/SKILL.md` and execute
  its procedure. Produce its named product in `from-codex/`. Commit +
  push.
- If the next driver is **CC**: do nothing. Report
  "waiting on CC" and exit. CC's watcher will pick up the next CC
  product when it lands.

### 5. Report status
Print one short status block summarizing what you found:

```text
temporal-phase-codex-sync status:
  OriginHead:        <short SHA>
  Verifiers:         <PASS / FAIL summary>
  Open Phase:        <phase-id | none>
  Current state:     <STATE | none>
  Latest artifact:   <mailbox>/<filename>
  Next action:       <run lane X | waiting on CC | no Phase open>
```

## Authority
Codex-only. CC does not invoke this skill; CC has its own
`/temporal-phase-watch` and `/temporal-phase-start` skills.

## Fallback modes
When Host B restricts slash-command registration, `python` subprocesses,
`git push` confirmation, or `.codex/skills.json` visibility, see
`references/fallback-modes.md` for the four documented fallbacks
(slash-command not recognised; python subprocess blocked; git push
requires confirmation; cannot read `.codex/skills.json`).

## See also
`workflows/temporal-phase/HANDOFF.md` (Codex entry), `workflows/temporal-phase/BATON.schema.md`,
`.claude/skills/temporal-phase-watch/SKILL.md` (CC counterpart),
`.claude/skills/temporal-phase-start/SKILL.md` (CC orchestrator that
writes the kickoff this skill consumes).
