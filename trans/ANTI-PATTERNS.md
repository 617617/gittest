# ANTI-PATTERNS — What we tried that did not work

Each entry: **What we did**, **Why it broke**, **What we changed it
to**. These are real mistakes from the temporal-phase conversion;
encountering them again is a signal to stop and rethink.

---

## A1 — Single `_active.md` pointer to gate which workflow is "live"

**What we did.** `workflows/_active.md` carried `Active: <preset>`. The
SessionStart hook read it and branched to one watcher. The
`<preset>-watch` skill read it as "Step 0" and bailed if the value
didn't match. The verifier strict-asserted `Active: temporal-phase`.

**Why it broke.** The mental model assumed "only one workflow is live
at any moment". As soon as the user said "we want to develop temporal
and blue in parallel", the model fell over: switching `_active.md` to
`temporal-phase` would kill the testkit watcher, and switching back
would kill the temporal-phase one. Two presets cannot coexist.

**What we changed it to.** Each preset has its own watcher and
orchestrator. Watchers do not read `_active.md`. Enablement is by
directory existence + registered skills. `_active.md` is downgraded to
"informational only — primary focus hint". The SessionStart hook lists
all watchers; CC picks the relevant ones. See PATTERNS P12.

**Lesson.** Single-pointer "active" models are a code smell whenever
the system might serve more than one customer at a time. Default to
per-customer state, not global state.

---

## A2 — Hardcoded state count in HANDOFF

**What we did.** HANDOFF.md wrote "(24 states + legal transitions + 5
invariants)". The actual enumeration had 25 states.

**Why it broke.** Miscount caught by Agent D's regression audit. Drift
between "number written in prose" and "actual enumeration count" is
guaranteed if you don't tie them.

**What we changed it to.** Fixed to 25. **The deeper fix is in P13:
the verifier should programmatically count states from a single source
of truth.** That fix is queued, not yet in.

**Lesson.** Any number that humans type into prose has a probability
of drifting. If the number matters, derive it; if it doesn't matter,
do not write it.

---

## A3 — `Codex must refuse` only as a default_prompt string

**What we did.** CC-only lanes' `agents/openai.yaml` `default_prompt`
includes the phrase "Codex must refuse...". We assumed Codex reading
the skill card would refuse.

**Why it's weak.** It is a prompt string, not a runtime gate. A
determined or sloppy invocation could still write into the wrong
mailbox. The verifier only checks that the literal string appears;
that does not enforce behavior at write time.

**What we layered on.** The artifact checker enforces
mailbox-routing at file-write detection time (`AUTHORITY VIOLATION`
error). The default_prompt remains as defense-in-depth, not as the
gate.

**Lesson.** Prompt-text discipline is a layer, not a guarantee. Always
back it with a runtime check.

---

## A4 — "BatonNext" rule documented in prose only

**What we did.** The first-line `BatonNext: <STATE>` convention was
explained in ROLES.md and HANDOFF.md as a rule humans would follow.
No script enforced it.

**Why it broke.** Agent D's regression audit flagged this as HIGH:
typos like `BatonNext: PRE_AUDIT_R4` or omission of the line would go
undetected, and the state machine would silently corrupt. The whole
baton mechanism depends on this line being correct.

**What we changed it to.** `scripts/check_baton_artifacts.py`
parses the first non-empty line of every artifact against
`^BatonNext:\s+([A-Z_0-9]+)\s*$`, validates the state is in the
enumerated set, and exits non-zero with the offending file listed.
The watcher runs the checker before arming. See PATTERNS P7.

**Lesson.** Any invariant that the state machine relies on must be
checked by code. Documentation describes the rule; the code enforces
it.

---

## A5 — Single SKILL.md per side (one for CC, one for Codex)

**What we did.** Originally `skills/cc/SKILL.md` and
`skills/codex/SKILL.md` aggregated all lanes per side.

**Why it broke at scale.** With 5 CC lanes and 10 Codex lanes, each
file was getting long and section boundaries within the file did
double duty as "lane boundaries". Editing one lane risked touching the
text of a neighbor. Skill registration requires one entry per
invocable lane, so aggregation didn't help Codex CLI's discovery
anyway.

**What we changed it to.** One directory per lane:
`workflows/<preset>/skills/<preset>-<lane>/SKILL.md`. 15 directories.
The skills/README.md became an index of them. See PATTERNS P5.

**Lesson.** "One file, many sections" is fine for small N. The moment
N > ~5 and each section has its own contract, split into one file per
section.

---

## A6 — Generator/Runner not mentioned by name in lane SKILLs

**What we did.** First draft of `temporal-phase-blueprint/SKILL.md`
said "Codex creates the Phase blueprint" without referencing the
work-repo skill `temporal-stage-package-generator` by name.

**Why it broke.** Codex on Host B has `temporal-stage-package-generator`
registered as a real skill in the project repo. If the lane SKILL
doesn't tell Codex to invoke that skill, Codex will hand-roll a
"blueprint" from imagination instead of running the Generator's
standard procedure (which has its own `BLOCK→GENERATION_BLOCKED`
terminal, multi-reviewer requirement, and standard output shape).
That is silent divergence between what was supposed to happen and
what actually happens.

**What we changed it to.** Added a `## Tools` section that names the
work-repo skill, gives its SKILL.md path, summarizes its contract,
and offers two invocation modes. The verifier now enforces that the
named skill appears in the SKILL.md text. See PATTERNS P6.

**Lesson.** Delegation must be explicit. "Codex will figure it out" is
not delegation; it is hope.

---

## A7 — Hardcoded paths in lane SKILLs

**What we did.** Early drafts had `cd E:\code\temporal && pytest ...`
literally in lane SKILLs.

**Why it broke.** That works only on Host A. Host B uses
`D:\code\temporal`. Cross-host machine paths in shared docs are
guaranteed drift.

**What we changed it to.** All docs use `<project>:<rel>` prefixes
and `<project>@<short-sha>` commit refs. Resolution is per-host via
`PATHS.md`. The verifier scans each SKILL folder for absolute machine
paths and rejects them (except in `PATHS.md` itself). See PATTERNS P2.

**Lesson.** Any document that two hosts will read must be
machine-independent. PATHS.md is the one allowed place for machine
paths.

---

## A8 — Strict testkit verifier blocking new presets

**What we did.** The testkit's verifier strict-asserted "skills.json
must contain exactly the testkit's 12 entries — no more, no less".

**Why it broke.** Adding a new preset's 15 entries to the same
`.codex/skills.json` made the testkit verifier FAIL on those entries
as "extras".

**What we changed it to.** One small patch: the testkit verifier
ignores entries it does not recognize (it continues to strict-check
the 12 it owns). The new preset writes its own verifier scoped to its
15. See PATTERNS P14.

**Lesson.** Strict equality on a shared registry is hostile to growth.
Each verifier owns its own slice; verify what is yours, ignore the
rest.

---

## A9 — Bash-specific Monitor command without noting the shell

**What we did.** The Monitor command in `temporal-phase-watch/SKILL.md`
used `comm -13 <(...) <(...)` (bash process substitution).

**Why it would have broken.** On a Windows host where the harness ran
the command under `cmd.exe` or PowerShell, process substitution does
not exist; the command would have silently emitted no events.

**What we changed it to.** Step 5 explicitly notes "Shell: bash
(required)" and explains how to wrap with `bash -c '...'` if the
default shell differs.

**Lesson.** When you use shell-specific syntax, name the shell.

---

## A10 — Asking the AI for a blueprint after we built a workflow that says only Codex writes blueprints

**What we did.** During development, the user asked CC ("you draft the
blueprint"). The schema we had just locked in said: blueprint is a
Codex lane; CC writing it to `from-codex/` is an authority violation.

**Why it was a trap.** Without pushback, CC could have produced a
"blueprint" in violation of the very invariants we wrote. The schema
would be undermined on its first real use.

**What we did instead.** Surfaced the authority conflict explicitly,
gave the user three options (route to Codex, draft as a labeled
example outside `from-codex/`, or amend the schema), and waited for
direction. The user chose "never mind".

**Lesson.** When the user asks you to do a thing that contradicts a
rule the user themselves agreed to, do not silently do it. Surface
the contradiction. The user usually wants the rule preserved more
than they want the immediate action.

---

## A11 — Forgetting Codex can't see the Generator from a coord-repo session

**What we did.** Initial plan assumed `/temporal-stage-package-generator`
would just work from `D:\code\gittest`.

**Why it broke.** `.codex/skills.json` has `allowGlobalFallback: false`.
The Generator lives in `D:\code\temporal\.codex\skills\` (the work
repo). A Codex CLI booted in the coord repo only sees the 27
project-scoped skills there; it does **not** see the work-repo
skills.

**What we resolved it to.** Lane SKILLs document two invocation modes:
(A) follow the Generator's SKILL.md procedure inline (no slash command
needed — Codex re-executes the steps in the work repo), or (B) open a
second Codex session in the work repo and invoke the slash command
there. Either works; A is recommended because it avoids context
switching.

**Lesson.** When delegating to another skill, do not assume cross-repo
visibility. State both how-to paths in the lane SKILL.

---

## A12 — Mid-session memory drift: "all MD must be English"

**What we did.** Wrote a workflow preset entirely in Chinese over many
turns. User then said "all MD must be English; persistent memory".

**Why it caused rework.** We had to translate ~20 files in a follow-up
batch. The translation itself was fine, but it consumed a session
turn that could have been useful work.

**What we changed it to.** Updated memory file
(`feedback_language.md`) with an explicit rule: chat replies in
Chinese, but all written artifacts (MD, YAML, SKILL.md, README,
HANDOFF, schemas, agents YAML) in English. Future sessions inherit
this.

**Lesson.** When in doubt about output language for an artifact, ask
once at the start, save the answer to memory, and apply consistently.
Translating later is mechanical but wasteful.
