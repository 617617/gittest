# Scenario Matrix

Run:

```powershell
python .\blue-k-git-baton-testkit\scripts\bk_sync_sim.py --all
```

## Scenarios

| Scenario | Purpose | Expected First Line |
| --- | --- | --- |
| `ready_codex_main` | Happy path for Codex main runner | `NEXT: In Codex chat, send: /bk work` |
| `ready_cc_planner` | Happy path for CC planner with authorization | `NEXT: In CC chat, send: /bk work` |
| `planner_missing_authorization` | Planner cannot plan/advance without human authorization | `NEXT: Do not run /bk work` |
| `audit_pending_blocks_runner` | Plan Next audit pending is not runner-ready | `NEXT: Do not run /bk work` |
| `audit_report_blocks_runner` | BLOCK audit verdict blocks runner | `NEXT: Do not run /bk work` |
| `role_mismatch` | Current window role is wrong | `NEXT: In Codex chat, send: /bk work` |
| `work_head_mismatch` | origin work branch differs from BATON head | `NEXT: Do not run /bk work` |
| `local_behind_origin` | local branch is behind origin | `NEXT: Do not run /bk work` |
| `atomic_unavailable` | unattended mode cannot push safely | `NEXT: Do not run /bk work` |
| `active_lease_other_holder` | Another active lease blocks work | `NEXT: Do not run /bk work` |
| `stale_lease_resume_original` | Stale lease defaults to original holder resume | `NEXT: Resume in original holder chat: /bk work --resume` |
| `stale_lease_takeover_required` | Cross-side takeover needs explicit risky command | `NEXT: Takeover requires explicit command: /bk work --takeover --from-last-pushed --abandon-unpushed-ok` |
| `same_holder_dirty_resume` | Dirty same-holder resume routes to runner recovery | `NEXT: Resume in original holder chat: /bk work --resume` |
| `competing_running_conflict` | Different running lane/package blocks takeover | `NEXT: Do not run /bk work` |
| `other_dependency_recovery` | Other runner may show dependency target | `NEXT: In Codex chat, send: /bk work` |
| `state_conflict` | BATON/progress/audit disagree | `NEXT: Do not run /bk work` |

## Review Questions

- Does each first line tell the user exactly what to do?
- Does every blocked case name the failure code?
- Does every runner case say the runner selects/resumes from progress table?
- Does takeover distinguish last pushed checkpoint from local unpushed work?
- Does the protocol block unsafe automatic work when atomic push is missing?
