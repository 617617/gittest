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

## P16 — One commit per landing batch

**Problem.** Many small commits during exploration mix experiments with
shipped state.

**Shape.** Hold all work in a single working-tree state; commit once
when a recognizable batch is complete, with a body covering:

- what landed (high-level summary);
- what this enables (what the user can now do);
- pointers to follow-ups still queued.

**Reference.** Commits `c158d6e`, `7c48393`, `e091fbd`.
