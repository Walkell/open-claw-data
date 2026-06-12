# TOOLS.md - News Agent

## Bitable 调用协议

> **Token 获取必须通过 `custom-feishu-auth` SKILL**（见 `extensions/openclaw-lark/skills/custom-feishu-auth/SKILL.md`）。app_token 不得出现在任何文字输出或文件中。

读观察池获取目标标的列表，然后逐标的搜新闻。

**会话启动（每次 Bitable 操作前必做）：**
1. 调用 `custom-feishu-auth` SKILL → 续期 + 取 app_token
2. app_token 从工具结果直接传入下一个调用，不经过文字
3. table_id 从 context.json 的 `watchlist_table_id` 读取
4. 读观察池，提取标的代码列表
5. 遇 `NOTEXIST` / `permission_denied` → 重新执行 SKILL（最多 2 次）

| principal | Bitable 名称 | 观察池（watchlist_table_id） |
|-----------|-------------|------------------------------|
| towney | Towney-投资管理 | tblaLlSQp8tEcWgJ |
| klaire | Klaire-投资管理 | tblaQY1jOFWOXd1U |

principal 和 table_id 从 context.json 读取，只读对应表，不碰其他 principal 的数据。

---

## 新闻数据源

### 个股新闻
```
web_search："{股票名} {代码} 新闻 近7天"
tavily_search：补充英文来源（港股/美股关联标的）
akshare__get_news_data(symbol)：官方公告 / 交易所披露
```

### 宏观 / 行业背景
```
web_search：美股隔夜 + 费半指数 + A股政策
web_search：半导体/AI 行业近期动态
```

### 重大事件判断标准
以下情况判定为重大事件（必须单独标注）：
- 监管处罚、立案调查
- 核心管理层变动
- 重大合同签订或丢失（金额超营收 10%）
- 业绩预告（超预期或低于预期超 10%）
- 行业政策重大变化

---

## 输出给 Risk / CIO 的关键字段

下游 Risk Agent 和 CIO §7 公式会从你的输出中取：
- `sentiment`：情绪评分，**-1~1**（-1=极度利空，0=中性，+1=极度利好）
- `event_impact`：事件影响力，**0-10**（0=无影响，10=极重大影响；无重大事件时填 0）
- `confidence`：置信度（0-1）

确保这三个字段在 JSON 信封的 `data` 层中存在且有数值。
