---
name: blue-k-git-baton-testkit
description: Test and review a simulated Blue-K Git baton protocol for cross-machine CC/Codex coordination. Use when validating the forget-safe workflow `bk sync` plus AI chat `/bk work`/`/bk resume`/`/bk takeover`, coordination-branch BATON semantics, lease/takeover rules, runner assignment boundaries, plan/code consensus gates, or handoff readiness for repository 617617/gittest.
---

# Blue-K Git Baton Testkit

Use this skill to simulate and review the Blue-K Git baton protocol in the
test repository `617617/gittest`. It is intentionally small and fast: it does
not run the real DND backend, Blue-K runners, or code graph gate. It tests the
control-plane decisions that decide which chat command `bk sync` should print.

## Roles

- `bk sync` is a shell-side control command. It fetches/inspects remote state,
  safely fast-forwards a clean local branch when possible, prints the next safe
  action, and copies the printed `ChatCommand` when possible. It must not
  execute Blue-K tasks.
- `/bk work`, `/bk resume`, and `/bk takeover` are AI chat commands. Humans
  should not memorize these variants; `bk sync` selects and prints the one to
  paste. `/bk takeover` still requires explicit in-chat confirmation.
- CC normally owns planner/audit/review lanes.
- Codex normally owns main/other runner execution lanes.

## Quick Start

1. Read `HANDOFF.md` first when acting as the other AI.
2. Read `HANDOFF_BLUE_K_WORKFLOW_SKILL_BUNDLE.md` when validating the portable
   project-local Blue-K skill bundle.
3. Read `references/protocol-v0.10.md` before changing the protocol.
4. Run the normal user sync entry:

```powershell
.\blue-k-git-baton-testkit\scripts\bk.ps1 sync
```

5. To test boundary coverage without exposing internal cases to the user:

```powershell
.\blue-k-git-baton-testkit\scripts\bk.ps1 sync -Coverage
```

6. If the user runs shell-side work by mistake:

```powershell
.\blue-k-git-baton-testkit\scripts\bk.ps1 work
```

It must only tell the user to run `bk sync`, then paste the printed
`ChatCommand` in the AI chat window named by `bk sync`.

## What To Validate

Check that each user-facing entry produces one clear first-line action. The
coverage mode may run many internal scenarios, but the user still enters
through `bk sync -Coverage`.

- `NEXT: In Codex chat, send: /bk work`
- `NEXT: In CC chat, send: /bk work`
- `NEXT: Do not run /bk work`
- `NEXT: Resume in original holder chat: /bk resume`
- `NEXT: In CC chat, send: /bk takeover`

Each runnable decision must also include:

- `Task`, `Holder`, and `Last` status lines;
- `ChatTarget` and `ChatCommand`;
- `WindowMatch`, telling the human which lane line to match in the AI chat;
- `AfterWork: Done. Now run: bk sync`.

The simulator intentionally covers edge cases:

- audit report blocks runner startup;
- local/head/remote/BATON head mismatch;
- stale lease without automatic takeover;
- same-holder resume with dirty local state;
- cross-side takeover from last pushed checkpoint;
- missing human authorization for planner;
- other-runner dependency recovery display;
- atomic push unavailable;
- role mismatch;
- coordination/work branch race.

## Portable Blue-K Skills

The real workflow skill closure is packaged under:

```text
blue-k-git-baton-testkit/skills/
```

Use `HANDOFF_BLUE_K_WORKFLOW_SKILL_BUNDLE.md` for the role split, review
consensus loops, dependency recommendation loop, and relative-path setup notes.
- plan consensus after audit;
- code consensus after runner checkpoint;
- docs-only consensus freeze;
- stale consensus-topic invalidation;
- runner `review_pending` finalization;
- runner-owned fix lanes;
- dependency recovery fix target ownership;
- human-blocked decisions.
- forget-safe status and chat command display.

## Hard Rules

- Treat the coordination branch as the only control truth source:
  `origin/blue-k/coordination:.blue-k/BATON.yaml`.
- Treat the work branch as the only business truth source.
- Ordinary `/bk work` start requires:
  `local HEAD == origin/<work-branch> == BATON.WorkBranchHead`.
- Unattended mode requires atomic push for work branch plus coordination branch.
- Do not allow automatic merge, rebase, force push, or cross-side takeover.
- A stale lease is a warning, not authorization.
- A matching `running` progress row is a resume target, not a blocker.
- A competing different running lane/package is a blocker.
- Wrapper must not select packages, write progress tables, run stage-loop-auto,
  run code graph gates, or create runner checkpoint commits.
- Plan output must pass a consensus synthesis before runner execution.
- Code/package output must pass a consensus review before runner finalization.
- Lower-gate `BLOCK` cannot be converted to `PASS` by consensus or human risk
  acceptance.
- Consensus topics become invalid when a new subject commit appears.
- Between subject and acceptance commits, only the topic directory under
  `docs/mian-k/_consensus/<topic-id>/` may change.
- `docs/mian-k` is the intentional current Blue-K path name in this testkit.
- `bk sync` must be forget-safe: the human can run it at any time and receive
  one non-destructive next action.
- AI chat commands must self-correct wrong-window use instead of starting work.
- Every AI chat should announce its role/lane on first reply and end with
  `Done. Now run: bk sync` after writing/pushing the next safe BATON handoff.

## Resources

- `HANDOFF.md`: short handoff for the other AI.
- `HANDOFF_REGISTER_CLAUDE_PROJECT_SKILLS.md`: handoff for Claude to register
  the two exposed project entries in the real repository.
- `references/protocol-v0.10.md`: current forget-safe protocol specification.
- `references/protocol-v0.9.md`: previous baseline retained for comparison.
- `references/autonomy-proposal.md`: v0.11 autonomous loop proposal; read only
  when evaluating future safe auto-advance, not for normal v0.10 testing.
- `references/protocol-v0.5.md`: earlier baseline retained for comparison.
- `references/scenario-matrix.md`: expected decision matrix.
- `scripts/bk_sync_sim.py`: deterministic decision simulator.
- `scripts/bk.ps1`: user-facing shell wrapper for `bk sync` / guarded
  shell-side `bk work`.
- `assets/sample-artifacts/`: sample BATON/progress/audit files for inspection.
