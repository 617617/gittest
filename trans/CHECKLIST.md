# CHECKLIST — Ship checklist for a new preset

Run through this when landing a new `workflows/<preset>/`. Tick each
item as it passes. Anything unticked is a known gap; document it
before shipping.

## Pre-flight: design

- [ ] You can describe the workflow in 5–10 lines without rereading the
      source document.
- [ ] You can name the unit of work (Phase / Sprint / etc.) and the
      role split (creative driver vs reviewer vs synthesizer vs
      closure judge).
- [ ] You have decided path X vs path Y and recorded the choice in
      CHARTER.
- [ ] You can list every completion criterion with a stable ID.
- [ ] Iteration bounds are explicit (e.g., "max 3 rounds of audit",
      "second audit one-shot"). They will become BATON.schema
      invariants.

## Files

### `workflows/<preset>/`

- [ ] `CHARTER.md` — goal, scope, completion criteria with `CC-NN`
      stable IDs, isolation statement, **unit-id naming + concurrency
      rule**.
- [ ] `ROLES.md` — step matrix; `Conventions` block names mailbox
      paths, filename pattern, BatonNext convention.
- [ ] `BATON.schema.md` — state enumeration, legal transitions,
      driver authority, **invariants numbered §1..§N**.
- [ ] `PATHS.md` — host table + role-to-host binding + prefix
      convention. No machine paths anywhere else.
- [ ] `HANDOFF.md` — entry point for the other AI; required-reading
      list; state→lane lookup table; hard rules.
- [ ] `_coord/README.md` — mailbox description.
- [ ] `_coord/from-cc/.gitkeep` and `_coord/from-codex/.gitkeep`.
- [ ] `skills/README.md` — lane index.
- [ ] `skills/<preset>-<lane>/SKILL.md` × N — one per lane.
- [ ] `skills/<preset>-<lane>/agents/openai.yaml` × N — one per lane.
- [ ] **`## Tools` section** in every lane that delegates to a work-repo
      skill (Generator, Runner, etc.), naming the work-repo skill.
- [ ] **`Codex must refuse`** appears in `agents/openai.yaml`
      `default_prompt` for every CC-only lane.
- [ ] ROLES.md has a Step 0 — kickoff (CC writes
      from-cc/<unit-id>__kickoff.md with BatonNext:
      <initial-driver-state>).
- [ ] BATON.schema.md has a (no-prior-state) -> <initial-driver-state>
      transition driven by the kickoff.
- [ ] Cross-repo lanes (those that touch both work repo and coord
      repo) carry a "## Push order" section: work-repo push first,
      coord-repo push second.
- [ ] CC-only lanes carry a "## Push procedure" section: write ->
      check -> commit -> pull --rebase -> push (commit-before-rebase
      order).

### `workflows/_active.md`

- [ ] ChainMode: line set to one of {auto, confirm, off} before
      launching the first unit (default: confirm).

### `.codex/skills.json`

- [ ] Each lane appended with a unique `name` and `path` to the lane
      directory.
- [ ] Codex lanes carry `"codexLane": true`. CC lanes do not.
- [ ] Existing presets' entries (e.g., testkit) untouched.

### `.claude/skills/`

- [ ] `<preset>-watch/SKILL.md` — watcher modeled on existing
      examples. **Does not read `_active.md`.**
- [ ] `<preset>-start/SKILL.md` — orchestrator with Branch A / B / C
      logic.
- [ ] `<preset>-watch/SKILL.md` present.
- [ ] `<preset>-start/SKILL.md` present, with Branch A
      (kickoff-artifact, no copy-paste) and Branch C (chain-mode
      decision tree).

### Non-orchestrator side

- [ ] `<preset>-<other>-sync` registered (operational, codexLane:
      true if Codex-side) — provides the catch-up path when the
      other side is offline.

### Cross-cutting

- [ ] `issue/` tracker exists at repo root with README + open/ +
      closed/ subdirs.

### `scripts/`

- [ ] `verify_<preset>_skills.py` — registration verifier.
- [ ] `check_baton_artifacts.py` — runtime artifact validator (this
      can be a shared script across presets if you generalize, or a
      per-preset script if you keep it scoped).
- [ ] `scripts/verify_<preset>_skills.py` PASSes.
- [ ] `scripts/check_baton_artifacts.py` PASSes (treats the new
      preset's mailbox conventions; may need preset-specific
      step-tag additions).
- [ ] `scripts/verify_cross_repo_refs.py` runs and PASSes on hosts
      with a work-repo clone (manual spot-check, not part of default
      flow).

### `.claude/settings.json`

- [ ] SessionStart hook `additionalContext` mentions
      `/<preset>-start` and `/<preset>-watch`.

### `workflows/README.md`

- [ ] "Currently registered presets" list updated.
- [ ] "Quick-start shortcuts" table updated.

## Verification gates

- [ ] `python scripts/verify_<preset>_skills.py` → `PASS`.
- [ ] `python scripts/check_baton_artifacts.py` → `PASS` (mailboxes
      empty is fine).
- [ ] All other presets' verifiers still PASS (run them all).
- [ ] Open a fresh CC session: SessionStart hook surfaces the new
      orchestrator and watcher.
- [ ] Invoke `/<preset>-watch`: Monitor arms; no FAIL.
- [ ] Invoke `/<preset>-start`: it diagnoses state (Branch A) and
      emits the Codex bootstrap text.

## Authority / refusal smoke tests

Run these to confirm the artifact checker catches violations:

- [ ] Drop a fake file named `phase-99__pre-audit-codex-r1.md` into
      `from-cc/` with content `Hello`. Run
      `python scripts/check_baton_artifacts.py`. Expect two FAILs:
      `AUTHORITY VIOLATION` and `first non-empty line must be
      BatonNext: <STATE>`. Delete the file.
- [ ] Drop `phase-99__blueprint.md` into `from-codex/` with first line
      `BatonNext: BLUEPRINT_REVISION_R1`. Expect a FAIL on the
      authority side (Codex should not declare CC-driver states from
      Codex products is acceptable but check the policy you wrote);
      at minimum the runtime artifact checker confirms the state name
      is valid.
- [ ] Drop two files for two different phase-ids without close.md.
      Expect FAIL: "more than one open Phase".

## Multi-agent audit (optional but recommended)

Before shipping, spawn 3–4 parallel subagents along these angles
(see PATTERNS P15):

- [ ] Source-document fidelity.
- [ ] Workflow correctness vs user's described flow.
- [ ] Skill invocation guarantee (would registered skills actually be
      invoked at runtime?).
- [ ] Regression + new-holes audit.

Address every flagged item or queue it explicitly as a follow-up.

## Ship

- [ ] Single commit with a descriptive title and body summarizing what
      landed, what it enables, and what is queued.
- [ ] Push to `origin/master`.
- [ ] Tell the other AI on the other host to `git pull` and restart
      its CLI so the new lanes register.
- [ ] Run `/<preset>-start` to smoke-test the entry.

## After ship

- [ ] First unit of work (e.g., "Phase 0 — workflow smoke test") goes
      through every state without manual baton fixes.
- [ ] Any drift discovered during the first unit is folded back into
      the preset (lane SKILLs, CHARTER, verifier).
