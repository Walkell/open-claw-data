# TOWNEY_CONFIG.md — principal 配置档

## principal 标识

```yaml
principal:
  id: "towney"
  display_name: "Towney"
```

## 数据域（隔离核心）

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

## 委员会构成

```yaml
active_members: ["research", "industry", "news", "risk"]
```

## 盈利目标

```yaml
profit_target:
  annual_return: "30%"  # 2026年度年化收益目标
  set_date: "2026-06-15"
```

## 风险阈值

```yaml
risk_thresholds:
  veto: 7      # ≥7 自动 VETO
  hard_veto: 9 # ≥9 硬否决，不可 override
```

## 仓位体系

- 每只独立满仓线，不跨标的对比
- 不涉及总资金金额数字
- 建仓建议：仓位% + 建仓价 + 目标价
- 减仓建议：当前仓位% → 目标仓位%

## 输出通道

- **私聊:** DM Towney（ou_aa8d3c082f316a8c9e18b9e6e8eeb88b）
- **群聊（禁持仓数据）:** Klaire+投委会+Towney 群

## cron 清单

| 名称 | 频率 | 输出 | agentId |
|------|------|------|---------|
| towney-pre-market | 每早 8:30（二-五） | DM Towney | butler |
| towney-monday-briefing | 每周一 8:20 | DM Towney | butler |
| towney-opening-bell | 每日 9:30（周一-五） | DM Towney | butler |
| towney-morning-check | 每15分钟 9-11 | 写表 | monitor |
| towney-afternoon-check-pm | 每15分钟 13-15 | 写表 | monitor |
| towney-eod-review | 收盘 18:30 | DM Towney | butler |
| towney-weekly-review | 每周五 18:40 | DM Towney | butler |
| towney-monthly-review | 每月末 18:50 | DM Towney | butler |

---

_配置档版本化，修改时不影响框架代码。_
