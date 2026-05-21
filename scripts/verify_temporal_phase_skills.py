#!/usr/bin/env python3
"""Verify temporal-phase preset skills are registered correctly.

Scope: only the 15 entries under workflows/temporal-phase/skills/ inside
.codex/skills.json. Testkit entries are validated separately by
blue-k-git-baton-testkit/scripts/verify_project_scoped_skills.py.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / ".codex" / "skills.json"
SKILL_ROOT = Path("workflows/temporal-phase/skills")

CODEX_LANES = {
    "temporal-phase-blueprint",
    "temporal-phase-pre-audit-codex",
    "temporal-phase-execute",
    "temporal-phase-postexec-subagent-review",
    "temporal-phase-postexec-synthesize",
    "temporal-phase-postexec-fix",
    "temporal-phase-second-audit-decision",
    "temporal-phase-second-audit-codex",
    "temporal-phase-second-audit-fix",
    "temporal-phase-close",
}
CC_LANES = {
    "temporal-phase-pre-audit-cc",
    "temporal-phase-pre-audit-synthesize",
    "temporal-phase-blueprint-revise",
    "temporal-phase-postexec-cc",
    "temporal-phase-second-audit-cc",
}
EXPECTED_SKILLS = CODEX_LANES | CC_LANES

ABSOLUTE_PATH_RE = re.compile(r"(?:[A-Za-z]:[\\/]|^/|\\\\|~[/\\]|%USERPROFILE%|\$HOME)")
MACHINE_PATH_RE = re.compile(r"(?:(?<![A-Za-z])[A-Za-z]:[\\/]|%USERPROFILE%|\$HOME)")
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json"}

# PATHS.md is the *one* place absolute machine paths are allowed.
EXCLUDE_FROM_MACHINE_PATH_SCAN = {
    "workflows/temporal-phase/PATHS.md",
}

REQUIRED_SKILL_MARKERS = ("BatonNext", "Trigger", "Reads", "Writes")

# Lanes that must explicitly delegate to a work-repo Codex skill via a
# ## Tools section that names the work-repo skill.
TOOL_DELEGATION = {
    "temporal-phase-blueprint": "temporal-stage-package-generator",
    "temporal-phase-execute": "temporal-package-runner",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_relative(path_text: str, field: str) -> Path:
    if ABSOLUTE_PATH_RE.search(path_text):
        fail(f"{field} uses non-project path: {path_text}")
    path = Path(path_text)
    if path.is_absolute():
        fail(f"{field} is absolute: {path_text}")
    return path


def assert_inside_skill_root(path: Path, field: str) -> None:
    root = (REPO_ROOT / SKILL_ROOT).resolve()
    resolved = (REPO_ROOT / path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        fail(f"{field} resolves outside temporal-phase skill root: {path}")


def scan_machine_paths(folder: Path, skill_name: str) -> None:
    for path in folder.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel in EXCLUDE_FROM_MACHINE_PATH_SCAN:
            continue
        text = read_text(path)
        if MACHINE_PATH_RE.search(text):
            fail(f"{skill_name} contains machine-specific path text in {rel}")


def main() -> int:
    if not CONFIG_PATH.exists():
        fail(f"missing {CONFIG_PATH.relative_to(REPO_ROOT)}")

    config = json.loads(read_text(CONFIG_PATH))
    entries = config.get("skills")
    if not isinstance(entries, list):
        fail("skills must be a list")

    by_name = {str(e.get("name")): e for e in entries}
    missing = sorted(EXPECTED_SKILLS - set(by_name))
    if missing:
        fail(f"missing temporal-phase skills: {missing}")

    for name in sorted(EXPECTED_SKILLS):
        entry = by_name[name]
        rel_path = assert_relative(str(entry.get("path", "")), f"{name}.path")
        assert_inside_skill_root(rel_path, f"{name}.path")

        folder = REPO_ROOT / rel_path
        skill_file = folder / "SKILL.md"
        metadata_file = folder / "agents" / "openai.yaml"
        if not skill_file.exists():
            fail(f"missing {skill_file.relative_to(REPO_ROOT)}")
        if not metadata_file.exists():
            fail(f"missing {metadata_file.relative_to(REPO_ROOT)}")

        skill_text = read_text(skill_file)
        if f"name: {name}" not in skill_text:
            fail(f"{name} SKILL.md does not declare expected name")
        for marker in REQUIRED_SKILL_MARKERS:
            if marker not in skill_text:
                fail(f"{name} SKILL.md is missing required marker: {marker}")

        if name in TOOL_DELEGATION:
            tool_name = TOOL_DELEGATION[name]
            if "## Tools" not in skill_text:
                fail(f"{name} SKILL.md must contain '## Tools' section delegating to {tool_name}")
            if tool_name not in skill_text:
                fail(f"{name} SKILL.md must mention work-repo skill name '{tool_name}'")

        if name in CC_LANES:
            if "must refuse" not in read_text(metadata_file).lower() and \
               "must refuse" not in skill_text.lower():
                fail(f"{name} (CC lane) must declare Codex-side refusal in SKILL.md or agents/openai.yaml")

        scan_machine_paths(folder, name)

        metadata_text = read_text(metadata_file)
        if "default_prompt:" not in metadata_text:
            fail(f"{name} metadata lacks default_prompt")
        if "allow_implicit_invocation: false" not in metadata_text:
            fail(f"{name} metadata must set allow_implicit_invocation: false")

        if name in CODEX_LANES:
            if not entry.get("codexLane"):
                fail(f"{name} must be marked codexLane=true")
        else:
            if entry.get("codexLane"):
                fail(f"{name} is a CC lane; codexLane must not be true")
            if entry.get("mixedLane"):
                fail(f"{name} is a CC lane; mixedLane must not be true")

    # PATHS.md must declare both Host A and Host B.
    paths_file = REPO_ROOT / "workflows/temporal-phase/PATHS.md"
    if not paths_file.exists():
        fail("missing workflows/temporal-phase/PATHS.md")
    paths_text = read_text(paths_file)
    for marker in ("Host A", "Host B", "F:\\gittest\\gittest", "E:\\code\\temporal",
                   "D:\\code\\gittest", "D:\\code\\temporal"):
        if marker not in paths_text:
            fail(f"PATHS.md missing required marker: {marker}")

    # workflows/_active.md is informational only (does not gate this preset).
    # Multiple workflows can be enabled in parallel; the presence of this
    # preset directory and its registered skills is the actual enablement
    # signal.

    # HANDOFF.md §3.1 state -> lane table must cover every Codex lane
    # exactly once, with the right (state, lane) pairing.
    handoff_path = REPO_ROOT / "workflows/temporal-phase/HANDOFF.md"
    if not handoff_path.exists():
        fail("missing workflows/temporal-phase/HANDOFF.md")
    handoff_text = read_text(handoff_path)
    expected_state_to_lane = {
        "DRAFTING_BLUEPRINT": "temporal-phase-blueprint",
        "PRE_AUDIT_R{1,2,3}": "temporal-phase-pre-audit-codex",
        "EXECUTING": "temporal-phase-execute",
        "POSTEXEC_SUBAGENT_REVIEW": "temporal-phase-postexec-subagent-review",
        "POSTEXEC_SYNTHESIS": "temporal-phase-postexec-synthesize",
        "POSTEXEC_FIX": "temporal-phase-postexec-fix",
        "SECOND_AUDIT_DECISION": "temporal-phase-second-audit-decision",
        "SECOND_AUDIT_CODEX": "temporal-phase-second-audit-codex",
        "SECOND_AUDIT_FIX": "temporal-phase-second-audit-fix",
        "PHASE_CLOSING": "temporal-phase-close",
    }
    for state, lane in expected_state_to_lane.items():
        # Look for a markdown table row pairing the state with the lane
        # name; tolerate code-fence backticks around either token.
        row_re = re.compile(
            r"\|\s*`?" + re.escape(state) + r"`?\s*\|\s*`?"
            + re.escape(lane) + r"`?\s*\|",
        )
        if not row_re.search(handoff_text):
            fail(
                f"HANDOFF.md state->lane table missing or mis-paired row: "
                f"`{state}` -> `{lane}`"
            )

    # Cross-check completion-criteria IDs: CHARTER and close SKILL must
    # carry the same CC-NN set verbatim.
    charter_text = read_text(REPO_ROOT / "workflows/temporal-phase/CHARTER.md")
    close_skill_text = read_text(
        REPO_ROOT / "workflows/temporal-phase/skills/temporal-phase-close/SKILL.md"
    )
    cc_re = re.compile(r"CC-\d{2}")
    charter_ids = set(cc_re.findall(charter_text))
    close_ids = set(cc_re.findall(close_skill_text))
    if not charter_ids:
        fail("CHARTER.md has no CC-NN completion-criterion IDs")
    if charter_ids != close_ids:
        only_charter = sorted(charter_ids - close_ids)
        only_close = sorted(close_ids - charter_ids)
        fail(
            "Completion-criterion ID mismatch between CHARTER and close SKILL; "
            f"only-in-CHARTER={only_charter}; only-in-close-SKILL={only_close}"
        )

    print("PASS: temporal-phase skills verified")
    print(f"SkillRoot: {SKILL_ROOT.as_posix()}")
    print("CodexLanes: " + " ".join(sorted(CODEX_LANES)))
    print("CCLanes:    " + " ".join(sorted(CC_LANES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
