#!/usr/bin/env python3
"""Simulate bk sync decisions for the Blue-K Git baton protocol.

The script is intentionally self-contained. It does not mutate git state.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from typing import Dict, Iterable, List, Optional, Tuple


GOOD_WORK_HEAD = "1111111"
REMOTE_WORK_HEAD_CHANGED = "2222222"
NEW_SUBJECT_HEAD = "3333333"
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
    consensus_kind: str = "none"
    consensus_mode: str = "none"
    consensus_status: str = "none"
    topic_status: str = "none"
    subject_commit: str = GOOD_WORK_HEAD
    acceptance_subject_commit: Optional[str] = None
    auto_accepted: bool = False
    acceptance_hash_ok: bool = True
    docs_only_freeze_ok: bool = True
    lower_gates_ok: bool = True
    lower_gate_block: bool = False
    live_opinions_ok: bool = True
    waiver_used: bool = False
    role_signals_pass: bool = True
    review_status: str = ""
    human_decision: Optional[str] = None
    fix_target: Optional[str] = None
    active_package: Optional[str] = None
    dependency_recovery_target: Optional[str] = None
    progress_row_id: Optional[str] = None
    finding_set_commit: Optional[str] = None
    full_mode_reason: Optional[str] = None
    consensus_dirty: bool = False


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
    extra_lines: Tuple[str, ...] = ()

    def render(self, scenario: Scenario) -> str:
        chat_command = command_from_next(self.next_line)
        lines = [
            self.next_line,
            "Task: blue-k/k1",
            f"Holder: {role_label(scenario.owner_role)} ({scenario.lane}) {holder_status(scenario)}",
            f"Last: origin/blue-k/k1@{self.safe_point}",
            f"ChatTarget: {chat_target_from_next(self.next_line)}",
            f"ChatCommand: {chat_command}",
        ]
        if chat_command != "-":
            lines.extend(
                [
                    f"WindowMatch: {window_match_hint(scenario, self.next_line)}",
                    "AfterWork: Done. Now run: bk sync",
                ]
            )
        lines.extend(
            [
            f"HERE: BK_ROLE={scenario.here_role}",
            f"WHY: {self.why}",
            f"UNIT: {self.unit}",
            f"LOCK: {self.lock}",
            f"SAFE_POINT: origin/blue-k/k1@{self.safe_point}",
            f"STOP_IF: {self.stop_if}",
            ]
        )
        if has_consensus_info(scenario):
            lines.extend(consensus_lines(scenario))
        lines.extend(self.extra_lines)
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


def has_consensus_info(scenario: Scenario) -> bool:
    return (
        scenario.consensus_kind != "none"
        or scenario.consensus_mode != "none"
        or scenario.consensus_status != "none"
        or scenario.topic_status != "none"
        or bool(scenario.review_status)
        or bool(scenario.human_decision)
        or bool(scenario.fix_target)
        or bool(scenario.dependency_recovery_target)
        or scenario.consensus_dirty
    )


def consensus_lines(scenario: Scenario) -> List[str]:
    acceptance_subject = scenario.acceptance_subject_commit or "-"
    lines = [
        f"ConsensusKind: {scenario.consensus_kind}",
        f"ConsensusMode: {scenario.consensus_mode}",
        f"ConsensusStatus: {scenario.consensus_status}",
        f"TopicStatus: {scenario.topic_status}",
        f"SubjectCommit: {scenario.subject_commit}",
        f"AcceptanceSubjectCommit: {acceptance_subject}",
        f"AutoAccepted: {str(scenario.auto_accepted).lower()}",
    ]
    if scenario.full_mode_reason:
        lines.append(f"FullModeReason: {scenario.full_mode_reason}")
    if scenario.review_status:
        lines.append(f"ReviewStatus: {scenario.review_status}")
    if scenario.human_decision:
        lines.append(f"HumanDecision: {scenario.human_decision}")
    if scenario.active_package:
        lines.append(f"ActivePackage: {scenario.active_package}")
    if scenario.dependency_recovery_target:
        lines.append(
            f"DependencyRecoveryTarget: {scenario.dependency_recovery_target}"
        )
    if scenario.fix_target:
        lines.append(f"FixTarget: {scenario.fix_target}")
    if scenario.progress_row_id:
        lines.append(f"ProgressRowId: {scenario.progress_row_id}")
    if scenario.finding_set_commit:
        lines.append(f"FindingSetCommit: {scenario.finding_set_commit}")
    return lines


def unpushed_summary(scenario: Scenario) -> str:
    if scenario.local_head != scenario.origin_work_head:
        return f"{scenario.origin_work_head}..{scenario.local_head}"
    return "none"


def command_from_next(next_line: str) -> str:
    if "send:" in next_line:
        return next_line.split("send:", 1)[1].strip()
    if "command:" in next_line:
        return next_line.split("command:", 1)[1].strip()
    if "original holder chat:" in next_line:
        return next_line.split("original holder chat:", 1)[1].strip()
    return "-"


def chat_target_from_next(next_line: str) -> str:
    if "In Codex chat" in next_line:
        return "Codex chat"
    if "In CC chat" in next_line:
        return "CC chat"
    if "original holder chat" in next_line:
        return "original holder chat"
    if "Takeover requires" in next_line:
        return "takeover-confirming AI chat"
    return "-"


def window_match_hint(scenario: Scenario, next_line: str) -> str:
    if "/bk takeover" in next_line:
        return (
            f"paste into the {role_label(scenario.here_role)} takeover chat; "
            f"it must show takeover basis for Lane: {scenario.lane}"
        )
    return f"paste into the chat whose first reply says Lane: {scenario.lane}"


def holder_status(scenario: Scenario) -> str:
    if scenario.lease_status != "none":
        stale = "stale" if scenario.stale_lease else "active"
        return f"{stale} lease; progress={scenario.progress_status}"
    return f"state={scenario.baton_state}; progress={scenario.progress_status}"


def unit_for(scenario: Scenario) -> str:
    consensus_unit = consensus_unit_for(scenario)
    if consensus_unit:
        return consensus_unit
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


def consensus_unit_for(scenario: Scenario) -> str:
    if scenario.consensus_kind == "plan" and scenario.consensus_status == "needed":
        return (
            "blue-k-consensus plan synthesis; write docs under "
            "docs/mian-k/_consensus/<topic-id>/ only"
        )
    if scenario.consensus_kind == "code" and scenario.consensus_status == "needed":
        return (
            "blue-k-consensus code review; bind runner checkpoint, lower gates, "
            "LIVE_OPINIONS, and AcceptanceHash"
        )
    if scenario.review_status == "review_pending" and scenario.consensus_status == "accepted":
        return "runner finalize current review_pending row only, then stop"
    if scenario.consensus_status == "fix_required":
        return "runner-owned fix lane; wrapper must not preselect packages"
    if scenario.human_decision == "request_code_fix":
        return "runner-owned fix lane requested by human decision"
    if scenario.human_decision == "request_plan_revision":
        return "blue-k-planner plan revision requested by human decision"
    return ""


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


def consensus_blocker(scenario: Scenario) -> Optional[Tuple[str, str]]:
    if scenario.lower_gate_block:
        return (
            "LOWER_GATE_BLOCK_CANNOT_BE_ACCEPTED",
            "lower-gate BLOCK must return to planner repair or runner fix",
        )
    if scenario.consensus_dirty:
        return (
            "CONSENSUS_DIRTY_DRAFT",
            "dirty or unpushed consensus draft cannot authorize runner start",
        )
    if not scenario.docs_only_freeze_ok:
        return (
            "CONSENSUS_FREEZE_VIOLATION",
            "non-consensus files changed between SubjectCommit and AcceptanceCommit",
        )
    if not scenario.acceptance_hash_ok:
        return (
            "ACCEPTANCE_HASH_MISMATCH",
            "canonical AcceptanceHash does not match exact commit blobs",
        )
    if not scenario.live_opinions_ok:
        return (
            "LIVE_OPINIONS_HASH_MISMATCH",
            "LIVE_OPINIONS or closure marker is not bound by AcceptanceHash",
        )
    if scenario.topic_status == "superseded":
        return (
            "CONSENSUS_TOPIC_SUPERSEDED",
            "a newer SubjectCommit superseded this consensus topic",
        )
    if scenario.topic_status == "cancelled":
        return (
            "CONSENSUS_TOPIC_CANCELLED",
            "human cancelled the topic; wait for new instruction",
        )
    if scenario.consensus_status == "accepted" and not scenario.acceptance_subject_commit:
        return (
            "ACCEPTANCE_SUBJECT_COMMIT_REQUIRED",
            "accepted consensus must bind the accepted subject commit",
        )
    if (
        scenario.consensus_status == "accepted"
        and scenario.acceptance_subject_commit
        and scenario.acceptance_subject_commit != scenario.subject_commit
    ):
        return (
            "ACCEPTANCE_SUBJECT_COMMIT_MISMATCH",
            "accepted consensus binds an old subject commit",
        )
    if scenario.auto_accepted and (
        scenario.consensus_mode != "light"
        or scenario.waiver_used
        or not scenario.role_signals_pass
        or not scenario.lower_gates_ok
    ):
        return (
            "AUTO_ACCEPT_NOT_ALLOWED",
            "light auto-accept requires PASS role signals, PASS lower gates, and no waiver",
        )
    if scenario.consensus_status == "fix_required":
        if not scenario.finding_set_commit:
            return (
                "FINDING_SET_REQUIRED",
                "fix_required must bind the review finding set commit",
            )
        if scenario.lane == "blue-k-other-runner" and not scenario.fix_target:
            return (
                "FIX_TARGET_REQUIRED",
                "other-runner dependency recovery fix must bind FixTarget",
            )
    if scenario.review_status == "review_failed":
        return (
            "REVIEW_FAILED_NEEDS_DECISION",
            "failed review must route to retry_fix, planner_repair, or human_blocked",
        )
    if scenario.human_decision == "accept_risk" and (
        scenario.lower_gate_block or not scenario.lower_gates_ok
    ):
        return (
            "ACCEPT_RISK_CANNOT_OVERRIDE_LOWER_GATE",
            "human risk acceptance cannot override lower-gate BLOCK",
        )
    return None


def consensus_decision(scenario: Scenario) -> Optional[Decision]:
    if scenario.consensus_kind in {"plan", "code"} and scenario.consensus_status == "needed":
        return Decision(
            next_line=f"NEXT: In {role_label(scenario.owner_role)} chat, send: /bk work",
            why=(
                f"{scenario.consensus_kind} consensus required in "
                f"{scenario.consensus_mode} mode before the next lane"
            ),
            unit=unit_for(scenario),
            lock=lock_for(scenario),
            safe_point=scenario.origin_work_head,
            stop_if="only consensus topic docs may change before acceptance",
        )
    if (
        scenario.review_status == "review_pending"
        and scenario.consensus_status == "accepted"
    ):
        return Decision(
            next_line=f"NEXT: In {role_label(scenario.owner_role)} chat, send: /bk work",
            why="accepted code consensus unlocks runner finalization only",
            unit=unit_for(scenario),
            lock=lock_for(scenario),
            safe_point=scenario.origin_work_head,
            stop_if="finalize current row and stop; do not start another package",
        )
    if scenario.consensus_status == "fix_required":
        return Decision(
            next_line=f"NEXT: In {role_label(scenario.owner_role)} chat, send: /bk work",
            why="consensus requested a runner-owned fix lane",
            unit=unit_for(scenario),
            lock=lock_for(scenario),
            safe_point=scenario.origin_work_head,
            stop_if="new checkpoint must create a new SubjectCommit and topic",
        )
    if scenario.human_decision == "request_code_fix":
        return Decision(
            next_line="NEXT: In Codex chat, send: /bk work",
            why="human requested code fix; runner owns repair",
            unit=unit_for(scenario),
            lock=lock_for(scenario),
            safe_point=scenario.origin_work_head,
            stop_if="runner fix must produce new checkpoint and supersede old topic",
        )
    if scenario.human_decision == "request_plan_revision":
        return Decision(
            next_line="NEXT: In CC chat, send: /bk work",
            why="human requested plan revision",
            unit=unit_for(scenario),
            lock=lock_for(scenario),
            safe_point=scenario.origin_work_head,
            stop_if="new plan revision must create a new SubjectCommit and topic",
        )
    return None


def decide(scenario: Scenario) -> Decision:
    if scenario.state_conflict:
        return block(
            scenario,
            "STATE_CONFLICT",
            "BATON, progress, audit, or roadmap state disagree",
        )

    consensus_failure = consensus_blocker(scenario)
    if consensus_failure:
        code, why = consensus_failure
        return block(scenario, code, why)

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
                        f"NEXT: In {role_label(scenario.here_role)} chat, send: /bk takeover"
                    ),
                    why="stale lease; takeover resumes only from last pushed checkpoint",
                    unit=unit_for(scenario),
                    lock=lock_for(scenario),
                    safe_point=scenario.origin_work_head,
                    stop_if="do not use local unpushed work from the unavailable holder",
                    failure_code="STALE_LEASE_TAKEOVER_EXPLICIT",
                    remote_takeover_allowed="yes",
                    takeover_basis="matching running row from last pushed checkpoint",
                    extra_lines=(
                        'TakeoverConfirmation: AI chat must require "yes, abandon" after showing current remote evidence',
                    ),
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

    consensus_route = consensus_decision(scenario)
    if consensus_route:
        return consensus_route

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
        next_line="NEXT: Resume in original holder chat: /bk resume",
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
        "plan_consensus_ready_standard": replace(
            base,
            name="plan_consensus_ready_standard",
            here_role="cc",
            owner_role="cc",
            lane="blue-k-consensus",
            authorized_action="plan_consensus_requested",
            consensus_kind="plan",
            consensus_mode="standard",
            consensus_status="needed",
            topic_status="open",
        ),
        "plan_consensus_after_warn_full": replace(
            base,
            name="plan_consensus_after_warn_full",
            here_role="cc",
            owner_role="cc",
            lane="blue-k-consensus",
            authorized_action="plan_consensus_requested",
            audit_verdict="WARN",
            warn_accepted=True,
            consensus_kind="plan",
            consensus_mode="full",
            consensus_status="needed",
            topic_status="open",
            full_mode_reason="accepted audit WARN",
        ),
        "code_consensus_light_auto_accept": replace(
            base,
            name="code_consensus_light_auto_accept",
            lane="blue-k-consensus",
            authorized_action="code_consensus_requested",
            consensus_kind="code",
            consensus_mode="light",
            consensus_status="needed",
            topic_status="open",
            auto_accepted=True,
            review_status="review_pending",
            active_package="docs/mian-k/main/03_rules",
            progress_row_id="main:03",
        ),
        "review_pending_finalize_only": replace(
            base,
            name="review_pending_finalize_only",
            lane="blue-k-main-runner",
            authorized_action="runner_finalize_requested",
            consensus_kind="code",
            consensus_mode="light",
            consensus_status="accepted",
            topic_status="accepted",
            acceptance_subject_commit=GOOD_WORK_HEAD,
            review_status="review_pending",
            active_package="docs/mian-k/main/03_rules",
            progress_status="review_pending",
            progress_row_id="main:03",
        ),
        "fix_required_routes_runner_fix": replace(
            base,
            name="fix_required_routes_runner_fix",
            lane="blue-k-main-runner",
            authorized_action="runner_fix_requested",
            consensus_kind="code",
            consensus_mode="standard",
            consensus_status="fix_required",
            topic_status="accepted",
            acceptance_subject_commit=GOOD_WORK_HEAD,
            review_status="review_pending",
            active_package="docs/mian-k/main/03_rules",
            progress_status="review_pending",
            progress_row_id="main:03",
            finding_set_commit="4444444",
        ),
        "review_failed_human_blocked": replace(
            base,
            name="review_failed_human_blocked",
            lane="blue-k-main-runner",
            authorized_action="runner_review_recovery_requested",
            consensus_kind="code",
            consensus_mode="full",
            consensus_status="human_blocked",
            topic_status="open",
            review_status="review_failed",
            active_package="docs/mian-k/main/03_rules",
            progress_status="review_failed",
            progress_row_id="main:03",
        ),
        "superseded_topic_after_code_fix": replace(
            base,
            name="superseded_topic_after_code_fix",
            lane="blue-k-main-runner",
            authorized_action="runner_finalize_requested",
            consensus_kind="code",
            consensus_mode="light",
            consensus_status="accepted",
            topic_status="superseded",
            subject_commit=NEW_SUBJECT_HEAD,
            acceptance_subject_commit=GOOD_WORK_HEAD,
            review_status="review_pending",
            progress_status="review_pending",
            progress_row_id="main:03",
        ),
        "old_acceptance_rejected_after_new_subject": replace(
            base,
            name="old_acceptance_rejected_after_new_subject",
            lane="blue-k-main-runner",
            authorized_action="runner_finalize_requested",
            consensus_kind="code",
            consensus_mode="light",
            consensus_status="accepted",
            topic_status="accepted",
            subject_commit=NEW_SUBJECT_HEAD,
            acceptance_subject_commit=GOOD_WORK_HEAD,
            review_status="review_pending",
            progress_status="review_pending",
            progress_row_id="main:03",
        ),
        "accepted_consensus_missing_subject": replace(
            base,
            name="accepted_consensus_missing_subject",
            lane="blue-k-main-runner",
            authorized_action="runner_finalize_requested",
            consensus_kind="code",
            consensus_mode="light",
            consensus_status="accepted",
            topic_status="accepted",
            review_status="review_pending",
            progress_status="review_pending",
            progress_row_id="main:03",
        ),
        "dependency_fix_target_active": replace(
            base,
            name="dependency_fix_target_active",
            lane="blue-k-other-runner",
            authorized_action="runner_fix_requested",
            consensus_kind="code",
            consensus_mode="standard",
            consensus_status="fix_required",
            topic_status="accepted",
            acceptance_subject_commit=GOOD_WORK_HEAD,
            active_package="docs/mian-k/other/07_sidequest",
            dependency_recovery_target="docs/mian-k/main/02_prereq",
            fix_target="active_package",
            progress_status="review_pending",
            progress_row_id="other:07",
            finding_set_commit="5555555",
        ),
        "dependency_fix_target_prereq": replace(
            base,
            name="dependency_fix_target_prereq",
            lane="blue-k-other-runner",
            authorized_action="runner_fix_requested",
            consensus_kind="code",
            consensus_mode="standard",
            consensus_status="fix_required",
            topic_status="accepted",
            acceptance_subject_commit=GOOD_WORK_HEAD,
            active_package="docs/mian-k/other/07_sidequest",
            dependency_recovery_target="docs/mian-k/main/02_prereq",
            fix_target="dependency_recovery_target",
            progress_status="review_pending",
            progress_row_id="other:07",
            finding_set_commit="6666666",
        ),
        "dependency_fix_target_both": replace(
            base,
            name="dependency_fix_target_both",
            lane="blue-k-other-runner",
            authorized_action="runner_fix_requested",
            consensus_kind="code",
            consensus_mode="full",
            consensus_status="fix_required",
            topic_status="accepted",
            acceptance_subject_commit=GOOD_WORK_HEAD,
            active_package="docs/mian-k/other/07_sidequest",
            dependency_recovery_target="docs/mian-k/main/02_prereq",
            fix_target="both",
            progress_status="review_pending",
            progress_row_id="other:07",
            finding_set_commit="7777777",
            full_mode_reason="dependency recovery touches active and prerequisite packages",
        ),
        "dependency_fix_missing_target": replace(
            base,
            name="dependency_fix_missing_target",
            lane="blue-k-other-runner",
            authorized_action="runner_fix_requested",
            consensus_kind="code",
            consensus_mode="standard",
            consensus_status="fix_required",
            topic_status="accepted",
            acceptance_subject_commit=GOOD_WORK_HEAD,
            active_package="docs/mian-k/other/07_sidequest",
            dependency_recovery_target="docs/mian-k/main/02_prereq",
            progress_status="review_pending",
            progress_row_id="other:07",
            finding_set_commit="8888888",
        ),
        "human_blocked_request_code_fix": replace(
            base,
            name="human_blocked_request_code_fix",
            lane="blue-k-main-runner",
            authorized_action="runner_fix_requested",
            consensus_kind="code",
            consensus_mode="full",
            consensus_status="human_blocked",
            topic_status="open",
            human_decision="request_code_fix",
            active_package="docs/mian-k/main/03_rules",
            progress_status="review_pending",
            progress_row_id="main:03",
        ),
        "human_blocked_request_plan_revision": replace(
            base,
            name="human_blocked_request_plan_revision",
            here_role="cc",
            owner_role="cc",
            lane="blue-k-planner",
            authorized_action="plan_revision_requested",
            consensus_kind="plan",
            consensus_mode="full",
            consensus_status="human_blocked",
            topic_status="open",
            human_decision="request_plan_revision",
        ),
        "human_blocked_cancel_topic": replace(
            base,
            name="human_blocked_cancel_topic",
            lane="blue-k-main-runner",
            authorized_action="runner_finalize_requested",
            consensus_kind="code",
            consensus_mode="full",
            consensus_status="human_blocked",
            topic_status="cancelled",
            human_decision="cancel_topic",
            progress_status="review_pending",
        ),
        "waiver_not_auto_accept": replace(
            base,
            name="waiver_not_auto_accept",
            lane="blue-k-consensus",
            authorized_action="code_consensus_requested",
            consensus_kind="code",
            consensus_mode="light",
            consensus_status="needed",
            topic_status="open",
            auto_accepted=True,
            waiver_used=True,
        ),
        "docs_only_freeze_violation": replace(
            base,
            name="docs_only_freeze_violation",
            lane="blue-k-main-runner",
            authorized_action="runner_finalize_requested",
            consensus_kind="code",
            consensus_mode="light",
            consensus_status="accepted",
            topic_status="accepted",
            acceptance_subject_commit=GOOD_WORK_HEAD,
            docs_only_freeze_ok=False,
            progress_status="review_pending",
        ),
        "acceptance_hash_mismatch": replace(
            base,
            name="acceptance_hash_mismatch",
            lane="blue-k-main-runner",
            authorized_action="runner_finalize_requested",
            consensus_kind="code",
            consensus_mode="light",
            consensus_status="accepted",
            topic_status="accepted",
            acceptance_subject_commit=GOOD_WORK_HEAD,
            acceptance_hash_ok=False,
            progress_status="review_pending",
        ),
        "lower_gate_block_cannot_be_accepted": replace(
            base,
            name="lower_gate_block_cannot_be_accepted",
            lane="blue-k-consensus",
            authorized_action="code_consensus_requested",
            consensus_kind="code",
            consensus_mode="full",
            consensus_status="needed",
            topic_status="open",
            lower_gate_block=True,
            lower_gates_ok=False,
            review_status="review_pending",
        ),
        "consensus_dirty_blocks_runner": replace(
            base,
            name="consensus_dirty_blocks_runner",
            lane="blue-k-main-runner",
            authorized_action="runner_finalize_requested",
            consensus_kind="code",
            consensus_mode="light",
            consensus_status="accepted",
            topic_status="accepted",
            acceptance_subject_commit=GOOD_WORK_HEAD,
            consensus_dirty=True,
            progress_status="review_pending",
        ),
        "full_mode_graph_high_risk": replace(
            base,
            name="full_mode_graph_high_risk",
            lane="blue-k-consensus",
            authorized_action="code_consensus_requested",
            consensus_kind="code",
            consensus_mode="full",
            consensus_status="needed",
            topic_status="open",
            full_mode_reason="code graph high-risk overlay edge changed",
            active_package="docs/mian-k/main/05_graph",
            progress_row_id="main:05",
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
