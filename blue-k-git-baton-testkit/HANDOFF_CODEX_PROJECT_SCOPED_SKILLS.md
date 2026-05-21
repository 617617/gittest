# Handoff: Codex — Register Blue-K Skills Project-Scoped Only

Audience: the Codex agent that will participate in v0.10 baton testing on
617617/gittest.

From: CC (Claude) working in the same repository.

## Why this handoff exists

For this testkit we want Codex's Blue-K skills to live **strictly inside this
repository's relative paths**, not under any global Codex registry, home
directory, or machine-wide skill store. That keeps the testkit portable, lets
me coordinate with you through git alone, and avoids the "works on my
machine" problem.

So: please register the skills project-scoped. Do not promote any of them to
a global Codex skill location.

## The hard rule

```text
All Blue-K skill discovery must resolve through paths under:

    blue-k-git-baton-testkit/skills/

relative to the repository root.

No copy into a global Codex skills directory.
No symlink into a home-directory skill store.
No machine-specific absolute path.
```

If your current Codex setup cannot scope skills to a project-relative path,
stop and tell the human in chat. Do not "work around" by registering
globally — that breaks the whole point of this testkit.

## Read first, in this order

```text
AGENTS.md
blue-k-git-baton-testkit/SKILL.md
blue-k-git-baton-testkit/HANDOFF.md
blue-k-git-baton-testkit/HANDOFF_BLUE_K_WORKFLOW_SKILL_BUNDLE.md
blue-k-git-baton-testkit/HANDOFF_CODEX_V0_10_TEST_PREP.md
blue-k-git-baton-testkit/references/protocol-v0.10.md
blue-k-git-baton-testkit/references/ai-chat-contract.md
blue-k-git-baton-testkit/references/scenario-matrix.md
```

Then your three lane skills:

```text
blue-k-git-baton-testkit/skills/blue-k-main-runner/SKILL.md
blue-k-git-baton-testkit/skills/blue-k-other-runner/SKILL.md
blue-k-git-baton-testkit/skills/blue-k-other-index/SKILL.md
```

Each lane skill now has an `AI Chat Contract (v0.10)` section at the top.
The v0.10 contract is normative — see `references/ai-chat-contract.md`.

## Project-local skill closure

The minimum portable closure you must be able to invoke, every entry resolved
relative to the repo root:

```text
blue-k-git-baton-testkit/skills/blue-k-planner/
blue-k-git-baton-testkit/skills/blue-k-plan-audit/
blue-k-git-baton-testkit/skills/blue-k-main-runner/
blue-k-git-baton-testkit/skills/blue-k-other-runner/
blue-k-git-baton-testkit/skills/blue-k-other-index/
blue-k-git-baton-testkit/skills/traceable-plan/
blue-k-git-baton-testkit/skills/pre-doc-review/
blue-k-git-baton-testkit/skills/stage-loop-auto/
blue-k-git-baton-testkit/skills/stage-loop/
blue-k-git-baton-testkit/skills/doc-review/
blue-k-git-baton-testkit/skills/traceable-review/
```

You own runtime invocation on the Codex side for these three lanes:

```text
blue-k-main-runner
blue-k-other-runner
blue-k-other-index
```

CC owns `blue-k-planner` and `blue-k-plan-audit`. If `bk sync` selects one
of those, refuse per the wrong-window rule in `ai-chat-contract.md`.

## Each skill already ships its own Codex metadata

Every skill folder contains an `agents/openai.yaml` file. Example
(`blue-k-main-runner/agents/openai.yaml`):

```yaml
interface:
  display_name: "Blue K Main Runner"
  short_description: "Run Blue-K main trunk packages serially."
  default_prompt: "Use $blue-k-main-runner to continue the Blue-K main package queue."
policy:
  allow_implicit_invocation: false
```

Use these YAML files as-is. They were authored alongside the SKILL.md files
to give Codex the registration metadata it needs without any extra step from
you. If your discovery requires a different schema field, adapt only the
discovery-side wrapper; do not edit the workflow semantics inside the skill
folders.

## Registration steps (project-scoped)

You know your own discovery mechanism better than I do. Whatever you use,
make sure the registration matches these rules:

1. **Project root anchor.** Skill resolution must start at the repository
   root that contains `blue-k-git-baton-testkit/`. Use a relative path like
   `./blue-k-git-baton-testkit/skills`. Never use `~`, `$HOME`,
   `%USERPROFILE%`, `C:\Users\...`, or any path outside this repo.
2. **No copying.** Do not duplicate any `SKILL.md` or `agents/openai.yaml`
   outside `blue-k-git-baton-testkit/skills/`. Register by pointing at the
   existing files in-place.
3. **No global config writes.** Do not write any Codex/OpenAI config files
   outside this repository. If a per-project config file is needed, place
   it inside the repo (e.g. `.codex/`) and add a one-line entry to
   `.gitignore` only if it contains machine-specific cache state — never
   ignore the registration itself.
4. **Run from repo root.** Both `codex` interactive and `codex exec`
   invocations must be launched with `--cd .` (or equivalent) anchored to
   this repository, so relative paths resolve correctly.
5. **Headless mode uses the same skills.** `codex exec` should resolve
   skills against the same project-relative paths. The `--sandbox
   workspace-write` mode is the right default for this testkit; reserve
   `danger-full-access` for isolated runners.

If your Codex tooling needs a `codex-skills.json` or similar file, write it
to a path like:

```text
.codex/skills.json
```

and reference each skill by its repo-relative folder. Do not place this
file outside the repository.

## Verification — what "project-scoped" looks like in practice

After registration, all of these must be true:

- [ ] Running `codex` interactive from the repository root lets you invoke
      `$blue-k-main-runner`, `$blue-k-other-runner`, and
      `$blue-k-other-index` by name.
- [ ] The same invocations from any other working directory either fail or
      route through an explicit `--cd <repo-root>` argument; they must not
      succeed by falling back to a globally registered copy.
- [ ] Renaming or deleting `blue-k-git-baton-testkit/skills/` breaks skill
      discovery completely. If discovery still succeeds after deletion,
      something is registered globally — please find and remove it.
- [ ] No file outside this repository was created or modified by the
      registration step.
- [ ] `git status` after registration shows changes only inside this repo
      (and, ideally, only inside `.codex/` if you used that pattern).

Run the wrapper to confirm round-trip:

```powershell
.\blue-k-git-baton-testkit\scripts\bk.ps1 sync
.\blue-k-git-baton-testkit\scripts\bk.ps1 sync -Coverage
```

The `WindowMatch` line in the output should name one of your three lanes
when the simulator picks a Codex scenario.

## How I (CC) will coordinate with you for the actual test

I plan to drive the test through `bk sync` and the BATON, not through chat
DMs. Concretely:

1. The human runs `bk sync` and pastes the printed `ChatCommand` into
   whichever AI window the simulator selects.
2. When the lane is one of yours, you do **one safe assignment** per the
   v0.10 contract (self-announce, self-check, do the work, push atomically,
   write next holder into BATON, close with `Done. Now run: bk sync`), then
   stop.
3. When the lane is one of CC's, I do the same on my side.
4. We never edit each other's files in the same invocation. Coordination
   travels only through:

   ```text
   origin/blue-k/coordination:.blue-k/BATON.yaml
   ```

   plus the work branch.
5. For meta-work on the testkit itself (this doc, the protocol, the skill
   files), we'll use commit messages and PR-style diffs as the
   coordination channel. If you need to change a file I authored in the
   testkit, please push a commit; I'll see it on `git fetch`. Same the
   other direction.

If you ever need a synchronous decision from me before pushing, write the
question into a new file under:

```text
blue-k-git-baton-testkit/_coord/from-codex/<short-topic>.md
```

and push to a branch named `coord/from-codex/<short-topic>`. I'll see it
when I `git fetch`, answer in a sibling file, and push back. This keeps
both sides asynchronous, observable, and reviewable.

## The walk-through plan

Once you've finished registering project-scoped:

1. Acknowledge readiness using the exact string from
   `HANDOFF_CODEX_V0_10_TEST_PREP.md` section 9:

   ```text
   I am Codex. Lane: blue-k-main-runner blue-k-other-runner blue-k-other-index.
   v0.10 test-prep acknowledged.
   ```

2. The human will run `bk sync`. Whatever the simulator decides, we follow
   it through. We'll walk the scenario list in
   `HANDOFF_CODEX_V0_10_TEST_PREP.md` section 8 — start with the easy
   `ready_codex_main`, then move into the refusal/precondition scenarios,
   then takeover, then consensus, then dependency recovery.

3. After each scenario, the human pastes your reply (or its diff against
   expectation) back to me through git or chat so I can confirm. If we
   diverge, I'll write a short note under `_coord/from-cc/` and we'll
   reconcile before continuing.

4. When we've walked the full list with no surprises, the protocol is
   green-lit and we can think about the v0.11 autonomy work in
   `references/autonomy-proposal.md`.

## Stop and report instead of registering if

- the only available Codex skill mechanism is global;
- registration would require writing outside this repository root;
- any of the skill folders or YAML files listed above are missing;
- `references/protocol-v0.10.md` or `references/ai-chat-contract.md` is
  missing;
- `bk sync` does not run or does not produce a `WindowMatch` line.

In any of those cases, write a short note describing the blocker into:

```text
blue-k-git-baton-testkit/_coord/from-codex/blocker-<topic>.md
```

push to a branch named `coord/from-codex/blocker-<topic>`, and stop.

## Final acceptance

The registration is acceptable when:

- skill discovery resolves only through repo-relative paths;
- deleting `blue-k-git-baton-testkit/skills/` breaks discovery;
- no global Codex config was created or modified;
- `bk sync` printed `WindowMatch` correctly selects a Codex chat for
  Codex-owned scenarios and a CC chat for CC-owned scenarios;
- you can produce the acknowledgement string above on demand;
- you have read and understood the AI Chat Contract.

When all six are true, push a small commit adding your name and a short
note to:

```text
blue-k-git-baton-testkit/_coord/from-codex/registration-ack.md
```

I'll see it on fetch and we'll start the walk-through.
