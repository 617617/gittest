# Doc Review Termination Protocol

Load this file only when `doc-review` returns `TERMINATE` or when iteration
fatigue signals make normal R1/R2/R3 convergence unlikely.

## Diagnose The Spiral

Run or adapt these checks:

```bash
git log --all --oneline -- <plan-dir>/ | wc -l
grep -E "BLOCKED|NO-GO|FAIL|PENDING" <plan-dir>/**/*.md | wc -l
find <plan-dir>/ -name "EXECUTE.md" | wc -l
```

Use the output as evidence. Do not terminate based only on vibes.

## Triage Rules

Rule A: Force Walking Skeleton

- Pick the smallest executable packet.
- Verify it meets Definition of Ready.
- Approve only that packet.
- Defer every other packet.

Rule B: Reclassify NO-GO Items

For each `NO-GO` or `BLOCKED` item, ask whether it can be answered without
executing code.

- If yes, keep it `BLOCKING`.
- If no, reclassify it as `FOLLOW-UP` and move it into execution evidence.

Rule C: Freeze Constitution

- Freeze constraint documents as they exist now.
- Future concerns become amendments, not edits to the main body.

Rule D: Single Owner Decree

- Pick one owner.
- Reviewers may submit findings.
- Only the owner decides what blocks execution.

Rule E: Time Box

- Set an appetite: this plan ships its smallest packet in N days or gets split.
- When the box ends, approved scope executes and the rest is deferred.

## REVIEW_TERMINATION.md Template

Write this file at `<plan-dir>/REVIEW_TERMINATION.md`:

```markdown
# <plan-name> Review Termination

**Date**: <YYYY-MM-DD>
**Iteration count when terminated**: <N>
**Trigger signal**: <which anti-pattern signal fired>

## Approved for Execution
- Packet: <smallest packet path>
- Owner: <name>
- Appetite: <N days>
- Definition of Ready: <X/9 satisfied>

## Reclassified Items
| Original status | Item | New status | Reason |
|---|---|---|---|
| NO-GO 1 | <text> | FOLLOW-UP | Answerable only by execution |
| BLOCKED row 5 | <text> | IMPROVEMENT | Style only, not contract |

## Frozen Constitution
- File: <path>
- Frozen at commit: <hash>
- Future changes: amendments only, no edits to main body

## Deferred to Future Plans
- <list of packets / workstreams not in scope of approved packet>

## Termination Decision
APPROVED FOR EXECUTION (smallest packet only).
Further plan review on this `<name>/` is BLOCKED until first commit lands.
```

After this file is written, do not review the plan again until execution
produces a commit. The next review event is `traceable-review` on that commit.
