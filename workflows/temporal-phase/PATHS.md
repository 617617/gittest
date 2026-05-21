# PATHS — temporal-phase path mapping

Per-host pinning of the two paths each host uses. Subsequent blueprints
and audits only use **prefix references** (e.g. `temporal:src/foo/bar.go`)
and each host resolves the prefix against its own row.

## Host path table

| Host | coord repo (this repo root) | work repo (Temporal project root) |
|------|------------------------------|------------------------------------|
| **Host A** (current CC) | `F:\gittest\gittest\` | `E:\code\temporal\` |
| **Host B**              | `D:\code\gittest\`    | `D:\code\temporal\`               |

> Role (CC / Codex) binding is **not** kept in this table — see the next
> section. This lets CC or Codex run on any host, so long as a matching
> row exists.

## Role ↔ host binding

| Role  | Host   |
|-------|--------|
| CC    | Host A |
| Codex | Host B |

If a host changes or an instance is added, edit this single table; no
other file needs to change.

## Prefix convention

When these prefixes appear in any document, each side resolves them
against its own row:

- `gittest:<relative>` → `<coord_repo>/<relative>`
- `temporal:<relative>` → `<work_repo>/<relative>`

Commit references use `temporal@<short-sha>` (7-character short SHA,
identical across hosts).
Range reference: `temporal@<base>..<head>`.

## Examples

A document writes:
```text
AllowedFiles:
  - temporal:src/foo/bar.go
Validation:
  - cd $(temporal:) && pytest tests/foo/
BaseCommit: temporal@a1b2c3d
```

Host A resolves it as:
```text
AllowedFiles:
  - E:\code\temporal\src\foo\bar.go
Validation:
  - cd E:\code\temporal && pytest tests\foo\
BaseCommit: a1b2c3d  (in E:\code\temporal git)
```

Host B resolves it as:
```text
AllowedFiles:
  - D:\code\temporal\src\foo\bar.go
Validation:
  - cd D:\code\temporal && pytest tests\foo\
BaseCommit: a1b2c3d  (in D:\code\temporal git)
```

## Maintenance

- If a host changes its path, **edit this file, commit, push** — nothing
  else needs to change.
- New host (third machine, etc.): add a row.
- Do not hard-code machine paths in CHARTER / ROLES / BATON.schema —
  those files must stay machine-independent.
