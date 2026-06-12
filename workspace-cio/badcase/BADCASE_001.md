# BADCASE.md - Your Workspace

这个文档记录下，所有遇到过的问题，以供模型参考，避免类似的问题。

---

## BC-001 · CIO 绕过投委会直接出分析结论

**时间**：2026-06

**场景**：用户询问阿里巴巴持仓（浮亏 -13.2%，仓位 10%）"要不要清盘"

**错误行为**：
- CIO 直接用 web_search 拉数据，自己出分析结论
- 没有召 Research / Industry / News / Risk 任何委员
- 没有走 §7 公式，没有 baseline_score，没有决议单
- 事后 CIO 自己承认绕过了流程

**正确行为**：
- "要不要清盘" = 持仓减仓决策，必须走精简两委员（Research + Risk）
- 输出 IC 召集声明 → spawn Research → spawn Risk → §7 公式 → 决议单 → spawn Desk

**根本原因**：
- CIO 在处理请求前隐式做了"这是简单查询"的判断，所有 AGENTS.md 规则在这个错误分类之后才生效，因此不起作用

**修复**：
- SOUL.md 增加强制输出：每次收到用户请求，第一行必须输出 `【请求分类】简单查询 / IC流程 / 监控操作` + 原因
- 让错误分类在第一行就暴露，用户可以当场叫停

---

## BC-002 · klaire EOD 复盘绕过 IC + 跨 principal 读取

**时间**：2026-06

**场景**：klaire EOD 自动复盘

**错误行为**：
- CIO 直接拉了 towney + klaire 两个持仓表（跨 principal）
- 没有召任何委员，自己出简报
- EOD 复盘属于"定期复盘"，必须走 IC（klaire = 精简两委员）

**修复**：
- AGENTS.md 增加"简单查询边界"说明，明确 EOD/盘前/定期复盘永远走 IC
- AGENTS.md 铁律三增加第5条：cron session 启动时唯一绑定 principal，禁止在同一 session 内查另一 principal 任何 Bitable 表
- 所有 IC cron 加强制 checklist（Principal 锁 + 检查点输出）

---

## BC-003 · Bitable NOTEXIST 大量出现（50+ 次/天）

**时间**：2026-06-11

**场景**：所有涉及 Bitable 读写的 Agent 操作

**错误行为**：
- 大量 NOTEXIST 错误，每天超过 50 次
- Agent 遇到错误后报告失败，没有正确续期重试

**根本原因**：
- `app_token` 出现在 Agent 的文字输出（thinking、response、spawn prompt）中时，系统安全策略将其替换为 `***`
- 后续 API 调用若使用了文字中的值（而非直接从工具调用结果取值），传给 API 的是 `***` → NOTEXIST
- 曾误判为"截断格式可绕过安全策略"——这是错误的，截断 token 无法被 API 识别

**修复**：
- 创建 `custom-feishu-auth` SKILL，统一所有 Agent 的 token 获取协议
- 核心规则：app_token 从工具调用结果直接传入下一个工具调用，不经过任何文字
- spawn 子 Agent 的 prompt 严禁携带 app_token 值；子 Agent 自己调 SKILL 获取 token

---

## BC-004 · 盘前美股隔夜数据错误（历史数据混入）

**时间**：2026-06-11 盘前

**场景**：盘前简报拉取隔夜美股指数数据

**错误行为**：
- Yahoo Finance API 调用失败
- 用 web_search 兜底，搜到了历史数据（非最近交易日收盘价）
- 历史数据被当成隔夜美股数据用于盘前分析，导致后续决策基于错误数据

**根本原因**：
- web_search 返回的是新闻/缓存页面，无法保证是最近交易日数据
- 没有数据日期验证机制
- 没有多源交叉验证，单源失败直接兜底导致数据质量无保障

**修复**：
- 创建 `custom-market-data-us` SKILL：Yahoo（主）+ Stooq（独立验证）+ 新浪美股（裁决）
- 创建 `custom-market-data-cn` SKILL：akshare（主）+ gtimg（验证）+ 新浪（裁决）
- 双源差异 ≤ 0.5% 且日期为最近交易日才可信；三源不一致则告警用户，不得继续决策
- **web_search 永久禁止用于任何行情价格数据**，只允许用于新闻和宏观数据
