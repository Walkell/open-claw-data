# KLAIRE_CONFIG.md — principal 配置档

## principal 标识

```yaml
principal:
  id: "klaire"
  display_name: "Klaire"
```

## 数据域（隔离核心）

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

## 委员会构成

```yaml
active_members: ["research", "risk"]  # 精简两委员；深度分析例外走四委员
```

## 风险阈值

```yaml
risk_thresholds:
  veto: 7      # ≥7 自动 VETO
  hard_veto: 9 # ≥9 硬否决，不可 override
```

## 仓位体系

- 每只独立满仓线
- 不涉及总资金金额数字

## 输出通道

- **群聊:** Klaire+投委会+Towney（oc_c19042fb899cda7eeca1bbbd7d981d1a）
- ⚠️ 群内禁输出持仓数据（成本/盈亏/仓位/交易记录），禁写 Bitable

## cron 清单

| 名称 | 频率 | 输出 | agentId |
|------|------|------|---------|
| klaire-pre-market | 每早 8:35（二-五） | 群 | butler |
| klaire-monday-briefing | 每周一 8:25 | 群 | butler |
| klaire-opening-bell | 每日 9:30（周一-五） | 群 | butler |
| klaire-intraday-monitor | 每15分 9-11 | 写表 | monitor |
| klaire-afternoon-monitor-pm | 每15分 13-15 | 写表 | monitor |
| klaire-eod-review | 收盘 18:45 | 群 | butler |
| klaire-weekly-review | 每周五 18:50 | 群 | butler |
| klaire-monthly-review | 每月末 18:55 | 群 | butler |

---

_配置档版本化，修改时不影响框架代码。_
