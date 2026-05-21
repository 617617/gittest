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

The `Owner` column names the lane runner and, for consensus, the synthesizer.
It does NOT mean only one AI looks at the artifact — see the next section.

## Review vs Synthesis vs Repair

Plan and code consensus require **independent review opinions from both AIs**.
Only the synthesis step and the follow-up repair are single-owner.

| Stage | Independent reviews | Synthesizer | Repair / fix owner |
| --- | --- | --- | --- |
| Plan consensus (after `blue-k-plan-audit` PASS or accepted WARN) | CC + Codex | CC | CC (`blue-k-planner`) |
| Code consensus (after runner checkpoint) | CC + Codex | Codex | Codex (`blue-k-main-runner` / `blue-k-other-runner` fix lane) |

Rules:

- `blue-k-plan-audit` (CC) is the structured pre-gate. The cross-AI step is
  `blue-k-consensus` of kind `plan`, where both sides leave an independent
  plan-review opinion before CC synthesizes.
- `planner_repair` decisions return the plan to `blue-k-planner` (CC).
  `fix_required` decisions return code to the runner fix lane (Codex).
- The synthesizer reads both reviews to produce `accepted` / `fix_required` /
  `planner_repair` / `human_blocked`. Synthesis must not weaken a lower gate.
- The repair owner reads both review opinions plus the synthesis decision
  before editing.

This keeps the edit owner aligned with strength — CC on plan structure and
coordination prose, Codex on test/code evidence and fix loops — while still
folding the other side's independent review into every decision.

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