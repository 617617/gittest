#!/usr/bin/env python3
"""Verify reference files under SKILL.md directories.

Closes R2 (cross-reference rot) from the round-5 audit risk register.
Two checks:

1. **Required markers.** Each reference file has a list of load-bearing
   tokens (state names, command idioms, error names, etc.) that MUST
   appear. If a refactor drops one, the cross-reference has rotted.

2. **Broken-link scan.** Every `references/<name>.md` mention in a
   SKILL.md or sibling reference must resolve to an existing file.

Run manually, or as part of `/temporal-phase-watch` step 3.6.

Exit 0 on PASS; exit 1 with a list of issues on FAIL.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

# Per-reference required markers. Drop a marker -> the reference has
# drifted from the load-bearing content it should preserve.
REFERENCE_MARKERS: dict[str, list[str]] = {
    ".claude/skills/temporal-phase-start/references/branch-a-fresh-start.md": [
        "BatonNext: DRAFTING_BLUEPRINT",
        "git pull --rebase origin master",
        "CHAIN_COLLISION",
        "check_baton_artifacts.py",
        "kickoff",
    ],
    ".claude/skills/temporal-phase-start/references/branch-b-in-progress.md": [
        "BatonNext",
        "HANDOFF.md",
        "temporal-phase-codex-sync",
        "lane",
    ],
    ".claude/skills/temporal-phase-start/references/branch-c-chain-decision.md": [
        "ChainMode",
        "NextPhasePlan",
        "CHAIN_COLLISION",
        "archive_phase.py",
        "rm -rf",
        "git pull --rebase origin master",
        "chain: archive",  # atomic commit message format
    ],
    ".claude/skills/temporal-phase-watch/references/event-handling.md": [
        "close",  # close step-tag
        "Branch C",  # routes to Branch C of /temporal-phase-start
        "BatonNext",
    ],
    ".claude/skills/temporal-phase-watch/references/monitor-command.md": [
        "bash",  # shell requirement
        "<(",  # process substitution syntax
        "git ls-tree",
    ],
    ".claude/skills/temporal-phase-watch/references/failure-modes.md": [
        "FAIL",
    ],
    "workflows/temporal-phase/skills/temporal-phase-codex-sync/references/fallback-modes.md": [
        "slash command",
        "subprocess",
        "git push",
        "skills.json",
    ],
    "workflows/temporal-phase/skills/temporal-phase-codex-sync/references/sort-tiebreak.md": [
        "DRAFTING_BLUEPRINT",  # kickoff special case
        "phase-id",
        "step-tag",
    ],
    "workflows/temporal-phase/skills/temporal-phase-blueprint/references/tools-generator.md": [
        "temporal-stage-package-generator",
        "GENERATION_REVIEW_REPORT",
        "BLOCK",
        "pending/",
        "PACKAGE_CHARTER",
    ],
    "workflows/temporal-phase/skills/temporal-phase-blueprint/references/push-order.md": [
        "CROSS_REPO_MISSING_REF",
        "verify_cross_repo_refs.py",
        "work repo",
        "coord repo",
    ],
    "workflows/temporal-phase/skills/temporal-phase-execute/references/tools-runner.md": [
        "temporal-package-runner",
        "stage-loop-auto",
        "RUN_AFTER_EXECUTION_PROTOCOL",
        "package-runner subagent",
        "ActualChanges",
    ],
    "workflows/temporal-phase/skills/temporal-phase-execute/references/push-order.md": [
        "CROSS_REPO_MISSING_REF",
        "verify_cross_repo_refs.py",
        "work repo",
        "coord repo",
    ],
    "workflows/temporal-phase/skills/temporal-phase-execute/references/crash-recovery.md": [
        "stage-loop-auto",  # resume mechanism
        "git log",
        "execution-report",
        "fabricated",  # the "fabricated SHAs caught at audit time" warning
    ],
}

# Skill directories that have a references/ subdir; we scan their
# SKILL.md and every reference for broken `references/<name>.md` links.
SKILLS_WITH_REFERENCES = [
    ".claude/skills/temporal-phase-start",
    ".claude/skills/temporal-phase-watch",
    "workflows/temporal-phase/skills/temporal-phase-codex-sync",
    "workflows/temporal-phase/skills/temporal-phase-blueprint",
    "workflows/temporal-phase/skills/temporal-phase-execute",
]

REF_LINK_RE = re.compile(r"references/([\w\-\.]+\.md)")


def main() -> int:
    errors: list[str] = []

    # Check 1: every required marker is present in its reference file.
    for rel_path, markers in REFERENCE_MARKERS.items():
        f = REPO_ROOT / rel_path
        if not f.exists():
            errors.append(f"{rel_path}: missing reference file")
            continue
        text = f.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                errors.append(
                    f"{rel_path}: missing required marker `{marker}` "
                    f"(load-bearing token has drifted)"
                )

    # Check 2: every `references/<name>.md` link resolves to an
    # existing file within that skill's references/ directory.
    n_refs_total = 0
    for skill_dir_rel in SKILLS_WITH_REFERENCES:
        skill_dir = REPO_ROOT / skill_dir_rel
        if not skill_dir.exists():
            errors.append(f"{skill_dir_rel}: missing skill directory")
            continue
        refs_dir = skill_dir / "references"
        if not refs_dir.exists():
            errors.append(f"{skill_dir_rel}: missing references/ subdirectory")
            continue

        ref_files = sorted(refs_dir.glob("*.md"))
        n_refs_total += len(ref_files)

        # Scan SKILL.md + each reference for `references/<name>.md`
        scan_files = [skill_dir / "SKILL.md"]
        scan_files.extend(ref_files)

        for f in scan_files:
            if not f.exists():
                continue
            text = f.read_text(encoding="utf-8")
            for m in REF_LINK_RE.finditer(text):
                ref_name = m.group(1)
                target = refs_dir / ref_name
                if not target.exists():
                    errors.append(
                        f"{f.relative_to(REPO_ROOT)}: broken link "
                        f"`references/{ref_name}` -> file does not exist"
                    )

    if errors:
        print("FAIL: cross-reference consistency check found issues:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASS: cross-reference consistency verified")
    print(
        f"  Checked {len(REFERENCE_MARKERS)} reference files for required markers"
    )
    print(
        f"  Scanned {len(SKILLS_WITH_REFERENCES)} skill directories "
        f"with {n_refs_total} references for broken links"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
