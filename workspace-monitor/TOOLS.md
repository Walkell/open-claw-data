# TOOLS.md - Monitor Agent

## Bitable 调用协议

> **Token 获取必须通过 `custom-feishu-auth` SKILL**（见 `extensions/openclaw-lark/skills/custom-feishu-auth/SKILL.md`）。app_token 不得出现在任何文字输出或文件中。

**会话启动（每次 Bitable 操作前必做）：**
1. 调用 `custom-feishu-auth` SKILL → 续期 + 取 app_token
2. app_token 从工具结果直接传入下一个调用，不经过文字
3. 读持仓表，获取持仓列表（代码、止损价、止盈价、仓位、备注）
4. 写监控记录前：`feishu_bitable_app_table_field.list()` 确认字段名 → `batch_create`
5. 遇 `NOTEXIST` / `permission_denied` → 重新执行 SKILL（最多 2 次）

`principal` 由 CIO 注入，只读写对应 principal 的数据，不碰另一方。

| principal | 读持仓 | 写监控记录 |
|-----------|--------|-----------|
| towney | tblUeTGMf0IKJ8Pk | tblFAfrZs4Rz4AOu |
| klaire | tbl9xYrGkBDZlnYm | tblHkc0MfQbe2x37 |

---

## 行情拉取

**必须使用 `custom-market-data-cn` SKILL**（见 `extensions/openclaw-lark/skills/custom-market-data-cn/SKILL.md`）。该 SKILL 处理双源验证（akshare + gtimg）+ 三源裁决，Monitor 直接用 SKILL 输出的 `price` / `change_pct` 字段写入监控记录，不自行维护原始 API 调用逻辑。

⚠️ **涨跌幅铁律**：写入监控记录时只用 SKILL 输出的 `change_pct` 字段。Bitable 里任何价格字段都是上次 Monitor 写入的历史快照，禁止用于任何计算。

港股（hk09988 等）行情为港币，推送时注明。

---

## 交易时段判断

```python
python3 -c "
import datetime
t = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
h, m = t.hour, t.minute
am = (h == 9 and m >= 30) or (h == 10) or (h == 11 and m <= 30)
pm = (h == 13) or (h == 14) or (h == 15 and m == 0)
print('TRADING' if (am or pm) else 'NOTRADE')
"
```

非交易时段直接 `NO_REPLY`，不拉行情不写表。

---

## 预警推送

预警发送至 `feishu_im_user_message`，delivery mode 为 none 时仍可直接调工具发送。

推送地址从当前 principal 的配置档读取（`workspace-cio/TOWNEY_CONFIG.md` / `workspace-cio/KLAIRE_CONFIG.md` 的「输出通道」字段），不得硬编码，不得混发两个 principal 的渠道。

非预警时不发任何消息，保持静默。
