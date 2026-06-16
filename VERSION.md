# OpenClaw 版本历史

---

## v5.5
> 日期：2026/06/16

Corona 接管全部 cron 触发任务，cron 体系统一改造，配置档规范化，鉴权方式迁移。

- **Corona 上线**：所有 cron 触发任务（投委会编排 + 盘中监控）的第一入口，独立于 Butler，持久化 per-principal session（`agent:corona:cron:{principal}`），通过状态文件 `shared/corona-status/{principal}.json` 与 Butler 桥接；Butler 仅服务用户消息触发的 IC
- **cron 体系统一改造**：全部 cron job 改为 `agentId: "corona"`、`sessionTarget: "main"`、`payload.kind: "systemEvent"`，移除独立 `delivery` 块，统一走 Corona session；子委员（Research/Industry/News/Risk/Monitor）仍为 `sessionTarget: "isolated"`
- **清理 4 条过期 monitor cron**：`towney-{morning,afternoon}-monitor` / `klaire-{morning,afternoon}-monitor` 已被更细粒度的 3 段式监控（`*-monitor-am-0930/0920`、`*-monitor-am-h10-11`、`*-monitor-pm`，共 6 条）完全取代，删除而非保留修补
- **principal 配置档规范化**：`KLAIRE_CONFIG.md` / `TOWNEY_CONFIG.md` 重命名为 `CONFIG_KLAIRE.md` / `CONFIG_TOWNEY.md`，新增 `CONFIG_SAMPLE.md` 模板；新增 `custom-config-read`（唯一正确读取方式，强制按 principal 隔离）与 `custom-config-maintain`（模板与真实配置档结构同步检查清单）两个 SKILL
- **鉴权方式迁移为 auto-auth**：移除各 agent 行为文档中手动调用 `feishu_oauth` 的描述，改为"`permission_denied` 时直接重试原调用（最多 2 次），令牌由 auto-auth 在后台自动续期，禁止手动调用任何 `feishu_oauth` 命名工具"；工具仍保留在 `tools.alsoAllow` 列表中（可用性与行为指令是两层）
- **移除 Desk/Secretary 孤立目录**：`agents/desk`、`agents/secretary` 未在 `openclaw.json` 注册、仓库内无消费方，确认为遗留死配置后删除
- **删除孤立 SKILL `feishu-bitable-auth`**：仓库自建（非飞书官方），与现行 `custom-feishu-auth` 描述高度重叠且内容停留在旧鉴权方式（手动调用 `feishu_oauth` 续期），全仓库无任何文档按名调用，存在被 description 误匹配触发的风险，确认后删除
- **文档一致性修复**：补全 CLAUDE.md 的 Agents 表格 Corona 行与 Decision Flow 图，修正 Cron Jobs / Data Sources 两节与本版本架构不一致的残留描述

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
