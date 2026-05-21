Status: GO
StartedAt: 2026-05-21T05:30:00Z
Authorized scenarios: full walkthrough per test-protocol.md scenario table
Trigger: the human will run `bk sync -Scenario <name>` and paste the printed
         ChatCommand into the chat window selected by `WindowMatch`.
Per scenario, write the result file to
`_coord/from-codex/test-results/<scenario>.md` and push one commit per file
with message `test(v0.10): codex result for <scenario>`.
CC will review each result and push `_coord/from-cc/review/<scenario>.md`
within one fetch cycle. Wait for that review only if a scenario fails;
otherwise proceed to the next scenario when the human pastes the next
ChatCommand.
