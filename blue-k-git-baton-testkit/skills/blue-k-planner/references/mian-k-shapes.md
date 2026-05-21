# mian-k Shapes

Load this reference only when creating or validating the on-disk `mian-k`
directory shape.

## Single-Package K Shape

Use only when `topology: single_traceable_package` or when `main_layout:
integration_gate_only` explicitly allows the main gate package to live directly
under `main`.

`main` and every executable `other` branch must be a traceable-plan-style
package, not just a loose `scope.md` / `EXECUTE.md` / `evidence.md` trio.

```text
docs/mian-k
  Kx_INDEX.md
  SOURCE_PLANNING_BRIEF.md
  PACKAGE_GENERATION_MAP.yaml
  AUDIT_MANIFEST.yaml
  BLUE_K_PLAN_AUDIT_REPORT.md
  PRE_REVIEW_REPORT.md
  main\
    00_master.md
    PACKAGE_CHARTER.md
    scope.md
    audit_trace.md
    AUDIT_CONTEXT.md
    HANDOFF_execute.md
    HANDOFF_review.md
    stage-01_<name>.md
    stage-01_<name>\
      scope.md
      evidence.md
      EXECUTE.md
  other\
    00_<branch_name>\
      00_master.md
      PACKAGE_CHARTER.md
      scope.md
      audit_trace.md
      AUDIT_CONTEXT.md
      HANDOFF_execute.md
      HANDOFF_review.md
      stage-01_<branch_name>.md
      PRE_REVIEW_REPORT.md
      stage-01_<branch_name>\
        scope.md
        evidence.md
        EXECUTE.md
    01_<branch_name>\
      00_master.md
      PACKAGE_CHARTER.md
      scope.md
      audit_trace.md
      AUDIT_CONTEXT.md
      HANDOFF_execute.md
      HANDOFF_review.md
      stage-01_<branch_name>.md
      PRE_REVIEW_REPORT.md
      stage-01_<branch_name>\
        scope.md
        evidence.md
        EXECUTE.md
```

For compatibility with older docs, reject this older loose shape as non-strict:

```text
other\
  00_<branch_name>\
    scope.md
    evidence.md
    EXECUTE.md
```

It lacks the traceable-plan audit layer and is not sufficient for new Plan Next
output.

Each branch-level `stage-01_<branch_name>.md` must contain the traceable-plan
stage card sections:

```text
Entry Condition
Exit Target
In-Scope Concerns
Explicit Non-Goals
Recommended Sequencing
Deliverables
Contribution To Final Acceptance
Execution Mode
Source References
```

Each branch-level `HANDOFF_execute.md` must point to only that branch's
`stage-01_<branch_name>\EXECUTE.md`.

Every branch-level `EXECUTE.md` must remain thin and executor-facing. It must
not ask the executor to read the branch `00_master.md` unless escalation is
needed.

Every branch-level `evidence.md` must start as pending, `BLOCK`, or
`OPTIONAL_PENDING`; never mark a new branch as `PASS` before tool-grounded
execution evidence exists.

`main` is the serial trunk. `other` contains ordered parallel branches. Prefix
`other` directories with `00_`, `01_`, `02_` so the user can execute them in
dependency-safe order.

Every `other` branch must declare the branch contract in its branch-level
`scope.md`:

```yaml
branch_id:
mode: required_other | optional_other | future_other
depends_on:
can_run_parallel_with:
must_merge_before:
forbidden:
evidence_required:
```

The branch contract must also be summarized in `Kx_INDEX.md`.

## Package-Set K Shape

Use when `topology: k_package_set` and `main_layout: serial_package_set`.

```text
docs/mian-k
  Kx_INDEX.md
  SOURCE_PLANNING_BRIEF.md
  PACKAGE_GENERATION_MAP.yaml
  AUDIT_MANIFEST.yaml
  BLUE_K_PLAN_AUDIT_REPORT.md
  PRE_REVIEW_REPORT.md
  main\
    PACKAGE_SET_INDEX.md
    00_<package_name>\
      00_master.md
      PACKAGE_CHARTER.md
      scope.md
      audit_trace.md
      AUDIT_CONTEXT.md
      HANDOFF_execute.md
      HANDOFF_review.md
      stage-01_<package_name>.md
      PRE_REVIEW_REPORT.md
      stage-01_<package_name>\
        scope.md
        evidence.md
        EXECUTE.md
    01_<package_name>\
      00_master.md
      PACKAGE_CHARTER.md
      scope.md
      audit_trace.md
      AUDIT_CONTEXT.md
      HANDOFF_execute.md
      HANDOFF_review.md
      stage-01_<package_name>.md
      PRE_REVIEW_REPORT.md
      stage-01_<package_name>\
        scope.md
        evidence.md
        EXECUTE.md
  other\
    00_<parallel_package_name>\
      00_master.md
      PACKAGE_CHARTER.md
      scope.md
      audit_trace.md
      AUDIT_CONTEXT.md
      HANDOFF_execute.md
      HANDOFF_review.md
      stage-01_<parallel_package_name>.md
      PRE_REVIEW_REPORT.md
      stage-01_<parallel_package_name>\
        scope.md
        evidence.md
        EXECUTE.md
    01_<parallel_package_set_name>\
      PACKAGE_SET_INDEX.md
      00_<subpackage_name>\
        00_master.md
        PACKAGE_CHARTER.md
        scope.md
        audit_trace.md
        AUDIT_CONTEXT.md
        HANDOFF_execute.md
        HANDOFF_review.md
        stage-01_<subpackage_name>.md
        PRE_REVIEW_REPORT.md
        stage-01_<subpackage_name>\
          scope.md
          evidence.md
          EXECUTE.md
```

`PACKAGE_SET_INDEX.md` must record package order, dependencies, merge gate,
required packages, optional packages, and stop conditions. The executor must not
skip forward to a later numbered main package unless this index explicitly says
it can run in parallel.

For `other` branch package sets, the branch `PACKAGE_SET_INDEX.md` must also
record the parent branch id, branch mode, branch dependencies, allowed parallel
siblings, merge target, and whether the branch blocks the K gate.
