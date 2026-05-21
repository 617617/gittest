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

This is **operational**, not part of the state machine. It does not
write `BatonNext:` artifacts; see the §Writes section below.

## Reads
- The current `from-cc/` and `from-codex/` mailbox listings under
  `workflows/temporal-phase/_coord/`.
- All lane SKILLs under `workflows/temporal-phase/skills/` (lookup
  per state).
- `workflows/temporal-phase/BATON.schema.md` for state enumeration and
  transitions.
- `workflows/temporal-phase/HANDOFF.md` §3.1 state→lane table.

## Writes
None. This skill is informational only. It does not produce any baton
artifact; therefore the usual `BatonNext: <STATE>` first-line rule
does not apply here. Lane skills (e.g., `temporal-phase-blueprint`,
`temporal-phase-execute`) own all artifact-writing.

## Steps

### 1. Sync repo

Resolve your coord-repo path via `PATHS.md` (Host B row → coord repo
column), then:

```bash
cd $(coord-repo-on-host-B-from-PATHS.md)
git pull origin master
```

If pull fails (conflict / diverged), stop and surface — do not act on
a stale baseline.

### 2. Verify registrations + artifacts

```bash
python scripts/verify_temporal_phase_skills.py
python scripts/check_baton_artifacts.py
```

Both must PASS before you act on the baton state. On FAIL, surface
the errors and stop.

### 3. Diagnose what is pending

List the two mailboxes:

```bash
ls workflows/temporal-phase/_coord/from-cc/
ls workflows/temporal-phase/_coord/from-codex/
```

(Skip `_coord/archive/<phase-id>/` directories — those are closed
Phases.)

Identify the **most recent artifact across both mailboxes**. Rules:

- If only one non-`.gitkeep` artifact exists across both mailboxes,
  that is the most recent (no tiebreak needed).
- If multiple artifacts exist, sort by `phase-id` (highest wins;
  there should normally be only one open phase-id), then by step-tag
  using the baton transition order in `BATON.schema.md` — later
  states sort later. Round-numbered tags (`pre-audit-codex-r2`)
  sort after lower-round (`pre-audit-codex-r1`).
- If still ambiguous, fall back to git commit order:
  `git log --format='%H %s' workflows/temporal-phase/_coord/`.

Read its first line `BatonNext: <STATE>`. That is the current baton
state.

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

Special case — first artifact for a Phase ever: the most recent
artifact is `from-cc/<phase-id>__kickoff.md`. Its `BatonNext:` is
`DRAFTING_BLUEPRINT`. That is your trigger to enter the blueprint lane
(`workflows/temporal-phase/skills/temporal-phase-blueprint/SKILL.md`).
Read the kickoff completely for `PhaseId:`, `Goal:`, `SourceAnchor:`,
`PreviousPhaseClose:`, then proceed.

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

## Fallback modes (when something on Host B is restricted)

The protocol assumes Codex CLI can (a) load this skill from
`.codex/skills.json`, (b) run `python` subprocesses, and (c) `git
push` without per-action confirmation. None of these are guaranteed
universally. If any fails, the chain must not silently corrupt —
fall back as follows:

- **Slash command `/temporal-phase-codex-sync` not recognised** —
  Codex CLI may not auto-register every entry from
  `.codex/skills.json` as a slash command. Fallback: open this file
  (`workflows/temporal-phase/skills/temporal-phase-codex-sync/SKILL.md`)
  by path and follow steps 1–5 manually. Same effect.
- **`python` subprocess blocked** — your CLI may refuse to spawn
  python. Surface the verifier output to the user: "subprocess
  blocked; please run `python scripts/verify_temporal_phase_skills.py`
  and `python scripts/check_baton_artifacts.py` manually and paste
  the output back". Do NOT proceed with `git push` until the user
  confirms both PASS.
- **`git push` requires per-action confirmation** — if your CLI
  prompts for confirmation on every push, surface that to the user
  rather than guessing. State the exact `git push` command being
  proposed, wait for user approval, then proceed.
- **Cannot read `.codex/skills.json` to enumerate skills** — surface
  this to the user as "skill registry not visible from this session".
  Recovery: open this SKILL file directly by path
  (`workflows/temporal-phase/skills/temporal-phase-codex-sync/SKILL.md`)
  and follow steps 1–5 manually. The slash form will start working
  once the registry can be loaded (likely after Codex restart in the
  correct CWD = the coord-repo root).

## See also
`workflows/temporal-phase/HANDOFF.md` (Codex entry), `workflows/temporal-phase/BATON.schema.md`,
`.claude/skills/temporal-phase-watch/SKILL.md` (CC counterpart),
`.claude/skills/temporal-phase-start/SKILL.md` (CC orchestrator that
writes the kickoff this skill consumes).
