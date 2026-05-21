# PLAYBOOK — Converting a workflow document into a git-baton preset

End-to-end recipe distilled from the temporal-phase conversion. Seven
steps; each step lists the **input**, **output**, and the **gate** that
proves the step is done.

## Step 0 — Confirm the workflow fits

Before doing anything else, check the scope rules in `README.md`. If the
target workflow does not have two AI roles or does not need
git-auditable coordination, stop and use a simpler tool (a single skill,
a slash command, a script).

## Step 1 — Read the source workflow document end-to-end

**Input.** A document describing the workflow (typically Markdown,
typically in the target project's `docs/` somewhere).

**Output.** Three things written down (on scratchpad or in chat, not yet
in files):

1. The **unit of work** (e.g., Phase, Sprint, Release, Ticket).
2. The **roles** and what each role does (creative driver vs. reviewer
   vs. synthesizer vs. closure judge). The temporal-phase source had an
   asymmetric split: CC synthesizes pre-execution, Codex synthesizes
   post-execution. Watch for this — it usually isn't symmetric.
3. The **terminal conditions**: what counts as "done", what counts as
   "blocked", what is the upper bound on iteration (almost every
   workflow has one).

**Gate.** You can describe the workflow in 5–10 lines without re-reading
the source. If you can't, read again.

## Step 2 — Decide coord-vs-work repo (path X vs path Y)

**Input.** Where does the real code work happen? Same repo as
coordination, or different?

**Decision.**

- **Path X (different repos, recommended for cross-project workflows):**
  coordination artifacts live in this `gittest`-style repo; code
  changes happen in the target project repo; the two are linked by
  commit SHA and a `<project>:<rel>` prefix convention defined in
  `PATHS.md`. Reuse the existing baton infrastructure here. This is
  what temporal-phase uses.
- **Path Y (same repo):** coord artifacts live inside the target
  project; the project carries its own state machine. Higher
  isolation but no infra reuse.

**Output.** Path choice recorded in the new CHARTER.

**Gate.** You can answer: "where does the AI write the blueprint?
where does the AI commit the code change?" If those two answers
involve different repos, you're on path X.

## Step 3 — Distill source → CHARTER + ROLES + BATON.schema

This is the heart of the conversion. Three files:

### 3a. CHARTER.md

Capture the **goal, scope, completion criteria, and isolation
statement**. Completion criteria get **stable IDs** (`CC-01`, `CC-02`,
…) — both the CHARTER and the closing lane SKILL must use the same
IDs. The verifier cross-checks the sets.

Template: `templates/CHARTER.template.md`.
Reference: `workflows/temporal-phase/CHARTER.md`.

### 3b. ROLES.md

A **step matrix**: each row is one step in the workflow, columns are
`step #`, `step name`, `driver`, `input`, `product`, `mailbox`.

Every product file has:

- a filename pattern `<unit-id>__<step-tag>.md`;
- a first line `BatonNext: <STATE>`.

Template: `templates/ROLES.template.md`.
Reference: `workflows/temporal-phase/ROLES.md`.

### 3c. BATON.schema.md

The **state machine**:

- state enumeration (every distinct state the workflow can be in,
  including terminal `COMPLETED`, `BLOCKED_*`);
- legal transitions (one per line, `FROM_STATE -> TO_STATE`);
- driver authority (who can drive each transition);
- **invariants** (the structural locks — bounded iteration, one-shot
  branches, completion gates).

Template: `templates/BATON.schema.template.md`.
Reference: `workflows/temporal-phase/BATON.schema.md`.

**Gate.** All three files exist; ROLES Step Matrix step tags ↔
BATON.schema states map cleanly; CHARTER completion criteria match the
closing-state condition in BATON.schema.

## Step 4 — Author PATHS.md (host table + role binding)

PATHS.md pins **per-host paths** (coord repo + work repo) and
**role-to-host bindings**. Documents reference work-repo paths only
via prefix (`<project>:<rel>`), never absolute machine paths.

Template: `templates/PATHS.template.md`.
Reference: `workflows/temporal-phase/PATHS.md`.

**Gate.** Every host that will participate has a row. Each role has a
host assignment. No hardcoded machine paths appear in CHARTER / ROLES /
BATON.schema.

## Step 5 — Author per-lane SKILLs (the actual procedure)

For every distinct (state, driver) combination in BATON.schema, create
**one skill directory** under `workflows/<preset>/skills/<preset>-<lane>/`:

- `SKILL.md` — YAML frontmatter (`name`, `description`) + body sections
  in this fixed order: `## Trigger`, `## Reads`, `## Tools` (if the lane
  delegates to a work-repo skill), `## Writes`, `## Product structure`,
  `## Authority`, `## See also`.
- `agents/openai.yaml` — `interface.display_name`, `short_description`,
  `default_prompt`; `policy.allow_implicit_invocation: false`.

For lanes whose "real work" is done by a work-repo skill (e.g., a
package generator or runner), include a `## Tools` section that:

- names the work-repo skill;
- gives the resolved path of its SKILL.md;
- offers two invocation modes (follow procedure inline / switch CWD);
- describes the **coord-side product** (a pointer file, not a copy of
  the work product).

For CC-only lanes, the `agents/openai.yaml` `default_prompt` must
contain the literal phrase `must refuse` so the verifier picks it up as
a refusal declaration.

Templates: `templates/lane-SKILL.template.md`,
`templates/lane-agents-openai.template.yaml`.
References: `workflows/temporal-phase/skills/temporal-phase-blueprint/SKILL.md`
(Codex creative lane with `## Tools`),
`workflows/temporal-phase/skills/temporal-phase-pre-audit-cc/SKILL.md`
(CC-only lane).

**Gate.** Every state in BATON.schema that has a driver has exactly one
lane skill. Every lane skill is in the correct mailbox-side authority.

## Step 6 — Registration + verifier + artifact checker

Two scripts and one config:

- `.codex/skills.json` — append one entry per lane, with `codexLane: true`
  for Codex lanes. Do not change `skillRoot` or `allowGlobalFallback`
  if the existing testkit is sharing the file (testkit verifier strict-
  checks those; the entry-list check was relaxed to allow extras).
- `scripts/verify_<preset>_skills.py` — static registration check. Must
  verify: every expected lane present in skills.json; each entry has
  SKILL.md + agents/openai.yaml; CC lanes carry refusal; CHARTER ↔
  closing-lane SKILL CC-NN IDs match; HANDOFF state→lane table covers
  every Codex lane with the right pairing.
- `scripts/check_baton_artifacts.py` (one file, shared across presets
  if you generalize, or per-preset if scoped tightly) — runtime
  validator: filename matches `<unit-id>__<step-tag>.md`; `unit-id`
  format regex; step-tag is in the right mailbox; first line
  `BatonNext: <STATE>` and STATE is enumerated; at most one open Phase.

Templates: `templates/verify-preset-skills.template.py`,
`templates/check-baton-artifacts.template.py`.

**Gate.** Both scripts run with exit 0 against the new preset. Existing
preset verifiers (e.g., testkit's) still pass.

## Step 7 — Watcher skill + orchestrator skill + SessionStart hook

- `.claude/skills/<preset>-watch/SKILL.md` — pulls origin, runs both
  verifiers + artifact checker, arms a persistent Monitor over the
  preset's `from-codex/` mailbox. Idempotent. Does NOT read
  `workflows/_active.md` (each preset's watcher is independent).
- `.claude/skills/<preset>-start/SKILL.md` — single-command
  orchestrator. Diagnoses baton state, emits the right next action
  including any copy-paste text the user needs to send to the other
  side. The user only has to remember this one command per preset.
- `.claude/settings.json` — SessionStart hook lists all available
  watchers and start orchestrators so a new session is auto-oriented.

Templates: `templates/watch-skill.template.md`,
`templates/start-skill.template.md`.
References: `.claude/skills/temporal-phase-watch/SKILL.md`,
`.claude/skills/temporal-phase-start/SKILL.md`.

**Gate.** Open a new Claude Code session in the repo: SessionStart hook
mentions the new `/<preset>-start`; invoking it diagnoses state
correctly; invoking `/<preset>-watch` arms the monitor; running both
verifiers + the artifact checker returns PASS.

## Step 8 — Smoke run the first unit of work

Pick a trivial first unit (e.g., "Phase 0: validate the preset
end-to-end with a no-op change"). Walk it through the full state
machine. At each transition, run `check_baton_artifacts.py` to catch
typos early.

**Gate.** The first unit reaches `COMPLETED` (or you intentionally
abort to `BLOCKED_*` for testing) without manual fixes to baton state.

## After landing

- Update `workflows/README.md` "Currently registered presets" list.
- Update `workflows/README.md` "Quick-start shortcuts" table.
- Commit + push.
- Tell the other AI (on the other host) to `git pull` and restart its
  CLI so the new lanes register.
