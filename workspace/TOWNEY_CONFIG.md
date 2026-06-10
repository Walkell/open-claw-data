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
  app_token: "OcmCb7TQYaHqnvsjBjAc0GRdnTb"
  bitable_name: "Towney-投资管理"
  positions_table: "持仓表"
  watchlist_table: "观察池"
  reports_table: "报告表"
  trades_table: "交易记录"
  monitor_table: "监控记录"
  decisions_table: "决策复盘"
  write_scope: "OcmCb7TQYaHqnvsjBjAc0GRdnTb 内全部表"
```

## 行情数据源

```yaml
market_adapter:
  quotes: "腾讯财经 qt.gtimg.cn（主）｜ akshare（备）"
  hist_data: "akshare | Yahoo Finance（美股兜底）"
  news: "akshare get_news_data | web_search | tavily_search"
```

## 委员会构成

```yaml
active_members: ["research", "industry", "news", "risk"]
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

| 名称 | 频率 | 输出 |
|------|------|------|
| towney-pre-market | 每早 8:30 | DM Towney |
| towney-monday-briefing | 每周一 8:20 | DM Towney |
| towney-monitor-write-am | 每10分钟 9-11 | 写表 |
| towney-morning-check | 每10分钟 9-11 | 写表 |
| towney-builder-reminder | 每30分钟 9-14 | DM Towney |
| towney-afternoon-check-pm | 每10分钟 13-15 | 写表 |
| towney-eod-review | 收盘 18:30 | DM Towney |
| towney-weekly-review | 每周五 18:40 | DM Towney |
| towney-monthly-review | 每月末 18:50 | DM Towney |

---

_配置档版本化，修改时不影响框架代码。_
