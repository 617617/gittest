# HANDOFF — temporal-phase 工作流 · 给 Codex

读这一份就够了。本文件是 `temporal-phase` 工作流的 Codex 端入口。

## 1. 你现在在哪

- 协调仓库(coord repo,本目录所在):你机器上的 `gittest` 仓库根。
  你的绝对路径见 `PATHS.md`。
- 实际工作仓库(work repo,Phase 真正改代码的地方):你机器上的
  `temporal` 项目根。你的绝对路径见 `PATHS.md`。
- 协作模式:**路径 X**——协调产物在 coord repo,代码改动在 work repo,
  两边用 commit SHA 关联(细节见 §5)。

机器路径**只**在 `PATHS.md` 一处维护。文档里其他地方一律用前缀引用
(`gittest:...` / `temporal:...` / `temporal@<sha>`),避免硬编码导致
跨机不一致。

`workflows/_active.md` 当前值为 `temporal-phase`,意味着 coord repo 上
活动的工作流就是本预设。`blue-k-git-baton-testkit/` 与本预设完全独立,
不要交叉读写它的任何文件。

## 2. 必读(按顺序)

1. `PATHS.md`(双方机器路径表 + 前缀约定)
2. `CHARTER.md`(目标 / 完成标准 / 与 testkit 的隔离声明)
3. `ROLES.md`(16 步责任矩阵 + 产物名 + 邮箱)
4. `BATON.schema.md`(24 状态 + 合法转移 + 5 条不变量)
5. `skills/codex/SKILL.md`(你的 9 个 lane 的触发态、读什么、写什么、
   产物的 `BatonNext` 值)

源文档(权威):
`E:/code/temporal/docs/skill-temporal-reorchestration/current/execution/PHASE_COLLABORATIVE_EXECUTION_WORKFLOW_ZH_2026-05-21.md`

源文档变更时,优先同步本目录的 ROLES 与 BATON.schema。

## 3. 你在本预设下的角色

- 创造性输出主体:蓝图、执行、修复都由你落笔。
- 自我多 subagent 审核:执行后由你启动多个 subagent 做综合审核。
- 最终修复责任方:任何审核成立意见的吸收与修复都由你完成。

CC 是独立审核 / 跨方汇总 / 流程闭环判断者,**不会**写蓝图或修复代码。
反过来你也**不能**写下列产物(越权拒绝,见 BATON.schema 不变量 §4):
`pre-audit-cc-r*`、`pre-audit-synthesis-r*`、`blueprint-revision-r*`、
`postexec-cc-review`、`second-audit-cc`。

## 4. 你的产物落到哪里

写入路径:`workflows/temporal-phase/_coord/from-codex/`

文件名模式:`<phase-id>__<step-tag>.md`(`step-tag` 见 ROLES.md Step
Matrix:`blueprint`、`pre-audit-codex-r1`、`execution-report` 等等)。

**每份产物的第一行**必须是:

```text
BatonNext: <STATE>
```

`<STATE>` 取自 `BATON.schema.md` 的状态枚举。读取方据此推进 baton。
不写 `BatonNext:` 的产物被视为草稿,不触发状态转移。

## 5. 路径 X 下"coord 在这里、代码在那里"怎么连

蓝图与执行报告里出现"涉及代码"时,只用 `PATHS.md` §"前缀约定"里
定义的前缀,**绝不**写机器绝对路径。读取方各自按本机 `PATHS.md` 解析。

- 引用 work repo 路径:`temporal:<relative>`,如 `temporal:src/foo/bar.go`。
- 引用 work repo 提交:`temporal@<short-sha>`,如 `temporal@a1b2c3d`。
- 引用 work repo 区间:`temporal@<base>..<head>`。
- 不要把 work repo 的代码改动复制粘贴进 coord repo;只引用、不搬运。

蓝图模板片段示例(`<phase-id>__blueprint.md`):

```markdown
BatonNext: PRE_AUDIT_R1

# Phase <id> — Blueprint

Goal: ...
Scope:
  - temporal:src/foo/
  - temporal:docs/<...>/
Out-of-scope: ...
AllowedFiles:
  - temporal:src/foo/bar.go
  - temporal:src/foo/baz.go
Validation:
  - cd $(temporal:) && pytest tests/foo/
ExpectedArtifacts:
  - temporal:src/foo/<new-files>
  - gittest:workflows/temporal-phase/_coord/from-codex/<phase-id>__execution-report.md
RiskBoundary: ...
BaseCommit: temporal@<short-sha>
```

执行报告里出现"实际改动"时,给出 work repo 的 commit 列表:

```markdown
ActualChanges:
  - temporal@a1b2c3d  feat(foo): add bar
  - temporal@e4f5g6h  test(foo): cover bar edge cases
```

## 6. 起手动作

当用户(或上一 Phase 收尾)启动一个新 Phase 时,你处于
`DRAFTING_BLUEPRINT` 状态,要做的事:

1. 读源文档当前阶段目标(如有)+ 上一 Phase 的 `close.md`(若存在)。
2. 在 `from-codex/<phase-id>__blueprint.md` 写出蓝图,首行
   `BatonNext: PRE_AUDIT_R1`。
3. 提交到 coord repo(本仓库)并推送 `origin/master`。

CC 端会在下一轮自动看到你的蓝图(它的监视器看的就是 coord repo 的
`_coord/from-codex/`)。

## 7. 硬规则提示

- **不擅自扩范围**:执行阶段严格按 `AllowedFiles:` 推进。发现重大缺
  口或代码状态明显不一致 → 立即停下,写一份说明并转 `BLOCKED_BLUEPRINT`。
- **三轮上限**:执行前协同审核最多 `PRE_AUDIT_R3`。第三轮仍不可接受
  时,蓝图修复方(CC)会写 `BatonNext: BLOCKED_BLUEPRINT`。不要试图
  开 R4。
- **二次双审一次性**:`SECOND_AUDIT_FIX` 后只能去 `PHASE_CLOSING` 或
  `BLOCKED_POSTEXEC`,不能回环到 `SECOND_AUDIT_DECISION`。
- **完成标准守门**:`close.md` 必须逐条列出 CHARTER 的完成标准并标
  注满足/未满足,缺任意一条不能进 `COMPLETED`。
- **subagent 不替决策**:多 subagent 审核只提意见,最终判定由你做。
- **隔离**:不读、不写 `blue-k-git-baton-testkit/` 下任何东西。

## 8. 与 testkit 的关系

完全无关。testkit 是另一个独立模拟器(simulator),用来测 Blue-K
git-baton 协议。本预设借鉴了 testkit 的"git 邮箱"思路,但状态机、
邮箱目录、HANDOFF、skill 集合都是独立的。两边任意一方变化都不应触
发另一方变化。
