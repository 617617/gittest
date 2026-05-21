# _coord — temporal-phase mailbox

This directory is the git-tracked mailbox for the `temporal-phase`
preset. It is fully independent from `blue-k-git-baton-testkit/_coord/`.

- `from-cc/` — products CC sends to Codex (pre-execution audit,
  synthesis, repair, post-execution audit, etc.).
- `from-codex/` — products Codex sends to CC (blueprint, execution
  report, subagent review, synthesis, repair, close, etc.).

Filename convention: `<phase-id>__<step-tag>.md` (see Step Matrix in
`../ROLES.md`). Every product's first line must be `BatonNext: <STATE>`,
explicitly declaring the next state to which the state machine should
transition (state names in `../BATON.schema.md`).
