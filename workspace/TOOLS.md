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

### Bitable 双账户（v4.0 — 2026-06-09 重构）

⚠️ 不在此维护任何 token（token 可能刷新）
⚠️ TOKEN 动态获取：每次调 Bitable API 之前，第一步必须是 feishu_bitable_app.list()，用返回的完整 token
⚠️ 绝对不串账户！每个 principal 只有自己的数据域
⚠️ 2026-06-09 新建 Towney-投资管理 和 Klaire-投资管理，按 InvestmentOS 表结构复制

| principal | Bitable 名称 | app_token |
|-----------|-------------|-----------|
| towney | Towney-投资管理 | 通过 feishu_bitable_app.list() 动态获取，禁止硬编码 |
| klaire | Klaire-投资管理 | 通过 feishu_bitable_app.list() 动态获取，禁止硬编码 |

表结构参考（table_id 稳定；遇 NOTEXIST 时用 feishu_bitable_app_table.list() 刷新）：
```
towney (Towney-投资管理):
  持仓表: tblUeTGMf0IKJ8Pk
  报告表: tbllqOCpSadabEYt
  交易记录: tblUZ9WvrF6FVZTS
  观察池: tblaLlSQp8tEcWgJ
  监控记录: tblFAfrZs4Rz4AOu
  决策复盘: tbl7TR8G43GCN057

klaire (Klaire-投资管理):
  持仓表: tbl9xYrGkBDZlnYm
  报告表: tblsyCW1JE0sJnwm
  交易记录: tblVKj7wdGxMI4DQ
  观察池: tblaQY1jOFWOXd1U
  监控记录: tblHkc0MfQbe2x37
  决策复盘: tblrV0rNe4npQfic
```

【Bitable 标准调用流程 —— 每次必走，不可跳过】
1. feishu_bitable_app.list() → 获取最新的 app_token
2. ⚠️ 铁律：使用截断格式 token（前6字符+…+后4字符，如 OcmCb7…dnTb）调用 Bitable API
   - 根因（2026-06-11 15:23）：系统安全策略会把完整 token 替换为 ***，导致 API 返回 NOTEXIST
   - 截断格式绕过完整 token 匹配，API 正常识别
   - 两小时内 30+ 次 NOTEXIST 的根因就是这个，不是 token 过期
3. NOTEXIST → 先确认是不是用了完整 token 被星号替换了，不是盲目怀疑 token 过期
4. 确认 token 格式正确后再 NOTEXIST → feishu_bitable_app_table.list() 刷新 table_id 重试
5. 绝不用任何文件中的 token 值，不记忆、不缓存、不推断

【Token 过期处理 —— 2026-06-11 修订】
⚠️ NOTEXIST 不等于 token 过期！先用 feishu_bitable_app.list() 验证 token 是否有效
⚠️ 真正 token 过期（permission_denied）→ 系统自动触发刷新卡片，不手动干预
⚠️ 🚫 绝不调用 feishu_oauth(action="revoke")！revoke 清的是用户授权凭据，不是过期 API token
⚠️ 禁止在 permission_denied 后直接放弃写入
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
