# CONFIG_KLAIRE.md — principal 配置档

## principal 标识

> 说明：`id` 必填，全小写，用于 cycle_id 前缀、cron job 名称前缀（如 `xxx-eod-review`）、sessionKey（`agent:corona:cron:xxx`）。
> `display_name` 必填，人类可读名称，用于输出文案。

```yaml
principal:
  id: "klaire"
  display_name: "Klaire"
  front_agent: "Butler"
```

## 数据域（隔离核心，必填）

> 说明：
> - `app_token` 固定写法不要改，禁止硬编码真实 token，运行时通过 `feishu_bitable_app.list()` 动态获取
> - `bitable_name` 该 principal 专属的多维表格应用名
> - `positions_table` / `watchlist_table` / `reports_table` / `trades_table` / `monitor_table` 必填
> - `decisions_table` 可选，若该 principal 不需要决策复盘表可整行删除（klaire 当前未启用）
> - 还可按需追加其他扩展表，klaire 这里多了 kpi_table/playbook_table/notes_table，表名自定义
> - `write_scope` 必填，写入范围说明

```yaml
ledger:
  app_token: "[通过 feishu_bitable_app.list() 动态获取，禁止硬编码]"
  bitable_name: "Klaire-投资管理"
  positions_table: "持仓表"
  watchlist_table: "观察池"
  reports_table: "报告表"
  trades_table: "交易记录"
  monitor_table: "监控记录"
  kpi_table: "KPI追踪"
  playbook_table: "执行手册"
  notes_table: "说明"
  write_scope: "Klaire-投资管理 内全部表"
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

## 输出通道（必填）

> 说明：ID 前缀本身就是类型，不需要额外配置类型字段——`ou_` 开头 = 单聊 ID，`oc_` 开头 = 群聊 ID。
> **渠道归属是永久且排他的**：这个群聊永久绑定 klaire——哪怕 towney 在这个群里发消息/@Butler，
> principal 仍然始终判定为 klaire，不会因为消息内容切换。本节是这条绑定关系的唯一权威来源，towney
> 的对应渠道见 `workspace-dexter/CONFIG_TOWNEY.md` 的"输出通道"一节。

```
ID：oc_c19042fb899cda7eeca1bbbd7d981d1a
```

- 群聊（投委会群）：klaire 专属，唯一输出通道，全权限。即使 towney 在该群发言，也按 klaire 处理，绝不切换到 towney 的数据域

## cron 配置（必填，但本文件不维护具体内容）

> 说明：权威来源见 `cron/jobs.json`（按 `{principal_id}-*` 前缀过滤即为本 principal 的任务）。本文件不重复维护
> 频率/agentId 等会随架构调整变动的字段，避免双写不同步。

权威来源见 `cron/jobs.json`（按 `klaire-*` 前缀过滤即为本 principal 的任务）。

---

_配置档版本化，修改时不影响框架代码。_
