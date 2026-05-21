#!/usr/bin/env python3
"""Verify every `temporal@<sha>` reference in coord artifacts resolves
to an actual commit in the local Temporal work-repo clone.

This is an **optional** check, NOT part of the standard verifier flow.
Run it when you suspect a cross-repo inconsistency (e.g., someone
pushed the coord pointer before pushing the work repo).

Usage:
    python scripts/verify_cross_repo_refs.py

Procedure:
    1. Read workflows/temporal-phase/PATHS.md and resolve the
       `temporal:` path for the host this script is running on.
    2. Scan workflows/temporal-phase/_coord/{from-cc,from-codex} and
       _coord/archive/<phase-id>/{from-cc,from-codex} for every .md
       file containing `temporal@<short-sha>` tokens.
    3. For each unique SHA, run `git -C <temporal-repo> rev-parse
       --verify <sha>` and report PASS / MISSING per SHA.

Exit codes:
    0 = every referenced SHA resolves locally.
    1 = one or more refs are missing OR PATHS.md cannot be resolved.

Notes:
    - Host detection: matches the current working directory against
      each row's coord-repo column in PATHS.md. If you run this script
      from elsewhere, set TEMPORAL_REPO env var to override.
    - "Missing" can mean: SHA was never pushed to the local clone yet
      (run `git -C <temporal-repo> fetch --all` first), OR the
      coord-side pointer was written before the corresponding
      work-repo commit was pushed (the bug this script catches).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
COORD_ROOT = REPO_ROOT / "workflows/temporal-phase/_coord"
PATHS_MD = REPO_ROOT / "workflows/temporal-phase/PATHS.md"

# Match `temporal@<7-or-more-hex-chars>` with optional `..<another>` range.
SHA_RE = re.compile(r"temporal@([0-9a-fA-F]{7,40})(?:\.\.([0-9a-fA-F]{7,40}))?")


def fail(msg: str) -> int:
    print(f"FAIL: {msg}")
    return 1


def resolve_temporal_path() -> Path:
    """Resolve this host's temporal: path from PATHS.md."""
    override = os.environ.get("TEMPORAL_REPO")
    if override:
        path = Path(override)
        if not path.exists():
            sys.exit(fail(f"TEMPORAL_REPO env var points to nonexistent path: {override}"))
        return path

    if not PATHS_MD.exists():
        sys.exit(fail(f"missing {PATHS_MD}"))
    text = PATHS_MD.read_text(encoding="utf-8")

    # The PATHS.md table rows look like:
    #   | **Host A** ... | `F:\gittest\gittest\` | `E:\code\temporal\` |
    # We match coord-repo column against CWD to pick the right row.
    cwd = Path.cwd().resolve()
    row_re = re.compile(
        r"\|\s*\*\*Host\s+\S+\*\*[^|]*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|",
    )
    for m in row_re.finditer(text):
        coord_path = Path(m.group(1).rstrip("\\/")).resolve()
        work_path = Path(m.group(2).rstrip("\\/")).resolve()
        try:
            cwd.relative_to(coord_path)
        except ValueError:
            continue
        return work_path

    sys.exit(fail(
        f"could not match CWD {cwd} against any Host row in PATHS.md. "
        f"Set TEMPORAL_REPO env var to override."
    ))


def collect_shas() -> dict[str, list[str]]:
    """Walk both mailboxes + the archive subtree. Return {sha: [file, ...]}."""
    sha_origins: dict[str, list[str]] = {}

    def scan(folder: Path) -> None:
        if not folder.exists():
            return
        for p in folder.rglob("*.md"):
            try:
                text = p.read_text(encoding="utf-8")
            except OSError:
                continue
            for m in SHA_RE.finditer(text):
                rel = p.relative_to(REPO_ROOT).as_posix()
                for grp in (m.group(1), m.group(2)):
                    if grp:
                        sha_origins.setdefault(grp.lower(), []).append(rel)

    scan(COORD_ROOT / "from-cc")
    scan(COORD_ROOT / "from-codex")
    scan(COORD_ROOT / "archive")
    return sha_origins


def verify_sha(temporal_path: Path, sha: str) -> bool:
    """Return True if the SHA resolves in the local work-repo clone."""
    try:
        result = subprocess.run(
            ["git", "-C", str(temporal_path), "rev-parse", "--verify", f"{sha}^{{commit}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"  ERROR running git for {sha}: {exc}")
        return False
    return result.returncode == 0


def main() -> int:
    temporal_path = resolve_temporal_path()
    if not (temporal_path / ".git").exists():
        return fail(
            f"{temporal_path} does not look like a git repo "
            f"(no .git/ directory). PATHS.md may be out of date."
        )

    sha_origins = collect_shas()
    if not sha_origins:
        print(f"PASS: no temporal@<sha> references found in mailboxes/archive")
        print(f"  work repo checked: {temporal_path}")
        return 0

    missing: list[tuple[str, list[str]]] = []
    passed = 0
    for sha in sorted(sha_origins):
        if verify_sha(temporal_path, sha):
            passed += 1
        else:
            missing.append((sha, sha_origins[sha]))

    print(f"work repo: {temporal_path}")
    print(f"references found: {len(sha_origins)} unique SHA(s)")
    print(f"  resolved: {passed}")
    print(f"  missing:  {len(missing)}")

    if missing:
        print()
        print("FAIL: the following SHAs do NOT resolve in the local work repo:")
        for sha, files in missing:
            print(f"  - temporal@{sha}")
            for f in sorted(set(files)):
                print(f"      cited in: {f}")
        print()
        print("Hint: run `git -C <temporal-repo> fetch --all` first; if the SHAs")
        print("still do not resolve, the coord-side pointer was likely pushed")
        print("before the corresponding work-repo commit was pushed. Push the")
        print("work repo and re-run.")
        return 1

    print("PASS: every temporal@<sha> reference resolves in the local work repo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
