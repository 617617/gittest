# workflows/ — 多 AI 协作工作流插槽注册表

本目录是**工作流预设的注册表**。每一个子目录就是一个 plug-and-play
的协作工作流(preset),描述某个具体项目场景下 CC 与 Codex 如何分工、
通过哪些状态、按什么样的 baton 交接来推进。

`blue-k-git-baton-testkit/` **不**位于此目录下,也**不**读取本目录中
的任何文件——它是已经定型的第一个工作流实例,保持原样冻结。本注册表
是面向"以后还会有其他项目想接入双 AI 协作"的增量机制。

## 目录结构

```text
workflows/
  README.md           ← 本文件
  _active.md          ← 单一活动指针:当前生效的 preset 名(或 none)
  <preset-name>/      ← 一个工作流预设
    CHARTER.md        ← 流程章程:目标、范围、完成标准
    ROLES.md          ← 步骤 × AI 责任矩阵
    BATON.schema.md   ← 状态机:状态、合法转移、驱动者
    _coord/
      from-cc/        ← CC → Codex 的邮箱(git-tracked)
      from-codex/     ← Codex → CC 的邮箱(git-tracked)
    skills/           ← 该 preset 专属的 lane skill 占位
```

## 新增一个 preset

1. 在本目录下新建 `<preset-name>/`。
2. 拷贝既有 preset 的四个核心文件(CHARTER / ROLES / BATON.schema /
   `_coord/`)作为骨架。
3. 用源工作流文档逐节填充 CHARTER 与 ROLES。
4. 从 ROLES 矩阵推出 BATON 状态机。
5. 为每个 lane 在 `skills/` 下写一份 SKILL.md 占位(可以先只写"何时
   触发、读什么、写什么、产物")。
6. 不要在新 preset 里复制 `blue-k-git-baton-testkit/` 的任何内容——
   两边互不相干。

## 激活机制

`workflows/_active.md` 写一个 preset 名(或 `none`)。同一时间只有
一个 preset 是"活动的"。切换 preset = 编辑这一个文件 + 切到该
preset 的 skill 集合。

`blue-k-git-baton-testkit/` 不读这个指针,所以无论 `_active.md` 指向
谁,testkit 的现有流程都不受影响。

## 当前已注册的 preset

- `temporal-phase` — 源自
  `E:/code/temporal/docs/skill-temporal-reorchestration/current/execution/PHASE_COLLABORATIVE_EXECUTION_WORKFLOW_ZH_2026-05-21.md`
  的 Phase 协同开发流程。
