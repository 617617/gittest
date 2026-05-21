BatonNext: DRAFTING_BLUEPRINT

# Phase phase-r — Kickoff

PhaseId: phase-r
StartedBy: CC (Host A)
StartedAt: 2026-05-21T13:48:16Z

Goal:
Sidecar evidence backfill per Phase R R0 decision (`BACKFILL_PHASE_R1_R4`):
produce retrospective package-runner completion evidence for roadmap
Phases 1-4 (R1 Local Skill Bundle, R2 Shared Contracts, R3 StageWorkflow,
R4 PackageWorkflow). Each retrospective package must label evidence as
retrospective backfill (`run_phase: exploration`,
`result_included_in_paper: false`), not original historical execution.
Phase R must resolve before Phase 13A admits locked benchmark data,
unless a limitation is pre-registered in Phase 11.

SourceAnchor:
temporal:docs/skill-temporal-reorchestration/current/PHASE_R_R0_DECISION_ZH_2026-05-19.md
(cross-ref: temporal:docs/skill-temporal-reorchestration/current/execution/STAGE_LOOP_AUTO_EXECUTION_QUEUE_ZH_2026-05-16.md
row R, current cursor "Sidecar decision: Phase R R0 = BACKFILL_PHASE_R1_R4")

PreviousPhaseClose:
N/A (first Phase under the temporal-phase coord workflow; the work-repo
roadmap's most recent archived package is
temporal:docs/skill-temporal-reorchestration/stage-loop-auto-packages/history/2026-05-21-completed-phase-11-evaluation-protocol/)

Notes for Codex (blueprint lane):
- Follow `workflows/temporal-phase/skills/temporal-phase-blueprint/SKILL.md`.
- Its `## Tools` section delegates to the work-repo skill
  `temporal-stage-package-generator`. Generator SKILL.md resolves
  via `PATHS.md` to
  `temporal:.codex/skills/temporal-stage-package-generator/SKILL.md`.
- Use phase-id `phase-r` consistently in package-id selection
  and product filenames.
