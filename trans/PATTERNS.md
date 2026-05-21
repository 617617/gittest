# PATTERNS — Reusable design patterns for git-baton presets

Each pattern is independent: pick the ones that apply, skip the rest.
Each section follows the same shape: **Pattern**, **Problem it solves**,
**Shape**, **Reference**.

---

## P1 — Coord-vs-work repo (path X)

**Problem.** Two AIs need an auditable trail of coordination, but the
real code work happens in a different project repo.

**Shape.**
- This repo (`gittest`) hosts the baton mailbox under
  `workflows/<preset>/_coord/{from-cc,from-codex}/`.
- The project's actual code repo is referenced via the
  `<project>:<rel>` prefix and `<project>@<short-sha>` commit anchors.
- Coord artifacts are pointers; they never copy code content across
  repos.

**Reference.** `workflows/temporal-phase/PATHS.md`,
`workflows/temporal-phase/HANDOFF.md` §5.

---

## P2 — PATHS.md per-host table + role binding

**Problem.** Two hosts have different absolute paths to the same logical
repo. Hardcoding paths in every doc creates drift.

**Shape.**
- One file `PATHS.md` carries a host table and a role-to-host binding.
- Two prefixes defined: `gittest:<rel>` and `<project>:<rel>`.
- Commit references use `<project>@<short-sha>` (identical across
  hosts).
- All other docs (CHARTER, ROLES, BATON.schema, lane SKILLs) stay
  machine-independent.

**Reference.** `workflows/temporal-phase/PATHS.md`.

---

## P3 — BATON state machine with explicit invariants

**Problem.** Without explicit structural locks, "max three rounds" or
"second audit one-shot" become documentation prose that AIs drift away
from.

**Shape.**
- A finite state enumeration (every round of an iteration is its own
  state: `PRE_AUDIT_R1`, `PRE_AUDIT_R2`, `PRE_AUDIT_R3`). If `R4` is
  forbidden, do not even define an `R4` state.
- Legal transitions listed one per line.
- Numbered invariants near the bottom: "three-round cap", "second
  audit one-shot", "completion criteria gate", "authority refusal",
  "isolation".

**Reference.** `workflows/temporal-phase/BATON.schema.md`.

---

## P4 — Stable CC-NN IDs for completion criteria

**Problem.** Completion-criteria text drifts between CHARTER and the
closing lane's product template.

**Shape.**
- Each completion criterion gets a stable ID like `CC-NN` in CHARTER.
- The closing lane's product template uses the same IDs and verbatim
  text.
- The verifier extracts `CC-\d{2}` from both files and asserts the sets
  are equal.

**Reference.** `workflows/temporal-phase/CHARTER.md` §"Completion
criteria", `workflows/temporal-phase/skills/temporal-phase-close/SKILL.md`
§"Product structure", `scripts/verify_temporal_phase_skills.py`
"CC-NN cross-check" block.

---

## P5 — Per-lane skill directory

**Problem.** One big SKILL.md per side (CC and Codex) confuses
authority and makes per-lane changes risky.

**Shape.** One directory per (state, driver) combination:
```text
workflows/<preset>/skills/<preset>-<lane>/
  SKILL.md          # frontmatter + Trigger/Reads/Tools/Writes/Authority
  agents/openai.yaml
```

**Reference.** Any directory under
`workflows/temporal-phase/skills/temporal-phase-*/`.

---

## P6 — `## Tools` delegation to a work-repo skill

**Problem.** The "real" work (e.g., generating a package, executing a
runner) is owned by a project-specific skill registered in the work
repo, not in our coord repo. We do not want to re-implement it in the
lane SKILL.

**Shape.** The lane SKILL has a `## Tools` section that:
- names the work-repo skill;
- gives the resolved path of its SKILL.md (via the project prefix);
- explains the work-repo skill's contract (boundaries, output shape,
  required reviews);
- offers two invocation modes (follow procedure inline, or switch CWD
  and invoke the slash command);
- describes the **coord-side product** as a pointer (PackagePath,
  PackageCommit, status) rather than a copy of the work product.

**Reference.** `workflows/temporal-phase/skills/temporal-phase-blueprint/SKILL.md`
§"Tools" (delegates to `temporal-stage-package-generator`),
`workflows/temporal-phase/skills/temporal-phase-execute/SKILL.md`
§"Tools" (delegates to `temporal-package-runner`).

---

## P7 — BatonNext first-line invariant

**Problem.** State transitions need a single deterministic signal that
both AIs and tools can parse.

**Shape.**
- Every baton artifact's first non-empty line is exactly
  `BatonNext: <STATE>`.
- `<STATE>` is in the BATON.schema enumeration; anything else fails
  the artifact checker.
- The artifact checker scans every file under
  `_coord/{from-cc,from-codex}/` on every watcher boot.

**Reference.** `scripts/check_baton_artifacts.py` (the `BATON_NEXT_RE`
regex and `BATON_STATES` set),
`workflows/temporal-phase/ROLES.md` "Conventions" block.

---

## P8 — Authority-mailbox routing

**Problem.** A driver writing into the wrong mailbox (e.g., Codex
writing a CC product into `from-codex/`) corrupts the state machine.

**Shape.**
- Each step-tag (e.g., `blueprint`, `pre-audit-cc-r1`) belongs to
  exactly one mailbox.
- The artifact checker has a `step_tag_belongs_to(tag, mailbox)`
  function listing both sides; a mismatch produces a loud
  `AUTHORITY VIOLATION` error.
- Lane SKILLs all carry an `## Authority` section restating CC-only /
  Codex-only.
- CC-only lanes' `agents/openai.yaml` declare `must refuse` so Codex
  reading the skill-card refuses the lane.

**Reference.** `scripts/check_baton_artifacts.py` `CC_STEP_TAGS` /
`CODEX_STEP_TAGS` lists; `workflows/temporal-phase/BATON.schema.md`
invariant §4.

---

## P9 — Phase-id format + open-Phase concurrency lock

**Problem.** Multiple in-flight units of work in the same preset's
mailboxes scramble state recovery.

**Shape.**
- Unit IDs match a strict regex (e.g., `phase-\d+`).
- Filename pattern enforced: `<unit-id>__<step-tag>.md`.
- The artifact checker enforces "at most one open unit" (open = has
  artifacts but no matching `<unit-id>__close.md`).
- A second concurrent unit is a verifier-time FAIL, not a silent
  duplicate.

**Reference.** `workflows/temporal-phase/CHARTER.md`
§"Phase-id naming and concurrency", `scripts/check_baton_artifacts.py`.

---

## P10 — Watcher skill (`<preset>-watch`)

**Problem.** CC needs to be notified when the other side pushes a new
coord artifact. Polling by hand is fragile.

**Shape.** A `.claude/skills/<preset>-watch/SKILL.md` that:
- pulls origin;
- runs both verifiers + artifact checker;
- arms one persistent Monitor over the preset's `from-codex/` mailbox
  using `git ls-tree origin/master:...` polling at 60s;
- is idempotent (dedup-checks the Monitor by description before
  arming);
- does NOT read `workflows/_active.md` — each preset's watcher is
  independent and can run in parallel with others.

**Reference.** `.claude/skills/temporal-phase-watch/SKILL.md`.

---

## P11 — Orchestrator skill (`<preset>-start`)

**Problem.** The user has to remember a bootstrap sequence, a status
query, a "what now" routing decision, and a Codex bootstrap text. That
is too many things.

**Shape.** A `.claude/skills/<preset>-start/SKILL.md` that:
- ensures the watcher is armed (auto-invokes if not);
- runs all verifiers and reports;
- diagnoses current baton state by reading the latest artifact's
  `BatonNext:` line;
- branches into A (fresh start) / B (in progress) / C (closed) and
  emits the right next-action text including any copy-paste blocks for
  the other host;
- never writes a baton artifact itself — lane skills still own those.

The user's whole surface becomes `/<preset>-start` plus the occasional
Phase-goal description.

**Reference.** `.claude/skills/temporal-phase-start/SKILL.md`.

---

## P12 — Multi-workflow parallel enablement

**Problem.** Multiple workflows in the same repo (e.g., testkit +
temporal-phase + a future blue-project) must coexist without gating
each other.

**Shape.**
- No single "active" pointer that picks one preset. The single-active
  model breaks under multi-project reality. (See ANTI-PATTERNS A1.)
- A workflow is "enabled" by existing on disk with its registered
  skills.
- Each preset has its own watcher and its own orchestrator; all run in
  parallel.
- `workflows/_active.md` is informational only (records the user's
  primary focus); it does not gate anything.
- SessionStart hook lists all available watchers and orchestrators.

**Reference.** `workflows/README.md` §"Enablement",
`.claude/settings.json` SessionStart hook,
`workflows/_active.md`.

---

## P13 — Two-tier verification

**Problem.** Static registration consistency (do skills exist, are they
listed) and runtime state validity (are the actual files in mailboxes
well-formed) are different concerns and rot independently.

**Shape.** Two scripts:

- `scripts/verify_<preset>_skills.py` — static. Run on session boot
  and on CI. Validates registry consistency, presence of required
  files, HANDOFF tables, completion-criterion ID parity.
- `scripts/check_baton_artifacts.py` — runtime. Run on session boot
  (via the watcher) and after any push. Validates filenames, mailbox
  routing, `BatonNext` lines, open-unit count.

Both must pass before arming the watcher's Monitor.

**Reference.** `scripts/verify_temporal_phase_skills.py`,
`scripts/check_baton_artifacts.py`.

---

## P14 — Loosen-then-extend for shared infrastructure

**Problem.** Existing infrastructure (e.g., testkit's verifier) is
strict — it fails on any extra entry. New presets need to add entries
to the shared registry.

**Shape.**
- Loosen the existing verifier with a **single minimal change**: skip
  entries it does not own (e.g., `if name not in EXPECTED_SKILLS:
  continue`), but keep strict on its own entries.
- Each preset writes its own verifier scoped to its own entries.
- Total registry now carries 12 + 15 + ... entries; each verifier
  checks its own slice.

**Reference.** The two-line patch to
`blue-k-git-baton-testkit/scripts/verify_project_scoped_skills.py`
(commit `7c48393`).

---

## P15 — Multi-agent audit method

**Problem.** A single reviewer can miss something. We want
high-confidence checks before declaring a preset "good".

**Shape.** Spawn 3–4 parallel subagents, each with a different angle:

1. **Source-doc fidelity** — does the preset map back to the source
   document's intent without drift?
2. **Workflow correctness** — does the lane structure match the
   user's described workflow point-by-point?
3. **Skill invocation guarantee** — would the registered skills
   actually be invoked at runtime? Where are the silent-failure
   surfaces?
4. **Regression + new-holes** — what previously-known issues remain;
   what new issues did this batch introduce?

Each subagent reads a disjoint slice of files and reports back in
under ~600 words with file:line citations. CC then synthesizes.

**Reference.** This session's audit messages (search the transcript
for "Agent A", "Agent B", "Agent C", "Agent D").

---

## P21 — Lightweight git-tracked friction tracker

**Problem.** While running a baton workflow, an AI notices the
protocol is wrong, ambiguous, or the tooling fights it. Stopping
mid-Phase to triage corrupts focus; emitting only chat complaints
loses the friction forever. A hosted issue tracker (Linear, GitHub
issues) is too heavy for an AI to drive mid-flow.

**Shape.** A plain-text directory `issue/` with two subfolders:

```text
issue/
  README.md                       # template + conventions
  open/<YYYY-MM-DD>__<slug>.md
  closed/<YYYY-MM-DD>__<slug>.md
```

Conventions:
- AIs file an issue at the moment of friction, push, and continue.
  The baton does NOT pause on issue filing.
- Issue file template: Reporter, Workflow, Severity (blocker / major
  / minor / nit), Context, What felt wrong, Suggested fix, Workaround.
- Closing an issue is a `git mv open/ -> closed/` plus a `## Resolution`
  section citing the fix commits.
- HANDOFF documents on each side instruct the AI to file friction
  without blocking the baton.

**Why this works.** The baton workflows already have a "git is the
only truth source" stance. Friction is workflow truth that needs to
live in git, too. By making the format trivial (one markdown file)
and the protocol explicit (no triage gate during filing), AIs are
willing to actually file instead of letting friction silently
accumulate.

**Reference.**
- `issue/README.md` — template + conventions.
- `workflows/temporal-phase/HANDOFF.md` §7.1 — instructions for
  Codex.
- `.claude/skills/temporal-phase-watch/SKILL.md` and
  `temporal-phase-start/SKILL.md` — optionally report open-issue count
  in their status blocks (advisory; does not block).

---

## P20 — Chained units via NextPhasePlan + ChainMode

**Problem.** The user's stated goal: "one Phase as one closed-loop
invocation; when complete, automatically proceed to the next Phase per
the blueprint." Without explicit infrastructure, every Phase-to-Phase
transition forces the user back into the loop to choose phase-id +
goal, breaking the "set it and forget it" promise of chained roadmaps.

**Shape.**
- Closing lane SKILL gets a `NextPhasePlan:` block in its product
  template with fields: `NextPhaseId`, `NextPhaseGoal`,
  `NextSourceAnchor`, `StopReason` (mutually-exclusive with
  `NextPhaseId`).
- `workflows/_active.md` gains a `ChainMode:` line with three values:
  - `auto` — zero-touch advance on every COMPLETED + populated plan.
  - `confirm` — one-click confirmation prompt (recommended default).
  - `off` — never auto-advance.
- Watcher reacts to `NEW_FROM_CODEX: <phase-id>__close.md` by running
  the orchestrator's "Branch C" logic; the orchestrator centralises
  the chain decision tree.
- Hard-stop safety overrides apply regardless of `ChainMode`:
  - BLOCKED close → stop chain.
  - Missing / malformed `NextPhasePlan` → chain ended naturally.
  - `NextPhaseId` collision with live or archived id → stop with loud
    error.
- Verifier validates `ChainMode:` value (only `auto`/`confirm`/`off`
  allowed if the line is present).

**Why centralise in the orchestrator.** The chain decision is the
same whether the user invoked `/temporal-phase-start` manually or the
watcher detected a close.md event. Both paths funnel into the same
Branch C decision tree, so the rules live in one place.

**Reference.**
- Close template: `workflows/temporal-phase/skills/temporal-phase-close/SKILL.md`
  §"Product structure" + §"NextPhasePlan — when to include / when to omit".
- ChainMode field: `workflows/_active.md`,
  `workflows/temporal-phase/CHARTER.md` §"Chain mode and auto-advance".
- Orchestrator decision tree:
  `.claude/skills/temporal-phase-start/SKILL.md` Branch C.
- Watcher event hook:
  `.claude/skills/temporal-phase-watch/SKILL.md` §"Event handling".
- Verifier validation: `scripts/verify_temporal_phase_skills.py`
  ChainMode regex block.

---

## P18 — On-demand sync skill on the non-orchestrator side

**Problem.** CC has a watcher + a one-command orchestrator. The other
side (Codex) only has lane skills, so the user has no single command
to ask "where are we" from that side — and if Codex was offline when
CC pushed a kickoff, there is no mechanism for Codex to catch up on
boot.

**Shape.**
- A Codex-side operational skill (e.g., `temporal-phase-codex-sync`)
  registered in `.codex/skills.json` with `codexLane: true`.
- The skill is **operational**, not a lane: it does NOT produce a
  baton artifact. Document this in the skill's `## Writes` section
  so the verifier's marker check still finds "Writes" but readers know
  no artifact is produced.
- Procedure: pull origin → run verifiers → list mailboxes → find the
  latest artifact's `BatonNext:` → cross-reference against the
  state→lane table → report next action (run lane X / waiting on
  other side / no Phase open).
- The HANDOFF for the non-orchestrator side names this skill as the
  "every session start" entry. The orchestrator side's one-time
  onboarding line mentions it.

**Why it matters.** The non-orchestrator side does not need to stay
online between Phases. The sync skill is how it catches up on
anything pending whenever its CLI boots. This is the symmetric
counterpart of the orchestrator skill's status-query mode.

**Reference.**
`workflows/temporal-phase/skills/temporal-phase-codex-sync/SKILL.md`;
`.codex/skills.json` entry for it;
`workflows/temporal-phase/HANDOFF.md` §2.2 "Boot procedure".

---

## P19 — Archive closed units on close

**Problem.** Mailboxes accumulate artifacts as Phases close. Long-running
projects (50+ closed Phases) hit checker slowdown, status-output
clutter, and reviewer-navigation friction.

**Shape.**
- Archive directory under the coord root, e.g., `_coord/archive/`.
- A script `scripts/archive_phase.py <phase-id>` that:
  - Preconditions: close.md exists with terminal `BatonNext:`; no
    other Phase is open.
  - Action: move all `<phase-id>__*.md` from `from-cc/` and
    `from-codex/` into `_coord/archive/<phase-id>/{from-cc,from-codex}/`.
  - Does NOT commit — the caller does. (Lets the orchestrator wrap
    the move + commit + push in one user-facing step.)
- Artifact checker skips the archive directory (the mailboxes only
  scan their own contents; archive is a sibling).
- The orchestrator's Branch C ("Phase just closed") offers the
  archive step right after reporting the close.
- CHARTER documents the policy in a `## Archival policy` section.

**Why preserve archived files.** Git history retains the move (it's
just a rename), so audit trail is intact. Archived files remain
greppable and `git log -- archive/<phase-id>/` works for forensic
review.

**Reference.**
`scripts/archive_phase.py`;
`scripts/check_baton_artifacts.py` directory-skip;
`workflows/temporal-phase/CHARTER.md` §"Archival policy";
`.claude/skills/temporal-phase-start/SKILL.md` Branch C.

---

## P17 — Kickoff-as-artifact (no chat relay)

**Problem.** The "start signal" of a new unit of work tends to live in
chat as a copy-paste-able instruction the user relays from one host to
the other. Anything that lives only in chat is invisible to the git
history, breaks if a session restarts, and forces the user into a
manual relay role.

**Shape.**
- The orchestrator skill (`<preset>-start`) on the CC side asks the
  user for unit id + goal in chat.
- It then writes a real baton artifact
  `from-cc/<unit-id>__kickoff.md` carrying `BatonNext: <initial-driver
  state>`, commits, and pushes.
- The other side's watcher fires on the new file. Its first lane
  reads the kickoff as its primary input (goal text, source anchor,
  previous-close pointer) and enters the initial state.
- The orchestrator never emits multi-block copy-paste text. The only
  text the user ever relays is a single one-time onboarding line
  (e.g., "you are in `<preset>`, read HANDOFF.md") for a never-before-
  seen session on the other host.

**Constraints.**
- Add `^kickoff$` to the CC step-tag list in the artifact checker (or
  whichever side actually initiates units).
- The first-state lane SKILL must declare the kickoff in its `## Reads`
  and use it as the trigger.
- ROLES.md gains a Step 0 for the kickoff. BATON.schema gains a
  `(no prior state) -> <initial state>` transition driven by the
  kickoff writer.
- HANDOFF on the other side must explicitly say "the kickoff file is
  the only sanctioned Phase start signal; do not start a Phase based
  on chat instructions alone".

**Reference.** Implemented in commit after `c5c4cee`:
- `workflows/temporal-phase/BATON.schema.md` legal transitions +
  driver authority table;
- `workflows/temporal-phase/ROLES.md` Step 0;
- `workflows/temporal-phase/skills/temporal-phase-blueprint/SKILL.md`
  `## Trigger` and `## Reads`;
- `workflows/temporal-phase/HANDOFF.md` §6;
- `.claude/skills/temporal-phase-start/SKILL.md` Branch A;
- `scripts/check_baton_artifacts.py` `CC_STEP_TAGS`.

---

## P16 — One commit per landing batch

**Problem.** Many small commits during exploration mix experiments with
shipped state.

**Shape.** Hold all work in a single working-tree state; commit once
when a recognizable batch is complete, with a body covering:

- what landed (high-level summary);
- what this enables (what the user can now do);
- pointers to follow-ups still queued.

**Reference.** Commits `c158d6e`, `7c48393`, `e091fbd`.
