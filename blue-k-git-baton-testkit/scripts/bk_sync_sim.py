#!/usr/bin/env python3
"""Simulate bk sync decisions for the Blue-K Git baton protocol.

The script is intentionally self-contained. It does not mutate git state.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from typing import Callable, Dict, Iterable, List, Optional


GOOD_WORK_HEAD = "1111111"
REMOTE_WORK_HEAD_CHANGED = "2222222"
LOCAL_OLD_HEAD = "0000000"
COORD_HEAD = "aaaaaaa"


@dataclass(frozen=True)
class Scenario:
    name: str
    here_role: str
    owner_role: str
    lane: str
    authorized_action: str
    baton_state: str = "ready"
    audit_verdict: str = "PASS"
    audit_pending: bool = False
    progress_status: str = "pending"
    running_lane: Optional[str] = None
    running_index: Optional[str] = None
    dependency_target: Optional[str] = None
    local_head: str = GOOD_WORK_HEAD
    origin_work_head: str = GOOD_WORK_HEAD
    baton_work_head: str = GOOD_WORK_HEAD
    atomic_push: bool = True
    lease_status: str = "none"
    lease_holder_role: Optional[str] = None
    lease_holder_machine: Optional[str] = None
    current_machine: str = "machine-a"
    stale_lease: bool = False
    original_available: bool = True
    takeover_requested: bool = False
    abandon_unpushed_ok: bool = False
    local_dirty: bool = False
    untracked: bool = False
    state_conflict: bool = False
    strict_shape_ok: bool = True
    warn_accepted: bool = True


@dataclass(frozen=True)
class Decision:
    next_line: str
    why: str
    unit: str
    lock: str
    safe_point: str
    stop_if: str
    failure_code: Optional[str] = None
    remote_takeover_allowed: str = "no"
    takeover_basis: str = "not requested"

    def render(self, scenario: Scenario) -> str:
        lines = [
            self.next_line,
            f"HERE: BK_ROLE={scenario.here_role}",
            f"WHY: {self.why}",
            f"UNIT: {self.unit}",
            f"LOCK: {self.lock}",
            f"SAFE_POINT: origin/blue-k/k1@{self.safe_point}",
            f"STOP_IF: {self.stop_if}",
        ]
        if self.failure_code:
            lines.extend(
                [
                    f"FailureCode: {self.failure_code}",
                    f"Lane: {scenario.lane}",
                    "ProgressFile: " + progress_file(scenario.lane),
                    f"ProgressIndex: {scenario.running_index or '-'}",
                    f"ProgressStatus: {scenario.progress_status}",
                    f"BatonState: {scenario.baton_state}",
                    f"LeaseToken: {'sim-token' if scenario.lease_status != 'none' else '-'}",
                    f"RemoteHead: {scenario.origin_work_head}",
                    f"LastPushedCommit: {scenario.origin_work_head}",
                    f"LastLocalCommit: {scenario.local_head}",
                    f"UnpushedCommits: {unpushed_summary(scenario)}",
                    f"LocalDirty: {str(scenario.local_dirty or scenario.untracked).lower()}",
                    f"RemoteTakeoverAllowed: {self.remote_takeover_allowed}",
                    f"TakeoverBasis: {self.takeover_basis}",
                    f"Next command: {command_from_next(self.next_line)}",
                    "Log path: blue-k-git-baton-testkit/logs/simulated.log",
                ]
            )
        return "\n".join(lines)


def progress_file(lane: str) -> str:
    if lane == "blue-k-main-runner":
        return "docs/mian-k/MAIN_PACKAGE_PROGRESS.md"
    if lane == "blue-k-other-runner":
        return "docs/mian-k/OTHER_MIN_PACKAGE_PROGRESS.md"
    return "-"


def unpushed_summary(scenario: Scenario) -> str:
    if scenario.local_head != scenario.origin_work_head:
        return f"{scenario.origin_work_head}..{scenario.local_head}"
    return "none"


def command_from_next(next_line: str) -> str:
    if "send:" in next_line:
        return next_line.split("send:", 1)[1].strip()
    if "command:" in next_line:
        return next_line.split("command:", 1)[1].strip()
    return "-"


def unit_for(scenario: Scenario) -> str:
    if scenario.lane == "blue-k-main-runner":
        return "blue-k-main-runner will select/resume from MAIN_PACKAGE_PROGRESS.md"
    if scenario.lane == "blue-k-other-runner":
        base = "blue-k-other-runner will select/resume from OTHER_MIN_PACKAGE_PROGRESS.md"
        if scenario.dependency_target:
            return f"{base}; DependencyRecoveryTarget={scenario.dependency_target}"
        return base
    if scenario.lane == "blue-k-planner":
        return f"blue-k-planner AuthorizedAction={scenario.authorized_action}"
    if scenario.lane == "blue-k-plan-audit":
        return "blue-k-plan-audit continuation"
    return scenario.lane


def lock_for(scenario: Scenario) -> str:
    if scenario.lease_status == "none":
        return "no active lease"
    suffix = "stale" if scenario.stale_lease else "active"
    holder = scenario.lease_holder_role or "unknown"
    return f"{suffix} lease held by {holder}/{scenario.lease_holder_machine or 'unknown'}"


def block(scenario: Scenario, code: str, why: str) -> Decision:
    return Decision(
        next_line="NEXT: Do not run /bk work",
        why=why,
        unit=unit_for(scenario),
        lock=lock_for(scenario),
        safe_point=scenario.origin_work_head,
        stop_if="blocked until failure is resolved",
        failure_code=code,
    )


def decide(scenario: Scenario) -> Decision:
    if scenario.state_conflict:
        return block(
            scenario,
            "STATE_CONFLICT",
            "BATON, progress, audit, or roadmap state disagree",
        )

    if scenario.audit_pending:
        return block(
            scenario,
            "PLAN_NEXT_BLOCKED_AUDIT_PENDING",
            "mandatory planner audit is pending; not runner-ready",
        )

    if scenario.audit_verdict == "BLOCK":
        return block(
            scenario,
            "AUDIT_REPORT_BLOCKS_RUNNER",
            "BLUE_K_PLAN_AUDIT_REPORT verdict is BLOCK",
        )

    if scenario.audit_verdict == "WARN" and not scenario.warn_accepted:
        return block(
            scenario,
            "AUDIT_WARN_NOT_ACCEPTED",
            "audit WARN lacks an execution acceptance source",
        )

    if not scenario.strict_shape_ok:
        return block(
            scenario,
            "NON_STRICT_PACKAGE",
            "package strict readiness files are missing or inconsistent",
        )

    if scenario.lane == "blue-k-planner" and scenario.authorized_action in {
        "",
        "inspect_only",
    }:
        return block(
            scenario,
            "PLANNER_AUTHORIZATION_REQUIRED",
            "planner cannot plan/advance without durable human authorization",
        )

    if scenario.origin_work_head != scenario.baton_work_head:
        return block(
            scenario,
            "REMOTE_WORK_HEAD_CHANGED",
            "origin work branch head differs from BATON.WorkBranchHead",
        )

    if scenario.local_head != scenario.origin_work_head:
        return block(
            scenario,
            "LOCAL_HEAD_NOT_AT_REMOTE",
            "local HEAD must equal origin work branch before ordinary start",
        )

    if not scenario.atomic_push:
        return block(
            scenario,
            "ATOMIC_PUSH_UNAVAILABLE",
            "unattended mode requires atomic push of work and coordination branches",
        )

    if scenario.lease_status == "active" and not scenario.stale_lease:
        if same_holder(scenario):
            return resume_decision(scenario, "SAME_HOLDER_ACTIVE_LEASE")
        return block(
            scenario,
            "ACTIVE_LEASE_OTHER_HOLDER",
            "another holder has an active coordination lease",
        )

    if scenario.lease_status == "active" and scenario.stale_lease:
        if same_holder(scenario) and scenario.original_available:
            return resume_decision(scenario, "STALE_LEASE_SAME_HOLDER")
        if scenario.takeover_requested:
            if competing_running(scenario):
                return block(
                    scenario,
                    "COMPETING_RUNNING_CONFLICT",
                    "a different running lane/package conflicts with takeover",
                )
            if scenario.abandon_unpushed_ok:
                return Decision(
                    next_line=(
                        "NEXT: Takeover requires explicit command: "
                        "/bk work --takeover --from-last-pushed --abandon-unpushed-ok"
                    ),
                    why="stale lease; takeover resumes only from last pushed checkpoint",
                    unit=unit_for(scenario),
                    lock=lock_for(scenario),
                    safe_point=scenario.origin_work_head,
                    stop_if="do not use local unpushed work from the unavailable holder",
                    failure_code="STALE_LEASE_TAKEOVER_EXPLICIT",
                    remote_takeover_allowed="yes",
                    takeover_basis="matching running row from last pushed checkpoint",
                )
            return block(
                scenario,
                "TAKEOVER_REQUIRES_ABANDON_UNPUSHED_ACK",
                "cross-side takeover must explicitly accept abandoning unpushed local work",
            )
        return resume_decision(scenario, "STALE_LEASE_RESUME_ORIGINAL")

    if scenario.local_dirty or scenario.untracked:
        return block(
            scenario,
            "LOCAL_DIRTY_ORDINARY_START",
            "ordinary start requires clean worktree including untracked non-ignored files",
        )

    if scenario.here_role != scenario.owner_role:
        return Decision(
            next_line=f"NEXT: In {role_label(scenario.owner_role)} chat, send: /bk work",
            why=f"BATON Owner={scenario.owner_role}; current role is {scenario.here_role}",
            unit=unit_for(scenario),
            lock=lock_for(scenario),
            safe_point=scenario.origin_work_head,
            stop_if="do not run from the wrong role window",
        )

    return Decision(
        next_line=f"NEXT: In {role_label(scenario.owner_role)} chat, send: /bk work",
        why=(
            f"BATON Owner={scenario.owner_role}; audit verdict={scenario.audit_verdict}; "
            f"progress status={scenario.progress_status}"
        ),
        unit=unit_for(scenario),
        lock=lock_for(scenario),
        safe_point=scenario.origin_work_head,
        stop_if="local dirty, branch mismatch, remote head changed",
    )


def same_holder(scenario: Scenario) -> bool:
    return (
        scenario.lease_holder_role == scenario.here_role
        and scenario.lease_holder_machine == scenario.current_machine
    )


def competing_running(scenario: Scenario) -> bool:
    return bool(scenario.running_lane and scenario.running_lane != scenario.lane)


def resume_decision(scenario: Scenario, code: str) -> Decision:
    return Decision(
        next_line="NEXT: Resume in original holder chat: /bk work --resume",
        why="matching holder should re-enter runner recovery gate",
        unit=unit_for(scenario),
        lock=lock_for(scenario),
        safe_point=scenario.origin_work_head,
        stop_if="wrapper must not repair dirty state directly",
        failure_code=code,
        remote_takeover_allowed="no",
        takeover_basis="same holder recovery preferred",
    )


def role_label(role: str) -> str:
    return "Codex" if role == "codex" else "CC"


def scenarios() -> Dict[str, Scenario]:
    base = Scenario(
        name="base",
        here_role="codex",
        owner_role="codex",
        lane="blue-k-main-runner",
        authorized_action="run_main_requested",
    )
    return {
        "ready_codex_main": replace(base, name="ready_codex_main"),
        "ready_cc_planner": replace(
            base,
            name="ready_cc_planner",
            here_role="cc",
            owner_role="cc",
            lane="blue-k-planner",
            authorized_action="plan_next_requested",
        ),
        "planner_missing_authorization": replace(
            base,
            name="planner_missing_authorization",
            here_role="cc",
            owner_role="cc",
            lane="blue-k-planner",
            authorized_action="inspect_only",
        ),
        "audit_pending_blocks_runner": replace(
            base,
            name="audit_pending_blocks_runner",
            audit_pending=True,
            lane="blue-k-main-runner",
        ),
        "audit_report_blocks_runner": replace(
            base,
            name="audit_report_blocks_runner",
            audit_verdict="BLOCK",
        ),
        "role_mismatch": replace(
            base,
            name="role_mismatch",
            here_role="cc",
            owner_role="codex",
        ),
        "work_head_mismatch": replace(
            base,
            name="work_head_mismatch",
            origin_work_head=REMOTE_WORK_HEAD_CHANGED,
        ),
        "local_behind_origin": replace(
            base,
            name="local_behind_origin",
            local_head=LOCAL_OLD_HEAD,
        ),
        "atomic_unavailable": replace(
            base,
            name="atomic_unavailable",
            atomic_push=False,
        ),
        "active_lease_other_holder": replace(
            base,
            name="active_lease_other_holder",
            lease_status="active",
            lease_holder_role="codex",
            lease_holder_machine="machine-b",
        ),
        "stale_lease_resume_original": replace(
            base,
            name="stale_lease_resume_original",
            lease_status="active",
            lease_holder_role="codex",
            lease_holder_machine="machine-a",
            stale_lease=True,
        ),
        "stale_lease_takeover_required": replace(
            base,
            name="stale_lease_takeover_required",
            here_role="cc",
            owner_role="codex",
            lease_status="active",
            lease_holder_role="codex",
            lease_holder_machine="machine-z",
            stale_lease=True,
            original_available=False,
            takeover_requested=True,
            abandon_unpushed_ok=True,
            progress_status="running",
            running_lane="blue-k-main-runner",
            running_index="03",
        ),
        "same_holder_dirty_resume": replace(
            base,
            name="same_holder_dirty_resume",
            lease_status="active",
            lease_holder_role="codex",
            lease_holder_machine="machine-a",
            stale_lease=True,
            local_dirty=True,
            progress_status="running",
            running_lane="blue-k-main-runner",
            running_index="02",
        ),
        "competing_running_conflict": replace(
            base,
            name="competing_running_conflict",
            here_role="cc",
            owner_role="codex",
            lease_status="active",
            lease_holder_role="codex",
            lease_holder_machine="machine-z",
            stale_lease=True,
            original_available=False,
            takeover_requested=True,
            abandon_unpushed_ok=True,
            progress_status="running",
            running_lane="blue-k-other-runner",
            running_index="07",
        ),
        "other_dependency_recovery": replace(
            base,
            name="other_dependency_recovery",
            lane="blue-k-other-runner",
            authorized_action="run_other_requested",
            progress_status="running",
            running_lane="blue-k-other-runner",
            running_index="04",
            dependency_target="docs/mian-k/main/02_prereq",
        ),
        "state_conflict": replace(
            base,
            name="state_conflict",
            state_conflict=True,
        ),
    }


def run(names: Iterable[str]) -> int:
    all_scenarios = scenarios()
    unknown = [name for name in names if name not in all_scenarios]
    if unknown:
        print("Unknown scenario(s): " + ", ".join(unknown))
        return 2
    for index, name in enumerate(names):
        scenario = all_scenarios[name]
        if index:
            print("\n" + "=" * 72 + "\n")
        print(f"SCENARIO: {name}")
        print("-" * 72)
        print(decide(scenario).render(scenario))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="list scenario names")
    parser.add_argument("--all", action="store_true", help="run all scenarios")
    parser.add_argument("--scenario", action="append", help="run a named scenario")
    args = parser.parse_args(argv)

    all_scenarios = scenarios()
    if args.list:
        for name in sorted(all_scenarios):
            print(name)
        return 0
    if args.all:
        return run(sorted(all_scenarios))
    if args.scenario:
        return run(args.scenario)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
