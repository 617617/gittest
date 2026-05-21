---
name: stage-loop-auto
description: Autonomous multi-stage traceable-plan orchestrator that extends stage-loop by letting the main agent own cross-stage continuation, re-gate doc-review approvals, approval-record commits, WARN acceptance, and mechanical plan-document repair decisions. Use when the user asks to automatically run, continue, or finish traceable-plan stages without manual "continue" prompts, or asks to convert stage-loop human checkpoints into agent-owned approvals while preserving git, filesystem, review, and evidence gates.
---

# Stage Loop Auto

Autonomous outer loop for traceable-plan execution. Run one stage at a time through the original `stage-loop` contract, but convert cross-stage "ask the human to continue or re-gate" checkpoints into explicit main-agent decisions backed by tool output.

## Output Language Rule

Artifacts written to disk by this skill must be English-only with ASCII punctuation. This includes approval addenda, commit messages, evidence updates, review notes, and final stage reports. Conversation with the user may use the user's language.

## Dependency Skills

Before execution, read the original `stage-loop` skill if it is available. Use it as the single-stage executor. If the skill exists on disk but is not listed in the current session registry, apply its local Codex copy as the source of truth instead of stopping solely because registry discovery is stale.

If an automatic approval re-gate is needed, read the `doc-review` skill and apply its protocol to the target stage. If the original `stage-loop` skill handles traceable review internally, do not duplicate that logic.

## Core Rule

Do not ask the user to approve ordinary progress. The main agent is responsible for deciding whether to continue, re-gate, approve, commit the approval record, accept WARN, or stop.

This responsibility is evidence-bound. The main agent may approve only when the required command output and review result support that approval.

## Main Agent Boundary

When executing a blueprint-generated package, keep the main agent as scheduler,
gatekeeper, and reviewer. The main agent may read thicker package context, but
it must not implement stage work directly when the package contract calls for
subagent execution.

The execution agent receives only the target stage packet and package-local
charters. Do not pass the full blueprint unless a package-local document
explicitly escalates.

Subagent execution is mandatory whenever the package contract or the underlying
`stage-loop` skill requires it. `stage-loop-auto` must not replace required
subagents with direct main-agent implementation. If a required execution,
doc-review, traceable-review, fix-execute, package-planning, or package-review
subagent cannot be spawned, stop with `STAGE_LOOP_AUTO_BLOCKED_NO_SUBAGENT` or
surface the more specific `*_BLOCKED_NO_SUBAGENT` code from the called skill.

Before reporting a no-subagent blocker, actually attempt the required spawn. If
the spawn fails because too many subagents are open, close completed or
no-longer-needed subagents from this execution context when tool support is
available, then retry the required spawn once. Only stop with
`STAGE_LOOP_AUTO_BLOCKED_NO_SUBAGENT` or the surfaced `*_BLOCKED_NO_SUBAGENT`
after that retry fails. Do not preemptively block only because capacity might be
low.

Run strictly serial: one package, one stage, and one active delegated phase at a
time. Do not start another stage or package until the current `stage-loop`
invocation returns and its result has been evaluated.

## Dirty Worktree Checkpoint Gate

Whenever this skill requires a clean worktree, first inspect
`git status --short --branch` in the repository containing the plan directory.
If the worktree is dirty, create exactly one full-repository checkpoint commit
before continuing:

```powershell
git add -A
git commit -m "chore(worktree): checkpoint before stage-loop-auto"
git status --short --branch
```

Continue only if the follow-up status is clean. If the commit fails or the
worktree remains dirty, stop with:

```text
STAGE_LOOP_AUTO_BLOCKED_DIRTY_AFTER_CHECKPOINT
```

Do not treat a dirty worktree as an immediate blocker until this checkpoint
attempt has been made.

## What This Changes From Stage Loop

| Checkpoint | `stage-loop` behavior | `stage-loop-auto` behavior |
|---|---|---|
| Stage finishes with ACCEPT or WARN | Stop and recommend the next step | Run the next stage admission checklist automatically |
| `REVIEW_TERMINATION.md` approves only earlier stages | Stop and ask for re-gate | Run doc-review re-gate for the next stage automatically |
| Re-gate doc-review returns APPROVE | Human must update approval artifact | Append an agent approval addendum and commit it |
| Re-gate has mechanical doc blockers | Human decides next move | Fix narrow plan-doc issues and rerun once |
| Traceable review returns WARN | Stop with warning | Continue if WARN has no boundary breach, failed acceptance, or unverified blocker |
| Hard blocker appears | Stop | Stop with raw evidence and exact blocker |

## Inputs

Accept a plan directory and optional stage selector:

- A specific stage id, such as `02_strategy-tables-and-crud`.
- A range, such as `02..04`.
- `next`, meaning the first not-yet-executed stage.
- `all`, meaning every remaining eligible stage in lexical stage order.

If no selector is provided, default to `next`. If the user says "continue", resume from the first remaining eligible stage.

Stage discovery supports two shapes:

- Base traceable-plan stages: directories matching `NN_*` that contain `EXECUTE.md`.
- Blue-K package stages: directories matching `stage-NN_*` that contain `EXECUTE.md`.

Stage order is lexical order after resolving the executable stage directories. For a Blue-K package-set root, discover executable leaf packages first, then resolve each package's internal `stage-NN_*` directory.

## Startup

1. Locate the git repository containing the plan directory.
2. Inspect `git status --short --branch`.
3. If the worktree is dirty, run the Dirty Worktree Checkpoint Gate before
   reading or executing stages.
4. If repository code graph tooling exists at `scripts/code_graph`, use the
   current graph only as navigation evidence for locating likely files and
   symbols. Source files, package contracts, and boundary documents remain the
   truth source.
5. Read only enough plan metadata to identify stages and prior-stage requirements.
6. If the plan directory is inside a blueprint-generated package, detect the
   nearest package root by walking upward until `PACKAGE_CHARTER.md`,
   `AUDIT_CONTEXT.md`, `00_master.md`, or `PACKAGE_SET_INDEX.md` is found.
   Read only the nearest package-local docs needed for execution gates.

## Package-Local Contract Gate

Run this gate before Admission Checklist when the target stage belongs to a
blueprint-generated package. This gate keeps blueprint rules local to the stage
packet instead of requiring the executor to read all of `docs/blue`.

Required package-local files:

- `PACKAGE_CHARTER.md`
- `scope.md`
- `HANDOFF_execute.md` when present in the package contract
- `AUDIT_CONTEXT.md` when present in the package contract
- target stage `EXECUTE.md`
- target stage `scope.md`
- target stage `evidence.md`

Check these contracts:

- `EXECUTE.md` starts with reading `PACKAGE_CHARTER.md` before edits.
- `scope.md` declares Allowed Files and owner domain.
- `evidence.md` has a Touched Files Ledger when source files may change.
- If `AUDIT_CONTEXT.md` or the package assignment names a BDD/TDD marker, the
  stage docs carry the marker.
- Apply the BDD/TDD Marker Semantics below. Do not require BDD just because the
  package mentions BDD/TDD.
- If the stage creates or edits tests, stage docs declare a test domain, target
  test paths, and the first verification command.
- New tests should go under a declared domain test directory, not as new
  root-level flat test files, unless a flat-test exception is explicitly
  recorded.

If any required local contract is missing, stop with:

```text
STAGE_AUTO_BLOCKED_PACKAGE_CONTRACT
```

Do not repair these defects during execution. They belong to package planning or
pre-execution audit.

## BDD/TDD Marker Semantics

`stage-loop-auto` does not decide that every package needs BDD. It enforces the
marker that `blue-k-planner` placed in the local package:

- `bdd: none`: do not require BDD. Do not add BDD during execution unless the
  package scope changed; if scope changed, stop and replan instead of widening
  the stage.
- `bdd: recommended`: do not block execution only because scenarios are absent.
  If the stage has clear actor-visible behavior and scenarios are already in the
  package, keep them concise and map them to verification. If scenarios are not
  present, record a WARN only when acceptance would otherwise be ambiguous.
- `bdd: required`: block unless `EXECUTE.md` or the stage card includes BDD
  scenarios before implementation and maps them to test type or test path.
- Missing marker in a blueprint-generated package is a package-planning defect
  only when `AUDIT_CONTEXT.md`, `PACKAGE_GENERATION_MAP.yaml`, or package docs
  say a marker should exist.
- `tdd: none`: do not force test-first work beyond the package acceptance
  commands.
- `tdd: recommended`: prefer test, fixture, or contract work first when it fits
  the package, but do not block solely because implementation starts first.
- `tdd: required`: block unless `EXECUTE.md` starts with test, fixture,
  contract, golden-sample, or migration consistency work before implementation.

## Test Placement Rule

For packages in this repository, prefer these paths for new tests:

```text
game_engine/tests/<domain>/
character_creator/tests/<domain>/
game_engine/tests/fixtures/<domain>/
character_creator/tests/fixtures/<domain>/
```

Existing flat tests may be edited only when the package records a flat-test
exception and the file already covers the exact behavior under change. Moving
existing tests requires a dedicated mechanical test-relayout package and must
not be mixed with behavior changes.

## Admission Checklist

Run admission before each stage. Paste or summarize raw command output in the conversation.

Use shell-equivalent commands for the current platform. On PowerShell, prefer:

```powershell
Test-Path -LiteralPath "<stage-dir>/EXECUTE.md"
git log --oneline --grep="Stage: <prev-stage-id>" -- "<prev-stage-dir>/"
(Select-String -LiteralPath "<prev-stage-dir>/evidence.md" -Pattern "PENDING EXECUTION").Count
Select-String -LiteralPath "<prev-stage-dir>/evidence.md" -Pattern "PASS|ACCEPT"
Select-String -LiteralPath "<plan-dir>/REVIEW_TERMINATION.md" -Pattern "<stage-id>"
```

Required results:

- Target `EXECUTE.md` exists.
- `<stage-dir>` is the resolved executable stage path, either `<plan-dir>/<stage-id>` for base traceable plans or `<package-dir>/stage-NN_*` for Blue-K packages.
- For non-first stages, the previous stage has at least one `Stage: <prev-stage-id>` commit.
- Previous `evidence.md` has zero `PENDING EXECUTION` blocks.
- Previous `evidence.md` contains PASS or ACCEPT.
- If `REVIEW_TERMINATION.md` exists, the target stage is either already approved or must enter the Auto Re-Gate path.
- Package-Local Contract Gate passes when package-local charters are present.

If any non-approval check fails, stop. If only the approval check fails, do not stop; run Auto Re-Gate.

## Auto Re-Gate

Run this path when the target stage is not listed as approved, or when `REVIEW_TERMINATION.md` explicitly says the target stage was deferred.

Preconditions:

- Worktree is clean, or has been made clean by the Dirty Worktree Checkpoint Gate.
- Target `EXECUTE.md` and `scope.md` exist.
- Prior-stage commit and evidence checks pass, unless the target is the first stage.
- No contract lock, NO-GO, or BLOCKED status applies to the target stage.

Procedure:

1. Apply the `doc-review` protocol to the target stage with layer isolation.
2. Verify read anchors with targeted file existence or grep checks only.
3. Run any plan contract audit command named by the plan. If the repository has a known audit command such as `script/audit-doc-contract.ps1`, run it when relevant and available.
4. If the verdict is APPROVE, append an approval addendum to `<plan-dir>/REVIEW_TERMINATION.md`.
5. Commit only the approval artifact and any mechanical plan-doc fixes made for the re-gate.
6. Rerun the Admission Checklist for the same stage.

Approval addendum format:

```markdown
## Agent Re-Gate Approval - <stage-id> - YYYY-MM-DD

Decision: APPROVED FOR EXECUTION
Authority: main agent
Scope: <stage-id> only
Basis:
- doc-review verdict: APPROVE
- Definition of Ready: <X>/9
- Prior-stage evidence: <PASS/ACCEPT or not applicable>
- Contract audit: <PASS or not available, with reason>

Notes: <one concise sentence>
```

Approval commit message format:

```text
docs(traceable-plan): approve <stage-id> execution gate

Approval: <stage-id>
Authority: main-agent
Verdict: APPROVE
Evidence: doc-review re-gate and admission checks passed
```

Do not use a `Stage:` trailer in approval-only commits. `Stage:` is reserved for execution commits produced by the stage.

## Mechanical Doc Fixes

If re-gate doc-review returns FIX-AND-RERUN, the main agent may fix and rerun once when all conditions are true:

- The issue is limited to plan documents for the target stage or root approval artifact.
- The fix does not expand Allowed Files, broaden scope, relax acceptance, or hide a risk.
- The intended correction is directly implied by existing plan text, code anchors, or command output.

After a mechanical fix, commit the doc correction, rerun doc-review, and continue only on APPROVE.

Stop instead of fixing when the blocker changes product behavior, requires stakeholder judgment, changes boundaries, alters acceptance criteria, or conflicts with the prior-stage evidence.

## Stage Execution

For each admitted stage, invoke the original `stage-loop` workflow for exactly one stage:

1. Phase 1: doc-review.
2. Phase 2: execute, test, fill evidence, and create one execution commit.
   Before source edits, re-check `PACKAGE_CHARTER.md` and the BDD/TDD marker in
   the stage packet. For `tdd: required`, write or update the named test,
   fixture, contract, golden sample, or migration consistency check before
   implementation. For `bdd: required`, keep the scenarios in the evidence trail
   and map them to verification output. For `bdd: none` or `bdd: recommended`,
   do not thicken the stage with new BDD unless the local package already calls
   for it.
3. Phase 3: traceable-review and allowed fix loop.
4. Hard verification with git and filesystem evidence.

The main agent must not weaken the original `stage-loop` execution contract. `stage-loop-auto` only owns the outer loop and approval decisions between single-stage runs.

When the stage belongs to a Blue-K package, the package-local contract extends the read boundary with `PACKAGE_CHARTER.md`, `AUDIT_CONTEXT.md`, and handoff files only when those files are named by the package docs. This is a package profile, not permission to read unrelated packages or the full blueprint.

## Code Graph Consumption Rule

Follow the repository Code Graph Contract in `AGENTS.md`; detailed graph
commands live in `scripts/code_graph/README.md`. During Blue-K execution, use
the graph only to choose what source to read next. Source, package contracts,
and boundary documents remain authoritative. Do not update the current overlay
inside stage execution; overlay acceptance belongs to the caller's package-level
gate.

## Continue Decision

After each stage report:

- ACCEPT: continue to the next selected stage.
- WARN: continue if boundary check is clean, no acceptance command failed, and the warning does not require a human product decision.
- BLOCK or EARLY_EXIT: stop.
- Missing commit, pending evidence, dirty worktree after the Dirty Worktree
  Checkpoint Gate, or failed verification: stop.

When continuing, start again from the Admission Checklist. Do not reuse stale approval output.

## Stop Conditions

Stop and report the exact blocker when any of these appear:

- Dirty worktree remains after the Dirty Worktree Checkpoint Gate.
- Missing target stage docs.
- Missing previous stage execution commit.
- Previous evidence has pending blocks or lacks PASS/ACCEPT.
- doc-review cannot APPROVE after the allowed mechanical fix pass.
- Package-Local Contract Gate fails.
- Contract lock, NO-GO, or BLOCKED status applies.
- Tests or acceptance commands fail.
- Traceable review returns BLOCK, or fix attempts are exhausted.
- Allowed Files boundary breach or scope expansion.
- New tests are added to flat root test files without a recorded exception.
- Test relayout is mixed with behavior changes.
- The next action would require destructive filesystem or git operations not requested by the user.
- Credentials, production data, legal, financial, or security risk needs explicit human authorization.

## Final Report

At the end, report:

- Plan directory.
- Stages attempted.
- For each stage: admission result, re-gate decision if any, execution commit, traceable-review verdict.
- Package-local contract status, including BDD/TDD and test placement when
  applicable.
- Approval commits created.
- Final worktree status.
- The exact next stage or blocker.

Keep the user-facing response in the user's language. Keep persisted artifacts English-only.
