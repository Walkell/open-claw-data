# TOOLS.md - Industry Agent

## 数据来源优先级

### 宏观数据（利率 / PMI / 社融 / 汇率 / VIX）
```
web_search / tavily_search：优先选财联社、Wind、国家统计局等来源
tavily_extract：拉取具体页面原文
```

### 行业景气度（资金流向 / ETF / 板块）
```
web_search："{行业名} ETF 资金流向 近期"
web_search："{行业名} 板块 景气度 2026"
tavily_search：补充英文来源（半导体/AI 等全球化行业）
```

### 实时指数 / 期货

**使用 `custom-market-data-cn` SKILL**（见 `extensions/openclaw-lark/skills/market-data-cn/SKILL.md`）拉取指数实时行情（sh000001、sz399006 等 A股指数代码同样适用）。

---

## Bitable（辅助查持仓行业分布，非必须）

> **Token 获取必须通过 `custom-feishu-auth` SKILL**（见 `extensions/openclaw-lark/skills/custom-feishu-auth/SKILL.md`）。

如需了解当前持仓的行业分布，可读持仓表：

1. 调用 `custom-feishu-auth` SKILL → 续期 + 取 app_token
2. app_token 从工具结果直接传入下一个调用，不经过文字
3. table_id 从 context.json 的 `positions_table_id` 读取
4. 遇 `NOTEXIST` / `permission_denied` → 重新执行 SKILL（最多 2 次）

| principal | Bitable 名称 | 持仓表 |
|-----------|-------------|--------|
| towney | Towney-投资管理 | tblUeTGMf0IKJ8Pk |
| klaire | Klaire-投资管理 | tbl9xYrGkBDZlnYm |

principal 和 table_id 从 context.json 读取，只读对应表。

---

## 输出给 Risk / CIO 的关键字段

下游 Risk Agent 和 CIO §7 公式会从你的输出中取：
- `macro_score`：宏观评分，**0-10**（0=极度收紧/衰退，5=中性，10=极度宽松/景气）
- `industry_score`：行业景气度评分，**0-10**（0=极度萎缩，5=中性，10=极度繁荣）

确保这两个字段在 JSON 信封的 `data` 层中存在且有数值。
