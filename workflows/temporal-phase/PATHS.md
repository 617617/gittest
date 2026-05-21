# PATHS — temporal-phase 路径映射表

固定**每台主机**上的两条路径,后续蓝图/审核里只用**前缀引用**(如
`temporal:src/foo/bar.go`),各方按本机这一行解析为绝对路径。

## 主机路径表

| 主机 | coord repo(本仓库根) | work repo(Temporal 项目根) |
|------|------------------------|------------------------------|
| **Host A** (当前 CC 所在) | `F:\gittest\gittest\` | `E:\code\temporal\` |
| **Host B** | `D:\code\gittest\`    | `D:\code\temporal\`         |

> 角色(CC / Codex)与主机的绑定**不在本表里**——见下一节"角色 ↔ 主机
> 绑定"。这样允许 CC、Codex 之中任意一方在任意主机上落地,只要在本表
> 里能找到一行匹配自己的主机。

## 角色 ↔ 主机绑定

| 角色 | 主机 |
|------|------|
| CC   | Host A |
| Codex | Host B |

如未来换机或新增实例,改本表一行即可,不动其他文件。

## 前缀约定

文档里出现以下前缀时,各方按自己一行解析:

- `gittest:<relative>` → `<coord_repo>/<relative>`
- `temporal:<relative>` → `<work_repo>/<relative>`

提交引用统一写作:`temporal@<short-sha>`(7 位短 SHA,跨机器一致)。
区间引用:`temporal@<base>..<head>`。

## 示例

文档里写:
```text
AllowedFiles:
  - temporal:src/foo/bar.go
Validation:
  - cd $(temporal:) && pytest tests/foo/
BaseCommit: temporal@a1b2c3d
```

Host A 解析为:
```text
AllowedFiles:
  - E:\code\temporal\src\foo\bar.go
Validation:
  - cd E:\code\temporal && pytest tests\foo\
BaseCommit: a1b2c3d  (in E:\code\temporal git)
```

Host B 解析为:
```text
AllowedFiles:
  - D:\code\temporal\src\foo\bar.go
Validation:
  - cd D:\code\temporal && pytest tests\foo\
BaseCommit: a1b2c3d  (in D:\code\temporal git)
```

## 维护

- 任意一台主机换了路径,**只改本文件、提交、推送**即可,无须修改其
  他任何文件。
- 新增主机(例如第三台机器)在表里加一行。
- 不要在 CHARTER / ROLES / BATON.schema 里写死任何机器路径——它们应
  保持机器无关。
