# TOOLS.md - Research Agent

## Bitable 调用协议

**每次必走，不可跳过：**
1. `feishu_bitable_app.list()` → 找到 principal 对应 Bitable，取完整 app_token（不缓存、不假设）
2. table_id 从 context.json 的 `positions_table_id` / `watchlist_table_id` 读取；遇 NOTEXIST 时调 `feishu_bitable_app_table.list()` 按名查找
3. 用步骤1的 app_token + table_id 调 `feishu_bitable_app_table_record.list()`
4. `permission_denied` / `NOTEXIST` → 自动走 `feishu_oauth` 续期 → 重新 `list()` → 继续，不放弃

**principal 和 table_id 从 context.json 读取（备用参考）：**

| principal | Bitable 名称 | 持仓表 | 观察池 |
|-----------|-------------|--------|--------|
| towney | Towney-投资管理 | tblUeTGMf0IKJ8Pk | tblaLlSQp8tEcWgJ |
| klaire | Klaire-投资管理 | tbl9xYrGkBDZlnYm | tblaQY1jOFWOXd1U |

---

## 行情数据源

### A股 / 港股 实时行情
```
主：akshare__get_realtime_data(source=eastmoney_direct)
备：python3 -c "import urllib.request; r=urllib.request.urlopen(
      'https://qt.gtimg.cn/q=sh688120,...', timeout=10).read().decode('gbk'); ..."
```
港股代码格式：`hk09988`（前缀 hk，不加 .HK）
港股行情为港币，换算人民币：港币 × 当日汇率（约 0.927，用 web_search 确认当日值）

### ⚠️ 涨跌幅铁律（违反 = 数据污染，整票作废）

**涨跌幅必须直接取自行情 API 的预计算字段，绝对禁止自行计算。**

| 来源 | 今日涨跌幅字段 | 昨收字段 |
|------|--------------|--------|
| gtimg（备路径） | `f[34]`（百分比，已含±号）| `f[33]` |
| akshare__get_realtime_data | `change_pct` 或 `涨跌幅` | `昨收` |

**Bitable 持仓表只含元数据字段：**

| 字段 | 用途 |
|------|------|
| 成本价 | 计算浮盈浮亏 |
| 止损价 | 判断是否触发止损 |
| 止盈价 | 判断是否触发止盈 |
| 仓位% | 读取当前仓位 |
| 备注 | 读取风险标记 |

持仓表不含任何行情字段（当前价 / 市值 / 涨跌幅已从表结构删除）。现价永远从行情 API 现拉。

**⚠️ 输出铁律：Research 的 JSON 输出不得包含任何具体价格数值。**
技术面评分（0-10）体现在 `dimensions.technical.score` 中，`note` 字段只写定性描述（如"站稳60日均线"），不写具体价格数字。CIO 把 Research 输出 inline 给 Risk 时，Risk 看到的不应有任何 Bitable 快照价。

### A股历史 / K线
```
akshare__get_hist_data(symbol, source=sina/eastmoney, interval=day/week/month, recent_n=N)
```

### 财报数据
```
akshare__get_income_statement(symbol)      # 利润表
akshare__get_balance_sheet(symbol)         # 资产负债表
akshare__get_cash_flow(symbol)             # 现金流量表
akshare__get_financial_metrics(symbol)     # 关键指标（ROE/PE/PB等）
```

### 研报 / 估值参考
```
web_search / tavily_search："{股票名} 研究报告 估值 2026"
```

---

## 仓位体系（只读，不推断）

- 每只持仓有独立满仓线，仓位 % = 该标的自身满仓额的百分比，不是总资产
- 不跨标的对比仓位百分比，不推算总资金金额
- 实际仓位/成本/止损/止盈 → 只从 Bitable 持仓表读，不用任何记忆中的快照
