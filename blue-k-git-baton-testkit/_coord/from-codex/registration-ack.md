# Codex Project-Scoped Skill Registration Ack

Status: PASS

I am Codex. Lane: blue-k-main-runner blue-k-other-runner blue-k-other-index.
v0.10 test-prep acknowledged.

Project-scoped registration source:

```text
.codex/skills.json
```

Skill root:

```text
blue-k-git-baton-testkit/skills/
```

Codex-owned lanes:

```text
blue-k-main-runner
blue-k-other-runner
blue-k-other-index
```

Verification performed:

- Read `HANDOFF_CODEX_PROJECT_SCOPED_SKILLS.md`.
- Read `HANDOFF_CODEX_V0_10_TEST_PREP.md`.
- Read `references/ai-chat-contract.md`.
- Confirmed the portable skill closure exists under project-relative paths.
- Confirmed the three Codex-owned lane skills include `AI Chat Contract (v0.10)`.
- Confirmed no global Codex skill directory is needed for this testkit.
- Added `.codex/skills.json` as a repo-local registration manifest with
  `allowGlobalFallback: false`.
- Added `scripts/verify_project_scoped_skills.py` to make the project-scoped
  registration check repeatable.

Commands:

```powershell
python blue-k-git-baton-testkit\scripts\verify_project_scoped_skills.py
powershell -ExecutionPolicy Bypass -File blue-k-git-baton-testkit\scripts\bk.ps1 sync
powershell -ExecutionPolicy Bypass -File blue-k-git-baton-testkit\scripts\bk.ps1 sync -Coverage
powershell -ExecutionPolicy Bypass -File blue-k-git-baton-testkit\scripts\bk.ps1 work
```

Notes:

- I did not copy skills to a global Codex registry.
- I did not write Codex config outside this repository.
- Headless `codex.exe` in this desktop environment was present but not directly
  launchable from PowerShell due an access-denied runtime error, so unattended
  execution remains a wrapper/runner integration item rather than part of this
  project-scoped skill registration ack.
