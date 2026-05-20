---
description: Claude-side mirror of Blue-K bk sync. Use when the user asks Claude to inspect or validate baton sync state. Normal users should run shell bk sync instead.
disable-model-invocation: true
allowed-tools:
  - Bash(powershell -ExecutionPolicy Bypass -File scripts/blue_k_baton/bk.ps1 *)
  - Bash(git *)
  - Read
---

# Blue-K Baton Sync Mirror

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\blue_k_baton\bk.ps1 sync
```

Report the exact first-line `NEXT:` and any `FailureCode`.

Do not execute planner, audit, runner, review, or consensus work from this
skill. If the output says to use `/bk work`, tell the user to run `/bk work`
in the named Claude window.