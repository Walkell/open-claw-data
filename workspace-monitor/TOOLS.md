# TOOLS.md - Monitor Agent

## Bitable 调用协议

**每次必走，不可跳过：**
1. `feishu_bitable_app.list()` → 找到 principal 对应 Bitable，取完整 app_token（不缓存、不假设）
2. 用步骤1 token + 下方 table_id 读持仓表，获取当前持仓列表（代码、止损价、止盈价、仓位、备注）
3. `permission_denied` / `NOTEXIST` → `feishu_oauth` 续期 → 重新 `list()` → 继续，不放弃写入

`principal` 由 CIO 注入，只读写对应 principal 的数据，不碰另一方。

| principal | 读持仓 | 写监控记录 |
|-----------|--------|-----------|
| towney | tblUeTGMf0IKJ8Pk | tblFAfrZs4Rz4AOu |
| klaire | tbl9xYrGkBDZlnYm | tblHkc0MfQbe2x37 |

写监控记录前必须先 `feishu_bitable_app_table_field.list()` 确认字段名，再 `batch_create`。

---

## 行情拉取

### 主路径（优先）
```
akshare__get_realtime_data(source=eastmoney_direct)
```

⚠️ **涨跌幅铁律**：写入监控记录时的涨跌幅只用行情 API 返回的预计算字段（`f[34]` 或 `change_pct`）。Bitable 里任何价格字段都是上次 Monitor 写入的历史快照，禁止用于任何计算。

### 备用路径（主路径 502 时）
```python
python3 -c "
import urllib.request
codes = 'sh688120,sh688008,sz300394,sh688041,sh588090,sz159949,sh510500,sh513300,sh513650,sh518880,hk09988'
r = urllib.request.urlopen(f'https://qt.gtimg.cn/q={codes}', timeout=10).read().decode('gbk')
for line in r.strip().split('\n'):
    if '~' not in line: continue
    f = line.split('~')
    print(f[2], f[1], float(f[3]), float(f[32]), float(f[34]), float(f[33]))
    # 代码, 名称, 现价, 涨跌额, 涨跌%, 昨收
"
```

港股（hk09988）行情为港币，推送时注明。

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

预警发送至 `feishu_im_user_message`，delivery mode 为 none 时仍可直接调工具发送：
- towney 私聊：`ou_aa8d3c082f316a8c9e18b9e6e8eeb88b`

非预警时不发任何消息，保持静默。
