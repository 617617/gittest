---
name: temporal-phase-execute
description: Codex executes the Phase per the accepted blueprint. Trigger EXECUTING; stay strictly inside AllowedFiles; on significant gap, stop and transition to BLOCKED_BLUEPRINT; writes from-codex/<phase-id>__execution-report.md; BatonNext = EXECUTION_REPORTED.
---

# temporal-phase / execute (Codex lane)

## Trigger
- Baton state: `EXECUTING` (entered from `BLUEPRINT_ACCEPTED`)

## Reads
- The final accepted blueprint (original blueprint or the last
  `blueprint-revision-r*.md`)
- The blueprint's `PackagePath:` pointer + `PackageCommit:` SHA
- Inside the package: `PACKAGE_CHARTER.md` / `scope.md` /
  `HANDOFF_execute.md` / each `stage-NN/{EXECUTE,scope,evidence}.md`
- You must follow the `## Tools` section below — **do not** rewrite
  stages manually.

## Tools — Delegate to the Temporal Package Runner

The actual executor is the work-repo-registered Codex skill
`temporal-package-runner`. This lane is only the coord-side "launch +
acceptance" shell.

### 1. The Runner's contract (authoritative source)

Runner SKILL.md location (resolved via the `temporal:` prefix in
`PATHS.md`):

```text
temporal:.codex/skills/temporal-package-runner/SKILL.md
temporal:local-skill-bundles/temporal-skills-2026-05-21/local/temporal-package-runner/SKILL.md
```

Read it before opening this lane. It defines:
- the allowed repository scope (`temporal:` only);
- the strict-serial contract across three layers: main runner /
  package-runner subagent / stage-loop-auto — **exactly one** per layer;
- `pending/` exactly-one before any run;
- package-local mandatory reads: `PACKAGE_CHARTER`, `scope`,
  `HANDOFF_execute`, `stage-*/*`;
- post-execution archive: follow `RUN_AFTER_EXECUTION_PROTOCOL.md`; the
  Runner owns package-store moves, queue/index updates, and the final
  user report;
- post-execution audit / repair orchestration also belongs to the main
  Runner. Note: this overlaps conceptually with our three `postexec-*`
  lanes; the coord side synthesizes both (see §4).

### 2. Invocation paths

Given that Codex-side `.codex/skills.json` currently keeps
`allowGlobalFallback: false`, pick one of:

- **Option A (recommended, no CWD switch).** This lane is "follow the
  Runner's SKILL.md procedure" — read the Runner SKILL.md, then in the
  work repo enforce the strict-serial contract:
  `Runner → exactly one package-runner subagent → stage-loop-auto`.
- **Option B (explicit CWD switch).** Open a second Codex session with
  CWD = `temporal:` and run `/temporal-package-runner` there.

The Runner's code changes land in the work repo. It does **not** write
into the coord mailbox.

### 3. coord-side product (what this lane writes)

The coord side carries one "execution report + work-repo change
pointers" file — no code is copied across:

```text
BatonNext: EXECUTION_REPORTED

# Phase <id> — Execution Report

PackagePath: temporal:docs/.../stage-loop-auto-packages/<dest>/<package-id>/
            (after Runner moves it, record the final location)
RunnerVerdict: COMPLETED | BLOCKED | PARTIAL
ActualChanges:
  - temporal@<sha1>  <commit subject>
  - temporal@<sha2>  ...
ValidationResults:
  - <stage-NN>: <evidence path + conclusion>
ResidualRisks: ...
EvidenceArtifacts:
  - temporal:<stage-NN>/evidence.md
NextStepSuggestions: ...
```

### 4. Relationship to subsequent baton lanes

The Runner does its own post-execution audit / repair internally. The
`postexec-subagent-review` lane in this baton then runs an **outer
second pass** with fresh Codex subagents — it does not replace the
Runner's internal audit. The outer pass works on the full evidence
already in the coord mailbox and asks: "does this match the Phase
blueprint, do we need Phase-level repair?"

## Execution constraints
- **No scope creep.** Stay strictly inside `AllowedFiles:`.
- On a significant gap, or when code state contradicts blueprint
  assumptions, **stop, write a note, transition to
  `BLOCKED_BLUEPRINT`**.
- Code changes go to the work repo (`temporal:` resolved); commit
  normally with the work-repo's git. The coord repo only references
  `temporal@<short-sha>`; do not copy code.

## Writes
- `from-codex/<phase-id>__execution-report.md` (the coord product from
  §3)
- BatonNext: `EXECUTION_REPORTED`

## Push order (cross-repo consistency)

Execution writes commits in **two repos** (work repo for the actual
code changes; coord repo for the execution-report pointer). To avoid
dangling references — where the coord-side `ActualChanges:` cites a
`temporal@<sha>` that exists only on your local machine — push in
this strict order:

1. **First**, push the work repo (Temporal):
   ```bash
   cd $(temporal:)
   git push origin <work-branch>
   ```
   Confirm exit 0 before continuing.

2. **Only then**, push the coord repo (gittest):
   ```bash
   cd $(gittest:)
   git push origin master
   ```

If the first push fails (network drop, lock, conflict): do **not**
push the coord repo. On next `/temporal-phase-codex-sync` you will
see baton state still `EXECUTING` (no execution-report in coord);
retry the work-repo push first, then write/push the coord pointer.

If somehow the coord push happened but the work-repo push failed:
CC's `postexec-subagent-review` lane will fail to resolve the
`ActualChanges:` SHAs and surface a `CROSS_REPO_MISSING_REF` error;
recovery is "push the work repo, then have CC retry the audit". A
standalone check exists: `scripts/verify_cross_repo_refs.py` walks
both mailboxes + archive and flags any pointer whose `temporal@<sha>`
is unreachable from the local work-repo clone.

## Authority
Codex-only. CC must not write the execution report into `from-codex/`.

## See also
`ROLES.md` Step 7 · `BATON.schema.md` state `EXECUTING`
