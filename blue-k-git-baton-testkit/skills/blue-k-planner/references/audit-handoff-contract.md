# Audit Handoff Contract

Load this reference only in Plan Next Mode when preparing
`AUDIT_MANIFEST.yaml`, writing package `AUDIT_CONTEXT.md`, or invoking
`blue-k-plan-audit`.

## AUDIT_MANIFEST.yaml

Before any pre-execution review, prepare the handoff that lets
`blue-k-plan-audit` review each minimal executable package with precise context.

Write:

```text
docs/mian-k\AUDIT_MANIFEST.yaml
```

The manifest must list every minimal package that `stage-loop-auto` could
execute. Package-set router directories are not executable; their numbered child
packages are executable.

Required manifest fields:

```yaml
k_id:
generated_by: blue-k-planner
generated_at:
blue_lock_refs:
  roadmap_lock:
  topology:
  source_charter:
source_planning_brief:
package_generation_map:
packages:
  - package_id:
    package_path:
    executable: true
    package_kind: main | other | other_subpackage
    parent_package_set:
    stage_execute_path:
    origin:
      k_id:
      roadmap_lock_ref:
      topology_ref:
      source_planning_brief_ref:
      generation_assignment_ref:
      parent_branch_id:
    purpose:
    entry_condition:
    exit_target:
    dependencies:
    allowed_parallel_with:
    merge_target:
    required_for_k_gate: true
    forbidden:
    source_refs:
    source_discovery_commands:
    bdd_tdd_marker:
      source_ref:
      bdd:
      tdd:
      bdd_min_scenarios:
      bdd_test_mapping_required:
      audit_check:
    test_organization:
      source_ref:
      test_domain:
      target_test_paths:
      existing_tests_to_extend:
      flat_test_exception:
      first_verification_command:
    boundary_five_questions:
      what_was_replaced:
      what_was_preserved:
      what_was_frozen:
      truth_source:
      exit_condition:
    audit_context_path:
    review_report_path:
```

## AUDIT_CONTEXT.md

For every executable package listed in the manifest, write:

```text
<package_path>\AUDIT_CONTEXT.md
```

`AUDIT_CONTEXT.md` is a precise slice, not a blueprint dump. It must include:

```text
Origin:
Purpose:
Package Boundary:
Dependencies:
Source And Blueprint References:
BDD/TDD Marker:
Test Organization:
Source Grounding:
Boundary Five Questions:
Forbidden Work:
Reviewer Instructions:
```

The context must let an audit subagent understand where this package came from,
why it exists, what it must accomplish, what it depends on, and what it must not
touch. It must include the `PACKAGE_GENERATION_MAP.yaml` assignment id so the
audit skill can trace the package back to the exact package-planning subagent
assignment. It must not include unrelated K packages or broad blueprint prose.

If `AUDIT_MANIFEST.yaml` or any package `AUDIT_CONTEXT.md` is missing, the plan
is `NON_STRICT_PACKAGE`.

## Blue K Plan Audit Invocation

After the draft `mian-k` plan is written, passes the local shape check, and has
`AUDIT_MANIFEST.yaml` plus package `AUDIT_CONTEXT.md` files, invoke the local
`blue-k-plan-audit` skill.

`blue-k-plan-audit` is responsible for spawning one documentation-only subagent
per minimal executable package. Each package review subagent must use the local
`pre-doc-review` skill.

The main planner must give `blue-k-plan-audit` only:

- the target path `docs/mian-k`;
- the current K ID;
- the expected K layout from this skill;
- the `AUDIT_MANIFEST.yaml` path;
- the instruction to use `blue-k-plan-audit`;
- the instruction that package review subagents use `pre-doc-review`;
- the instruction to edit documentation only and never source code.

The audit skill must:

- discover every minimal `stage-loop-auto` executable package;
- verify the manifest and context slices match the package tree;
- spawn one `pre-doc-review` subagent per executable package;
- ensure each subagent receives only that package's `AUDIT_CONTEXT.md`, local
  package docs, local `PACKAGE_CHARTER.md`, and direct parent index snippets;
- write package-level `PRE_REVIEW_REPORT.md` files;
- fix `WILL_FAIL` documentation defects inside the package only;
- record doc fixes in the relevant package `audit_trace.md`;
- write `docs/mian-k\BLUE_K_PLAN_AUDIT_REPORT.md`;
- update `AUDIT_MANIFEST.yaml` with package review status;
- leave source code untouched.

The main agent must review the audit result before finalizing:

- If any `WILL_FAIL` finding remains, report `PLAN_REVIEW_BLOCKED`.
- If only `MAY_FAIL` or `SUGGESTION` findings remain, keep the plan but list
  them in the final report.
- If the audit skill edited docs, re-read changed files that affect execution
  order, branch dependencies, or lock compliance.
- If the aggregate report says any package was reviewed directly by the main
  agent instead of a package subagent, the plan is not strict-ready.
- If `BLUE_K_PLAN_AUDIT_REPORT.md` is missing, the plan is not strict-ready.
