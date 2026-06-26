# TOOLS.md - Research Agent

## Bitable 调用协议

> **Token 获取必须通过 `custom-feishu-auth` SKILL**（见 `extensions/openclaw-lark/skills/custom-feishu-auth/SKILL.md`）。app_token 不得出现在任何文字输出或文件中。

**会话启动（每次 Bitable 操作前必做）：**
1. 调用 `custom-feishu-auth` SKILL → 续期 + 取 app_token
2. app_token 从工具结果直接传入下一个调用，不经过文字
3. table_id 从 context.json 的 `positions_table_id` / `watchlist_table_id` 读取
4. `feishu_bitable_app_table_record.list()` 读取数据
5. 遇 `NOTEXIST` / `permission_denied` → 重新执行 SKILL（最多 2 次）

**principal 和 table_id 从 context.json 读取（备用参考）：**

| principal | Bitable 名称 | 持仓表 | 观察池 |
|-----------|-------------|--------|--------|
| towney | Towney-投资管理 | tblUeTGMf0IKJ8Pk | tblaLlSQp8tEcWgJ |
| klaire | Klaire-投资管理 | tbl9xYrGkBDZlnYm | tblaQY1jOFWOXd1U |

---

## 行情数据源

### A股 / 港股 实时行情

**必须使用 `custom-market-data-cn` SKILL**（见 `extensions/openclaw-lark/skills/market-data-cn/SKILL.md`）。该 SKILL 强制双源验证（akshare + gtimg）+ 三源裁决，禁止用 web_search 获取行情价格。

港股代码格式：`hk09988`（前缀 hk，不加 .HK）
港股行情为港币，换算人民币：港币 × 当日汇率（约 0.927，用 web_search 确认当日值）

### ⚠️ 涨跌幅铁律（违反 = 数据污染，整票作废）

**涨跌幅必须直接取自行情 API 的预计算字段，绝对禁止自行计算。** `custom-market-data-cn` SKILL 内部已处理此规则，直接用 SKILL 输出的 `change_pct` 字段即可。

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

**网络搜索强制优先级：**
1. **首选**：`zhipu-search__zhipu_web_search`（engine=`search_pro`，recency=`oneMonth`）
   - 敏感词（涉政/涉监管措辞）可能空返 → 切 tavily
2. **Fallback**：`tavily_search`（dev 额度可能耗尽，遇 432 → 降级单源并在 data_quality 标 ⚠️）
3. **页面原文**：`tavily_extract` 或 `web_fetch`

```
zhipu-search__zhipu_web_search(query="{股票名} 研究报告 估值 2026", recency="oneMonth")
```

⚠️ 同一 query 不在 zhipu 上重试超过 1 次；空返立刻换源/换措辞。

---

## 仓位体系（只读，不推断）

- 每只持仓有独立满仓线，仓位 % = 该标的自身满仓额的百分比，不是总资产
- 实际仓位/成本/止损/止盈 → 只从 Bitable 持仓表读，不用任何记忆中的快照
