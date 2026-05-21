# CC Review: ready_cc_planner

Verdict: WARN
DecisionRevision: 2 (under review) → 3 (after this fix lands)
ReviewedAt: 2026-05-21T06:45:00Z
CodexCommit: 5f0c4f9
Walkthrough: 2

## Outcome — correct

Refusing as REFUSE_WRONG_WINDOW is exactly what section 8 expected
when Codex receives `/bk work` for a scenario whose `ChatTarget: CC chat`.
No real Blue-K skill was invoked, no push, no progress write. ✅

## What earned the WARN

The Rule 1 self-announce line was:

```text
I am Codex. Lane: blue-k-planner.
```

But `blue-k-planner` is a CC-owned lane, not a Codex-owned lane. The
contract's intent is that Rule 1 lets the human compare the announce
against `WindowMatch` and immediately see whether the paste landed in
the right window. Announcing the **requested** lane (the lane in
WindowMatch) instead of the runtime's **owned** lane makes a wrong-window
paste look correct at a glance — which defeats the point.

Both readings of the old contract were defensible because the wording
`<lane-or-owned-lane-set>` did not say which to do. This review treats
the outcome as correct (refusal) but flags the Rule 1 ambiguity as a
WARN so the contract can be tightened before scenario 3.

## Fix applied in this commit (CC side)

`references/ai-chat-contract.md` Rule 1 now explicitly says:

> The `<lane>` value is what this runtime owns, never the lane named in
> the BATON / WindowMatch / ChatCommand. CC always announces CC-owned
> lanes; Codex always announces Codex-owned lanes. This rule holds even
> when the AI is about to refuse wrong-window input.

`autopilot-decision.md` is bumped to `DecisionRevision: 3` so the next
scenario picks up the clarification.

## What Codex should print for ready_cc_planner under revision 3

```text
I am Codex. Lane: blue-k-main-runner blue-k-other-runner blue-k-other-index blue-k-consensus.
...
REFUSE_WRONG_WINDOW: this Codex chat does not match ChatTarget: CC chat.
Correct ChatTarget: CC chat
Correct ChatCommand: /bk work
WindowMatch: paste into the chat whose first reply says Lane: blue-k-planner
```

The mismatch between the announced lanes (`main-runner / other-runner / other-index / consensus`)
and the `WindowMatch` (`blue-k-planner`) is now visible on the first
two lines of the reply.

## Continue / stop

Continue to scenario 3 (`role_mismatch`) with `DecisionRevision: 3`.
Codex does not need to re-run scenarios 1–2; the outcome on scenario 2
was correct and only the announce-line convention changed.

Codex must re-read `references/ai-chat-contract.md` before scenario 3
per the autopilot-decision.md gating rule.
