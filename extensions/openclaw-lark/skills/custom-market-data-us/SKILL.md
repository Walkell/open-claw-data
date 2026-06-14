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

行情数据只能来自以下独立 API 数据源。

---

## 数据源池（按优先级排序）

| 优先级 | 来源 | 服务器 | 调用方式 | 稳定性 |
|--------|------|--------|---------|--------|
| 源1 | Yahoo Finance | 美国 | Python HTTP | ⭐⭐⭐⭐⭐ |
| 源2 | Stooq | 欧洲（波兰） | Python HTTP CSV | ⭐⭐⭐⭐（偶尔 404） |
| 源3 | akshare 美股（MCP） | 东方财富 | MCP 工具 | ⭐⭐⭐⭐ |
| 源4 | 新浪财经美股 | 国内 | Python HTTP | ⭐⭐⭐（偶尔 403） |

> ⚠️ Yahoo Finance query1 和 query2 是**同一服务的不同 CDN**，不是独立数据源。不得将两者视为两个独立源。

---

## 查询流程

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

---

### 第二步：处理源调用结果

**情况A：两源均成功** → 先验证日期（见下），再进入第三步

**情况B：某源失败（超时/错误/HTTP错误）** → 按优先级尝试备源补位：
1. 先尝试**源3（akshare 美股，MCP）**
2. 若源3也失败，再尝试**源4（新浪财经美股）**

目标：凑齐两个可用且日期正确的源再做比对。

**备源调用方法：**

**源3 — akshare 美股（MCP）：**
```
akshare__stock_us_spot_em()  # 返回全量美股快照
# 或 akshare__get_realtime_data(source=eastmoney_us, symbols=[...])
# 字段：名称、最新价、涨跌幅、日期
```

**源4 — 新浪财经美股：**
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

---

### 第三步：验证数据日期（价格比对之前必做）

**在比较价格之前，先验证每个源的数据日期。**

- 美股交易日：周一至周五（美国联邦假日除外）
- 盘前简报（北京时间 8:30）获取的是**上一个完整交易日的收盘数据**
- 推算最近美股交易日：当前北京时间 → 换算为 ET → 往前找最近的周一~周五

```
若某源的 date < 最近美股交易日 → ❌ 该源数据陈旧，直接丢弃，不参与比对
若两源 date 不同 → 以较新日期为参考，丢弃旧日期的那源，尝试用备源替补
```

---

### 第四步：价格比对与裁决

```
差异率 = |价格A - 价格B| / max(价格A, 价格B)
```

- **差异率 ≤ 0.5%，且日期均为最近交易日** → ✅ 双源验证，输出结果，结束
- **差异率 > 0.5%** → 引入第三个可用源进行裁决

**裁决逻辑：**
三源中找到差异率 ≤ 0.5% 的两个（且日期均为最近交易日）→ 以均值为准，标注 `⚠️ 三源裁决，{源N} 为异常值（{价格}）`
三源均不一致 → 报告三源价格供参考，请用户核实，继续执行不依赖该数据的分析

---

### 第五步：降级处理（凑不到两个可用源时）

4 个源都尝试过，仍然只有 1 个可用：

```
⚠️ 数据质量警告：仅 {源N} 单源可用（其余 3 个数据源均不可用/日期陈旧），数据未经交叉验证。
{名称}（{symbol}）收盘 {price}，涨跌 {change_pct}%  [{日期}]  [⚠️ 单源未验证]
如发现价格异常，请告知 Butler 修正。IC 分析继续。
```

**IC 继续执行。** 不依赖实时价格的子 Agent（Research 基本面、Industry 行业、News 事件）不受影响；Risk 评分时注明数据质量。

全部 4 个源均失败（0 个可用）：

```
❌ 美股行情数据暂时不可用（全部 4 个数据源无响应）
受影响标的：{symbol 列表}
IC 分析继续（基本面/行业/新闻部分不受影响）；技术面/止损判断暂时跳过。
如需价格数据，请直接告知 Butler 当前价格。
```

---

## 常用 Symbol 速查

| 标的 | Yahoo | Stooq | akshare | 新浪 | 说明 |
|------|-------|-------|---------|------|------|
| S&P 500 | ^GSPC | ^spx.us | $spx | gb_$spx | 标普500 |
| 纳斯达克综合 | ^IXIC | ^ndq.us | $compq | gb_$compq | |
| 纳斯达克100 | ^NDX | ^ndx.us | $ndx | — | |
| 费城半导体 | ^SOX | ^sox.us | $sox | — | 费半 |
| VIX | ^VIX | ^vix.us | $vix | gb_$vix | 恐慌指数 |
| 道琼斯 | ^DJI | ^dji.us | $indu | gb_$indu | |
| 个股 | AAPL | aapl.us | AAPL | gb_aapl | 大小写均可 |

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
纳斯达克（^IXIC）   17,234.00  +0.52%  [2026-06-10]  [⚠️ 单源未验证 - 仅 Yahoo 可用，Stooq 404 / akshare 超时 / 新浪 403]
```
