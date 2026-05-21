# PATHS — <PRESET> path mapping

Per-host pinning of the two paths each host uses. All subsequent docs
reference work-repo paths only via prefix (`<project>:<rel>`); each
host resolves the prefix against its own row.

## Host path table

| Host | coord repo (this repo root) | work repo (`<project>` root) |
|------|------------------------------|------------------------------|
| **Host A** | `<absolute path>` | `<absolute path>` |
| **Host B** | `<absolute path>` | `<absolute path>` |

(Add more rows if more hosts participate.)

## Role ↔ host binding

| Role  | Host   |
|-------|--------|
| CC    | `<Host X>` |
| Codex | `<Host Y>` |

(If a host changes or an instance is added, edit this table; no other
file needs to change.)

## Prefix convention

When the following prefixes appear, each side resolves against its own
row:

- `gittest:<relative>` → `<coord_repo>/<relative>`
- `<project>:<relative>` → `<work_repo>/<relative>`

Commit references use `<project>@<short-sha>` (7-char short SHA,
identical across hosts).
Range reference: `<project>@<base>..<head>`.

## Examples

A document writes:
```text
AllowedFiles:
  - <project>:src/foo/bar.py
Validation:
  - cd $(<project>:) && pytest tests/foo/
BaseCommit: <project>@a1b2c3d
```

Host A resolves it as `<resolved path on Host A>`.
Host B resolves it as `<resolved path on Host B>`.

## Maintenance

- If a host changes its path, edit this file, commit, push — nothing
  else changes.
- New host: add a row.
- Do not hard-code machine paths in CHARTER / ROLES / BATON.schema or
  any lane SKILL — those files must stay machine-independent.
