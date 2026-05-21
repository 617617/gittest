---
name: blue-k-other-index
description: Build, refresh, and inspect the progress index for Blue-K packages under docs/mian-k\other. Use when Codex needs to discover minimum executable packages, distinguish package-set roots from leaf packages, create OTHER_MIN_PACKAGE_PROGRESS.md, resume an existing table without overwriting statuses, or choose the next package for a Blue-K other execution queue.
---

# Blue K Other Index

## Purpose

Create and maintain the progress table for minimum executable packages under:

```text
docs/mian-k\other
```

This skill does not execute packages. It only discovers leaf packages, writes
the progress table, and provides queue helpers for the runner skill.

## Key Rule

Treat a directory with `PACKAGE_SET_INDEX.md` as a package set, not as a minimum
executable package. Recurse into its child directories and index the children
that have a package-local execution shape.

Treat a directory as a minimum executable package when it has package-local
contract files and at least one `stage-*` directory with `EXECUTE.md`.

Examples:

- `other\00_backend_route_inventory` has `PACKAGE_SET_INDEX.md`, so it is not a
  minimum executable package.
- `other\00_backend_route_inventory\00_root_urlconf_inventory` is a minimum
  executable package.
- `other\01_front_blue_call_inventory` is itself a minimum executable package.

## Progress Table

Default output:

```text
docs/mian-k\OTHER_MIN_PACKAGE_PROGRESS.md
```

The table is human-readable Markdown with an embedded machine state comment.
Use the bundled script to update it instead of editing table rows by hand.

Statuses:

- `pending`: discovered but not started.
- `running`: handed to the runner or `stage-loop-auto`; resume this before new work.
- `done`: completed and recorded.
- `blocked`: stopped with a blocker that needs attention.
- `skipped`: intentionally not executed.

## Commands

Use the script:

```powershell
python "blue-k-git-baton-testkit/skills/blue-k-other-index/scripts/other_progress.py" build --mian-k "docs/mian-k"
python "blue-k-git-baton-testkit/skills/blue-k-other-index/scripts/other_progress.py" next --mian-k "docs/mian-k"
python "blue-k-git-baton-testkit/skills/blue-k-other-index/scripts/other_progress.py" mark --mian-k "docs/mian-k" --index "00.00" --status running --note "Starting stage-loop-auto."
```

Important operations:

- Run `build` before execution. It creates or refreshes the table while
  preserving existing item state by absolute package path.
- Run `next` to select work. It returns a `running` item first, so interrupted
  execution resumes before new pending work starts. If no item is running, it
  returns the first `pending` item in index order.
- Run `mark` to update one item. Mark `running` before calling an executor.
  Mark `done`, `blocked`, or `skipped` only after the executor result is known.
- Use `mark --reset-history` only to repair an accidental/self-test status. Do
  not erase real execution history without explicit user direction.

## Ordering

Order is top-level branch number, then child package number:

```text
00.00
00.01
01
02.00
02.01
...
```

Resume order is:

1. Existing `running` item.
2. First `pending` item in ascending index order.
3. Stop when no runnable item remains.

If the user explicitly requests reverse or manual order, explain the risk and
then follow the requested order only after the progress table exists.

## Safety

- Do not overwrite `done`, `blocked`, or `running` state during `build`.
- Do not execute `stage-loop-auto` from this skill.
- Do not treat numeric directory names as dependencies by themselves. Use the
  generated index for order and package documents for execution gates.
- If discovery finds no packages, inspect the directory shape before creating a
  blank progress table.
