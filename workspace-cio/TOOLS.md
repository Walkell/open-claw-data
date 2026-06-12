# CIO · 工具配置

## 📊 行情数据获取策略

**原则：按市场走各自最直接的数据源。Bitable 永远是唯一持仓元数据来源，不用任何缓存/记忆。**

### A股 / 港股
> 使用 `custom-market-data-cn` SKILL（双源验证 + 三源裁决）

```
源1: akshare__get_realtime_data(eastmoney_direct)
源2: qt.gtimg.cn（腾讯财经）
源3（裁决）: 新浪财经 hq.sinajs.cn
两源差异 ≤ 0.5% → 验证通过；否则引入源3裁决；三源不一致 → 告警用户
```
⚠️ **web_search 严禁用于行情价格数据**

### 美股 / 全球指数
> 使用 `custom-market-data-us` SKILL（多源独立验证 + 数据日期验证）

```
源1: Yahoo Finance API (query1.finance.yahoo.com)
源2: Stooq (stooq.com — 欧洲独立数据源，与 Yahoo 无关)
源3（裁决）: 新浪财经美股 (hq.sinajs.cn/list=gb_XXX)
两源差异 ≤ 0.5% 且日期均为最近交易日 → 验证通过；否则引入源3裁决；三源不一致 → 告警用户
```
⚠️ **web_search 严禁用于行情价格数据**（2026-06-11 教训：Yahoo 失败后兜底用 web_search，拉到历史数据，导致错误决策）
⚠️ Yahoo query1 和 query2 是同一服务不同 CDN，不是独立数据源，不可用作交叉验证

### Bitable 表 ID 速查

> **token 获取：使用 `custom-feishu-auth` SKILL**，app_token 不得出现在任何文字输出。绝不串账户。

```
towney (Towney-投资管理):
  持仓表: tblUeTGMf0IKJ8Pk  | 报告表: tbllqOCpSadabEYt  | 交易记录: tblUZ9WvrF6FVZTS
  观察池: tblaLlSQp8tEcWgJ  | 监控记录: tblFAfrZs4Rz4AOu | 决策复盘: tbl7TR8G43GCN057

klaire (Klaire-投资管理):
  持仓表: tbl9xYrGkBDZlnYm  | 报告表: tblsyCW1JE0sJnwm  | 交易记录: tblVKj7wdGxMI4DQ
  观察池: tblaQY1jOFWOXd1U  | 监控记录: tblHkc0MfQbe2x37 | 决策复盘: tblrV0rNe4npQfic
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
