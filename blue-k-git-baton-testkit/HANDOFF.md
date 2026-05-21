# Handoff - Blue-K Git Baton Testkit

Repository: `https://github.com/617617/gittest`

Local test root is the repository root containing this handoff. In examples,
run commands from that root:

```text
<repo-root>
```

Your task is to validate the v0.10 forget-safe Blue-K Git baton workflow:

```text
bk sync   - shell-side safe sync, status, clipboard, and decision sheet
/bk work  - AI chat command that executes the current assignment
```

This folder is a self-contained testkit. It does not require the real DND
backend. Use it to test protocol boundaries quickly.

Humans should not memorize resume/takeover flags. They run `bk sync`, then
paste the printed `ChatCommand` into the printed target chat. Valid chat
commands are `/bk work`, `/bk resume`, and `/bk takeover`; takeover still
requires explicit in-chat confirmation before any destructive recovery.

## Read First

1. `blue-k-git-baton-testkit/SKILL.md`
2. `blue-k-git-baton-testkit/HANDOFF_BLUE_K_WORKFLOW_SKILL_BUNDLE.md`
3. `blue-k-git-baton-testkit/references/protocol-v0.10.md`
4. `blue-k-git-baton-testkit/references/scenario-matrix.md`

Optional future context: `blue-k-git-baton-testkit/references/autonomy-proposal.md`
is v0.11-oriented. Do not enable autonomous loops while validating v0.10
forget-safe behavior.

## Fast Test Commands

From the repository root:

```powershell
.\blue-k-git-baton-testkit\scripts\bk.ps1 sync
```

Run boundary coverage through the same user entry:

```powershell
.\blue-k-git-baton-testkit\scripts\bk.ps1 sync -Coverage
```

Do not ask the user to run `git pull` as part of the normal workflow. `bk sync`
owns safe fetch/fast-forward behavior. Shell-side `bk work` is only a guard
that tells the user to send `/bk work` in the named AI chat window.

Do not ask the user to run per-scenario commands as the normal test path.
`-Scenario`, `-List`, and raw `bk_sync_sim.py` are developer diagnostics only.

## What To Check

- User-facing tests should enter through `scripts/bk.ps1 sync`, not raw
  simulator, per-scenario commands, or manual `git pull`.
- Normal sync must produce one unambiguous first-line `NEXT`.
- Runnable sync decisions must also print `Task`, `Holder`, `Last`,
  `ChatTarget`, and `ChatCommand`, and should copy `ChatCommand` to the
  clipboard when the shell supports it.
- Coverage mode must cover the internal scenario matrix while preserving the
  two-entry user surface: `bk sync` then `/bk work`.
- Runner scenarios must not show wrapper-selected packages.
- Planner scenarios must require durable `AuthorizedAction`.
- Audit-pending must not become runner-ready.
- Stale lease must not auto-takeover.
- Cross-side takeover must require explicit abandoned-unpushed-work acceptance.
- Wrong-window `/bk work`, `/bk resume`, or `/bk takeover` must refuse and
  print the correct target window/command.
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
