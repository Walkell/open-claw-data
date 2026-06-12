---
name: custom-market-data-us
description: |
  美股 + 全球指数（S&P500、纳斯达克、费城半导体、VIX 等）的实时/收盘行情查询，强制多源独立验证。
  任何涉及美股价格、指数涨跌的查询必须使用此 Skill。包含数据日期验证，防止历史数据混入。
  不允许用 web_search / tavily_search 获取行情价格数据。
---

# 美股 + 全球指数行情查询（多源独立验证）

## ⚠️ 行情数据红线

**web_search / tavily_search 严禁用于获取任何行情价格数据。**

根本原因：搜索引擎返回的是新闻标题、历史摘要、缓存页面，日期无法保证是最近交易日。2026-06-11 盘前曾因 Yahoo API 失败后用 web_search 兜底，拉到了历史数据并错误地用于决策——这是不可接受的。

行情数据只能来自以下三个真正独立的 API 数据源。

---

## 数据源（三个相互独立的服务）

| 编号 | 来源 | 服务器位置 | 调用方式 | 用途 |
|------|------|-----------|---------|------|
| 源1 | Yahoo Finance | 美国 | Python HTTP | 主路径 |
| 源2 | Stooq | 欧洲（波兰） | Python HTTP CSV | 验证路径，完全独立于 Yahoo |
| 源3 | 新浪财经美股 | 国内 | Python HTTP | 裁决路径，独立于前两源 |

> ⚠️ Yahoo Finance query1 和 query2 是**同一服务的不同 CDN**，不是独立数据源。源2 使用 Stooq（独立第三方），确保真正的交叉验证。

---

## 标准查询流程

### 第一步：同时调用源1 和 源2

**源1 — Yahoo Finance：**
```python
python3 -c "
import urllib.request, json, datetime

symbols = ['^GSPC', '^IXIC', '^SOX', '^VIX']  # 按需替换
results = {}
for sym in symbols:
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=5d&interval=1d'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        meta = data['chart']['result'][0]['meta']
        price = meta.get('regularMarketPrice') or meta.get('previousClose')
        prev = meta.get('previousClose', 0)
        results[sym] = {
            'price': price,
            'change_pct': round((price / prev - 1) * 100, 2) if prev else None,
            'date': datetime.datetime.fromtimestamp(meta.get('regularMarketTime', 0)).strftime('%Y-%m-%d'),
            'market_state': meta.get('marketState'),
        }
    except Exception as e:
        results[sym] = {'error': str(e)}
for k, v in results.items():
    print(k, v)
"
```

**源2 — Stooq（欧洲独立数据源）：**
```python
python3 -c "
import urllib.request, datetime

# Stooq symbol 映射（指数需加前缀）
stooq_map = {
    '^GSPC': '^spx.us',
    '^IXIC': '^ndq.us',
    '^NDX':  '^ndx.us',
    '^SOX':  '^sox.us',
    '^VIX':  '^vix.us',
    '^DJI':  '^dji.us',
}
# 个股直接加 .us，如 AAPL → aapl.us

for orig, stooq_sym in stooq_map.items():
    try:
        url = f'https://stooq.com/q/l/?s={stooq_sym}&f=sd2t2ohlcv&e=csv'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        r = urllib.request.urlopen(req, timeout=10).read().decode()
        lines = r.strip().split('\n')
        if len(lines) > 1:
            f = lines[1].split(',')
            # Name,Date,Time,Open,High,Low,Close,Volume
            close = float(f[6]) if f[6] != 'N/D' else None
            print(orig, f'date={f[1]}', f'close={close}')
    except Exception as e:
        print(orig, 'ERROR', str(e))
"
```

### 第二步：验证数据日期（价格比对之前必做）

**在比较价格之前，先验证每个源的数据日期。**

- 美股交易日：周一至周五（美国联邦假日除外）
- 盘前简报（北京时间 8:30）获取的是**上一个完整交易日的收盘数据**
- 推算最近美股交易日：当前北京时间 → 换算为 ET → 往前找最近的周一~周五

```
若某源的 date < 最近美股交易日 → ❌ 该源数据陈旧，直接丢弃，不参与比对
若两源 date 不同 → 以较新日期为参考，丢弃旧日期的那源
```

日期异常是数据来源可信度的最直接警示。

### 第三步：比对两源价格

```
差异率 = |价格1 - 价格2| / max(价格1, 价格2)
```

- **差异率 ≤ 0.5%，且日期均为最近交易日** → ✅ 双源验证通过
- **差异率 > 0.5%，或任一源失败/日期陈旧** → 进入第四步裁决

### 第四步：裁决——调用源3（新浪财经美股）

新浪财经提供美股实时数据，格式稳定，国内访问快：
```python
python3 -c "
import urllib.request, datetime

# 新浪美股格式：gb_ + 小写 symbol
# 指数：gb_\$indu（道琼斯）, gb_\$compq（纳斯达克）, gb_\$spx（S&P500）
# 个股：gb_aapl, gb_nvda
sina_map = {
    '^GSPC': 'gb_\$spx',
    '^IXIC': 'gb_\$compq',
    '^DJI':  'gb_\$indu',
    '^VIX':  'gb_\$vix',
    'AAPL':  'gb_aapl',
}
symbols_str = ','.join(sina_map.values())
url = f'https://hq.sinajs.cn/list={symbols_str}'
req = urllib.request.Request(url, headers={
    'Referer': 'https://finance.sina.com.cn',
    'User-Agent': 'Mozilla/5.0'
})
r = urllib.request.urlopen(req, timeout=10).read().decode('gbk', errors='ignore')
for orig, sina_sym in sina_map.items():
    for line in r.strip().split('\n'):
        if sina_sym.replace('gb_', '') in line or sina_sym in line:
            try:
                fields = line.split('\"')[1].split(',')
                # 新浪美股字段：名称,价格,涨跌,涨跌%,开,高,低,...,日期
                print(orig, f'price={fields[1]}', f'date={fields[-3] if len(fields) > 3 else \"?\"}')
            except Exception:
                pass
"
```

**裁决规则：**
- 三源中找到差异率 ≤ 0.5% 的两个，且日期均为最近交易日 → 以均值为准，标注 `⚠️ 三源裁决，源N 为异常值（{价格}）`
- 三源均不一致，或超过一源日期陈旧 → 进入第五步

### 第五步：三源均不一致——必须告警，停止决策

```
⚠️ 美股行情多源数据不一致，无法自动确认，等待人工输入

标的    ：{symbol}
源1 Yahoo  ：{price1}  日期：{date1}  {状态}
源2 Stooq  ：{price2}  日期：{date2}  {状态}
源3 新浪   ：{price3}  日期：{date3}  {状态}

如某源日期明显偏旧，该源可能存在缓存问题。
请告知正确价格和日期，或等待数据源恢复后重试。
```

**此状态下不得继续任何需要该数据的分析或决策。**

---

## 常用 Symbol 速查

| 标的 | Yahoo | Stooq | 新浪 | 说明 |
|------|-------|-------|------|------|
| S&P 500 | ^GSPC | ^spx.us | gb_$spx | 标普500 |
| 纳斯达克综合 | ^IXIC | ^ndq.us | gb_$compq | |
| 纳斯达克100 | ^NDX | ^ndx.us | — | |
| 费城半导体 | ^SOX | ^sox.us | — | 费半 |
| VIX | ^VIX | ^vix.us | gb_$vix | 恐慌指数 |
| 道琼斯 | ^DJI | ^dji.us | gb_$indu | |
| 个股 | AAPL | aapl.us | gb_aapl | 大小写均可 |

---

## 输出格式

验证通过后统一格式：
```
{名称}（{symbol}）  {收盘价}  {涨跌幅}%  [{交易日期}]  [{验证状态}]
```

示例：
```
S&P 500（^GSPC）    5,308.13  +0.87%  [2026-06-10]  [✅ 双源验证 Yahoo+Stooq]
费半（^SOX）        4,521.06  +1.24%  [2026-06-10]  [⚠️ 三源裁决，Stooq 为异常值（4,489.20）]
```
