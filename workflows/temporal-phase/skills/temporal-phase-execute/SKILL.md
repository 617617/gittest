---
name: temporal-phase-execute
description: Codex executes the Phase per the accepted blueprint. Trigger EXECUTING; stay strictly inside AllowedFiles; on significant gap, stop and transition to BLOCKED_BLUEPRINT; writes from-codex/<phase-id>__execution-report.md; BatonNext = EXECUTION_REPORTED.
---

# temporal-phase / execute (Codex lane)

## Trigger
- Baton state: `EXECUTING` (entered from `BLUEPRINT_ACCEPTED`).

## Reads
- The final accepted blueprint (original blueprint or the last
  `blueprint-revision-r*.md`).
- The blueprint's `PackagePath:` pointer + `PackageCommit:` SHA.
- Inside the package: `PACKAGE_CHARTER.md` / `scope.md` /
  `HANDOFF_execute.md` / each `stage-NN/{EXECUTE,scope,evidence}.md`.
- The Runner contract — see `## Tools` below; do **not** rewrite
  stages manually.

## Tools

Delegate to the work-repo Codex skill `temporal-package-runner`. This
lane is only the coord-side "launch + acceptance" shell; the Runner's
code changes land in the work repo.

Two invocation paths exist (no-CWD-switch follow-procedure, or
explicit `CWD = temporal:` + `/temporal-package-runner`).

Full contract (Runner SKILL.md locations, strict-serial three-layer
rule, package-local reads, post-execution archive, coord-side
product format, relationship to subsequent baton lanes): see
`references/tools-runner.md`.

## Execution constraints
- **No scope creep.** Stay strictly inside `AllowedFiles:`.
- On a significant gap, or when code state contradicts blueprint
  assumptions, **stop, write a note, transition to
  `BLOCKED_BLUEPRINT`**.
- Code changes go to the work repo (`temporal:` resolved); commit
  normally with the work-repo's git. The coord repo only references
  `temporal@<short-sha>`; do not copy code.

## Writes
- `from-codex/<phase-id>__execution-report.md` (the coord product
  shaped per `references/tools-runner.md` §3).
- BatonNext: `EXECUTION_REPORTED`.

## Push order
Work-repo push first, then coord-repo push. Full procedure +
first-push-failure / second-push-failure recovery + the
`CROSS_REPO_MISSING_REF` audit-side error live in
`references/push-order.md`. Crash mid-execution? See
`references/crash-recovery.md`.

## Authority
Codex-only. CC must not write the execution report into `from-codex/`.

## See also
- `references/tools-runner.md` — full Runner delegation contract
- `references/push-order.md` — cross-repo push order + recovery
- `references/crash-recovery.md` — resume after CLI kill mid-execution
- `ROLES.md` Step 7 · `BATON.schema.md` state `EXECUTING`
