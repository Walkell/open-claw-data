# OpenClaw 版本历史

---

## v5
> 日期：2026/06/12

Butler 升主、CIO 纯 isolated、Desk 退场、持仓保护、模型多样化。

- **Butler 升为主 agent**：所有请求（cron 或用户消息）的第一入口，负责 principal 确认、请求路由、IC 编排
- **CIO 改为 isolated-only**：只在 Butler spawn 的隔离 session 中运行，专注 §7 公式综合裁决，不再接收直接消息
- **Execution Desk 移除**：写库逻辑内联为 `custom-ic-write` SKILL，六闸门校验（principal 一致性 / Quorum / schema / 行情新鲜度 / baseline_score 复算 / VETO 一致性），减少一次 spawn/yield 往返
- **agentId `main` → `cio`**：语义对齐，Butler 才是真正的主 agent
- **workspace/ → workspace-cio/**：命名规范化，路径一致性
- **持仓状态保护**：任何 agent 禁止执行买卖、禁止修改持仓状态字段（持有 / 已卖出 / 已移除）；用户券商确认执行后告知 Butler，由 Butler 更新 Bitable
- **交易记录标注**：`custom-ic-write` 写入交易记录时 status 标注 `建议/待执行`，用户确认后更新为 `已执行`
- **修复 opening-bell 自我 spawn**：移除 Butler spawn 自身的错误模式，改为直接执行 `custom-ic-orchestrate` SKILL
- **模型多样化**：委员会五家族无同源重叠——research(minimax) / industry(kimi) / news(doubao) / risk(glm) / cio(deepseek)；Risk fallback 换为 kimi，彻底脱离 deepseek 家族
- **thinking 分级**：CIO / Butler / News / Risk 开启 high thinking；Research / Industry / Monitor 使用 medium

---

## v4
> 日期：2026/06/09

Arthur 投委会框架，专职委员分化，双 principal 完整上线。

- **Arthur 投委会结构**：CIO 不再兼任数据拉取，Research / Industry / News / Risk 四委员各司其职
- **Execution Desk sub-agent**：独立处理 Bitable 写库，CIO 综合后 spawn Desk 执行
- **flow_type 三级编排**：四委员（定期复盘）/ 三委员（新建仓）/ 精简两委员（EOD / 止损）
- **Bitable 表迁移**：持仓表 / 交易记录 / 观察池 / 监控记录 / 决策复盘 迁移至新表结构
- **双 principal 完整支持**：towney（DM）/ klaire（群聊）各自独立 Bitable 域、独立 cron 集
- **Cron 体系完善**：16 条 cron 覆盖盘前简报、开盘扫描、上午盘 / 下午盘监控、EOD 复盘、周报、月报
- **Risk VETO 机制**：risk_score ≥ 9 硬否决；7-8 软否决可 override，但需记录理由
- **自定义 SKILL 体系**：custom-feishu-auth / custom-ic-orchestrate / custom-ic-synthesise / custom-market-data-cn/us

---

## v3.1
> 日期：2026/06/09

初始提交，CIO + Table Desk 合一，投委会架构原型。

- **CIO + Table Desk 双角色合一**：单 agent 同时承担综合裁决和 Bitable 写库
- **基础投委会框架**：Research / Industry / News / Risk 四委员，§7 公式 baseline_score
- **子 Agent 派发协议**：spawn 时注入 principal + ledger_ref，sessions_yield 等待
- **Principal 隔离**：towney / klaire 数据域严格隔离，cross-principal 视为事故
- **白名单 .gitignore**：credentials / secrets / identity / sessions 等敏感路径排除

---
