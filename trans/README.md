# trans/ — Transferable experience for git-baton workflow conversion

This directory is the **playbook + pattern catalog + anti-pattern list**
for converting a project's collaborative workflow document into a
git-baton-driven dual-AI workflow under `workflows/<preset>/`.

It was distilled from one full conversion: the Temporal project's Phase
collaborative workflow → `workflows/temporal-phase/` (see commits
`c158d6e` through `e091fbd`). Future conversions (e.g., a `blue-project`
preset) should start here.

## Scope

This playbook applies when **all** of these are true:

- The target workflow has two AI roles that need to coordinate (one
  acting as creative driver, the other as independent reviewer /
  closure judge).
- The coordination should be auditable via Git history (commits, mailbox
  files, BatonNext lines).
- The work happens in a project repo that is **different** from the
  coordination repo (path X model). The two link via commit SHA and
  prefix references.
- Each AI runs on its own host (so dual sessions in parallel).

It does **not** apply when:

- A single AI is sufficient (use a regular skill, not a workflow
  preset).
- Coordination is real-time chat-only, with no auditable artifact trail.
- The two AIs share the same host AND the same repo (use a simpler
  per-task skill instead).

## Layout

```text
trans/
  README.md          # this file
  PLAYBOOK.md        # 7-step end-to-end recipe
  PATTERNS.md        # reusable design patterns with rationale
  ANTI-PATTERNS.md   # what we tried that did not work + why
  CHECKLIST.md       # quick pre-flight + ship checklist
  templates/         # copy-and-adapt file skeletons
    CHARTER.template.md
    ROLES.template.md
    BATON.schema.template.md
    PATHS.template.md
    HANDOFF.template.md
    lane-SKILL.template.md
    lane-agents-openai.template.yaml
    verify-preset-skills.template.py
    check-baton-artifacts.template.py
    watch-skill.template.md
    start-skill.template.md
```

## When to use

- You are starting the conversion of a new workflow document into a
  `workflows/<preset>/` preset. → Read PLAYBOOK end-to-end, then copy
  templates and follow CHECKLIST.
- You are mid-conversion and unsure how to encode a particular flow
  decision. → Look up PATTERNS by topic.
- Something feels off about a design choice. → Cross-check
  ANTI-PATTERNS.

## Reference implementation

Everything here points back to `workflows/temporal-phase/` for a
concrete example. When in doubt about how a pattern *actually* looks in
files, open the matching file under that preset.

| Concept | Reference file |
|---------|----------------|
| Charter | `workflows/temporal-phase/CHARTER.md` |
| Role matrix | `workflows/temporal-phase/ROLES.md` |
| State machine | `workflows/temporal-phase/BATON.schema.md` |
| Host paths | `workflows/temporal-phase/PATHS.md` |
| Codex entry | `workflows/temporal-phase/HANDOFF.md` |
| Codex creative lane | `workflows/temporal-phase/skills/temporal-phase-blueprint/SKILL.md` |
| CC-only lane | `workflows/temporal-phase/skills/temporal-phase-pre-audit-cc/SKILL.md` |
| Registration verifier | `scripts/verify_temporal_phase_skills.py` |
| Runtime artifact checker | `scripts/check_baton_artifacts.py` |
| Watcher | `.claude/skills/temporal-phase-watch/SKILL.md` |
| Orchestrator | `.claude/skills/temporal-phase-start/SKILL.md` |
| Skill registry | `.codex/skills.json` |

## Conventions

- **Language:** all written artifacts (this dir, workflow docs, lane
  SKILLs, scripts) are English-only. Chat with the user can be in
  whatever language they prefer.
- **Determinism:** every fact that must hold across files is verified
  by a script (verifier or artifact checker), not by hand.
- **Isolation:** new presets do not modify other presets' files. The
  testkit and temporal-phase are independent neighbors; a third preset
  must keep the same property.
