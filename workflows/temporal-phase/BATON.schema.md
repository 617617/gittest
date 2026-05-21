# temporal-phase — BATON State Schema

本预设的 baton 状态机。每一份产物文件首行 `BatonNext: <STATE>` 显式
声明转移目标;读取方据此确认状态推进。状态名一律大写蛇形,带语义后缀
区分轮次或可选环节。

## 状态枚举

```text
DRAFTING_BLUEPRINT             # Codex 起草蓝图,尚未交付
PRE_AUDIT_R1                   # 第 1 轮执行前审核(CC + Codex 并行)
PRE_AUDIT_SYNTHESIS_R1         # CC 汇总第 1 轮意见
BLUEPRINT_REVISION_R1          # CC 修复蓝图(第 1 轮后)
PRE_AUDIT_R2                   # 第 2 轮(必要时)
PRE_AUDIT_SYNTHESIS_R2
BLUEPRINT_REVISION_R2
PRE_AUDIT_R3                   # 第 3 轮(必要时,上限)
PRE_AUDIT_SYNTHESIS_R3
BLUEPRINT_REVISION_R3
BLUEPRINT_ACCEPTED             # 蓝图通过执行前审核
EXECUTING                      # Codex 执行 Phase
EXECUTION_REPORTED             # Codex 已交付执行报告
POSTEXEC_SUBAGENT_REVIEW       # Codex 多 subagent 综合审核
POSTEXEC_CC_REVIEW             # CC 执行后独立审核
POSTEXEC_SYNTHESIS             # Codex 汇总执行后两边意见
POSTEXEC_FIX                   # Codex 吸收修复
SECOND_AUDIT_DECISION          # Codex 决策是否进入二次双审
SECOND_AUDIT_CC                # (可选)二次双审 CC 侧
SECOND_AUDIT_CODEX             # (可选)二次双审 Codex 侧
SECOND_AUDIT_FIX               # (可选)二次双审后修复
PHASE_CLOSING                  # Codex 核对完成标准
COMPLETED                      # 终态:Phase 通过完成标准
BLOCKED_BLUEPRINT              # 终态:执行前三轮后仍阻塞
BLOCKED_POSTEXEC               # 终态:二次双审仍有阻塞性问题
```

## 合法转移

```text
DRAFTING_BLUEPRINT          -> PRE_AUDIT_R1                 (Codex 交付蓝图)

PRE_AUDIT_R1                -> PRE_AUDIT_SYNTHESIS_R1       (CC + Codex 双方都交付审核)
PRE_AUDIT_SYNTHESIS_R1      -> BLUEPRINT_REVISION_R1        (CC 汇总完毕,需修复)
PRE_AUDIT_SYNTHESIS_R1      -> BLUEPRINT_ACCEPTED           (CC 汇总完毕,无须修复,直接通过)
BLUEPRINT_REVISION_R1       -> BLUEPRINT_ACCEPTED           (修复完成且可接受)
BLUEPRINT_REVISION_R1       -> PRE_AUDIT_R2                 (修复完成但需再审)

PRE_AUDIT_R2                -> PRE_AUDIT_SYNTHESIS_R2
PRE_AUDIT_SYNTHESIS_R2      -> BLUEPRINT_REVISION_R2
PRE_AUDIT_SYNTHESIS_R2      -> BLUEPRINT_ACCEPTED
BLUEPRINT_REVISION_R2       -> BLUEPRINT_ACCEPTED
BLUEPRINT_REVISION_R2       -> PRE_AUDIT_R3

PRE_AUDIT_R3                -> PRE_AUDIT_SYNTHESIS_R3
PRE_AUDIT_SYNTHESIS_R3      -> BLUEPRINT_REVISION_R3
PRE_AUDIT_SYNTHESIS_R3      -> BLUEPRINT_ACCEPTED
BLUEPRINT_REVISION_R3       -> BLUEPRINT_ACCEPTED
BLUEPRINT_REVISION_R3       -> BLOCKED_BLUEPRINT            (上限达成仍阻塞)

BLUEPRINT_ACCEPTED          -> EXECUTING                    (Codex 起开始执行)
EXECUTING                   -> EXECUTION_REPORTED           (Codex 交付执行报告)
EXECUTING                   -> BLOCKED_BLUEPRINT            (执行中发现重大缺口,回退)

EXECUTION_REPORTED          -> POSTEXEC_SUBAGENT_REVIEW     (Codex 启动 subagent 审核)
POSTEXEC_SUBAGENT_REVIEW    -> POSTEXEC_CC_REVIEW           (subagent 审核交付后,等待 CC)
POSTEXEC_CC_REVIEW          -> POSTEXEC_SYNTHESIS           (CC 审核交付后,Codex 汇总)
POSTEXEC_SYNTHESIS          -> POSTEXEC_FIX                 (有需要修复)
POSTEXEC_SYNTHESIS          -> PHASE_CLOSING                (无须修复,直接收尾)
POSTEXEC_FIX                -> SECOND_AUDIT_DECISION

SECOND_AUDIT_DECISION       -> PHASE_CLOSING                (NO:修复小且不动核心)
SECOND_AUDIT_DECISION       -> SECOND_AUDIT_CC              (YES:进入二次双审)
SECOND_AUDIT_CC             -> SECOND_AUDIT_CODEX           (CC 二审交付,等待 Codex)
SECOND_AUDIT_CODEX          -> SECOND_AUDIT_FIX
SECOND_AUDIT_FIX            -> PHASE_CLOSING                (修复通过)
SECOND_AUDIT_FIX            -> BLOCKED_POSTEXEC             (仍阻塞,不再循环)

PHASE_CLOSING               -> COMPLETED                    (完成标准全部满足)
PHASE_CLOSING               -> BLOCKED_POSTEXEC             (完成标准未满足)
```

## 谁能驱动哪次转移

| 转移 | 驱动者 | 说明 |
|------|--------|------|
| `* -> PRE_AUDIT_R*`, `BLUEPRINT_REVISION_R*`, `PRE_AUDIT_SYNTHESIS_R*` | CC | CC 是执行前阶段的流程闭环判断者 |
| `* -> BLUEPRINT_ACCEPTED` | CC | 由汇总者签署"可接受" |
| `BLUEPRINT_ACCEPTED -> EXECUTING` | Codex | 起手即转此态 |
| `EXECUTING -> EXECUTION_REPORTED` | Codex | 主执行者交付 |
| `EXECUTION_REPORTED -> POSTEXEC_SUBAGENT_REVIEW`, `* -> POSTEXEC_SYNTHESIS`, `POSTEXEC_FIX`, `SECOND_AUDIT_DECISION` | Codex | 执行后主路径都由 Codex 驱动 |
| `POSTEXEC_SUBAGENT_REVIEW -> POSTEXEC_CC_REVIEW`(等待 CC)与 `SECOND_AUDIT_CC` | CC | CC 是执行后独立审核 / 二次双审 CC 侧 |
| `PHASE_CLOSING -> COMPLETED \| BLOCKED_POSTEXEC` | Codex | 收尾判定 |

## 不变量(invariants)

1. **三轮上限**:`PRE_AUDIT_R3` 是执行前协同审核可达的最大轮次;
   `BLUEPRINT_REVISION_R3` 若不能接受,**必须**转 `BLOCKED_BLUEPRINT`,
   不允许出现 R4 状态。
2. **完成标准守门**:从 `PHASE_CLOSING` 到 `COMPLETED` 的转移必须显式
   列举源文档 §11 的全部完成标准,且每条都已满足。
3. **二次双审一次性**:从 `POSTEXEC_FIX` 进入二次双审最多发生一次;
   `SECOND_AUDIT_FIX` 不能回环到 `SECOND_AUDIT_DECISION`。
4. **越权拒绝**:CC 不能写 `EXECUTION_REPORTED` / `POSTEXEC_FIX` 等
   "Codex 驱动"产物;Codex 不能写 `PRE_AUDIT_SYNTHESIS_*` /
   `BLUEPRINT_REVISION_*` 等"CC 驱动"产物。读取方发现越权产物应忽略
   并要求重发。
5. **隔离**:本状态机不引用、不读取、不依赖 `blue-k-git-baton-testkit/`
   下任何状态、邮箱或脚本。
