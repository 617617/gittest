# Branch A — Fresh start (no Phase open yet)

Reached when both `_coord/from-cc/` and `_coord/from-codex/` have no
phase artifacts (only `.gitkeep`).

CC writes a kickoff baton artifact and pushes it; Codex on the other
host picks it up next time `/temporal-phase-codex-sync` runs. **There
is no copy-paste chat relay for the kickoff** — it lives in git.

## Step A1 — prompt the user

Ask, in chat (not in a tool):

> Please provide:
>   1. A phase-id matching `^phase-\d+$` (e.g., `phase-01`,
>      `phase-11`).
>   2. A short Phase goal description (1-3 sentences).
>   3. (Optional) A source-document anchor: a short string
>      identifying the section of the Temporal workflow doc this
>      Phase implements.
>   4. (Optional) The previous Phase's close.md path (if any).

Wait for the user's reply. Then validate `<phase-id>` against the
regex; if invalid, ask again.

## Step A2 — write the kickoff baton artifact locally

Write `workflows/temporal-phase/_coord/from-cc/<phase-id>__kickoff.md`
with this body (substitute the user's values verbatim):

````text
BatonNext: DRAFTING_BLUEPRINT

# Phase <phase-id> — Kickoff

PhaseId: <phase-id>
StartedBy: CC (Host A)
StartedAt: <current ISO-8601 UTC timestamp>

Goal:
<goal>

SourceAnchor:
<source-anchor or "N/A">

PreviousPhaseClose:
<previous-close path resolved via PATHS.md, or "N/A (first Phase)">

Notes for Codex (blueprint lane):
- Follow `workflows/temporal-phase/skills/temporal-phase-blueprint/SKILL.md`.
- Its `## Tools` section delegates to the work-repo skill
  `temporal-stage-package-generator`. Generator SKILL.md resolves
  via `PATHS.md` to
  `temporal:.codex/skills/temporal-stage-package-generator/SKILL.md`.
- Use phase-id `<phase-id>` consistently in package-id selection
  and product filenames.
````

## Step A3 — check before committing

Run `python scripts/check_baton_artifacts.py` against the working
tree. The new kickoff is present locally; the checker confirms
filename, BatonNext, mailbox routing, and single-open-Phase.

**If it FAILs**: delete the local file
(`rm workflows/temporal-phase/_coord/from-cc/<phase-id>__kickoff.md`),
surface the error, and stop. Nothing has been committed or pushed.

## Step A4 — collision check vs archive

`check_baton_artifacts.py` does not scan `_coord/archive/`. Confirm
`<phase-id>` is unused across the full history:

```bash
ALL_IDS=$( {
  ls workflows/temporal-phase/_coord/from-cc/ workflows/temporal-phase/_coord/from-codex/ 2>/dev/null \
    | grep -oE '^phase-[0-9]+';
  ls workflows/temporal-phase/_coord/archive/ 2>/dev/null \
    | grep -oE '^phase-[0-9]+';
} | sort -u )
echo "$ALL_IDS" | grep -qx "<phase-id>" && echo "CHAIN_COLLISION: <phase-id> already in use" && exit 1
```

On collision: delete the local file, report `CHAIN_COLLISION`, ask
the user to pick a different phase-id, and stop.

## Step A5 — commit, then rebase, then push

The local commit must exist BEFORE pulling — `git pull --rebase`
refuses to run on a dirty working tree.

```bash
git add workflows/temporal-phase/_coord/from-cc/<phase-id>__kickoff.md
git commit -m "kickoff(<phase-id>): start Phase per temporal-phase workflow"
git pull --rebase origin master
git push origin master
```

If the rebase has conflicts: surface and stop — do not resolve
silently. If the push is rejected (hook, branch protection): surface
and stop; the local commit is intact, the user can investigate.

## Step A6 — report

```text
Kickoff pushed.
  File:    workflows/temporal-phase/_coord/from-cc/<phase-id>__kickoff.md
  Commit:  <short SHA>
  State:   DRAFTING_BLUEPRINT (Codex's turn)

The kickoff is now on origin/master. Codex on Host B does NOT have a
live watcher -- the next time the user opens Codex (or runs
/temporal-phase-codex-sync), Codex will pick up the kickoff and
enter the temporal-phase-blueprint lane.
```

## First-time Codex bootstrap (one-time only)

If the user mentions Codex on Host B has never participated in
temporal-phase before, also emit one short line for them to paste
once:

```text
You are the Codex side of the temporal-phase workflow on Host B.
Read workflows/temporal-phase/HANDOFF.md, then run /temporal-phase-codex-sync.
From now on, run /temporal-phase-codex-sync at every session start.
```

After that one-time onboarding, future Phases never need a chat
relay — the kickoff file is the only signal.
