---
name: pre-doc-review
description: Standalone feasibility review for future step execution documents before implementation. Use when Codex is asked to "提前审核", "pre-review", "review step N", or review a planned future traceable-plan/stage-loop step for document-level executor failure risks while ignoring whether upstream steps have completed.
---

# Pre Doc Review

Review a future step's execution documents early, so document defects can be fixed before the executor reaches that step.

## Dirty Worktree Checkpoint Gate

Whenever this skill or its calling protocol requires a clean worktree, first
inspect `git status --short --branch` in the repository containing the reviewed
future-step documents. If the worktree is dirty, create exactly one
full-repository checkpoint commit before continuing:

```powershell
git add -A
git commit -m "chore(worktree): checkpoint before pre-doc-review"
git status --short --branch
```

Continue only if the follow-up status is clean. If the commit fails or the
worktree remains dirty, stop with:

```text
PRE_DOC_REVIEW_BLOCKED_DIRTY_AFTER_CHECKPOINT
```

Do not treat a dirty worktree as an immediate blocker until this checkpoint
attempt has been made.

## Intent

Assume upstream steps will deliver what their documents promise. Do not report "upstream step not done yet" as a finding.

Focus on whether the executor will fail because the target documents themselves are wrong, incomplete, inconsistent, or misleading. Typical risks include invalid SQL types, missing imports, broken references, naming violations, contract inconsistencies, impossible file paths, and mismatched audit/scope/execute instructions.

## Inputs

Use the target step path from the user request. If it is omitted, infer it from the current repository context only when unambiguous; otherwise ask for the target step path.

Read the target step's execution documents, especially:

- `EXECUTE.md`
- `scope.md`
- files under `back/`, including `master`, `scope`, and `audit_trace` documents when present

Also read shared context that affects interfaces or contracts, when present:

- `SHARED_VOCABULARY`
- `SQL_VERSION_REGISTRY`
- contract documents
- `ANCHOR_REGISTRY`
- prior step `audit_trace` files needed for interface awareness

## Workflow

1. Gather target documents and shared context.
2. Choose review dimensions that fit the step. Examples: SQL correctness, API/contract consistency, file path and import feasibility, naming and vocabulary compliance, integration sequencing, audit/scope/execute alignment.
3. Spawn subagents for the selected review dimensions. Subagent review is mandatory: every dimension must be assigned to a subagent with non-overlapping ownership. If subagents cannot be spawned, stop with `PRE_DOC_REVIEW_BLOCKED_NO_SUBAGENT`; do not perform the same review directly in the main agent.
4. Collect findings in a flat table with columns: `#`, `File`, `Finding`, `Severity`, `Fix`.
5. Write or update `target-step/back/PRE_REVIEW_REPORT.md`, grouped by severity.
6. Fix `WILL_FAIL` findings in the target step's documentation when the user requested migration/execution, or when the request clearly asks to perform the review end to end. Record the fix in the target step's audit trace when such a document exists.

## Severity

- `WILL_FAIL`: the executor will hit a compile error, runtime error, missing file/reference, or contract breach.
- `MAY_FAIL`: the executor may fail depending on branch conditions, environment, or unresolved ambiguity.
- `SUGGESTION`: improvement that does not create a direct failure risk.

Include a cross-agent or cross-dimension conflict section when different review passes disagree on the same item.

## Hard Rules

- Do not flag incomplete upstream execution as a finding.
- Keep each review dimension focused and avoid duplicate findings.
- Only change documentation during this workflow. Never edit source code.
- Prioritize concrete executor failure risks over stylistic preferences.
