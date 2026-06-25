---
name: custom-market-data-cn
description: |
  A股 + 港股的实时行情查询，强制双源验证。任何涉及 A股/港股 价格、涨跌幅的查询必须使用此 Skill。
  不允许用 web_search / tavily_search 获取行情价格数据。
---

# A股 + 港股行情查询（双源验证）

## ⚠️ 行情数据红线

**web_search / tavily_search 严禁用于获取任何行情价格数据。**
搜索引擎结果可能是新闻摘要、历史数据或缓存页面，不是实时价格。

---

## 数据源池（按优先级排序）

| 优先级 | 来源 | 地址 | 稳定性 |
|--------|------|------|--------|
| 源1 | 东方财富 akshare（MCP） | MCP 工具 | ⭐⭐⭐⭐⭐ |
| 源2 | 腾讯 gtimg | qt.gtimg.cn | ⭐⭐⭐⭐⭐ |
| 源3 | 网易财经 | api.money.163.com | ⭐⭐⭐⭐ |
| 源4 | 同花顺 | d.10jqka.com.cn | ⭐⭐⭐⭐ |
| 源5 | 新浪财经 | hq.sinajs.cn | ⭐⭐⭐（偶尔 403） |

---

## 查询流程

### 第一步：同时调用源1 和 源2

**源1 — 东方财富 akshare（MCP）：**
```
akshare__get_realtime_data(source=eastmoney_direct, symbols=[...])
```
返回字段：`price`、`change_pct`、`name`、`volume_ratio`（量比，若接口返回则提取，否则为 N/A）

**源2 — 腾讯 gtimg：**
```python
python3 -c "
import urllib.request
codes = '{逗号分隔，格式 sh688120,sz300394,hk09988}'
r = urllib.request.urlopen(f'https://qt.gtimg.cn/q={codes}', timeout=10).read().decode('gbk')
for line in r.strip().split('\n'):
    if '~' not in line: continue
    f = line.split('~')
    vol_ratio = f[36] if len(f) > 36 and f[36] else 'N/A'
    print(f[2], f[1], float(f[3]), float(f[32]), float(f[34]), vol_ratio)
    # symbol, 名称, 现价, 涨跌额, 涨跌%, 量比
"
```

---

### 第二步：处理源调用结果

**情况A：两源均成功** → 进入第三步（价格比对）

**情况B：某源失败（超时/错误/HTTP错误）** → 按优先级尝试备源补位：
1. 先尝试**源3（网易财经）**
2. 若源3也失败，再尝试**源4（同花顺）**
3. 若源4也失败，再尝试**源5（新浪财经）**

目标：凑齐两个可用源再做比对。凑不到两个，进入单源降级处理。

**备源调用方法：**

**源3 — 网易财经：**
```python
python3 -c "
import urllib.request, json
# A股格式：0+代码（上证）或 1+代码（深证）；港股：hk+代码（如 hk09988）
symbols = '{逗号分隔，如 0600519,1000001}'
url = f'http://api.money.163.com/data/feed/{symbols},money.api'
r = json.loads(urllib.request.urlopen(url, timeout=10).read().decode())
for sym, d in r.items():
    if isinstance(d, dict):
        print(sym, d.get('name'), d.get('price'), d.get('percent'))
        # percent 已是百分比数值，如 1.23
"
```

**源4 — 同花顺：**
```python
python3 -c "
import urllib.request, json
# 代码格式：6位数字，无前缀（如 600519）
symbols = ['{code1}', '{code2}']
for sym in symbols:
    url = f'http://d.10jqka.com.cn/v2/realtime/code/{sym}/index.json'
    req = urllib.request.Request(url, headers={
        'Referer': 'http://m.10jqka.com.cn',
        'User-Agent': 'Mozilla/5.0'
    })
    r = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())
    d = r.get('data', {})
    print(sym, d.get('name'), d.get('price'), d.get('increase_rate'))
    # increase_rate 如 '1.23' 表示 +1.23%
"
```

**源5 — 新浪财经（最后备用）：**
```python
python3 -c "
import urllib.request
symbols = '{逗号分隔，格式 sh688120,sz300394,hk_09988}'
url = f'https://hq.sinajs.cn/list={symbols}'
req = urllib.request.Request(url, headers={'Referer': 'https://finance.sina.com.cn'})
r = urllib.request.urlopen(req, timeout=10).read().decode('gbk')
for line in r.strip().split('\n'):
    if ',' not in line: continue
    sym = line.split('=\"')[0].split('_')[-1]
    fields = line.split('\"')[1].split(',')
    if len(fields) > 3:
        print(sym, fields[0], float(fields[3]))
        # symbol, 名称, 现价
"
```

---

### 第三步：价格比对与裁决

```
差异率 = |价格A - 价格B| / max(价格A, 价格B)
```

- **差异率 ≤ 0.5%** → ✅ 双源验证，输出结果，结束
- **差异率 > 0.5%** → 引入第三个可用备源进行裁决

**裁决逻辑：**
三个价格中，找到差异率 ≤ 0.5% 的两个 → 以均值为准，标注 `⚠️ 三源裁决，{源N} 为异常值（{价格}）`
三源均不一致（两两差异均 > 0.5%）→ 报告三源价格，请用户核实，继续执行不依赖该数据的分析

---

### 第四步：降级处理（凑不到两个可用源时）

所有 5 个源都尝试过，仍然只有 1 个可用：

```
⚠️ 数据质量警告：仅 {源N} 单源可用（其余 4 个数据源均不可用），数据未经交叉验证。
{名称}（{symbol}）现价 {price}，涨跌 {change_pct}%  [⚠️ 单源未验证]
如发现价格异常，请告知 Butler/Dexter 修正。IC 分析继续。
```

**IC 继续执行。** 不依赖实时价格的子 Agent（Research 基本面、Industry 行业、News 事件）不受影响；Risk 评分时注明数据质量。

全部 5 个源均失败（0 个可用）：

```
❌ A股行情数据暂时不可用（全部 5 个数据源无响应）
受影响标的：{symbol 列表}
IC 分析继续（基本面/行业/新闻部分不受影响）；止损线/技术面判断暂时跳过。
如需价格数据，请直接告知 Butler/Dexter 当前价格。
```

---

## Symbol 格式对照

| 市场 | 源1/源2 (akshare/gtimg) | 源3 (网易) | 源4 (同花顺) | 源5 (新浪) |
|------|------------------------|-----------|-------------|-----------|
| 上交所 | sh688120 | 0688120 | 688120 | sh688120 |
| 深交所 | sz300394 | 1300394 | 300394 | sz300394 |
| 港股 | hk09988 | hk09988 | 不支持 | hk_09988 |

---

## 输出格式

```
{名称}（{symbol}）  {现价}  {涨跌幅}%  量比:{X.XX}  [{验证状态}]
```

量比来自主源（东方财富或腾讯），备源（网易/同花顺/新浪）无量比时标 `量比:N/A`。

示例：
```
阿里巴巴（hk09988）  80.35  +1.23%  量比:1.23  [✅ 双源验证 东方财富+腾讯]
中科飞测（sh688120）  156.20  -0.45%  量比:3.51  [⚠️ 三源裁决，腾讯 为异常值（159.80）]
比亚迪（sz002594）   328.50  +0.82%  量比:N/A  [⚠️ 单源未验证 - 仅东方财富可用]
```
