---
name: temporal-phase-blueprint
description: Codex creates the Phase execution blueprint. Trigger DRAFTING_BLUEPRINT; reads the source document and the previous Phase's close.md; writes from-codex/<phase-id>__blueprint.md; BatonNext = PRE_AUDIT_R1.
---

# temporal-phase / blueprint (Codex lane)

## Trigger
- Baton state: `DRAFTING_BLUEPRINT`, entered when a new
  `from-cc/<phase-id>__kickoff.md` lands carrying
  `BatonNext: DRAFTING_BLUEPRINT`. Do not draft until you see one.

## Reads
- `workflows/temporal-phase/_coord/from-cc/<phase-id>__kickoff.md` —
  Phase id, goal, source-doc anchor, optional previous-close pointer.
- Authoritative source document (anchor path at the top of
  `workflows/temporal-phase/CHARTER.md`, resolved via `PATHS.md`).
- Previous Phase's `from-codex/<prev-phase-id>__close.md` if named.
- The Generator contract — see `## Tools` below; do **not** hand-roll
  a blueprint from imagination.

## Tools

Delegate to the work-repo Codex skill
`temporal-stage-package-generator`. This lane is only the coord-side
pointer; the Generator's package writes go to the work repo.

Two invocation paths exist (no-CWD-switch follow-procedure, or
explicit `CWD = temporal:` + `/temporal-stage-package-generator`).

Full contract (Generator SKILL.md locations, package shape, status
enum, required inputs, mandatory multi-agent review, coord-side
product format): see `references/tools-generator.md`.

## Writes
- `workflows/temporal-phase/_coord/from-codex/<phase-id>__blueprint.md`
  — the pointer file shaped per `references/tools-generator.md` §3.
- First line `BatonNext: PRE_AUDIT_R1`.
- The actual package directory is written by the Generator inside the
  work repo, not into this coord mailbox.

## Push order
Work-repo push first, then coord-repo push. Full procedure +
first-push-failure / second-push-failure recovery + the
`CROSS_REPO_MISSING_REF` audit-side error and `verify_cross_repo_refs.py`
helper live in `references/push-order.md`.

## Path rules
Code references use the `temporal:<rel>` / `temporal@<sha>` prefixes
**only**; never write absolute machine paths. See `PATHS.md` for the
prefix resolution table.

## Authority
This lane is Codex-only. CC must not write a blueprint into
`from-codex/`. CC contributions belong in the `pre-audit-cc` lane.

## See also
- `references/tools-generator.md` — full Generator delegation contract
- `references/push-order.md` — cross-repo push order + recovery
- `CHARTER.md` · `ROLES.md` Step 1 · `BATON.schema.md` state
  `DRAFTING_BLUEPRINT` · `HANDOFF.md`
