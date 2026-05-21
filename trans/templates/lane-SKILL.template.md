# lane SKILL.md templates

Two variants follow. Pick the one matching the lane's role.

---

## Variant 1 — Codex creative lane that delegates to a work-repo skill

```markdown
---
name: <preset>-<lane>
description: <one-line description of what this lane does, what it reads, what it writes, and the BatonNext value.>
---

# <preset> / <lane> (Codex lane)

## Trigger
- Baton state: `<STATE>`

## Reads
- `<input files this lane reads, including prior mailbox products>`
- You must follow the `## Tools` section below — do not hand-roll the
  output from imagination.

## Tools — Delegate to the <Work-Repo Skill Name>

The actual producer is the work-repo-registered Codex skill
`<work-repo-skill-name>`. This lane is only the coord-side pointer.

### 1. The work-repo skill's contract (authoritative source)

Skill SKILL.md location (resolved via the `<project>:` prefix in
`PATHS.md`):

```text
<project>:.codex/skills/<work-repo-skill-name>/SKILL.md
```

Read it before opening this lane. It defines:
- `<allowed repo scope>`
- `<output shape>`
- `<mandatory pre/post review>`
- `<terminal block states>`

### 2. Invocation paths

Given that Codex-side `.codex/skills.json` has
`allowGlobalFallback: false`, pick one of:

- **Option A (recommended, no CWD switch).** Read the work-repo
  skill's SKILL.md and follow its procedure step-by-step in the work
  repo. That is exactly what the skill's prompt is doing.
- **Option B (explicit CWD switch).** Open a second Codex session
  with CWD = `<project>:` and run `/<work-repo-skill-name>` there.

### 3. coord-side product (what this lane writes)

The coord side carries one pointer file:

```text
BatonNext: <next state>

# <unit-id> — <Lane Display Name>

<PointerField1>: <project>:<path>
<PointerField2>: <project>@<short-sha>
<StatusField>: <enum>
<ReviewVerdictField>: PASS | BLOCK_<reason>

# Summary
<short fields summarizing the work-repo product>
```

### 4. Push order (cross-repo consistency)

Lanes that write commits in both the work repo and the coord repo
must push in this strict order:

1. **First**, push the work repo:
   ```bash
   cd $(<work-repo-prefix>:)
   git push origin <work-branch>
   ```
   Confirm exit 0 before continuing.
2. **Only then**, push the coord repo:
   ```bash
   cd $(gittest:)
   git push origin master
   ```

If the first push fails, do NOT push the coord repo — retry the
work-repo push first. If the second push fails (work pushed, coord
not), baton state has not advanced from any consumer's view; simply
retry the coord push. The reverse order leaves a dangling
`<work-repo-prefix>@<sha>` reference that breaks the downstream audit
lane with `CROSS_REPO_MISSING_REF`. The standalone
`scripts/verify_cross_repo_refs.py` walks both mailboxes + archive and
flags any unreachable reference. See PATTERNS P22.

## Writes
- `from-codex/<unit-id>__<step-tag>.md` (the pointer file)
- First line `BatonNext: <STATE>`.

## Authority
Codex-only. CC must not write this product into `from-codex/`.

## See also
`CHARTER.md` · `ROLES.md` Step `<#>` · `BATON.schema.md` state
`<STATE>` · `HANDOFF.md`
```

---

## Variant 2 — CC-only lane (audit, synthesis, repair)

```markdown
---
name: <preset>-<lane>
description: <one-line description.>
---

# <preset> / <lane> (CC lane)

## Trigger
- Baton state: `<STATE>`, with `<precondition: which mailbox files
  must already exist>`.

## Reads
- `<input files>`

## Writes
- `from-cc/<unit-id>__<step-tag>.md`
- First line `BatonNext: <STATE>`.

## Product structure
```text
BatonNext: <STATE>

<sections specific to this lane>
```

## Push procedure

Same shape as `/<preset>-start` Branch A (commit-before-rebase):

1. `python scripts/check_baton_artifacts.py` — must PASS against the
   working tree. On FAIL, `rm` the new file and stop.
2. `git add` the new product file.
3. `git commit -m "<step-tag>(<unit-id>): <brief>"`.
4. `git pull --rebase origin master` (tree is clean now).
5. `git push origin master`.

If rebase conflicts or push is rejected, surface and stop.

## Authority
CC-only. Codex must refuse — `<why>`.

## See also
`ROLES.md` Step `<#>` · `BATON.schema.md` state `<STATE>`
```

---

Both variants require a matching `agents/openai.yaml` (see
`templates/lane-agents-openai.template.yaml`).
