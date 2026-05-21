# AUDIT-LESSONS — what we learned from auditing temporal-phase

This file collects the **meta-lessons** from the audit cycles run
against the temporal-phase preset (commits ~`7c48393`, ~`f7ef41c`,
~`2296680`, and the post-`2296680` resilience audit). They are not
about "what's wrong with this codebase" — those go in
`ANTI-PATTERNS.md`. They are about **how to audit a baton workflow**
and **what surprised us each time**.

## Lesson 1 — Audits surface different kinds of problems at different stages

Each multi-agent audit round revealed a distinct class of issue:

| Round | What was being audited | Class of problem surfaced |
|-------|------------------------|---------------------------|
| Round 1 (right after Level 2 registration) | Static registration + workflow conformance | counts drift; markers missing; minor wording |
| Round 2 (after English translation) | Translation fidelity vs the original | accidental semantic drops; missing carve-outs |
| Round 3 (after chain mode + resilience layer) | Procedural integrity (push order, atomicity) | runtime race conditions; non-atomic state transitions; mythical assumptions about Codex CLI |

Plan an audit cadence that runs **after every meaningful protocol
addition**, not just "at the end". The earlier protocol-level mistakes
get caught, the cheaper they are to fix.

## Lesson 2 — Multi-agent audit shines on disjoint angles, fails on overlap

Four parallel angles in Round 3 (smoke / chain semantics / cross-
cutting consistency / Codex CLI assumptions) all returned different
findings. **None of the four reports duplicated another agent's
finding.** That worked because the prompts pre-partitioned the
concerns.

When prompts overlap, parallel agents waste cycles auditing the same
slice and produce conflicting recommendations on the same files. Two
practical guards:

- Each agent's prompt enumerates the **exact files** it should read.
  Other agents' files are off-limits.
- When dispatching parallel **fix-up** agents (not just audit
  agents), the file-ownership boundary is even stricter — concurrent
  edits to the same file produce stale-state errors. Pre-segment by
  directory or by file. See PATTERNS P15. Concrete example from this
  preset's fix-up batch: one agent owned `trans/` only, the other
  owned `workflows/temporal-phase/` + `scripts/`. Zero merge
  conflicts.

## Lesson 3 — "We say X happens" ≠ "X actually happens"

The single biggest finding (the "mythical Codex watcher") was a case
where protocol prose stated an autonomous behavior — Codex's watcher
fires on push — that was never verified and almost certainly does
not exist. The system was relying on it implicitly.

Rule of thumb: every sentence in protocol docs that says **"the other
side will X automatically"** is a candidate for an "are we sure?"
audit. If the answer is "we never tested it", either test it before
shipping, or rewrite the protocol so the user invokes X explicitly.

Practical mitigation patterns:

- Replace autonomous claims with sync-driven semantics ("on next
  `/<preset>-sync`, the AI sees X and reacts").
- Add a **fallback modes** section to every operational skill
  documenting what to do when a CLI feature is restricted (slash not
  recognised; subprocess blocked; push requires confirmation). The
  goal is "fail loudly, never silently corrupt".

## Lesson 4 — Counts in prose drift, and the verifier should catch them

After 5-6 batches of changes, the count of registered skills, the
count of states, the count of completion criteria, and the count of
patterns all developed drift in at least one cross-reference. The
recurring fix is "update HANDOFF / README / PATTERNS to say N+1
instead of N".

Better: let the verifier extract counts programmatically (e.g.,
count `temporal-phase-*` entries in `.codex/skills.json` rather than
hardcoding "16" in prose). When the verifier can't, an explicit
cross-check assertion (like the CC-NN ID parity check) at least
detects drift the next time something changes.

When you can't programmatically derive a count, **don't write the
count in prose at all** — write "one per X" or "see <source file>
for the list". See ANTI-PATTERNS A2 for the original HANDOFF
state-count drift incident that triggered this lesson.

## Lesson 5 — Push-order discipline is the most common operational mistake

In a path-X workflow with two repos, the order of pushes determines
recoverability. The audit kept surfacing variants of this:

- "Coord push succeeded but work repo didn't" → dangling
  `<project>@<sha>` reference; consumer audit lane breaks; messy.
- "Work repo push succeeded but coord didn't" → recoverable; just
  retry coord push. State hasn't advanced from any consumer's view.

Always: **substantive content first (work repo), pointer second
(coord repo)**. Document this in every lane SKILL that touches two
repos. Add a verifier (`verify_cross_repo_refs.py`) for the manual
spot-check. See PATTERNS P22.

## Lesson 6 — Check-before-push, not check-after-push

Early drafts of `/temporal-phase-start` ran the artifact checker
AFTER `git push`. That meant: if the checker FAILed, the corrupted
state was already on origin/master. Recovery required `git revert` or
re-pushing a fixed file.

Better order:

1. Write the artifact to the working tree.
2. Run the checker against the working tree.
3. If FAIL, revert locally (no push happened).
4. If PASS, `git pull --rebase`, commit, push.

The check + revert are pre-push gates. The push is the last action.

## Lesson 7 — Multi-step state transitions must be atomic at the commit level

The first Branch C chain-advance design archived in one commit and
wrote the next kickoff in a second commit. A network drop between
the two would leave the chain in an unrecoverable half-state:
archive on origin, kickoff stranded locally with no in-progress
marker.

Fix: combine into one commit. `git add -A` after both file operations
are done locally, single `git commit -m "chain: archive X +
kickoff Y"`, one push. If the push fails, the local commit is intact
and re-pushable; if it succeeds, both moves landed atomically.

Generalisation: **any baton step that mutates more than one file
should land in one commit, not two**. Reviewers can split the commit
later if they want; the protocol guarantee is atomic transition.

## Lesson 8 — Prose-level "must X" without code is not enforcement

Several "must refuse" / "must not collide" / "must include X" rules
existed only as English sentences in SKILLs. The audit caught real
gaps: refusal had no runtime gate; collision detection had no actual
logic. Each gap was a foot-gun waiting for the first user mistake.

Either:

- Layer an actual check (script, verifier, regex) that produces an
  error when the rule is violated; OR
- Acknowledge in the doc that the rule is advisory-only and explain
  the recovery path.

Hand-waving the difference between rule-as-doc and rule-as-gate is
where the protocol leaks credibility.

## Lesson 9 — Audit prompts that name files + scenarios beat audit prompts that ask "find issues"

The audits that returned the highest signal-to-noise were the ones
where the prompt specified:

- exactly which files to read (so the agent doesn't wander),
- a concrete scenario to trace step-by-step ("user opens window,
  runs /X, network drops, ..."),
- a verdict format per item (PASS / GAP / RISK with one-sentence
  evidence).

Vague prompts like "audit the workflow for problems" returned vague
answers. Specific prompts returned actionable findings with file:line
citations.

## Lesson 10 — Skills grow over iterations; refactor when they cross 150-200 lines

Every time we layered a new safety mechanism (Tools delegation,
push-order, crash-recovery, Fallback modes, atomic chain, collision
helpers), the affected SKILL.md grew. By round 5, the orchestrator
`temporal-phase-start/SKILL.md` had ballooned to 425 lines — well past
the threshold where a reader can hold it in working memory.

Symptom: the AI loads the entire SKILL.md into context every time the
skill is invoked, including pages of detail it does not need for the
current branch / state. Even an in-context model wastes attention on
irrelevant procedure.

Fix: **progressive disclosure**. The SKILL.md stays a thin dispatcher
(80-120 lines) covering:
- frontmatter,
- when to invoke,
- high-level steps (1-3 setup, then route),
- pointers to `references/<topic>.md` for the detail.

Detail (decision trees, full procedures, helper code blocks, fallback
modes, recovery paths) lives in `references/` subdirectory files,
each self-contained and loaded on demand based on the current branch
or scenario.

Watch for the trigger to refactor:
- SKILL.md > 200 lines → likely past the threshold; review.
- SKILL.md contains > 3 distinct concerns (e.g., Tools + Push order +
  Crash recovery + Fallback modes) → each concern wants its own
  reference file.
- One section is > 50 lines → consider extracting it.

Round-5 refactor results (committed in the same batch as this
lesson):
- `temporal-phase-start/SKILL.md`: 425 → 116 lines (Branch A/B/C
  decision trees + collision helper extracted to 3 references).
- `temporal-phase-watch/SKILL.md`: 178 → target ~100 lines.
- `temporal-phase-codex-sync/SKILL.md`: 162 → target ~100 lines.
- `temporal-phase-blueprint/SKILL.md`: 171 → target ~100 lines.
- `temporal-phase-execute/SKILL.md`: 181 → target ~100 lines.

Each verifier-checked marker (e.g., `BatonNext`, `## Tools`,
work-repo skill name) was preserved in the SKILL.md text; only
"second-tier" detail moved to references. See PATTERNS P23 for the
durable pattern.

## How to use this file

When designing the next preset (or the next major change to
temporal-phase), skim this file first. Each lesson is a checklist
item: have you considered counts drift? push order? check-before-
push? atomicity? mythical autonomy? prose-only enforcement?

When something here turns out to have a counter-example (a case
where the lesson doesn't apply), append a "Caveat" subsection to that
lesson, don't delete it. The lessons live forever; the caveats
sharpen them over time.
