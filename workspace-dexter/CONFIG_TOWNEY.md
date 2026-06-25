# CONFIG_TOWNEY.md — principal 配置档

## principal 标识

> 说明：`id` 必填，全小写，用于 cycle_id 前缀、cron job 名称前缀（如 `xxx-eod-review`）、sessionKey（`agent:corona:cron:xxx`）。
> `display_name` 必填，人类可读名称，用于输出文案。

```yaml
principal:
  id: "towney"
  display_name: "Towney"
  front_agent: "Dexter"
```

## 数据域（隔离核心，必填）

> 说明：
> - `app_token` 固定写法不要改，禁止硬编码真实 token，运行时通过 `feishu_bitable_app.list()` 动态获取
> - `bitable_name` 该 principal 专属的多维表格应用名
> - `positions_table` / `watchlist_table` / `reports_table` / `trades_table` / `monitor_table` 必填
> - `decisions_table` 可选，若该 principal 不需要决策复盘表可整行删除
> - 还可按需追加其他扩展表（参考 klaire 的 kpi_table/playbook_table/notes_table），表名自定义
> - `write_scope` 必填，写入范围说明

```yaml
ledger:
  app_token: "[通过 feishu_bitable_app.list() 动态获取，禁止硬编码]"
  bitable_name: "Towney-投资管理"
  positions_table: "持仓表"
  watchlist_table: "观察池"
  reports_table: "报告表"
  trades_table: "交易记录"
  monitor_table: "监控记录"
  decisions_table: "决策复盘"
  write_scope: "Towney-投资管理 内全部表"
```

## 盈利目标（必填）

> 说明：`annual_return` 该 principal 的年化收益目标；`set_date` 目标设定日期。

```yaml
profit_target:
  annual_return: "30%"  # 2026年度年化收益目标
  set_date: "2026-06-15"
```

## 风险阈值（必填，无特殊需求可直接沿用默认值）

> 说明：`veto` 达到该分数自动 VETO；`hard_veto` 达到该分数硬否决，不可 override。无特殊需求直接照抄下面的默认值即可。

```yaml
risk_thresholds:
  veto: 7      # ≥7 自动 VETO
  hard_veto: 9 # ≥9 硬否决，不可 override
```

## 仓位体系（可选，按 principal 实际需要的输出格式填写，没有就删掉本节）

- 建仓建议：仓位% + 建仓价 + 目标价
- 减仓建议：当前仓位% → 目标仓位%

## 输出通道（必填）

> 说明：ID 前缀本身就是类型，不需要额外配置类型字段——`ou_` 开头 = 单聊 ID，`oc_` 开头 = 群聊 ID。
> **渠道归属是永久且排他的**：一个 channel ID 只能属于一个 principal，不存在"共用群聊、按消息内容区分"这种模式——
> 哪怕另一个 principal 在这个渠道里说话，这个渠道仍然只认它声明的归属方，不切换。每个 principal 的
> CONFIG 文件本节就是该渠道归属的唯一权威来源，不存在另一份独立的绑定声明文件。如果两个 principal
> 真的需要同一个群聊，必须先在双方 CONFIG 的本节同步加一条明确说明，而不是在这里写"共用"。

```
ID：ou_aa8d3c082f316a8c9e18b9e6e8eeb88b
```

- 单聊（DM Towney）：towney 唯一输出通道，全权限
- `oc_c19042fb899cda7eeca1bbbd7d981d1a`（投委会群）已永久绑定 klaire（见 `workspace-butler/CONFIG_KLAIRE.md` 的"输出通道"一节），**不是** towney 的输出通道，即使 towney 在该群发言也不触发 towney 的 IC 或推送

## cron 配置（必填，但本文件不维护具体内容）

> 说明：权威来源见 `cron/jobs.json`（按 `{principal_id}-*` 前缀过滤即为本 principal 的任务）。本文件不重复维护
> 频率/agentId 等会随架构调整变动的字段，避免双写不同步。

权威来源见 `cron/jobs.json`（按 `towney-*` 前缀过滤即为本 principal 的任务）。

---

_配置档版本化，修改时不影响框架代码。_
