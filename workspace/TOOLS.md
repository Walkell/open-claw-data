# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## 📊 行情数据获取策略

**原则：按市场走各自最直接的数据源。Bitable 永远是唯一持仓元数据来源，不用任何缓存/记忆。**

### A股 / 港股
```
akshare__get_realtime_data (eastmoney_direct)
    ↓ 502挂了？
curl qt.gtimg.cn（腾讯财经，A股 sh/sz + 港股 hk 前缀）
```

### 美股 / 全球指数
```
Yahoo Finance API (curl + User-Agent: Mozilla/5.0)
https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}
    ↓ 挂了？
web_search / tavily_search 兜底
```

### 宏观数据（利率、汇率、VIX等）
```
web_search / tavily_search
```

### Bitable 双账户（v3.1）

⚠️ 不在此维护任何 token（token 可能刷新）
⚠️ TOKEN 动态获取：每次调 Bitable API 之前，第一步必须是 feishu_bitable_app.list()，用返回的完整 token
⚠️ 绝对不串账户！每个 principal 只有自己的数据域

| principal | Bitable 名称 | app_token |
|-----------|-------------|-----------|
| towney | InvestmentOS | ODPxbiwnzazrOSsrgY3c9sqGneg |
| chengke | 程珂 - 投资管理 | HYf4bOpq1RRdj6NRP5scjnqQsUnb |

表结构参考（通过 app.list() + table.list() 动态获取，此处仅供识别人名）：
```
towney (InvestmentOS):
  持仓表: tblGcWd82BIXTT9W
  报告表: tblTaIWRcRyZgd04
  交易记录: tbllEHanR9gTPnJU
  观察池: tblxfCjgr1zkKAbi
  监控记录: tbl8mYixzl6hztip
  决策复盘: tblaPynTH8R9SMKw

chengke (程珂 - 投资管理):
  持仓表: tblEsbj5wKnu4Jw4
  报告表: tbl9uqQYP6llgjPA
  交易记录: tbl1PXHGEwGZOoai
  观察池: tblZtpWCzAXJVvyY
  监控记录: tblDMOdxSKwetSzG
  KPI追踪: tblXE4UsBX6EAlap
  执行手册: tblrCkXtQDsd5XOF
```

【Bitable 标准调用流程 —— 每次必走，不可跳过】
1. feishu_bitable_app.list() → 获取最新的完整 app_token
2. 用步骤1返回的完整 token 调用 table_record.list() 等
3. 绝不用任何文件中的 token 值，不记忆、不缓存、不推断

【Token 过期处理 —— 2026-06-05 确立】
⚠️ permission_denied 不是权限配置问题，是飞书 user token 有有效期
⚠️ token 用久了会过期，过期后调用 Bitable API 返回 permission_denied
⚠️ 出现 permission_denied 时：
  a) 自动走一遍 feishu_oauth 重新授权流程
  b) 授权完成后再次 feishu_bitable_app.list() 获取新 token
  c) 用新 token 继续操作，不再报权限错误放弃
⚠️ 禁止在 permission_denied 后直接放弃写入（今天均胜的成本就因为 token 过期写错了两次）
```

### 数据获取优先级（按市场）
```
A股/港股实时: akshare__get_realtime_data(eastmoney_direct) → 腾讯财经 qt.gtimg.cn 兜底
A股/港股历史: akshare__get_hist_data(sina/eastmoney) → YFinance 兜底
美股/全球指数: Yahoo Finance API → web_search 兜底
宏观数据: web_search / tavily_search
⚠️ 日期用 akshare__get_time_info 确认，不用推算
⚠️ 美股收盘数据优先 YFinance 直接拉，不用财经新闻搜索（延迟高/日期易混）
```

---

## 🏗️ 仓位与资金体系（核心规则，永不遗忘）

### 每只独立满仓制
- 每只持仓有自己独立的"满仓线"，不同标的不通用
- 天孚通信满仓 X 万，澜起科技满仓 Y 万，X ≠ Y
- **仓位百分比 = 该标的自身满仓额的百分比，不是总资产的百分比**
- 天孚 50% + 澜起 40% 不能相加，单位不同

### 建仓/减仓体系
- 不讨论"总资金金额"（用户从未透露过具体金额数字）
- 不跨标的对比仓位（50% vs 40% 无意义）
- 建仓建议只出：仓位%（该标的满仓额的%）、建仓价、目标价
- 减仓建议只出：从当前仓位% → 目标仓位%，不提及金额

### 不可做的事（红线）
- ❌ 用"100万基准"反推具体金额
- ❌ 说"释放了XX万资金"
- ❌ 对比不同标的的仓位百分比大小
- ❌ 计算"总仓位"或"总持仓比例"
- ❌ 假设各标的满仓额相同

### 和用户沟通时的表述
- ✅ "天孚从50%减至30%"
- ✅ "建议海光信息仓位30%，建仓价260"
- ❌ "天孚仓位50%比澜起40%高"
- ❌ "释放了约20万额度"

---

Add whatever helps you do your job. This is your cheat sheet.

## Related

- [Agent workspace](/concepts/agent-workspace)
