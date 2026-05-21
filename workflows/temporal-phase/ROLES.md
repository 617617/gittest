# temporal-phase — Roles & Step Matrix

The flow in source-document §2–§10 broken into steps with **driver**,
**input**, **product**, and **destination mailbox** marked per step.
"Driver" is the AI primarily responsible for that step; when both Codex
and CC appear, both must produce their own deliverable.

Conventions:

- Mailbox locations:
  - CC → Codex write path = `workflows/temporal-phase/_coord/from-cc/`
  - Codex → CC write path = `workflows/temporal-phase/_coord/from-codex/`
- Filename convention: `<phase-id>__<step-tag>.md`, e.g.
  `phase-12__blueprint.md`.
- The first line of every product file must be `BatonNext: <STATE>`,
  naming the next baton state (see `BATON.schema.md`). That line is the
  explicit transition signal.

## Step matrix

| # | Step | Driver | Input | Product | Mailbox |
|---|------|--------|-------|---------|---------|
| 0 | Phase kickoff (start signal) | CC | user-supplied phase-id + goal + (optional) source-doc anchor | `<phase-id>__kickoff.md` (PhaseId / Goal / SourceAnchor / PreviousPhaseClose), `BatonNext: DRAFTING_BLUEPRINT` | from-cc/ |
| 1 | Create Phase execution blueprint | Codex | `<phase-id>__kickoff.md` + previous Phase close.md + source document | `<phase-id>__blueprint.md` (goal / scope / allowed files / validation / artifacts / risk) | from-codex/ |
| 2 | CC-side pre-execution audit | CC | blueprint | `<phase-id>__pre-audit-cc-r<N>.md` | from-cc/ |
| 3 | Codex-side pre-execution audit | Codex | blueprint | `<phase-id>__pre-audit-codex-r<N>.md` | from-codex/ |
| 4 | CC synthesizes pre-execution audit | CC | both pre-audit files | `<phase-id>__pre-audit-synthesis-r<N>.md` (Adopted / Recorded / Out-of-scope) | from-cc/ |
| 5 | CC repairs blueprint | CC | synthesis | `<phase-id>__blueprint-revision-r<N>.md` | from-cc/ |
| 6 | Decide whether to re-loop | CC | revised blueprint + remaining findings | `<phase-id>__pre-audit-verdict-r<N>.md` (ACCEPTED / RELOOP / ABANDON) | from-cc/ |
| 7 | Phase execution | Codex | accepted blueprint | `<phase-id>__execution-report.md` (changes / validation / residual risks / evidence / next-step suggestions) | from-codex/ |
| 8 | Codex multi-subagent integrated review | Codex | execution report | `<phase-id>__postexec-subagent-review.md` (multi-subagent findings) | from-codex/ |
| 9 | CC post-execution independent review | CC | execution report | `<phase-id>__postexec-cc-review.md` | from-cc/ |
| 10 | Codex synthesizes post-execution audit | Codex | §8 + §9 | `<phase-id>__postexec-synthesis.md` (Adopted / Recorded / Out-of-scope) | from-codex/ |
| 11 | Codex absorbs and repairs | Codex | synthesis | `<phase-id>__postexec-fix.md` (changes + validation + conclusion) | from-codex/ |
| 12 | Decide whether to run second dual audit | Codex | repair size / risk assessment | `<phase-id>__second-audit-decision.md` (YES / NO + rationale) | from-codex/ |
| 13 | (Optional) Second dual audit — CC | CC | §11 fix result | `<phase-id>__second-audit-cc.md` | from-cc/ |
| 14 | (Optional) Second dual audit — Codex subagents | Codex | §11 fix result | `<phase-id>__second-audit-codex.md` | from-codex/ |
| 15 | (Optional) Second dual audit synthesis & fix | Codex | §13 + §14 | `<phase-id>__second-audit-fix.md` | from-codex/ |
| 16 | Phase close | Codex | completion-criteria check | `<phase-id>__close.md` (COMPLETED or BLOCKED + reason + follow-up ownership) | from-codex/ |

## Role boundaries (from source document + testkit experience)

- **Codex** owns all "creative output + Codex-led multi-subagent review":
  blueprint, execution, post-execution review, synthesis, repair, close.
  Codex is the final repair owner of every Phase.
- **CC** owns all "independent-viewpoint audit + cross-side synthesis":
  pre-execution audit, pre-execution synthesis, blueprint repair,
  post-execution audit, (optional) second-dual-audit CC side. CC is the
  closure judge of the pre-execution loop.
- Subagents stay in their source-document §7 role: they emit opinions,
  they do not replace the main driver in the final decision.

## Failure / blocked handling

- After three rounds of pre-execution audit, if blockers remain → write
  `pre-audit-verdict-r3.md` with verdict `ABANDON`; baton enters
  `BLOCKED_BLUEPRINT`; this Phase is not forced into execution.
- After the second dual audit, if blockers remain → write `close.md`
  with `BLOCKED`, record reason and follow-up ownership; baton enters
  `BLOCKED_POSTEXEC` (no further loops).
