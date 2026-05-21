# skills/ — temporal-phase lane skills (registered)

One skill directory per baton lane, **15 in total**, all registered in
`.codex/skills.json` and validated by
`scripts/verify_temporal_phase_skills.py`.

## Layout

```text
skills/
  temporal-phase-<lane>/
    SKILL.md              # YAML frontmatter + trigger / reads / writes / BatonNext
    agents/openai.yaml    # display_name / short_description / default_prompt
```

## The 15 lanes (in baton order)

### Codex (10)
- `temporal-phase-blueprint` — DRAFTING_BLUEPRINT
- `temporal-phase-pre-audit-codex` — PRE_AUDIT_R{1,2,3}
- `temporal-phase-execute` — EXECUTING
- `temporal-phase-postexec-subagent-review` — POSTEXEC_SUBAGENT_REVIEW
- `temporal-phase-postexec-synthesize` — POSTEXEC_SYNTHESIS
- `temporal-phase-postexec-fix` — POSTEXEC_FIX
- `temporal-phase-second-audit-decision` — SECOND_AUDIT_DECISION
- `temporal-phase-second-audit-codex` — SECOND_AUDIT_CODEX
- `temporal-phase-second-audit-fix` — SECOND_AUDIT_FIX
- `temporal-phase-close` — PHASE_CLOSING

### CC (5)
- `temporal-phase-pre-audit-cc` — PRE_AUDIT_R{1,2,3}
- `temporal-phase-pre-audit-synthesize` — PRE_AUDIT_SYNTHESIS_R{1,2,3}
- `temporal-phase-blueprint-revise` — BLUEPRINT_REVISION_R{1,2,3}
- `temporal-phase-postexec-cc` — POSTEXEC_CC_REVIEW
- `temporal-phase-second-audit-cc` — SECOND_AUDIT_CC

## Invocation convention

- **Codex side.** Codex CLI reads `.codex/skills.json` and registers the
  10 lanes marked `codexLane: true`; each can be triggered directly via
  `/<lane-name>`. The 5 CC-only lanes are present so Codex knows they
  exist, but their `agents/openai.yaml` declares "Codex must refuse";
  if asked to take one of them, Codex must decline.
- **CC side.** CC looks up the current baton state in `ROLES.md` Step
  Matrix to find the corresponding lane name, then `Read`s
  `SKILL.md` to follow the lane's procedure.

## Verification

```bash
python scripts/verify_temporal_phase_skills.py
```

Expect `PASS: temporal-phase skills verified`. Any change that adds,
removes, or renames a lane must update both `.codex/skills.json` and
this verifier's `EXPECTED_SKILLS` set.
