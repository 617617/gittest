#!/usr/bin/env python3
"""Maintain the Blue-K other minimum-package progress table."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_MIAN_K = Path(r"docs/mian-k")
PROGRESS_NAME = "OTHER_MIN_PACKAGE_PROGRESS.md"
STATE_START = "<!-- blue-k-other-progress-state"
STATE_END = "blue-k-other-progress-state -->"
VALID_STATUSES = {"pending", "running", "done", "blocked", "skipped"}


@dataclass
class Item:
    index: str
    path: str
    branch: str
    kind: str
    stage_count: int
    status: str = "pending"
    attempts: int = 0
    last_started_at: str = ""
    last_finished_at: str = ""
    result_commit: str = ""
    notes: str = ""
    sort_key: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "path": self.path,
            "branch": self.branch,
            "kind": self.kind,
            "stage_count": self.stage_count,
            "status": self.status,
            "attempts": self.attempts,
            "last_started_at": self.last_started_at,
            "last_finished_at": self.last_finished_at,
            "result_commit": self.result_commit,
            "notes": self.notes,
            "sort_key": self.sort_key,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Item":
        return cls(
            index=str(data.get("index", "")),
            path=str(data.get("path", "")),
            branch=str(data.get("branch", "")),
            kind=str(data.get("kind", "")),
            stage_count=int(data.get("stage_count", 0) or 0),
            status=str(data.get("status", "pending")),
            attempts=int(data.get("attempts", 0) or 0),
            last_started_at=str(data.get("last_started_at", "")),
            last_finished_at=str(data.get("last_finished_at", "")),
            result_commit=str(data.get("result_commit", "")),
            notes=str(data.get("notes", "")),
            sort_key=list(data.get("sort_key", [])),
        )


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def leading_number(name: str) -> int:
    match = re.match(r"^(\d+)", name)
    if not match:
        return 999999
    return int(match.group(1))


def sanitize_cell(value: str) -> str:
    return value.replace("|", "/").replace("\r", " ").replace("\n", " ").strip()


def status_label(status: str) -> str:
    labels = {
        "pending": "[ ] pending",
        "running": "[>] running",
        "done": "[x] done",
        "blocked": "[!] blocked",
        "skipped": "[-] skipped",
    }
    return labels.get(status, status)


def discover_stage_dirs(package_dir: Path) -> list[Path]:
    if not package_dir.is_dir():
        return []
    return sorted(
        [
            child
            for child in package_dir.iterdir()
            if child.is_dir()
            and child.name.startswith("stage-")
            and (child / "EXECUTE.md").is_file()
        ],
        key=lambda p: p.name,
    )


def is_minimum_package(package_dir: Path) -> bool:
    return (
        (package_dir / "PACKAGE_CHARTER.md").is_file()
        and (package_dir / "scope.md").is_file()
        and bool(discover_stage_dirs(package_dir))
    )


def normalize_path(path: Path) -> str:
    return str(path.resolve())


def discover_items(mian_k: Path) -> list[Item]:
    other_root = mian_k / "other"
    if not other_root.is_dir():
        raise SystemExit(f"Missing other directory: {other_root}")

    items: list[Item] = []
    for branch_dir in sorted(
        [p for p in other_root.iterdir() if p.is_dir()],
        key=lambda p: (leading_number(p.name), p.name),
    ):
        branch_no = leading_number(branch_dir.name)
        branch_token = f"{branch_no:02d}" if branch_no != 999999 else branch_dir.name

        if (branch_dir / "PACKAGE_SET_INDEX.md").is_file():
            for child_dir in sorted(
                [p for p in branch_dir.iterdir() if p.is_dir()],
                key=lambda p: (leading_number(p.name), p.name),
            ):
                child_no = leading_number(child_dir.name)
                if not is_minimum_package(child_dir):
                    continue
                index = (
                    f"{branch_no:02d}.{child_no:02d}"
                    if branch_no != 999999 and child_no != 999999
                    else f"{branch_dir.name}.{child_dir.name}"
                )
                items.append(
                    Item(
                        index=index,
                        path=normalize_path(child_dir),
                        branch=branch_dir.name,
                        kind="branch_subpackage",
                        stage_count=len(discover_stage_dirs(child_dir)),
                        sort_key=[branch_no, child_no],
                    )
                )
            continue

        if is_minimum_package(branch_dir):
            items.append(
                Item(
                    index=branch_token,
                    path=normalize_path(branch_dir),
                    branch=branch_dir.name,
                    kind="single_traceable_package",
                    stage_count=len(discover_stage_dirs(branch_dir)),
                    sort_key=[branch_no, -1],
                )
            )

    return sorted(items, key=lambda item: item.sort_key)


def state_from_text(text: str) -> dict[str, Any] | None:
    pattern = re.compile(
        re.escape(STATE_START) + r"\s*\n(.*?)\n" + re.escape(STATE_END),
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return None
    return json.loads(match.group(1))


def read_state(progress_file: Path) -> dict[str, Any]:
    if not progress_file.is_file():
        return {"items": []}
    text = progress_file.read_text(encoding="utf-8")
    state = state_from_text(text)
    if state is None:
        raise SystemExit(
            f"Progress file has no machine state block. Rebuild or migrate: {progress_file}"
        )
    return state


def merge_items(discovered: list[Item], existing_state: dict[str, Any]) -> list[Item]:
    existing_by_path: dict[str, Item] = {}
    for raw in existing_state.get("items", []):
        item = Item.from_dict(raw)
        existing_by_path[item.path.lower()] = item

    merged: list[Item] = []
    for item in discovered:
        previous = existing_by_path.get(item.path.lower())
        if previous:
            item.status = previous.status if previous.status in VALID_STATUSES else "pending"
            item.attempts = previous.attempts
            item.last_started_at = previous.last_started_at
            item.last_finished_at = previous.last_finished_at
            item.result_commit = previous.result_commit
            item.notes = previous.notes
        merged.append(item)
    return merged


def progress_file_for(mian_k: Path, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    return mian_k / PROGRESS_NAME


def render_markdown(mian_k: Path, items: list[Item]) -> str:
    state = {
        "version": 1,
        "mian_k": normalize_path(mian_k),
        "generated_at": now_iso(),
        "progress_file": normalize_path(mian_k / PROGRESS_NAME),
        "items": [item.to_dict() for item in items],
    }
    lines = [
        STATE_START,
        json.dumps(state, ensure_ascii=True, indent=2),
        STATE_END,
        "",
        "# Blue K Other Minimum Package Progress",
        "",
        f"Source: `{normalize_path(mian_k / 'other')}`",
        f"Generated: `{state['generated_at']}`",
        "",
        "Discovery rule: directories with `PACKAGE_SET_INDEX.md` are package sets; leaf directories with package-local stage docs are minimum executable packages.",
        "",
        "| Index | Status | Minimum Executable Package | Branch | Kind | Stages | Attempts | Last Started | Last Finished | Commit | Notes |",
        "| --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- |",
    ]

    for item in items:
        path_cell = f"`{item.path}`"
        if item.status in {"done", "skipped"}:
            path_cell = f"~~{path_cell}~~"
        lines.append(
            "| "
            + " | ".join(
                [
                    sanitize_cell(item.index),
                    sanitize_cell(status_label(item.status)),
                    sanitize_cell(path_cell),
                    sanitize_cell(item.branch),
                    sanitize_cell(item.kind),
                    str(item.stage_count),
                    str(item.attempts),
                    sanitize_cell(item.last_started_at),
                    sanitize_cell(item.last_finished_at),
                    sanitize_cell(item.result_commit),
                    sanitize_cell(item.notes),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def write_progress(mian_k: Path, progress_file: Path, items: list[Item]) -> None:
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    progress_file.write_text(render_markdown(mian_k, items), encoding="utf-8")


def load_items(mian_k: Path, progress_file: Path) -> list[Item]:
    state = read_state(progress_file)
    return [Item.from_dict(raw) for raw in state.get("items", [])]


def cmd_build(args: argparse.Namespace) -> None:
    mian_k = resolve_mian_k(args)
    progress_file = progress_file_for(mian_k, resolve_progress_file(args))
    existing = read_state(progress_file)
    discovered = discover_items(mian_k)
    if not discovered:
        raise SystemExit(f"No minimum executable packages discovered under {mian_k / 'other'}")
    items = merge_items(discovered, existing)
    write_progress(mian_k, progress_file, items)
    print(json.dumps({"progress_file": str(progress_file), "count": len(items)}, indent=2))


def cmd_next(args: argparse.Namespace) -> None:
    mian_k = resolve_mian_k(args)
    progress_file = progress_file_for(mian_k, resolve_progress_file(args))
    items = load_items(mian_k, progress_file)
    running = [item for item in items if item.status == "running"]
    pending = [item for item in items if item.status == "pending"]
    chosen: Item | None = None
    action = ""
    selector = ""
    if running:
        chosen = sorted(running, key=lambda item: item.sort_key)[0]
        action = "resume"
        selector = "continue"
    elif pending:
        chosen = sorted(pending, key=lambda item: item.sort_key)[0]
        action = "start"
        selector = "all"

    if not chosen:
        print(json.dumps({"found": False, "reason": "no running or pending items"}, indent=2))
        return

    print(
        json.dumps(
            {
                "found": True,
                "action": action,
                "stage_loop_auto_selector": selector,
                "index": chosen.index,
                "status": chosen.status,
                "path": chosen.path,
                "branch": chosen.branch,
                "kind": chosen.kind,
                "attempts": chosen.attempts,
                "multiple_running": len(running) > 1,
            },
            indent=2,
        )
    )


def cmd_mark(args: argparse.Namespace) -> None:
    if args.status not in VALID_STATUSES:
        raise SystemExit(f"Invalid status {args.status}. Valid: {sorted(VALID_STATUSES)}")

    mian_k = resolve_mian_k(args)
    progress_file = progress_file_for(mian_k, resolve_progress_file(args))
    items = load_items(mian_k, progress_file)
    target: Item | None = None
    for item in items:
        if args.index and item.index == args.index:
            target = item
            break
        if args.path and item.path.lower() == str(Path(args.path).resolve()).lower():
            target = item
            break
    if target is None:
        raise SystemExit("No matching progress item. Provide --index or --path.")

    timestamp = now_iso()
    target.status = args.status
    if args.status == "running":
        target.attempts += 1
        target.last_started_at = timestamp
    if args.status in {"done", "blocked", "skipped"}:
        target.last_finished_at = timestamp
    if args.commit:
        target.result_commit = sanitize_cell(args.commit)
    if args.reset_history:
        target.attempts = 0
        target.last_started_at = ""
        target.last_finished_at = ""
        target.result_commit = ""
        target.notes = ""
    if args.replace_note:
        target.notes = sanitize_cell(args.note)
    elif args.note:
        note = sanitize_cell(args.note)
        if target.notes:
            target.notes = f"{target.notes}; {timestamp}: {note}"
        else:
            target.notes = f"{timestamp}: {note}"

    write_progress(mian_k, progress_file, items)
    print(
        json.dumps(
            {
                "progress_file": str(progress_file),
                "index": target.index,
                "status": target.status,
                "path": target.path,
            },
            indent=2,
        )
    )


def cmd_summary(args: argparse.Namespace) -> None:
    mian_k = resolve_mian_k(args)
    progress_file = progress_file_for(mian_k, resolve_progress_file(args))
    items = load_items(mian_k, progress_file)
    counts = {status: 0 for status in sorted(VALID_STATUSES)}
    for item in items:
        counts[item.status] = counts.get(item.status, 0) + 1
    print(json.dumps({"progress_file": str(progress_file), "count": len(items), "statuses": counts}, indent=2))


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--mian-k",
        default=argparse.SUPPRESS,
        help="Path to docs/mian-k. Defaults to docs/mian-k under the current working directory.",
    )
    parser.add_argument(
        "--progress-file",
        default=argparse.SUPPRESS,
        help="Optional explicit progress Markdown path.",
    )


def resolve_mian_k(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "mian_k", None) or DEFAULT_MIAN_K)


def resolve_progress_file(args: argparse.Namespace) -> str | None:
    return getattr(args, "progress_file", None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="Create or refresh progress table.")
    add_common_args(build)
    build.set_defaults(func=cmd_build)

    next_cmd = subparsers.add_parser("next", help="Return the next runnable item as JSON.")
    add_common_args(next_cmd)
    next_cmd.set_defaults(func=cmd_next)

    mark = subparsers.add_parser("mark", help="Update one progress item.")
    add_common_args(mark)
    mark.add_argument("--index", default=None)
    mark.add_argument("--path", default=None)
    mark.add_argument("--status", required=True)
    mark.add_argument("--note", default="")
    mark.add_argument("--replace-note", action="store_true")
    mark.add_argument("--reset-history", action="store_true")
    mark.add_argument("--commit", default="")
    mark.set_defaults(func=cmd_mark)

    summary = subparsers.add_parser("summary", help="Summarize progress statuses.")
    add_common_args(summary)
    summary.set_defaults(func=cmd_summary)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
