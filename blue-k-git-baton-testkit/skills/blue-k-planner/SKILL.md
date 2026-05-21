---
name: blue-k-planner
description: >-
  Manage the DND back blueprint K-stage workflow rooted at
  docs/blue. Use when the user asks to inspect the
  current K, advance/archive mian-k to past-k, update the blueprint stage lock,
  or decompose the next K into main and ordered parallel other branches with a
  mandatory source-grounded planning subagent, traceable-plan branch package
  discipline, mandatory execution subagents, audit manifest handoff, and a
  mandatory blue-k-plan-audit gate.
---

# Blue K Planner

This skill manages the K-stage blueprint workflow for:

```text
docs/blue
docs/mian-k
docs/past-k
docs/archive/finished/blue
```

`blue` is the only active blueprint and lock source. `mian-k` is the current
work package. `past-k` stores completed K packages. `archive\finished\blue` is
historical reference only.

## AI Chat Contract (v0.10)

This skill runs only inside a Blue-K baton chat selected by `bk sync`. Three
hard rules apply on every invocation — full text in
`blue-k-git-baton-testkit/references/ai-chat-contract.md`:

1. **First reply** begins with `I am <CC|Codex>. Lane: <lane>.` before any
   tool call or repo read. The human matches this against the `WindowMatch`
   hint printed by `bk sync`.
2. **Wrong-window input must refuse.** If this chat does not match the
   `ChatTarget` printed by the latest `bk sync`, do not acquire a lease,
   edit files, or call any Blue-K skill; reprint the correct
   `ChatTarget` / `ChatCommand` and stop.
3. **Finalize with a fixed closing line.** After one safe assignment, push
   the work branch and coordination branch atomically, write the next
   holder into `BATON.yaml`, and end the reply with exactly
   `Done. Now run: bk sync`. Do not chain into the next package, lane, or
   assignment.

For `/bk takeover`, no destructive recovery may begin before the human types
`yes, abandon` in this chat.

## Safety Rule

Do not advance, archive, move files, update locks, or create a new `mian-k`
unless the user explicitly asks to advance, archive, or split the next K.

Default to inspect mode when the request is ambiguous.

## Mandatory Subagent Gate

This skill requires subagents for every source-planning, package-planning,
package-execution, and package-review role that names a subagent. The main agent
is the dispatcher, reviewer, manifest owner, and lock owner; it must not replace
subagent work with direct main-agent work.

Mandatory subagents:

- Source Planning Gate: exactly one read-only source-planning subagent.
- Package Planning Gate: one package-planning subagent per minimal executable
  package, with disjoint write ownership.
- Execute Package Mode: one execution subagent for the target package.
- Blue K Plan Audit Gate: one pre-doc-review subagent per minimal executable
  package.

If any required subagent cannot be spawned, stop with the matching
`*_BLOCKED_NO_SUBAGENT` code. No direct main-agent substitute is allowed.

## Modes

### Execute Package Mode

Use when the user asks to execute a package under `mian-k/main` or `mian-k/other`.
The main agent must act as dispatcher, reviewer, and lock owner. The package
executor must be a subagent.

Execution role requirements:

- The main agent reads `blue` locks, `Kx_INDEX.md`, package-set indexes, and the
  target package handoff.
- The main agent verifies the target package has `PACKAGE_CHARTER.md`. If it is
  missing, stop with `EXECUTE_PACKAGE_BLOCKED_MISSING_CHARTER`.
- The main agent gives the execution subagent only the minimal package context:
  target package path, current K ID, dependency status, allowed files,
  forbidden actions, the package `PACKAGE_CHARTER.md`, and the target
  `HANDOFF_execute.md` / `EXECUTE.md`.
- The execution subagent executes only that package and must not read unrelated K packages
  unless its own `EXECUTE.md` escalates.
- The execution subagent must not advance the K lock, archive `mian-k`, or update
  `K_PROGRESS_INDEX.md`.
- The execution subagent must return changed files, evidence status, commands
  run, blockers, and any WARN items.
- After the subagent returns, the main agent re-reads changed package docs,
  reviews evidence, checks `git diff --stat`, verifies lock compliance, and then
  records the package result or asks for repair.
- The main agent must append a short dispatcher review entry to the target
  package `audit_trace.md` when present. Record subagent result, evidence
  verdict, diff scope, remaining WARN/BLOCK items, and whether the package can
  merge into its K gate.

If the execution subagent cannot be spawned, stop with
`EXECUTE_PACKAGE_BLOCKED_NO_SUBAGENT`.

This keeps bulky blueprint context out of the executor. The executor reads the
thin execution packet; the main agent keeps the global map.

### Inspect Mode

Use when the user asks whether the current K is done, asks about progress, or
mentions this skill without an explicit advance request.

1. Read:
   - `docs/blue\README.md`
   - `docs/blue\ROADMAP_LOCK.yaml`
   - `docs/blue\CURRENT_STAGE.md`
   - `docs/blue\STAGE_STATUS.md`
   - `docs/blue\STAGE_DECISIONS.md`
   - `docs/blue\STAGELOCK_PARALLEL_WORKFLOW.md`
   - `docs/blue\K_PROGRESS_INDEX.md` if present
   - current files under `docs/mian-k`
2. Check the current K against the completion rules below.
3. Report one status:
   - `INCOMPLETE`
   - `COMPLETE_READY_TO_ARCHIVE`
   - `BLOCKED`
   - `INCONSISTENT`
   - `NON_STRICT_PACKAGE`
4. Do not edit files.

Report `NON_STRICT_PACKAGE` when a package is usable as an older draft but does
not satisfy the current strict skill contract. Examples:

- Plan Next did not spawn the required source-planning subagent.
- `SOURCE_PLANNING_BRIEF.md` is missing.
- Plan Next did not run the required `blue-k-plan-audit` gate.
- Any executable package lacks a package-level `PRE_REVIEW_REPORT.md`.
- Any package-level review says it was performed directly by the main agent
  instead of a package review subagent using `pre-doc-review`.
- `AUDIT_MANIFEST.yaml` is missing.
- Any executable package is missing `AUDIT_CONTEXT.md`.
- `BLUE_K_PLAN_AUDIT_REPORT.md` is missing after Plan Next review.
- Any executable `other` branch uses the loose three-file shape instead of a
  traceable-plan-style branch package.
- Any executable branch is missing a stage card, branch `00_master.md`,
  `audit_trace.md`, or handoff files.
- Any executable package is missing `PACKAGE_CHARTER.md`.
- Any executable package `EXECUTE.md` does not require reading
  `PACKAGE_CHARTER.md` before edits.
- Any executable package `evidence.md` lacks a Touched Files Ledger.
- Any executable package with `bdd: required` lacks BDD scenarios and
  scenario-to-test mapping before implementation steps.
- Any executable package with `tdd: required` starts with implementation before
  test, fixture, contract, golden-sample, or migration consistency work.
- Any test-writing package lacks a declared test domain, target test paths, or
  Test Placement Ledger.

### Advance Mode

Use only when the user explicitly asks to advance, archive, close the current K,
or move to the next K.

1. Run Inspect Mode first.
2. Proceed only if status is `COMPLETE_READY_TO_ARCHIVE`.
3. Create or update `docs/blue\K_PROGRESS_INDEX.md`.
4. Create an `ARCHIVE_SUMMARY.md` in the current `mian-k` package before moving
   it. Include source path, target path, K ID, lock position, completion evidence,
   required branch results, optional branch results, accepted WARN items, blockers
   if any, and next K recommendation.
5. Move the completed package from `mian-k` to `past-k`.
6. Update the blueprint control files:
   - `ROADMAP_LOCK.yaml`
   - `CURRENT_STAGE.md`
   - `STAGE_STATUS.md`
   - `STAGE_DECISIONS.md`
   - `K_PROGRESS_INDEX.md`
7. Do not create the next `mian-k` unless the user also asks to split or plan it.

### Plan Next Mode

Use only when the user explicitly asks to split, decompose, or create the next K.
This mode must follow the local `traceable-plan` skill. Load it before producing
the plan.

Subagents are mandatory in Plan Next Mode:

- Run the Source Planning Subagent Gate before writing branch packages.
- Run the Package Planning Subagent Gate to draft each minimal executable
  package.
- Enforce the Source And Boundary Five Questions Gate for every package-planning
  subagent and every audit handoff.
- Prepare the Audit Handoff Gate before package review.
- Run the Blue K Plan Audit Gate after writing the draft plan.
- Do not silently downgrade any gate to direct main-agent work.
- If subagents cannot be used, stop with `PLAN_NEXT_BLOCKED_NO_SUBAGENT`.

Before splitting the next K, read:

- `docs/blue\README.md`
- `docs/blue\ROADMAP_LOCK.yaml`
- `docs/blue\CURRENT_STAGE.md`
- `docs/blue\STAGE_STATUS.md`
- `docs/blue\STAGE_DECISIONS.md`
- `docs/blue\STAGELOCK_PARALLEL_WORKFLOW.md`
- `docs/blue\K_STAGE_TOPOLOGY.md`
- `docs/blue\SOURCE_ORGANIZATION_CHARTER.md`
- `docs/blue\BDD_TDD_MARKERS.md`
- `docs/blue\TEST_ORGANIZATION_CHARTER.md`
- `docs/blue\04_research_and_source_map.md`
- `docs/blue\05_acceptance_gates.md`
- `docs/blue\06_risks_red_lines.md`
- `docs/blue\K_PROGRESS_INDEX.md` if present
- relevant files under `docs/past-k`
- relevant source code

After reading `ROADMAP_LOCK.yaml`, identify the current K topology fields before
planning:

```yaml
topology:
main_layout:
other_layout:
topology_ref:
other_packages:
```

If the fields are missing, read `K_STAGE_TOPOLOGY.md`. If the current K still has
no topology marker, stop with `PLAN_NEXT_BLOCKED_MISSING_TOPOLOGY`.

Research external sources only when the blueprint requires current facts,
the local references are stale, or implementation risk depends on current
library/API behavior.

#### Source Planning Subagent Gate

Before creating branch packages, spawn exactly one read-only subagent to produce
a source-grounded planning brief.

The main agent owns locks, archive state, shared router files, assignment maps,
and final plan acceptance. The source-planning subagent owns only code and
blueprint reconnaissance.

Give the source-planning subagent only the minimum necessary context:

- current K ID and target;
- relevant `ROADMAP_LOCK.yaml` constraints;
- relevant acceptance gate and risk red lines;
- latest `K_PROGRESS_INDEX.md` entry or previous K summary if present;
- specific blueprint source files or sections needed for this K;
- source-code search targets or likely entry points;
- the required output format below.

The source-planning subagent must not edit files. It must read relevant source code before
making planning claims. Claims that are not backed by a source path, blueprint
path, command, or explicit `[UNVERIFIED]` marker cannot be used as final planning
evidence.

Required subagent output:

```text
Current K:
Topology marker:
Source files inspected:
Blueprint files inspected:
Current code behavior:
Gap from blueprint:
Recommended main trunk:
Recommended required_other branches:
Recommended optional_other branches:
Dependency order:
Forbidden work:
Open questions:
Unverified claims:
Source anchors for package planning:
Boundary five questions draft:
```

After the subagent returns, the main agent must review the brief against `blue`
locks and gates. If the brief conflicts with `ROADMAP_LOCK.yaml`, missing source
evidence, or current K status, stop and report `INCONSISTENT` instead of writing
the next plan.

Persist the accepted brief as:

```text
docs/mian-k\SOURCE_PLANNING_BRIEF.md
```

The final plan is not strict-ready without this artifact.

#### Source And Boundary Five Questions Gate

Every package that will be generated through `traceable-plan` structure rules
must be source-grounded. Do not underfeed a package-planning subagent. Slight
context over-inclusion is allowed when it prevents a planner or reviewer from
guessing.

For each package, provide enough context to answer these five questions:

```text
1. What was replaced?
2. What was preserved?
3. What was frozen?
4. What is the truth source?
5. What is the exit condition?
```

The answers must be package-specific. If a question does not apply, the package
must say `Not applicable` and explain why.

Every package-planning subagent using `traceable-plan` rules must:

- read relevant source code before drafting package docs;
- record source files inspected and important symbols or routes inspected;
- use source evidence from actual files, not only from blueprint prose;
- answer the five questions in the package audit layer;
- include a concise five-question summary in `AUDIT_CONTEXT.md`;
- include enough source anchors in `EXECUTE.md` for the future executor to know
  what source area to inspect before edits;
- mark uncertain claims as `[UNVERIFIED]` instead of filling gaps by guesswork.

If relevant source code cannot be inspected, stop the package assignment with:

```text
PACKAGE_PLANNING_BLOCKED_NO_SOURCE_GROUNDING
```

#### Package Planning Subagent Gate

After accepting `SOURCE_PLANNING_BRIEF.md`, the main agent must not directly
write the thick contents of every executable package when the K contains more
than one minimal package.

The main agent owns:

- current K lock interpretation;
- package topology and dependency map;
- package assignment prompts;
- final manifest merge;
- final review of generated package docs;
- lock safety decisions.

Package-planning subagents own:

- drafting one assigned minimal executable package, or one assigned package set
  when the package set is explicitly small enough to keep coherent;
- applying the local `traceable-plan` structure rules to that package;
- reading only the context slice assigned by the main agent;
- producing package docs and the package `AUDIT_CONTEXT.md`;
- never advancing locks, archiving `mian-k`, or editing source code.

If a K has multiple independent packages, spawn package-planning subagents with
disjoint write ownership:

```text
docs/mian-k\main\00_<package>
docs/mian-k\other\NN_<branch>
docs/mian-k\other\NN_<branch_set>\MM_<subpackage>
```

The main agent may write only router and shared files directly:

```text
Kx_INDEX.md
SOURCE_PLANNING_BRIEF.md
PACKAGE_GENERATION_MAP.yaml
main\PACKAGE_SET_INDEX.md
other\NN_<branch_set>\PACKAGE_SET_INDEX.md
AUDIT_MANIFEST.yaml
```

Before spawning package-planning subagents, write:

```text
docs/mian-k\PACKAGE_GENERATION_MAP.yaml
```

Load `references/package-generation-contract.md` for the required
`PACKAGE_GENERATION_MAP.yaml` fields, package-planning subagent input shape,
subagent return shape, and main-agent verification checklist. This reference is
contract text, not optional guidance.

If package-planning subagents cannot be spawned, stop with:

```text
PLAN_NEXT_BLOCKED_NO_PACKAGE_PLANNING_SUBAGENT
```

#### Plan Topology Gate

Before writing `mian-k`, choose the output shape from the current K topology
marker. Do not infer shape from convenience.

Supported topology markers:

```text
single_traceable_package
k_package_set
integration_gate_only
serial_package_set
ordered_parallel_package_set
```

Rules:

- If `topology: single_traceable_package`, `mian-k/main` may be one
  traceable-plan package.
- If `topology: k_package_set`, `mian-k/main` is not automatically executable as
  one package. It must contain `PACKAGE_SET_INDEX.md` plus numbered package
  directories unless `main_layout: integration_gate_only`.
- If `main_layout: integration_gate_only`, `main` contains only the integration
  gate package that closes required evidence branches.
- If `main_layout: serial_package_set`, create numbered packages under `main`
  such as `00_*`, `01_*`, and a `main/PACKAGE_SET_INDEX.md` dependency map.
- If `other_layout: ordered_parallel_package_set`, every `other/NN_*` directory
  must be a traceable-plan-style package with its own audit, handoff, stage card,
  `EXECUTE.md`, `evidence.md`, and pre-review output.

For `k_package_set`, each package directory is the traceable-plan execution unit.
The K root is only a router, lock record, and integration surface.

#### Other Package Layout Gate

Before writing `other`, read the current K `other_packages` list from
`ROADMAP_LOCK.yaml`. Do not invent branch thickness from naming.

Each `other_packages` item controls one branch:

```yaml
id:
layout: single_traceable_package | branch_package_set
mode: required_other | optional_other
depends_on:
can_run_parallel_with:
must_merge_before:
```

Rules:

- If `layout: single_traceable_package`, create one traceable-plan-style package
  at `other/NN_<id>`.
- If `layout: branch_package_set`, create `other/NN_<id>/PACKAGE_SET_INDEX.md`
  plus numbered subpackages like `00_*`, `01_*`.
- If a branch has `depends_on`, its `HANDOFF_execute.md` must list those
  dependencies and tell the executor to stop if they are missing.
- Cross-K dependencies must resolve through `K_PROGRESS_INDEX.md`, archived
  `past-k` evidence, or a named integration gate. Do not execute a branch whose
  cross-K dependencies are not passed or explicitly unlocked.
- A branch may run in parallel only with IDs listed in `can_run_parallel_with`.
- A branch can merge only into IDs listed in `must_merge_before`.
- Required branches block the K gate. Optional branches block only when their
  own contract says they found a blocker.

#### Charter Injection Gate

Because `stage-loop-auto` executors read package documents, not `blue`, every
generated executable package must receive a local charter capsule.

Read:

```text
docs/blue\SOURCE_ORGANIZATION_CHARTER.md
docs/blue\TEST_ORGANIZATION_CHARTER.md
docs/blue\BDD_TDD_MARKERS.md
```

Then inject into every `main` package, every `other` package, and every
subpackage inside a package set:

```text
PACKAGE_CHARTER.md
```

Also inject charter references into:

- `scope.md`: owner domain, allowed files, forbidden moves, target-domain rule.
- `HANDOFF_execute.md`: point executor to `PACKAGE_CHARTER.md` first.
- `EXECUTE.md`: first step is read `PACKAGE_CHARTER.md`; stop if missing.
- `evidence.md`: include a Touched Files Ledger.
- `PRE_REVIEW_REPORT.md`: review charter compliance.
- `AUDIT_CONTEXT.md`: carry the package's origin, purpose, dependencies, and
  package-specific review context.
- test-writing packages: include the Test Placement Ledger and target test
  domain from `TEST_ORGANIZATION_CHARTER.md`.
- BDD/TDD packages: include the matching marker from `BDD_TDD_MARKERS.md` and
  put required BDD/TDD work before implementation steps.

Minimum `EXECUTE.md` preflight:

```text
1. Read PACKAGE_CHARTER.md.
2. Confirm Allowed Files and owner domain.
3. If existing source files must move, stop unless this is a dedicated
   mechanical relayout package.
4. If work needs files outside owner domain, stop and escalate.
```

Minimum `evidence.md` ledger:

```text
| Path | Domain | Action | Reason | Relayout? |
| --- | --- | --- | --- | --- |
```

Minimum Test Placement Ledger when tests may change:

```text
| Test path | Test domain | Action | Reason | Flat-test exception? |
| --- | --- | --- | --- | --- |
```

If a generated package lacks `PACKAGE_CHARTER.md` or the `EXECUTE.md` preflight,
mark it `NON_STRICT_PACKAGE`.

#### Audit Handoff Gate

Before any pre-execution review, prepare the handoff that lets
`blue-k-plan-audit` review each minimal executable package with precise context.

Write:

```text
docs/mian-k\AUDIT_MANIFEST.yaml
```

Load `references/audit-handoff-contract.md` for required manifest fields,
package `AUDIT_CONTEXT.md` sections, and the exact audit handoff. This
reference is contract text, not optional guidance.

#### Blue K Plan Audit Gate

After the draft `mian-k` plan is written, passes the local shape check, and has
`AUDIT_MANIFEST.yaml` plus package `AUDIT_CONTEXT.md` files, invoke the local
`blue-k-plan-audit` skill.

`blue-k-plan-audit` is responsible for spawning one documentation-only subagent
per minimal executable package. Each package review subagent must use the local
`pre-doc-review` skill. If audit subagents cannot be spawned, the audit gate
must block instead of direct-reviewing packages.

Load `references/audit-handoff-contract.md` for the exact
`blue-k-plan-audit` input, audit-skill obligations, and main-agent final
audit-result review rules.

## Completion Rules

A K is complete only when all of these are true:

- The serial `main` branch is complete.
- Every `required_other` branch is complete and merged into the K evidence.
- Optional branches are either complete or explicitly marked non-blocking.
- Evidence files exist and cite real file paths, commands, diffs, tests, or
  manual proof.
- The acceptance gate is `PASS`, or `WARN accepted` with the reason recorded.
- There is no unresolved `BLOCKER`.
- The work did not violate `ROADMAP_LOCK.yaml`.
- Dependencies on earlier K packages are recorded.
- Outputs needed by later K packages are indexed.

If any item is unclear, report `INCONSISTENT` or `BLOCKED` instead of advancing.

## Required `mian-k` Shape

When creating a new K package, first apply the Plan Topology Gate. `mian-k` may
be either a single-package K or a package-set K.

Load `references/mian-k-shapes.md` for the exact single-package and package-set
directory shapes, branch stage-card sections, loose-shape rejection rule, and
`PACKAGE_SET_INDEX.md` requirements. This reference is contract text, not
optional guidance.

## K Progress Index

Create `docs/blue\K_PROGRESS_INDEX.md` if missing.

Each entry should record:

```text
K ID:
Status:
Lock before:
Lock after:
Active package:
Archived package:
Blueprint sources:
Main result:
Required other results:
Optional other results:
Dependencies consumed:
Outputs produced:
Evidence files:
Gate result:
Decision log:
Next recommendation:
```

Keep the index append-only unless correcting a clear error. If correcting, add a
short correction note rather than silently rewriting history.

## Lock Rules

Only move the lock forward when:

- completion rules pass;
- the K gate passes or has an accepted WARN;
- required parallel branches are closed;
- the next K is allowed by `ROADMAP_LOCK.yaml`;
- `STAGE_DECISIONS.md` records why the lock moved.

Never let a side branch unlock a later K by itself. Side branches merge through
the K integration gate.

## Traceable Plan Coupling

When generating `mian-k`, apply the `traceable-plan` skill rules:

- English-only generated plan files.
- ASCII punctuation only.
- Three-layer structure: audit, execution, reference.
- Thin `EXECUTE.md` for executors.
- Evidence must be tool-grounded or marked unverified.
- No code implementation inside the planning step.

Adapt the traceable-plan output to the K layout above:

- Put the serial trunk in `main`.
- Put allowed concurrent branches in `other`.
- Mark dependency order with numeric prefixes.
- Keep forbidden future work out of executable scope.

## Stop Conditions

Stop and ask the user before changing files when:

- `mian-k` is missing and the user did not ask to plan a new K.
- Both `mian-k` and a plausible active package in `past-k` appear current.
- Completion evidence conflicts with the lock.
- The next K requires a decision not recorded in `blue`.
- The requested action would touch business source code rather than documents.
- The path is ambiguous between `mian-k` and `main-k`.

## Reporting

For inspect reports, be brief and concrete:

```text
Status: COMPLETE_READY_TO_ARCHIVE
Current K: K0
Why: main complete; required other complete; gate PASS.
Blocking issues: none.
Next safe action: archive K0 and update lock to K1.
```

For advance or plan-next work, report changed files and any checks that could
not be run.
