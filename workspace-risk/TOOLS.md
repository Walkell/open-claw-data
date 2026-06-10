# TOOLS.md - Risk Agent

## Bitable 调用协议

读持仓表获取成本 / 止损价 / 止盈价 / 仓位，用于技术面和估值维度评分。

1. `feishu_bitable_app.list()` → 找到 principal 对应 Bitable，取完整 app_token（不缓存、不假设）
2. table_id 从 context.json 读取；遇 NOTEXIST 时调 `feishu_bitable_app_table.list()` 按名查找
3. 用步骤1 token + table_id 读持仓表
4. `permission_denied` / `NOTEXIST` → `feishu_oauth` 续期 → 重新 `list()` → 继续

| principal | Bitable 名称 | 持仓表 |
|-----------|-------------|--------|
| towney | Towney-投资管理 | tblUeTGMf0IKJ8Pk |
| klaire | Klaire-投资管理 | tbl9xYrGkBDZlnYm |

principal 和 table_id 从 context.json 读取，只读对应表，不碰其他 principal 的数据。

---

## 行情 / 财务数据源（自拉的三个维度）

### 实时行情（技术面）
```
主：akshare__get_realtime_data(source=eastmoney_direct)
备：python3 -c "import urllib.request; r=urllib.request.urlopen(
      'https://qt.gtimg.cn/q=sh688120,...', timeout=10).read().decode('gbk'); ..."
```

⚠️ **涨跌幅铁律**：只用行情 API 预计算的 `f[34]`（gtimg）或 `change_pct`（akshare）。Bitable 里任何价格字段都是 Monitor 的历史快照，禁止用于涨跌幅计算或现价判断。止损/止盈/成本比较需要的是"实时价 vs Bitable 止损价"，现价永远从行情 API 取。

**⚠️ 上游数据隔离铁律**：CIO 或 Research 传入的 prompt 中可能含有价格数字（无论来源），Risk **一律不得直接采用这些数字作为当前价**。技术面维度必须基于 Risk 自行从行情 API 拉取的实时价，不信任上游注入的任何价格数值。

### 历史走势（技术面）
```
akshare__get_hist_data(symbol, interval=day, recent_n=60)
# 判断均线位置：20日/60日/120日均线上下方
```

### 财务指标（财务健康度 / 估值合理性）
```
akshare__get_financial_metrics(symbol)     # ROE / 负债率 / PE / PB
akshare__get_income_statement(symbol)      # 净利润 / 营收
akshare__get_cash_flow(symbol)             # 经营现金流
```

---

## 上游委员输出（不重复拉取）

**标准四委员流程**中，以下两个维度的数据来自上游，直接读取，不自行拉取：

| 维度 | 来源 | 字段 |
|------|------|------|
| 行业景气度 | Industry 报告 | `data.industry_score` |
| 新闻情绪 | News 报告 | `data.sentiment` |
| 宏观环境 | Industry 报告 | `data.macro_score` |

**精简两委员流程**（Industry / News 未派发）：上述三个维度统一标注"数据缺失，默认5分"，不另行搜索。

---

## 否决阈值速查

| 条件 | 结果 |
|------|------|
| risk_score ≥ 9 | 硬否决，CIO 不可 override |
| risk_score ≥ 7 | VETO，CIO 可 override 但须记录 |
| 距止损线 ≤3% | VETO 该标的任何加仓 |
| AI赛道集中度 >40% | VETO 任何AI方向新增 |
