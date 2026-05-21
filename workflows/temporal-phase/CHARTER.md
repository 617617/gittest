# temporal-phase — Charter

## Source document

`E:/code/temporal/docs/skill-temporal-reorchestration/current/execution/PHASE_COLLABORATIVE_EXECUTION_WORKFLOW_ZH_2026-05-21.md`

This preset is the "dual-AI git-collaboration mapping" of that source
document. The source remains the single authoritative text; this directory
only carries an **operational distillation** — turning the prose flow into
steps that a baton state machine can drive. When the source changes,
update ROLES and BATON.schema first.

## Unit of work

Phase. A Phase is considered closed only after the full lifecycle
(blueprint → pre-execution audit → execution → post-execution dual audit
→ acceptance / blocked) has run. The baton state machine in this preset
is that lifecycle.

## Flow highlights (distilled from §2–§10)

1. **Blueprint first.** For every Phase, Codex creates an executable
   blueprint stating goal, scope, allowed files, validation, expected
   artifacts, and risk boundary.
2. **Pre-execution collaborative audit.** Codex and CC each audit the
   blueprint from their own angle; CC synthesizes both sides.
3. **Blueprint repair.** CC absorbs valid findings and updates the plan.
   If the issues are many or severe, run another round.
4. **Audit loop is bounded to three rounds.** After round 3, if blockers
   remain, stop and re-assess Phase scope.
5. **Execution.** Codex drives execution strictly inside the accepted
   blueprint; it does not widen scope. If a significant gap shows up,
   stop and record rather than expand.
6. **Codex multi-subagent post-execution review.** Multiple angles on the
   execution result.
7. **CC independent post-execution review.** A separate viewpoint.
8. **Synthesis and repair.** Findings converge at Codex; Codex absorbs
   valid items and repairs; invalid / out-of-scope items still need an
   explicit disposition record.
9. **Optional second dual audit.** If post-execution repair is large or
   touches the core path, run one extra dual-audit round. Not unlimited.
10. **Completion criteria.** See the §Completion criteria section.

## Completion criteria (distilled from §11)

A Phase closes only if **all** of the following hold. Each criterion has
a stable ID (`CC-NN`); `temporal-phase-close/SKILL.md` and
`scripts/verify_temporal_phase_skills.py` must reference the same IDs.

- **CC-01** — The blueprint passed the pre-execution collaborative audit.
- **CC-02** — Execution did not exceed the confirmed scope, or any
  deviation was explicitly recorded and re-confirmed.
- **CC-03** — Codex completed execution and produced the execution
  report.
- **CC-04** — Codex subagents completed the post-execution review.
- **CC-05** — CC completed the independent post-execution review.
- **CC-06** — Codex synthesized both sides and absorbed the valid
  findings.
- **CC-07** — Required repairs and re-validation are complete (N/A if
  the synthesis Adopted set was empty).
- **CC-08** — If a large or high-risk repair happened, one extra
  dual-audit + repair cycle has completed (N/A if the
  second-audit-decision was NO).
- **CC-09** — Blockers are cleared; remaining risks have explicit
  recording and follow-up ownership.

## Phase-id naming and concurrency

- **Format.** Every Phase carries a `phase-id` matching the regex
  `phase-\d+` (e.g., `phase-01`, `phase-12`). The phase-id is chosen
  by CC in the kickoff artifact (see ROLES Step 0) and consumed by
  Codex in the blueprint lane.
- **One open Phase at a time.** A Phase is "open" from the moment its
  first artifact (the kickoff) lands in `from-cc/` until a matching
  `<phase-id>__close.md` is written by Codex. Two phase-ids may **not**
  both be open at the same time. To start the next Phase, the previous
  Phase must be closed.
- **Enforcement.** `scripts/check_baton_artifacts.py` walks both
  mailboxes and fails the run if (a) any filename does not match
  `<phase-id>__<step-tag>.md`, (b) any phase-id violates the regex, or
  (c) more than one open Phase exists. The `temporal-phase-watch` skill
  runs this checker on every session boot, so violations surface
  immediately.

## Archival policy

Closed Phases (`COMPLETED` or `BLOCKED_*`) accumulate artifacts. Letting
them sit in the live mailboxes makes the artifact checker scan stale
files and clutters status output. The policy:

- Once `<phase-id>__close.md` lands with a terminal `BatonNext:`, the
  Phase becomes eligible for archival.
- `scripts/archive_phase.py <phase-id>` moves all of that Phase's
  artifacts from `from-cc/` and `from-codex/` into
  `_coord/archive/<phase-id>/{from-cc,from-codex}/`, preserving the
  original mailbox split.
- Git history is preserved (a move is just a rename); the archived
  artifacts remain auditable via `git log`.
- The artifact checker ignores `_coord/archive/`; only the live
  mailboxes are validated.
- The archival step is offered by `/temporal-phase-start` Branch C
  after a Phase closes. Skipping archival is allowed but not
  recommended — long-running mailbox bloat will eventually slow
  reviews.

## Isolation from blue-k-git-baton-testkit

- This preset does **not** depend on the testkit's scripts, skills,
  `_coord/`, or protocol files.
- This preset does **not** modify any file inside the testkit.
- The two coexist in the repo; the testkit does not read
  `workflows/_active.md`.
- Any proposal to bridge testkit and this preset is a separate discussion
  and is **not** in scope for this preset.

## Out of scope for this preset

- Running Temporal code in real time (that belongs inside the Temporal
  project itself).
- Cross-project generic workflow abstractions. We intentionally do not
  abstract — get one preset right first.
- Workflow meta-tooling (e.g., a `workflow-onboard` generator). Save that
  for distillation from this preset's running samples.
