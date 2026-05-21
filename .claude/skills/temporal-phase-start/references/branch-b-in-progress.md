# Branch B — Phase in progress

Reached when an open Phase exists (artifacts in mailboxes, no
matching `<phase-id>__close.md`) and the latest artifact is NOT a
`close.md`.

This branch reports status and routes to the next lane; it does not
itself write artifacts.

## Step B1 — extract current state

From the diagnosis in SKILL.md Step 3:

- `<phase-id>` — the open Phase ID.
- `<STATE>` — the `BatonNext: <STATE>` value of the most recent
  artifact.
- `<mailbox>/<filename>` — the most recent artifact path.

## Step B2 — look up the next lane

Cross-reference `<STATE>` against the table in
`workflows/temporal-phase/HANDOFF.md` §3.1 "State → lane lookup".

That table only lists Codex-driven states. CC-driven states (those
where the next driver is CC) are:

| Current `<STATE>` | Next driver | Next lane |
|---|---|---|
| `PRE_AUDIT_R{1,2,3}` (CC half not yet delivered) | CC | `temporal-phase-pre-audit-cc` |
| `PRE_AUDIT_SYNTHESIS_R{1,2,3}` | CC | `temporal-phase-pre-audit-synthesize` |
| `BLUEPRINT_REVISION_R{1,2,3}` | CC | `temporal-phase-blueprint-revise` |
| `POSTEXEC_CC_REVIEW` | CC | `temporal-phase-postexec-cc` |
| `SECOND_AUDIT_CC` | CC | `temporal-phase-second-audit-cc` |

(`PRE_AUDIT_R{1,2,3}` is dual-driver — both CC and Codex must
deliver. If the Codex half is delivered but the CC half is not, it
is CC's turn.)

## Step B3 — emit the status block

```text
temporal-phase status:
  Open Phase:       <phase-id>
  Current state:    <STATE>
  Latest artifact:  <mailbox>/<filename>
  Next driver:      <CC | Codex>
  Next action:      <one sentence describing what should happen next>
  Next lane skill:  <lane name, e.g. temporal-phase-pre-audit-cc>
```

## Step B4 — route on next driver

### If next driver is CC

Offer to proceed now or wait:

> The baton is at `<STATE>`. CC's `<lane>` lane is ready to run.
> Proceed now or wait?

If the user says proceed: open the lane SKILL
(`workflows/temporal-phase/skills/<lane>/SKILL.md`) and follow its
procedure — including its `## Push procedure` section
(commit-before-rebase) for the actual push.

### If next driver is Codex

Emit a short reminder message the user can paste to Codex:

```text
The baton is at <STATE>. Please run /temporal-phase-codex-sync to
catch up; it will route you to the right lane (probably
<lane name from HANDOFF table>). Open that lane:
  workflows/temporal-phase/skills/<lane name>/SKILL.md
Read it, produce the corresponding artifact in
workflows/temporal-phase/_coord/from-codex/, then commit + push
following the lane's "Push order" / "Push procedure" section.
```

CC then takes no further action; the next Monitor event on
`from-codex/` will pick up Codex's push when it lands.
