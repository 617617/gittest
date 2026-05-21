#!/usr/bin/env python3
"""Verify Blue-K skills are registered project-scoped only."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / ".codex" / "skills.json"
SKILL_ROOT = Path("blue-k-git-baton-testkit/skills")
CODEX_LANES = {
    "blue-k-main-runner",
    "blue-k-other-runner",
    "blue-k-other-index",
}
MIXED_LANES = {"blue-k-consensus"}
CC_LANES = {
    "blue-k-planner",
    "blue-k-plan-audit",
}
BATON_LANES = CODEX_LANES | MIXED_LANES | CC_LANES
EXPECTED_SKILLS = {
    "blue-k-planner",
    "blue-k-plan-audit",
    "blue-k-main-runner",
    "blue-k-other-runner",
    "blue-k-other-index",
    "blue-k-consensus",
    "traceable-plan",
    "pre-doc-review",
    "stage-loop-auto",
    "stage-loop",
    "doc-review",
    "traceable-review",
}
ABSOLUTE_PATH_RE = re.compile(r"(?:[A-Za-z]:[\\/]|^/|\\\\|~[/\\]|%USERPROFILE%|\$HOME)")
MACHINE_PATH_RE = re.compile(r"(?:(?<![A-Za-z])[A-Za-z]:[\\/]|\\.codex[\\/]|%USERPROFILE%|\$HOME)")
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".py", ".ps1", ".txt"}
CHAT_RULE_MARKERS = (
    "First reply",
    "Wrong-window",
    "Done. Now run: bk sync",
    "yes, abandon",
)


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
        fail(f"{field} resolves outside project skill root: {path}")


def scan_machine_paths(folder: Path, skill_name: str) -> None:
    for path in folder.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = read_text(path)
        if MACHINE_PATH_RE.search(text):
            fail(f"{skill_name} contains machine-specific path text in {path.relative_to(REPO_ROOT)}")


def main() -> int:
    if not CONFIG_PATH.exists():
        fail(f"missing {CONFIG_PATH.relative_to(REPO_ROOT)}")

    config = json.loads(read_text(CONFIG_PATH))
    if config.get("scope") != "project":
        fail("skills.json scope must be project")
    if config.get("allowGlobalFallback") is not False:
        fail("allowGlobalFallback must be false")
    if assert_relative(str(config.get("skillRoot", "")), "skillRoot") != SKILL_ROOT:
        fail("skillRoot must be blue-k-git-baton-testkit/skills")
    assert_inside_skill_root(SKILL_ROOT / "__root_marker__", "skillRoot")

    entries = config.get("skills")
    if not isinstance(entries, list):
        fail("skills must be a list")

    names = {entry.get("name") for entry in entries}
    if names != EXPECTED_SKILLS:
        missing = sorted(EXPECTED_SKILLS - names)
        extra = sorted(names - EXPECTED_SKILLS)
        fail(f"skill set mismatch; missing={missing}; extra={extra}")

    for entry in entries:
        name = str(entry["name"])
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
        scan_machine_paths(folder, name)

        metadata_text = read_text(metadata_file)
        if "default_prompt:" not in metadata_text:
            fail(f"{name} metadata lacks default_prompt")

        if name in BATON_LANES:
            if "AI Chat Contract (v0.10)" not in skill_text:
                fail(f"{name} lacks AI Chat Contract (v0.10)")
            if "blue-k-git-baton-testkit/references/ai-chat-contract.md" not in skill_text:
                fail(f"{name} does not link ai-chat-contract.md")
            for marker in CHAT_RULE_MARKERS:
                if marker not in skill_text:
                    fail(f"{name} AI Chat Contract is missing marker: {marker}")
        if name in CODEX_LANES:
            if not entry.get("codexLane"):
                fail(f"{name} must be marked codexLane=true")
        elif name in MIXED_LANES:
            if not entry.get("mixedLane"):
                fail(f"{name} must be marked mixedLane=true")
        elif entry.get("codexLane"):
            fail(f"{name} is not a Codex-owned lane")
        elif entry.get("mixedLane"):
            fail(f"{name} is not a mixed lane")

    print("PASS: project-scoped Blue-K skills verified")
    print(f"SkillRoot: {SKILL_ROOT.as_posix()}")
    print("CodexLanes: " + " ".join(sorted(CODEX_LANES)))
    print("MixedLanes: " + " ".join(sorted(MIXED_LANES)))
    print("CCLanes:    " + " ".join(sorted(CC_LANES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
