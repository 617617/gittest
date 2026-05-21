# Scenario Matrix

Run:

```powershell
.\blue-k-git-baton-testkit\scripts\bk.ps1 sync -Coverage
```

Normal users should not run per-scenario commands. The table below documents
the internal decision partitions covered by `bk sync -Coverage`. Raw
`bk_sync_sim.py --scenario ...` is only a developer diagnostic path.

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
| `stale_lease_resume_original` | Stale lease defaults to original holder resume | `NEXT: Resume in original holder chat: /bk resume` |
| `stale_lease_takeover_required` | Cross-side takeover needs explicit short command plus in-chat confirmation | `NEXT: In CC chat, send: /bk takeover` |
| `same_holder_dirty_resume` | Dirty same-holder resume routes to runner recovery | `NEXT: Resume in original holder chat: /bk resume` |
| `competing_running_conflict` | Different running lane/package blocks takeover | `NEXT: Do not run /bk work` |
| `other_dependency_recovery` | Other runner may show dependency target | `NEXT: In Codex chat, send: /bk work` |
| `state_conflict` | BATON/progress/audit disagree | `NEXT: Do not run /bk work` |
| `plan_consensus_ready_standard` | Plan audit passed; plan needs standard consensus | `NEXT: In CC chat, send: /bk work` |
| `plan_consensus_after_warn_full` | Accepted WARN escalates to full plan consensus | `NEXT: In CC chat, send: /bk work` |
| `code_consensus_light_auto_accept` | Clean code review can light auto-accept | `NEXT: In Codex chat, send: /bk work` |
| `review_pending_finalize_only` | Accepted code consensus finalizes current row only | `NEXT: In Codex chat, send: /bk work` |
| `fix_required_routes_runner_fix` | Consensus fix_required routes to runner fix lane | `NEXT: In Codex chat, send: /bk work` |
| `review_failed_human_blocked` | Failed review cannot silently continue | `NEXT: Do not run /bk work` |
| `superseded_topic_after_code_fix` | Old consensus topic is invalid after new subject commit | `NEXT: Do not run /bk work` |
| `old_acceptance_rejected_after_new_subject` | Acceptance subject commit mismatch blocks next lane | `NEXT: Do not run /bk work` |
| `accepted_consensus_missing_subject` | Accepted consensus without bound subject commit blocks | `NEXT: Do not run /bk work` |
| `dependency_fix_target_active` | Other-runner fix targets active package | `NEXT: In Codex chat, send: /bk work` |
| `dependency_fix_target_prereq` | Other-runner fix targets prerequisite package | `NEXT: In Codex chat, send: /bk work` |
| `dependency_fix_target_both` | Other-runner fix targets both active and prerequisite packages | `NEXT: In Codex chat, send: /bk work` |
| `dependency_fix_missing_target` | Dependency recovery fix without target blocks | `NEXT: Do not run /bk work` |
| `human_blocked_request_code_fix` | Human asks for code fix; runner owns fix lane | `NEXT: In Codex chat, send: /bk work` |
| `human_blocked_request_plan_revision` | Human asks for plan revision; planner owns repair | `NEXT: In CC chat, send: /bk work` |
| `human_blocked_cancel_topic` | Cancelled topic blocks until new instruction | `NEXT: Do not run /bk work` |
| `waiver_not_auto_accept` | Waiver cannot participate in light auto-accept | `NEXT: Do not run /bk work` |
| `docs_only_freeze_violation` | Non-consensus changes between subject and acceptance invalidate topic | `NEXT: Do not run /bk work` |
| `acceptance_hash_mismatch` | Canonical acceptance hash mismatch blocks next lane | `NEXT: Do not run /bk work` |
| `lower_gate_block_cannot_be_accepted` | Consensus/human cannot override lower-gate BLOCK | `NEXT: Do not run /bk work` |
| `consensus_dirty_blocks_runner` | Dirty consensus draft cannot authorize runner start | `NEXT: Do not run /bk work` |
| `full_mode_graph_high_risk` | Graph high-risk overlay edge change triggers full code consensus | `NEXT: In Codex chat, send: /bk work` |

## Review Questions

- Does each first line tell the user exactly what to do?
- Does every blocked case name the failure code?
- Does every runner case say the runner selects/resumes from progress table?
- Does takeover distinguish last pushed checkpoint from local unpushed work?
- Does `bk sync` print `Task`, `Holder`, `Last`, `ChatTarget`, and `ChatCommand`
  so the human does not reconstruct the next action from memory?
- Does the copied/printed command use short chat verbs (`/bk work`, `/bk resume`,
  `/bk takeover`) while dangerous takeover still requires in-chat confirmation?
- Does `/bk takeover` name a takeover-confirming chat and recovery lane instead
  of looking like ordinary runner execution?
- Does the protocol block unsafe automatic work when atomic push is missing?
- Does plan output require consensus before runner execution?
- Does code output require consensus before runner finalization?
- Does runner finalization stop after the current `review_pending` row?
- Does every new subject commit supersede old consensus topics?
- Does dependency recovery consensus bind active package, prerequisite target,
  and `FixTarget`?
- Do docs-only freeze, lower-gate precedence, and acceptance hash checks block
  unsafe continuation?
