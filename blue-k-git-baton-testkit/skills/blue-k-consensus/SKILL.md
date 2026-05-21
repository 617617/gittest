---
name: blue-k-consensus
description: "Run the Blue-K docs-only consensus lane for plan synthesis and code review synthesis under docs/mian-k/_consensus topic directories. Use when bk sync routes /bk work to blue-k-consensus for plan consensus after audit, code consensus after runner checkpoint, full-mode review, light auto-accept validation, human-blocked synthesis, or acceptance/fix_required decisions."
---

# Blue K Consensus

## Purpose

Run one docs-only consensus assignment selected by `bk sync`. This skill
synthesizes plan-review or code-review inputs and records the decision under:

```text
docs/mian-k/_consensus/<topic-id>/
```

It must not execute packages, edit business source, update runner progress
tables, or bypass lower gates.

## AI Chat Contract (v0.10)

This skill runs only inside a Blue-K baton chat selected by `bk sync`. Three
hard rules apply on every invocation -- full text in
`blue-k-git-baton-testkit/references/ai-chat-contract.md`:

1. **First reply** begins with `I am <CC|Codex>. Lane: <lane>.` before any
   tool call or repo read. The human matches this against the `WindowMatch`
   hint printed by `bk sync`.
2. **Wrong-window input must refuse.** If this chat does not match the
   `ChatTarget` printed by the latest `bk sync`, do not acquire a lease,
   edit files, or call any Blue-K skill; reprint the correct
   `ChatTarget` / `ChatCommand` and stop.
3. **Finalize with a fixed closing line.** After one safe assignment, push
   the work branch and coordination branch atomically, write the next
   holder into `BATON.yaml`, and end the reply with exactly
   `Done. Now run: bk sync`. Do not chain into the next package, lane, or
   assignment.

For `/bk takeover`, no destructive recovery may begin before the human types
`yes, abandon` in this chat.

## Inputs

Read the latest `bk sync` decision fields before acting:

```text
ConsensusKind:
ConsensusMode:
ConsensusStatus:
TopicStatus:
SubjectCommit:
AcceptanceSubjectCommit:
AutoAccepted:
ActivePackage:
ProgressRowId:
FixTarget:
DependencyRecoveryTarget:
FindingSetCommit:
```

Consensus kinds:

- `plan`: synthesize plan review after `blue-k-plan-audit` PASS or accepted
  WARN. CC/Claude normally owns plan synthesis.
- `code`: synthesize code/package review after a runner checkpoint. Codex
  normally owns code synthesis.

Consensus modes:

- `light`: allowed only for clean code consensus where every lower gate and
  role signal is PASS and there is no waiver/substitute input.
- `standard`: default plan consensus or code fix decision path.
- `full`: required for accepted audit WARN, code graph high-risk changes,
  dependency recovery touching multiple targets, or human-blocked decisions.

## Hard Gates

Stop without accepting consensus when any of these are true:

- lower gate is `BLOCK`;
- topic is superseded or cancelled;
- `SubjectCommit` is missing or no longer matches the reviewed subject;
- accepted consensus lacks `AcceptanceSubjectCommit`;
- `AcceptanceSubjectCommit` differs from `SubjectCommit`;
- canonical acceptance hash does not match exact commit blobs;
- non-consensus files changed between `SubjectCommit` and `AcceptanceCommit`;
- consensus draft is dirty or unpushed;
- waiver/substitute input attempts light auto-accept;
- dependency recovery fix lacks `FixTarget`;
- human-blocked state lacks a clear human decision.

## Allowed Writes

Between `SubjectCommit` and `AcceptanceCommit`, write only under:

```text
docs/mian-k/_consensus/<topic-id>/
```

Do not edit:

- source files;
- package docs outside the consensus topic directory;
- `MAIN_PACKAGE_PROGRESS.md`;
- `OTHER_MIN_PACKAGE_PROGRESS.md`;
- audit reports;
- runner evidence files;
- BATON snapshots outside the coordination update.

## Decisions

Write one explicit decision:

```text
accepted
fix_required
planner_repair
human_blocked
cancelled
```

Rules:

- Plan critical/BLOCK returns to `planner_repair`.
- Code critical/BLOCK returns to `fix_required`.
- `accepted` must bind the exact `SubjectCommit`.
- `fix_required` must bind `FindingSetCommit`; dependency recovery must also
  bind `ActivePackage`, `DependencyRecoveryTarget`, and `FixTarget`.
- Accepted code consensus unlocks runner finalization only. It does not start
  the next package.

## Stop Conditions

Stop and report the exact failure code if:

- `LOWER_GATE_BLOCK_CANNOT_BE_ACCEPTED`
- `CONSENSUS_TOPIC_SUPERSEDED`
- `CONSENSUS_TOPIC_CANCELLED`
- `ACCEPTANCE_SUBJECT_COMMIT_REQUIRED`
- `ACCEPTANCE_SUBJECT_COMMIT_MISMATCH`
- `ACCEPTANCE_HASH_MISMATCH`
- `CONSENSUS_FREEZE_VIOLATION`
- `CONSENSUS_DIRTY_DRAFT`
- `AUTO_ACCEPT_NOT_ALLOWED`
- `FIX_TARGET_REQUIRED`
- `REVIEW_FAILED_NEEDS_DECISION`

## Final Report

Report:

- consensus kind and mode;
- topic path;
- subject commit;
- decision;
- files changed under `_consensus`;
- next holder/lane selected by BATON;
- any failure code.

End with the fixed closing line only after the assignment is safely pushed and
BATON names the next holder.


