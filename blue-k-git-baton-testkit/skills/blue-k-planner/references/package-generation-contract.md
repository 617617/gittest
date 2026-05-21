# Package Generation Contract

Load this reference only in Plan Next Mode when writing or validating
`PACKAGE_GENERATION_MAP.yaml`, package-planning subagent assignments, or package
planning subagent return checks.

## PACKAGE_GENERATION_MAP.yaml

Before spawning package-planning subagents, write:

```text
docs/mian-k\PACKAGE_GENERATION_MAP.yaml
```

Required fields:

```yaml
k_id:
generated_by: blue-k-planner
source_planning_brief:
topology:
main_layout:
other_layout:
assignments:
  - assignment_id:
    package_id:
    package_path:
    write_owner: package-planning-subagent
    package_kind: main | other | other_subpackage
    parent_package_set:
    traceable_plan_required: true
    context_slice:
      context_policy: sufficient_context_over_minimal_context
      purpose:
      entry_condition:
      exit_target:
      dependencies:
      allowed_parallel_with:
      merge_target:
      forbidden:
      source_required: true
      source_refs:
      source_discovery_commands:
      blueprint_refs:
      source_charter_required: true
      bdd_tdd_marker:
        source_ref:
        bdd:
        tdd:
        bdd_min_scenarios:
        bdd_test_mapping_required:
        audit_check:
      test_organization:
        source_ref: TEST_ORGANIZATION_CHARTER.md
        test_domain:
        target_test_paths:
        existing_tests_to_extend:
        flat_test_exception:
        first_verification_command:
      boundary_five_questions_required: true
      boundary_five_questions:
        what_was_replaced:
        what_was_preserved:
        what_was_frozen:
        truth_source:
        exit_condition:
    required_outputs:
      - 00_master.md
      - PACKAGE_CHARTER.md
      - scope.md
      - audit_trace.md
      - AUDIT_CONTEXT.md
      - HANDOFF_execute.md
      - HANDOFF_review.md
      - stage-01_<name>.md
      - stage-01_<name>\scope.md
      - stage-01_<name>\evidence.md
      - stage-01_<name>\EXECUTE.md
```

## Package Planning Subagent Input

For each package-planning subagent, provide only:

- the assignment entry from `PACKAGE_GENERATION_MAP.yaml`;
- the relevant `SOURCE_PLANNING_BRIEF.md` excerpt;
- the relevant `ROADMAP_LOCK.yaml` and `K_STAGE_TOPOLOGY.md` snippets;
- the relevant `SOURCE_ORGANIZATION_CHARTER.md` capsule;
- directly relevant previous K evidence from `past-k` or `K_PROGRESS_INDEX.md`;
- enough source paths, commands, and local behavior notes to avoid guessing;
- the instruction to use `traceable-plan` structure rules;
- the instruction to read relevant source code before writing package docs;
- the relevant `BDD_TDD_MARKERS.md` entry and the instruction to place it in the
  package stage docs before implementation steps;
- the relevant `TEST_ORGANIZATION_CHARTER.md` capsule when the package creates
  or edits tests;
- the instruction to answer the five questions in the package audit layer and
  `AUDIT_CONTEXT.md`;
- the instruction to write only its assigned package path.

## Package Planning Subagent Return

Each package-planning subagent must return:

```text
Assignment ID:
Package path:
Files written:
Traceable-plan structure check:
Charter injection check:
Source files inspected:
Boundary five questions:
AUDIT_CONTEXT.md path:
Open blockers:
```

## Main Agent Verification

After package-planning subagents return, the main agent must re-read generated
package docs and verify:

- no subagent wrote outside its assigned path;
- each minimal package has the required traceable-plan-style files;
- `EXECUTE.md` remains thin and executor-facing;
- `PACKAGE_CHARTER.md` exists and is referenced;
- BDD/TDD markers match `BDD_TDD_MARKERS.md` and required BDD/TDD appears before
  implementation steps;
- test-writing packages declare test domain, target test paths, and flat-test
  exceptions when needed;
- `AUDIT_CONTEXT.md` matches the assignment and does not include unrelated
  blueprint context;
- source files inspected are recorded and sufficient for the package;
- the five questions are answered or explicitly marked `Not applicable` with a
  reason;
- dependencies and allowed parallel relationships match the lock.
