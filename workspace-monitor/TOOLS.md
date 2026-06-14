# TOOLS.md - Monitor Agent

## Bitable 调用协议

> **Token 获取必须通过 `custom-feishu-auth` SKILL**（见 `extensions/openclaw-lark/skills/custom-feishu-auth/SKILL.md`）。app_token 不得出现在任何文字输出或文件中。

**会话启动（每次 Bitable 操作前必做）：**
1. 调用 `custom-feishu-auth` SKILL → 取 user_access_token
2. `feishu_bitable_app.list()` → 找到名称匹配 `bitable_name` 的应用 → 取 app_token（**不得出现在任何文字输出**）
3. `feishu_bitable_app_table.list(app_token)` → 按表名动态获取 table_id（详见 AGENTS.md 第1步）
4. 写监控记录前：`feishu_bitable_app_table_field.list()` 确认字段名 → `batch_create`
5. 遇 `NOTEXIST` / `permission_denied` → 重新执行 SKILL（最多 2 次）

`principal` 从 cron 消息中读取（不由 CIO 注入），只读写对应 principal 的数据，不碰另一方。

> ⚠️ table_id **不得硬编码**。Bitable 表重建后 ID 会变，必须每次通过 `feishu_bitable_app_table.list()` 动态查找表名对应的 ID。

---

## 行情拉取

**必须使用 `custom-market-data-cn` SKILL**（见 `extensions/openclaw-lark/skills/custom-market-data-cn/SKILL.md`）。该 SKILL 处理双源验证（akshare + gtimg）+ 三源裁决，Monitor 直接用 SKILL 输出的 `price` / `change_pct` / `量比` 字段写入监控记录，不自行维护原始 API 调用逻辑。

⚠️ **涨跌幅铁律**：写入监控记录时只用 SKILL 输出的 `change_pct` 字段。Bitable 里任何价格字段都是上次 Monitor 写入的历史快照，禁止用于任何计算。

港股（hk09988 等）行情为港币，推送时注明。

---

## 交易时段判断

```python
python3 -c "
import datetime
t = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
h, m = t.hour, t.minute
am = (h == 9 and m >= 25) or (h == 10) or (h == 11 and m <= 35)
pm = (h == 13) or (h == 14) or (h == 15 and m <= 5)
print('TRADING' if (am or pm) else 'NOTRADE')
"
```

非交易时段直接 `NO_REPLY`，不拉行情不写表。

---

## 预警推送

Monitor **不主动调用任何 feishu message 工具**。预警内容通过 cron job 的 `delivery` 字段自动推送——Monitor 只需输出文本，OpenClaw 框架负责发送到对应渠道。

推送目标已在 cron/jobs.json 各 Monitor job 的 `delivery.to` 中配置：
- towney：DM Towney
- klaire：群聊（Klaire+投委会+Towney）

非预警时输出 `NO_REPLY`，delivery 不推送，静默结束。
