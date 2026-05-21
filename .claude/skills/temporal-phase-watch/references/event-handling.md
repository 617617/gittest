# Event handling — what to do when the Monitor fires

The persistent Monitor armed in SKILL.md step 5 emits lines of the form
`NEW_FROM_CODEX: <filename>` whenever a new artifact lands in
`workflows/temporal-phase/_coord/from-codex/`. CC reacts per the
filename's step-tag, as follows:

| Step-tag | Reaction |
|----------|----------|
| `blueprint`, `pre-audit-codex-r<N>`, `postexec-subagent-review`, `postexec-synthesize`, `postexec-fix`, `second-audit-codex`, `second-audit-fix` | Process per the BATON state machine — read the artifact, look up the next lane in HANDOFF §3.1, run that lane. |
| `second-audit-decision` | Read; advance per the decision (YES/NO). |
| `execution-report` | Process per the state machine (POSTEXEC_SUBAGENT_REVIEW is Codex's turn — CC waits). |
| **`close`** | **Run `/temporal-phase-start` Branch C logic.** Read `workflows/_active.md` `ChainMode:`, read the close.md `NextPhasePlan:` block, then apply the Branch C decision tree (auto-advance / confirm / off / hard-stop). This is how Phase chaining actually fires: the Monitor's close.md event triggers the chain decision. |

If you are uncertain what reaction applies, invoke
`/temporal-phase-start` — it consolidates all the diagnostic logic.

In every case, the read of the artifact's first non-empty line
`BatonNext: <STATE>` is what drives the next-lane lookup in
`workflows/temporal-phase/HANDOFF.md` §3.1. Step-tag → reaction
above is a shortcut; `BatonNext` is the authoritative signal.
