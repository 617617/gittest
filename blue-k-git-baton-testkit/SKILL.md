---
name: blue-k-git-baton-testkit
description: Test and review a simulated Blue-K Git baton protocol for cross-machine CC/Codex coordination. Use when validating the two-entry workflow `bk sync` plus AI chat `/bk work`, coordination-branch BATON semantics, lease/takeover rules, runner assignment boundaries, or handoff readiness for repository 617617/gittest.
---

# Blue-K Git Baton Testkit

Use this skill to simulate and review the Blue-K Git baton protocol in the
test repository `617617/gittest`. It is intentionally small and fast: it does
not run the real DND backend, Blue-K runners, or code graph gate. It tests the
control-plane decisions that decide whether another AI should run `bk sync` or
`/bk work`.

## Roles

- `bk sync` is a shell-side read-only control command. It fetches/inspects
  remote state and prints the next safe action.
- `/bk work` is an AI chat command. It may call Blue-K skills in the real
  project. In this testkit it is simulated by scenario decisions only.
- CC normally owns planner/audit/review lanes.
- Codex normally owns main/other runner execution lanes.

## Quick Start

1. Read `HANDOFF.md` first when acting as the other AI.
2. Read `references/protocol-v0.5.md` before changing the protocol.
3. Run the simulator:

```powershell
python .\blue-k-git-baton-testkit\scripts\bk_sync_sim.py --list
python .\blue-k-git-baton-testkit\scripts\bk_sync_sim.py --all
```

4. For a single boundary case:

```powershell
python .\blue-k-git-baton-testkit\scripts\bk_sync_sim.py --scenario ready_codex_main
```

## What To Validate

Check that each scenario produces one clear first-line action:

- `NEXT: In Codex chat, send: /bk work`
- `NEXT: In CC chat, send: /bk work`
- `NEXT: Do not run /bk work`
- `NEXT: Resume in the original holder chat: /bk work --resume`
- `NEXT: Takeover requires explicit command: /bk work --takeover --from-last-pushed --abandon-unpushed-ok`

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

## Resources

- `HANDOFF.md`: short handoff for the other AI.
- `references/protocol-v0.5.md`: protocol specification under test.
- `references/scenario-matrix.md`: expected decision matrix.
- `scripts/bk_sync_sim.py`: deterministic decision simulator.
- `assets/sample-artifacts/`: sample BATON/progress/audit files for inspection.
