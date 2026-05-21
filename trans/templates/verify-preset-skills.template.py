#!/usr/bin/env python3
"""Verify <preset> preset skills are registered correctly.

Scope: only the entries this preset owns inside .codex/skills.json.
Other presets' entries are validated by their own verifiers.

Replace every `<preset>` and TODO placeholder when adapting.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / ".codex" / "skills.json"
SKILL_ROOT = Path("workflows/<preset>/skills")

# TODO — list every Codex-driven lane name (also include in skills.json
# with codexLane=true)
CODEX_LANES: set[str] = {
    "<preset>-<codex-lane-1>",
    "<preset>-<codex-lane-2>",
}

# TODO — list every CC-only lane name
CC_LANES: set[str] = {
    "<preset>-<cc-lane-1>",
}

EXPECTED_SKILLS = CODEX_LANES | CC_LANES

# TODO — adjust if you delegate via ## Tools sections; map each
# delegating lane to the work-repo skill name it must mention
TOOL_DELEGATION: dict[str, str] = {
    # "<preset>-<lane>": "<work-repo-skill-name>",
}

ABSOLUTE_PATH_RE = re.compile(r"(?:[A-Za-z]:[\\/]|^/|\\\\|~[/\\]|%USERPROFILE%|\$HOME)")
MACHINE_PATH_RE = re.compile(r"(?:(?<![A-Za-z])[A-Za-z]:[\\/]|%USERPROFILE%|\$HOME)")
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json"}

# PATHS.md is the one place absolute machine paths are allowed.
EXCLUDE_FROM_MACHINE_PATH_SCAN = {
    "workflows/<preset>/PATHS.md",
}

REQUIRED_SKILL_MARKERS = ("BatonNext", "Trigger", "Reads", "Writes")


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
        fail(f"{field} resolves outside <preset> skill root: {path}")


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
        fail(f"missing <preset> skills: {missing}")

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
                fail(f"{name} SKILL.md must contain '## Tools' delegating to {tool_name}")
            if tool_name not in skill_text:
                fail(f"{name} SKILL.md must mention work-repo skill name '{tool_name}'")

        if name in CC_LANES:
            if "must refuse" not in read_text(metadata_file).lower() and \
               "must refuse" not in skill_text.lower():
                fail(f"{name} (CC lane) must declare Codex-side refusal")

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

    # TODO — PATHS.md must declare every host you expect
    paths_file = REPO_ROOT / "workflows/<preset>/PATHS.md"
    if not paths_file.exists():
        fail("missing workflows/<preset>/PATHS.md")
    # TODO — add per-host markers your preset requires

    # TODO — HANDOFF.md state -> lane table cross-check (see
    # scripts/verify_temporal_phase_skills.py for the exact pattern)

    # TODO — CHARTER ↔ closing-SKILL CC-NN ID cross-check (see
    # scripts/verify_temporal_phase_skills.py)

    print("PASS: <preset> skills verified")
    print(f"SkillRoot: {SKILL_ROOT.as_posix()}")
    print("CodexLanes: " + " ".join(sorted(CODEX_LANES)))
    print("CCLanes:    " + " ".join(sorted(CC_LANES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
