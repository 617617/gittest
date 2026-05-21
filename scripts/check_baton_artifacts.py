#!/usr/bin/env python3
"""Validate runtime baton artifacts under workflows/temporal-phase/_coord.

Runs every check that turns silent corruption into a loud FAIL:

- filename matches `<phase-id>__<step-tag>.md`
- phase-id matches `phase-\\d+`
- step-tag is in the right mailbox (authority enforcement)
- first non-empty line is `BatonNext: <STATE>` and STATE is in the
  enumerated baton states from `BATON.schema.md`
- at most one open Phase across both mailboxes (an open Phase is any
  phase-id that appears in the mailboxes without a `close` step-tag)

Exit 0 = PASS. Exit 1 = FAIL with one or more issues listed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
COORD_ROOT = REPO_ROOT / "workflows/temporal-phase/_coord"
FROM_CC = COORD_ROOT / "from-cc"
FROM_CODEX = COORD_ROOT / "from-codex"

# 25 baton states (must match BATON.schema.md state enumeration)
BATON_STATES = {
    "DRAFTING_BLUEPRINT",
    "PRE_AUDIT_R1", "PRE_AUDIT_R2", "PRE_AUDIT_R3",
    "PRE_AUDIT_SYNTHESIS_R1", "PRE_AUDIT_SYNTHESIS_R2", "PRE_AUDIT_SYNTHESIS_R3",
    "BLUEPRINT_REVISION_R1", "BLUEPRINT_REVISION_R2", "BLUEPRINT_REVISION_R3",
    "BLUEPRINT_ACCEPTED",
    "EXECUTING",
    "EXECUTION_REPORTED",
    "POSTEXEC_SUBAGENT_REVIEW",
    "POSTEXEC_CC_REVIEW",
    "POSTEXEC_SYNTHESIS",
    "POSTEXEC_FIX",
    "SECOND_AUDIT_DECISION",
    "SECOND_AUDIT_CC",
    "SECOND_AUDIT_CODEX",
    "SECOND_AUDIT_FIX",
    "PHASE_CLOSING",
    "COMPLETED",
    "BLOCKED_BLUEPRINT",
    "BLOCKED_POSTEXEC",
}

# step-tag regex → which mailbox it must live in
CC_STEP_TAGS = [
    re.compile(r"^kickoff$"),
    re.compile(r"^pre-audit-cc-r[123]$"),
    re.compile(r"^pre-audit-synthesis-r[123]$"),
    re.compile(r"^pre-audit-verdict-r[123]$"),
    re.compile(r"^blueprint-revision-r[123]$"),
    re.compile(r"^postexec-cc-review$"),
    re.compile(r"^second-audit-cc$"),
]
CODEX_STEP_TAGS = [
    re.compile(r"^blueprint$"),
    re.compile(r"^pre-audit-codex-r[123]$"),
    re.compile(r"^execution-report$"),
    re.compile(r"^postexec-subagent-review$"),
    re.compile(r"^postexec-synthesis$"),
    re.compile(r"^postexec-fix$"),
    re.compile(r"^second-audit-decision$"),
    re.compile(r"^second-audit-codex$"),
    re.compile(r"^second-audit-fix$"),
    re.compile(r"^close$"),
]

PHASE_ID_RE = re.compile(r"^phase-[a-zA-Z0-9][a-zA-Z0-9\-]*$")
FILENAME_RE = re.compile(r"^(phase-[a-zA-Z0-9][a-zA-Z0-9\-]*)__(.+)\.md$")
BATON_NEXT_RE = re.compile(r"^BatonNext:\s+([A-Z_0-9]+)\s*$")


def step_tag_belongs_to(tag: str, mailbox: str) -> bool:
    if mailbox == "from-cc":
        return any(p.match(tag) for p in CC_STEP_TAGS)
    if mailbox == "from-codex":
        return any(p.match(tag) for p in CODEX_STEP_TAGS)
    return False


def main() -> int:
    errors: list[str] = []
    artifacts: list[tuple[str, str, str, str]] = []  # (mailbox, phase_id, step_tag, filename)

    for mailbox_name, mailbox_path in (("from-cc", FROM_CC), ("from-codex", FROM_CODEX)):
        if not mailbox_path.exists():
            errors.append(f"missing mailbox directory: workflows/temporal-phase/_coord/{mailbox_name}/")
            continue
        for f in sorted(mailbox_path.iterdir()):
            # Skip the archive directory (closed Phases live under
            # _coord/archive/<phase-id>/, not directly under from-cc/from-codex).
            if f.is_dir():
                continue
            if not f.is_file() or f.name == ".gitkeep":
                continue
            if f.suffix.lower() != ".md":
                # Allow README.md etc. in _coord/ root but not inside the mailbox subdirs
                errors.append(f"{mailbox_name}/{f.name}: only .md baton artifacts allowed in this mailbox")
                continue

            m = FILENAME_RE.match(f.name)
            if not m:
                errors.append(
                    f"{mailbox_name}/{f.name}: filename must match `<phase-id>__<step-tag>.md`"
                )
                continue
            phase_id, step_tag = m.group(1), m.group(2)

            if not PHASE_ID_RE.match(phase_id):
                errors.append(
                    f"{mailbox_name}/{f.name}: phase-id `{phase_id}` must match `phase-\\d+` (e.g. phase-01)"
                )

            if not step_tag_belongs_to(step_tag, mailbox_name):
                other = "from-codex" if mailbox_name == "from-cc" else "from-cc"
                if step_tag_belongs_to(step_tag, other):
                    errors.append(
                        f"AUTHORITY VIOLATION: {mailbox_name}/{f.name} -- "
                        f"step-tag `{step_tag}` belongs in {other}/"
                    )
                else:
                    errors.append(
                        f"{mailbox_name}/{f.name}: unknown step-tag `{step_tag}`"
                    )

            text = f.read_text(encoding="utf-8")
            first_line = next((line for line in text.splitlines() if line.strip()), None)
            if first_line is None:
                errors.append(f"{mailbox_name}/{f.name}: file has no non-empty lines (missing BatonNext)")
                continue
            bm = BATON_NEXT_RE.match(first_line)
            if not bm:
                errors.append(
                    f"{mailbox_name}/{f.name}: first non-empty line must be `BatonNext: <STATE>`; "
                    f"got `{first_line[:80]}`"
                )
                continue
            state = bm.group(1)
            if state not in BATON_STATES:
                errors.append(
                    f"{mailbox_name}/{f.name}: BatonNext state `{state}` is not in the "
                    f"BATON.schema.md state enumeration"
                )

            artifacts.append((mailbox_name, phase_id, step_tag, f.name))

    # at most one open Phase (a Phase is open if it has any artifact without a close.md)
    phases: dict[str, set[str]] = {}
    for _mailbox, phase_id, step_tag, _fname in artifacts:
        phases.setdefault(phase_id, set()).add(step_tag)
    open_phases = sorted(pid for pid, tags in phases.items() if "close" not in tags)
    if len(open_phases) > 1:
        errors.append(
            f"more than one open Phase: {open_phases}. Only one Phase may be open "
            f"(no close.md) at a time. Close the previous Phase before starting the next."
        )

    if errors:
        print("FAIL: baton artifact validation found issues:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"PASS: {len(artifacts)} baton artifact(s) checked")
    if not artifacts:
        print("  (mailboxes have no Phase artifacts yet)")
    else:
        print(f"  Phases seen: {sorted(phases)}")
        print(f"  Open Phases: {open_phases or ['<none>']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
