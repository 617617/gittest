# <PRESET> — Roles & Step Matrix

Conventions:

- Mailbox locations:
  - CC → Codex write path = `workflows/<preset>/_coord/from-cc/`
  - Codex → CC write path = `workflows/<preset>/_coord/from-codex/`
- Filename pattern: `<unit-id>__<step-tag>.md`.
- The first line of every product file must be `BatonNext: <STATE>`,
  naming the next baton state (see `BATON.schema.md`).

## Step matrix

| # | Step | Driver | Input | Product | Mailbox |
|---|------|--------|-------|---------|---------|
| 1 | `<step description>` | `Codex \| CC` | `<input artifacts>` | `<unit-id>__<step-tag>.md` | `from-codex/ \| from-cc/` |
| 2 | ... | ... | ... | ... | ... |
| N | Unit close | Codex | all prior products | `<unit-id>__close.md` | from-codex/ |

## Role boundaries

- **Codex** owns: `<list of creative / executive responsibilities>`.
- **CC** owns: `<list of review / synthesis / closure-judge
  responsibilities>`.
- Subagents emit opinions; they do not replace the main driver in any
  final decision.

## Failure / blocked handling

- `<condition that leads to BLOCKED_<reason> + which file is written and
  which state it carries in BatonNext>`.
