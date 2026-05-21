Status: GO
StartedAt: 2026-05-21T06:25:00Z
BaseCommit: 6a5e3ed
DecisionRevision: 2
Walkthrough: 2

Authorized scenarios: full queue per autopilot-decision.md ScenarioQueue
Mode: B autopilot — Codex feeds itself via `bk.ps1 sync -Scenario <name>`
ReviewGate: enabled — Codex must observe CC review of scenario N before
  pushing scenario N+1 (see autopilot-decision.md for gate details)

Per scenario, write the result file to
`_coord/from-codex/test-results/<scenario>.md` and push one commit per
file with message `test(v0.10): codex result for <scenario>`. Each
result file must record `DecisionRevision: 2`.

CC will fetch each result and write a paired
`_coord/from-cc/review/<scenario>.md` within one fetch cycle (currently
60s via the bk-watch Monitors). Wait for it before the next scenario.

Lessons from walkthrough-1 are at
`blue-k-git-baton-testkit/references/walkthrough-1-lessons.md` — read
them before starting; they describe the push-race recovery pattern and
the cross-document fix to row 8 of `test-protocol.md`.
