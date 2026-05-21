# _coord — temporal-phase 邮箱

本目录是 `temporal-phase` 预设的 git-tracked 邮箱,与
`blue-k-git-baton-testkit/_coord/` 完全独立。

- `from-cc/` — CC 发送给 Codex 的产物(执行前审核、汇总、修复、执行
  后审核等)。
- `from-codex/` — Codex 发送给 CC 的产物(蓝图、执行报告、subagent
  审核、汇总、修复、收尾等)。

文件命名:`<phase-id>__<step-tag>.md`(见 `../ROLES.md` Step Matrix
列出的产物名)。每份文件首行 `BatonNext: <STATE>` 显式声明状态机要转
移到的状态(状态名见 `../BATON.schema.md`)。
