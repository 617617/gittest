# AI Chat Contract — Blue-K Baton v0.10

Status: normative
Applies to: `blue-k-planner`, `blue-k-plan-audit`, `blue-k-main-runner`,
`blue-k-other-runner`, `blue-k-other-index`, and any future Blue-K lane skill
invoked through `/bk work`, `/bk resume`, or `/bk takeover`.

This document is the single source of truth for the in-chat behavior the v0.10
forget-safe rule depends on. Each lane skill restates the three rules inline
and links here for the full text. Lane-specific skills may add domain rules on
top of these three; none of those domain rules may relax this contract.

## Rule 1 — Self-announce on first reply

On the very first reply of any new invocation, before reading repository state,
before acting, and before calling any tool, the AI must print:

```text
I am <CC|Codex>. Lane: <lane-or-owned-lane-set>.
```

- `<CC|Codex>` is the runtime identity. Claude side prints `CC`; Codex side
  prints `Codex`.
- `<lane>` is one of:

  ```text
  blue-k-planner
  blue-k-plan-audit
  blue-k-main-runner
  blue-k-other-runner
  blue-k-other-index
  ```

- If the skill owns more than one lane in this invocation, list them
  space-separated on the same line.

The human matches this line against the `WindowMatch` hint printed by `bk sync`
to confirm the paste landed in the correct window.

## Rule 2 — Refuse wrong-window input

If `/bk work`, `/bk resume`, or `/bk takeover` was pasted but the latest
`bk sync` selected a different chat (different runtime, different lane, or no
chat command at all), the AI must:

1. Acknowledge the wrong-window paste.
2. Refuse to acquire a lease, edit files, or invoke any Blue-K skill.
3. Reprint the target window description and the exact command the human
   should paste there. Use the `ChatTarget`, `WindowMatch`, and `ChatCommand`
   text from the most recent `bk sync` verbatim when available.

A wrong-window invocation must end without progressing BATON state.

For `/bk takeover` specifically, no destructive recovery may begin before the
human types `yes, abandon` in this chat. The first reply may show takeover
basis evidence; it must not commit, push, or write progress tables before that
confirmation.

## Rule 3 — Finalize with a fixed closing line

After completing one safe assignment, the AI must:

1. Update and push the work branch and coordination branch atomically when the
   remote supports it:

   ```text
   git push --atomic origin <work-branch> blue-k/coordination
   ```

   If the remote cannot guarantee atomic push, stop with
   `ATOMIC_PUSH_UNAVAILABLE`. Do not push, do not mark the assignment complete.

2. Write the next holder into `BATON.yaml` on the coordination branch before
   signing off.

3. End the reply with exactly:

   ```text
   Done. Now run: bk sync
   ```

   The closing line is byte-for-byte fixed: no variant punctuation, no emojis,
   no trailing notes. It must be the final non-empty line of the reply.

The AI must not chain into the next package, next lane, or next assignment in
the same invocation, even if BATON state would allow it. The human re-enters
through `bk sync`.

## Failure modes and required behavior

| Symptom | Required AI behavior |
|---|---|
| First reply omits the Rule 1 line | Self-correct in the next reply; restate Rule 1, then proceed |
| Wrong-window `/bk` verb pasted | Apply Rule 2; do not advance BATON |
| Atomic push unavailable | Print `ATOMIC_PUSH_UNAVAILABLE`; do not push; do not print Rule 3 closing |
| Work finished but next holder not written into BATON | Treat assignment as incomplete; do not print Rule 3 closing |
| State would allow starting the next package | Refuse; print Rule 3 closing and stop |
| `/bk takeover` first reply before `yes, abandon` | Show evidence only; no commits, pushes, or progress writes |

## Relation to other documents

- `references/protocol-v0.10.md` — the normative protocol; this contract
  elaborates its "AI Chat Contract" section.
- `scripts/bk_sync_sim.py` and `scripts/bk.ps1` — produce the
  `Holder`, `ChatTarget`, `WindowMatch`, and `AfterWork` lines the human uses
  to verify Rules 1 and 2.
- `references/autonomy-proposal.md` — v0.11 draft. Until v0.11 is active, the
  rules above apply unchanged; v0.11 may extend them, never relax them.
