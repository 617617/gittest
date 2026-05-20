# HANDOFF: Codex Workflows for Claude

This file explains how Claude Code should coordinate with Codex through
the Blue-K Git baton protocol.

## Two Entries

```text
bk sync   - shell command; read-only remote inspection
/bk work  - AI chat command; executes BATON assignment
```

## When Claude Owns

- `blue-k-planner`: Plan next package, write plan docs.
- `blue-k-plan-audit`: Audit planner output, write audit report.
- `blue-k-consensus` (plan): Synthesize plan after audit PASS/WARN.

## When Codex Owns

- `blue-k-main-runner`: Execute main packages.
- `blue-k-other-runner`: Execute other packages.
- `blue-k-consensus` (code): Review code after runner checkpoint.

## Consensus Gates

- Plan must pass consensus before runner starts.
- Code must pass consensus before runner finalizes.

## Do Not

- Do not select packages in the wrapper.
- Do not write progress tables in the wrapper.
- Do not override lower-gate BLOCK.
- Do not auto-merge, auto-rebase, or auto-takeover.