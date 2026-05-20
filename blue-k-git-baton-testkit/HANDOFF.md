# Handoff - Blue-K Git Baton Testkit

Repository: `https://github.com/617617/gittest`

Local test root:

```text
D:\code\gittest
```

Your task is to validate the v0.9 two-entry Blue-K Git baton workflow:

```text
bk sync   - shell-side read-only status and decision sheet
/bk work  - AI chat command that executes the current assignment
```

This folder is a self-contained testkit. It does not require the real DND
backend. Use it to test protocol boundaries quickly.

## Read First

1. `blue-k-git-baton-testkit/SKILL.md`
2. `blue-k-git-baton-testkit/references/protocol-v0.9.md`
3. `blue-k-git-baton-testkit/references/scenario-matrix.md`

## Fast Test Commands

From `D:\code\gittest`:

```powershell
python .\blue-k-git-baton-testkit\scripts\bk_sync_sim.py --list
python .\blue-k-git-baton-testkit\scripts\bk_sync_sim.py --all
```

Run a single case:

```powershell
python .\blue-k-git-baton-testkit\scripts\bk_sync_sim.py --scenario ready_codex_main
python .\blue-k-git-baton-testkit\scripts\bk_sync_sim.py --scenario stale_lease_takeover_required
python .\blue-k-git-baton-testkit\scripts\bk_sync_sim.py --scenario code_consensus_light_auto_accept
python .\blue-k-git-baton-testkit\scripts\bk_sync_sim.py --scenario fix_required_routes_runner_fix
```

## What To Check

- Every scenario must produce one unambiguous first-line `NEXT`.
- Runner scenarios must not show wrapper-selected packages.
- Planner scenarios must require durable `AuthorizedAction`.
- Audit-pending must not become runner-ready.
- Stale lease must not auto-takeover.
- Cross-side takeover must require explicit abandoned-unpushed-work acceptance.
- Ordinary `/bk work` must block unless:
  `local HEAD == origin/work branch == BATON.WorkBranchHead`.
- Unattended mode must block when atomic push is unavailable.
- Plan output must route through consensus after audit PASS or accepted WARN.
- Code/package output must route through consensus after runner checkpoint.
- Accepted consensus must be rejected if the topic is superseded/cancelled or
  the subject commit no longer matches.
- Runner `review_pending + accepted consensus` must finalize only that package
  and stop, not start the next package.
- `fix_required` must route to a runner-owned fix lane with a bound fix target.
- Dependency recovery fixes must distinguish active package, prerequisite
  target, or both.
- Docs-only consensus freeze and canonical acceptance hash failures must block.

## Expected Result

If the simulator and references look coherent, report:

```text
Verdict: PASS / WARN / BLOCK
Findings:
- severity, scenario/file, issue, recommended fix
```

Do not modify production DND files. This repository is the sandbox.
