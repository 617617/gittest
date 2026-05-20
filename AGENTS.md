# AGENTS

This file describes the AI agents working on this repository.

## Blue-K Git Baton Roles

| Role | Owner | Lane |
| --- | --- | --- |
| Planner | CC | blue-k-planner |
| Plan Audit | CC | blue-k-plan-audit |
| Main Runner | Codex | blue-k-main-runner |
| Other Runner | Codex | blue-k-other-runner |
| Consensus | Mixed | blue-k-consensus |

## Entry Points

```text
bk sync   - shell-side read-only sync and decision sheet
/bk work  - Claude chat-side execution entry
```

## Truth Sources

- Control truth: `origin/blue-k/coordination:.blue-k/BATON.yaml`
- Business truth: work branch (`blue-k/<task>`)

## Workflow

1. Human runs `bk sync` in shell
2. `bk sync` prints `NEXT:` with the correct AI window
3. Human sends `/bk work` in that window
4. AI executes one assignment and pushes safe point
5. AI prints next `bk sync` instruction