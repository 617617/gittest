# Workflow runtime state (informational + chain control)

PrimaryFocus: temporal-phase
ChainMode: confirm

## `PrimaryFocus` — informational only

Records which workflow has the user's primary focus right now, as a
hint for new conversations. It is **not** read by any watcher,
verifier, or hook on its own to gate enablement. Multiple workflows
may be enabled in parallel — every workflow with a subdirectory under
`workflows/` (or `blue-k-git-baton-testkit/` for the testkit) is
enabled by virtue of existing. Each has its own watcher skill
(`/temporal-phase-watch`, `/bk-watch`, etc.) that arms independently
and only touches its own coord directory.

## `ChainMode` — controls Phase chaining for the temporal-phase preset

When a `<phase-id>__close.md` lands with `BatonNext: COMPLETED` and a
populated `NextPhasePlan:` block, CC's behaviour is decided by this
field:

| Value     | Behaviour |
|-----------|-----------|
| `auto`    | CC auto-archives the closed Phase, writes the next kickoff per `NextPhasePlan`, commits, and pushes. No user confirmation. Use when the chain is well-trusted (e.g., a smoke-test sequence). |
| `confirm` (default) | CC reports the close + the proposed next plan and asks the user "advance to `<NextPhaseId>` with this goal? [yes / edit / no]". On `yes`, runs the same actions as `auto`. On `edit`, prompts for changes before writing. On `no`, stops. |
| `off`     | CC reports the close and stops. The user must invoke `/temporal-phase-start` explicitly to advance. |

Safety overrides — applied **regardless** of `ChainMode`:

- A `BatonNext: BLOCKED_*` close **always** stops the chain.
- A missing or malformed `NextPhasePlan:` **always** stops the chain
  (treat as "chain naturally ends").
- A `NextPhaseId:` that collides with an existing phase-id (live or
  archived) **always** stops the chain with a loud error.

To pause an in-flight chain at any time: edit the `ChainMode:` line to
`off` and commit; the next close.md will not auto-advance.
