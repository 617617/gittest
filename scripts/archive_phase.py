#!/usr/bin/env python3
"""Archive a closed temporal-phase Phase's artifacts.

Usage:
    python scripts/archive_phase.py <phase-id>

Preconditions:
    - <phase-id> matches `phase-\\d+`.
    - `workflows/temporal-phase/_coord/from-codex/<phase-id>__close.md`
      exists and its first line is `BatonNext: COMPLETED` or
      `BatonNext: BLOCKED_POSTEXEC` (i.e. the Phase reached a terminal
      state).
    - There are no other phase-ids open in the mailboxes (the artifact
      checker would have caught this anyway).

Effect:
    - Creates `workflows/temporal-phase/_coord/archive/<phase-id>/`
      with two subdirectories `from-cc/` and `from-codex/`.
    - Moves every file matching `<phase-id>__*.md` from both mailboxes
      into the archive (preserving which mailbox each came from).
    - Prints a summary. Does NOT commit -- the caller (typically
      /temporal-phase-start Branch C) does the commit + push.

Exit 0 on success, non-zero with a clear FAIL on any precondition
violation.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
COORD_ROOT = REPO_ROOT / "workflows/temporal-phase/_coord"
FROM_CC = COORD_ROOT / "from-cc"
FROM_CODEX = COORD_ROOT / "from-codex"
ARCHIVE_ROOT = COORD_ROOT / "archive"

PHASE_ID_RE = re.compile(r"^phase-\d+$")
BATON_NEXT_RE = re.compile(r"^BatonNext:\s+([A-Z_0-9]+)\s*$")
# Only the `temporal-phase-close` lane writes a `<phase-id>__close.md`,
# and per `temporal-phase-close/SKILL.md` it emits only `COMPLETED` or
# `BLOCKED_POSTEXEC` as its terminal `BatonNext` values. `BLOCKED_BLUEPRINT`
# is reached via the `blueprint-revise` lane, which does NOT produce a
# close.md, so it can never appear here -- listing it would be misleading.
TERMINAL_STATES = {"COMPLETED", "BLOCKED_POSTEXEC"}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        fail("usage: archive_phase.py <phase-id>")
    phase_id = argv[1]
    if not PHASE_ID_RE.match(phase_id):
        fail(f"phase-id `{phase_id}` must match `phase-\\d+`")

    close_path = FROM_CODEX / f"{phase_id}__close.md"
    if not close_path.exists():
        fail(
            f"missing {close_path.relative_to(REPO_ROOT)} -- "
            f"can only archive a Phase that Codex has formally closed"
        )

    close_text = close_path.read_text(encoding="utf-8")
    first_line = next((line for line in close_text.splitlines() if line.strip()), "")
    bm = BATON_NEXT_RE.match(first_line)
    if not bm:
        fail(
            f"{close_path.relative_to(REPO_ROOT)} first non-empty line "
            f"must be `BatonNext: <STATE>`; got `{first_line[:80]}`"
        )
    state = bm.group(1)
    if state not in TERMINAL_STATES:
        fail(
            f"{close_path.relative_to(REPO_ROOT)} BatonNext is `{state}`, "
            f"not a terminal state ({sorted(TERMINAL_STATES)}). Cannot archive."
        )

    # Gather files for this phase-id from both mailboxes.
    cc_files = sorted(FROM_CC.glob(f"{phase_id}__*.md"))
    codex_files = sorted(FROM_CODEX.glob(f"{phase_id}__*.md"))
    if not cc_files and not codex_files:
        fail(f"no artifacts found for {phase_id} in either mailbox")

    # Other-phase open-check: any other phase-id without its own close
    # in mailboxes means we should refuse (the artifact checker also
    # enforces "at most one open" but it allows multiple closed Phases
    # to coexist before any of them archive; we still want a clean
    # baseline).
    def phase_ids_in(folder: Path) -> set[str]:
        ids = set()
        for f in folder.iterdir():
            if f.is_file() and "__" in f.name and f.name != ".gitkeep":
                ids.add(f.name.split("__", 1)[0])
        return ids

    all_ids = phase_ids_in(FROM_CC) | phase_ids_in(FROM_CODEX)
    other_ids = all_ids - {phase_id}
    open_other = [
        pid for pid in other_ids
        if not (FROM_CODEX / f"{pid}__close.md").exists()
    ]
    if open_other:
        fail(
            f"cannot archive {phase_id} while other Phases are still open: "
            f"{sorted(open_other)}"
        )

    # Prepare archive layout
    dest = ARCHIVE_ROOT / phase_id
    (dest / "from-cc").mkdir(parents=True, exist_ok=True)
    (dest / "from-codex").mkdir(parents=True, exist_ok=True)

    moved: list[str] = []
    for f in cc_files:
        target = dest / "from-cc" / f.name
        shutil.move(str(f), str(target))
        moved.append(f"  from-cc/{f.name} -> archive/{phase_id}/from-cc/{f.name}")
    for f in codex_files:
        target = dest / "from-codex" / f.name
        shutil.move(str(f), str(target))
        moved.append(f"  from-codex/{f.name} -> archive/{phase_id}/from-codex/{f.name}")

    print(f"PASS: archived {phase_id} ({state})")
    print(f"  artifacts: {len(moved)} file(s)")
    for line in moved:
        print(line)
    print()
    print(
        "Next: caller should `git add -A workflows/temporal-phase/_coord/`, "
        "commit (e.g. `archive: " + phase_id + " (" + state + ")`), and push."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
