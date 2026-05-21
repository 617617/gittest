# Blue-K Baton — Human Ergonomics Proposal

Status: draft
Author: CC (chat)
Target protocol: v0.9 → v0.10
Scope: reduce what a human must remember to keep the baton flowing correctly.

## Guiding Principle

> For every flag, role name, and state transition, ask: **"What happens if the human forgets?"**
> If the answer is "the protocol breaks", the human shouldn't have to remember it.

Convert *recall* into *recognition*: the system shows the next action; the human never reconstructs it from memory.

## Current Memory Load (ranked by friction)

| # | What the human must remember | Today | Failure mode |
|---|---|---|---|
| 1 | Which AI chat window to switch to | Reads `NEXT: In Codex chat` and switches manually | Paste into the wrong window → BATON drifts from reality |
| 2 | Long flag chains | Types `/bk work --takeover --from-last-pushed --abandon-unpushed-ok` | One typo / missing flag → wrong semantics |
| 3 | Re-run `bk sync` after the AI finishes | No prompt or alarm | Forgets → next handoff stalls |
| 4 | Which AI owns which lane | Holds the CC/Codex ↔ planner/runner map in head | Mix-up over time, especially on resume |
| 5 | When to use `--resume` vs plain vs `--takeover` | Reads BATON state and decides | Wrong choice → unpushed work discarded |

## Priority 1 — Cheap wins (touch `bk.ps1` + docs only)

### P1.1  `bk sync` copies the next chat command to the clipboard
```
NEXT: /bk work --resume
(copied to clipboard — paste into the chat whose lane line says "blue-k-main-runner")
```
Removes burden **#2** entirely. The human reads, switches, pastes — no typing.

Implementation sketch (PowerShell):
```powershell
Set-Clipboard -Value $nextCommand
Write-Host "(copied to clipboard)"
```

### P1.2  Fold long flag chains into single verbs
| Old | New |
|---|---|
| `/bk work --takeover --from-last-pushed --abandon-unpushed-ok` | `/bk takeover` |
| `/bk work --resume` | `/bk resume` |
| `/bk work` (normal start) | `/bk work` (unchanged) |

Dangerous confirmations move to an **interactive prompt inside the AI chat**, shown by the AI immediately after the verb is received:

```
You asked to take over from the last pushed checkpoint.
This will discard 2 unpushed commits on origin/blue-k/feat-x:
    abc1234  WIP add parser
    def5678  WIP fix edge case
Type "yes, abandon" to proceed, or "cancel".
```

Removes burden **#5**: the human no longer encodes "I accept the risk" into a flag string; they confirm against an explicit, current diff.

### P1.3  Every AI chat self-announces its role on first reply
```
I am CC.   Lane: blue-k-planner / blue-k-plan-audit.
```
`bk sync` then says:

```
NEXT: paste /bk work into the chat whose first line says "Lane: blue-k-main-runner".
```

Removes burden **#4**: the human matches strings instead of recalling "which window was Codex?".

### P1.4  AI's final line is always the next shell command, plus a bell
```
Done. Now run:  bk sync
^G  (terminal bell / OS notification)
```
Plus: the AI writes the next holder into BATON before signing off, so the next `bk sync` answers in O(1).

Removes burden **#3**: the human is *pulled* back to the loop, not relying on memory.

### P1.5  `bk sync` always prints a 3-line "where are we" header
```
Task:    blue-k/feat-parser
Holder:  Codex (blue-k-main-runner)   running 4m12s
Last:    CC plan-audit PASS @ a1b2c3d  (12m ago)
```
Even if the human walks away for an hour, one command rehydrates full context.

## Priority 2 — Medium effort, large payoff

### P2.1  Single verb `bk go` replaces the read-switch-paste dance
`bk go` does: `sync` → decide → push the command into the target AI chat directly (via that client's CLI/API/stdin if available; otherwise deep-link the window with the command pre-filled).

When achievable, this collapses the entire interaction surface to one word: **`bk go`**.

### P2.2  Shrink the set of human-gated handoffs
Currently every baton handoff requires a human relay. Define a **safe auto-advance whitelist**:

| Transition | Today | Proposed |
|---|---|---|
| CC plan-audit `PASS` → main runner start | human relays | auto-advance |
| Runner checkpoint → code consensus request | human relays | auto-advance |
| Anything → `--takeover` | human relays | **keep human-gated** |
| Anything → consensus gate decision | human relays | **keep human-gated** |
| Any `BLOCK` resolution | human relays | **keep human-gated** |

Roughly: real decisions are ~3 categories; relays are dozens. Cutting relays shrinks human burden by an order of magnitude while keeping every genuine judgment call human-gated.

Requires:
- A signed "auto-advance permitted from state X to state Y" table in `protocol-v0.10.md`.
- Atomic push of `(work-branch, coordination-branch)` for any auto-advance — fail closed if unavailable.

### P2.3  Always-visible status line
Shell prompt / tmux status bar element:
```
[blue-k/feat-parser | Codex running 4m | last sync 12s ago]
```
Color flips when the human is the bottleneck (e.g. red when `NEXT:` has been waiting on a human for >2 min). Eliminates the "is it my turn?" question without anyone asking.

## Priority 3 — Bigger structural changes (defer until P1/P2 prove the model)

### P3.1  Codify a "forget-safe" invariant in the protocol
Add to `protocol-v0.10.md`:

> **Forget-safe rule.** At any point, the human may type `bk sync` (and nothing else) and arrive at a correct, non-destructive next action. No prior in-flight knowledge is required.

This is partly the current design — promote it from emergent property to enforced invariant, with a test scenario per failure mode.

### P3.2  Make wrong-window inputs self-correct
If `/bk work` arrives in a chat whose lane doesn't match the BATON's expected holder, the AI must:
1. Refuse to act.
2. Print exactly the command the human should send, in the correct window — copy-pasteable.

Today the wrapper handles `bk work` shell-side misuse. Extend the same defensiveness into the AI side.

## What this is *not*

- Not a rewrite of the control-plane / business-plane split — that's working.
- Not relaxing any safety rule (atomic push, stale-lease, no auto-merge, lower-gate BLOCK irreversibility) — those stay.
- Not adding new scenarios — the goal is fewer things to remember, not more.

## Suggested rollout order

1. **P1.1 + P1.2 + P1.4** — single small PR to `bk.ps1` and the chat-side skill prompts. Immediate human relief, zero protocol change.
2. **P1.3 + P1.5** — small follow-up; touches AI skill prompts and `bk sync` output.
3. **P2.2 whitelist** — protocol-v0.10 draft, scenario-matrix update, simulator coverage.
4. **P2.1 `bk go`** — once P1 has reduced the surface to "sync → paste", evaluate whether wiring through a chat client is worth the integration cost.
5. **P3** — only after P1/P2 land and we have real friction data.

## Open questions for the human

- Is there a chat client we can drive programmatically (CLI / API), or is "copy to clipboard + switch window" the realistic ceiling for now?
- Are there handoffs in the current scenario matrix that you would *not* want auto-advanced even when safe? (helps shape P2.2's whitelist)
- Should the always-visible status line be a shell prompt segment, a separate `bk watch` window, or an OS notification?
