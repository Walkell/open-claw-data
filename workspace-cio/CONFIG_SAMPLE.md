# CONFIG_SAMPLE.md — principal 配置档模板

> 新增一个 principal 时：复制本文件，重命名为 `CONFIG_{PRINCIPAL_ID}.md`（全大写，如 `CONFIG_TOWNEY.md`），
> 放在该 principal 的前端 agent 工作目录下（即 `front_agent` 字段所指向的 agent，如 klaire→`workspace-butler/`、
> towney→`workspace-dexter/`），按每个章节的"说明"填入真实值即可，不需要再手动删除说明块——
> 留着不影响任何 agent 取值，以后想回头看某个字段该填什么也方便。本文件模板本身仍留在 `workspace-cio/`，
> 因为它不属于任何具体 principal。
>
> 本文件只是模板，不会被任何 agent 读取或解析——填好的 `CONFIG_{PRINCIPAL_ID}.md` 才是真正生效的配置档。
> 框架层文件（Butler/CIO/Corona/Monitor 的 AGENTS.md）不应该硬编码这里的任何值，应该按 principal
> 去对应的配置档里取。

## principal 标识

> 说明：`id` 必填，全小写，用于 cycle_id 前缀、cron job 名称前缀（如 `xxx-eod-review`）、sessionKey（`agent:corona:cron:xxx`）。
> `display_name` 必填，人类可读名称，用于输出文案。
> `front_agent` 必填，负责接收该 principal **用户消息**的前端 agent 名称（如 `Butler` / `Dexter`）——每个
> principal 固定由一个前端 agent 通过专属飞书机器人服务，且该 principal 的 CONFIG 文件就放在这个前端
> agent 的工作目录下（见上方说明）。渠道归属的权威来源是本文件"输出通道"一节，不需要另一份独立绑定文件。

```yaml
principal:
  id: ""
  display_name: ""
  front_agent: ""
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
  bitable_name: ""
  positions_table: ""
  watchlist_table: ""
  reports_table: ""
  trades_table: ""
  monitor_table: ""
  decisions_table: ""
  write_scope: ""
```

## 盈利目标（必填）

> 说明：`annual_return` 该 principal 的年化收益目标；`set_date` 目标设定日期。

```yaml
profit_target:
  annual_return: ""
  set_date: ""
```

## 风险阈值（必填，无特殊需求可直接沿用默认值）

> 说明：`veto` 达到该分数自动 VETO；`hard_veto` 达到该分数硬否决，不可 override。无特殊需求直接照抄下面的默认值即可。

```yaml
risk_thresholds:
  veto: 7
  hard_veto: 9
```

## 仓位体系（可选，按 principal 实际需要的输出格式填写，没有就删掉本节）

- 建仓建议：仓位% + 建仓价 + 目标价
- 减仓建议：当前仓位% → 目标仓位%

## 输出通道（必填）

> 说明：ID 前缀本身就是类型，不需要额外配置类型字段——`ou_` 开头 = 单聊 ID，`oc_` 开头 = 群聊 ID。
> **渠道归属是永久且排他的，不是"共用、按消息内容区分"**：一个 channel ID 只属于一个 principal，填在这里就代表
> 这个 principal 独占这个渠道——即使另一个 principal 在该渠道发消息，也不会触发它自己的 IC 或推送，永远按声明的
> 归属方处理。如果某个渠道确实需要被多个 principal 永久共用，要在涉及的所有 principal 的 CONFIG 文件本节同步
> 加一条明确说明，不要靠这里的字段隐含表达。
> Corona（cron 触发）没有挂载聊天会话，必须从这里读到明确的渠道 ID 才能推送；`front_agent`（用户对话触发）默认走
> 当前会话路由，不依赖这里的值。

```
ID：{群聊ID}/{单聊ID}
```

## cron 配置（必填，但本文件不维护具体内容）

> 说明：权威来源见 `cron/jobs.json`（按 `{principal_id}-*` 前缀过滤即为本 principal 的任务）。本文件不重复维护
> 频率/agentId 等会随架构调整变动的字段，避免双写不同步。
>
> 新增 principal 时，需要在 `cron/jobs.json` 里补对应的 `{principal_id}-*` job，并在 `workspace-corona/AGENTS.md`
> 的"盘中监控流程 → Monitor 任务与推送目标"表里补一行——这一步目前还没有 SKILL 化，是手动操作，操作时注意
> 不要动到其他 principal 的现有行。

权威来源：`cron/jobs.json`

---

_配置档版本化，修改时不影响框架代码。_
