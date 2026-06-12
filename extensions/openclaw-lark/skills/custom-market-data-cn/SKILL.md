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
行情数据只能来自以下三个 API 数据源。

---

## 数据源

| 编号 | 来源 | 调用方式 | 用途 |
|------|------|---------|------|
| 源1 | 东方财富（akshare） | MCP 工具 | 主路径 |
| 源2 | 腾讯 gtimg | Python HTTP | 验证路径 |
| 源3 | 新浪财经 | Python HTTP | 裁决路径（源1/源2 不一致时） |

---

## 标准查询流程

### 第一步：同时调用源1 和 源2

**源1 — akshare（东方财富）：**
```
akshare__get_realtime_data(source=eastmoney_direct, symbols=[...])
```
返回字段：`price`、`change_pct`、`name`

**源2 — 腾讯 gtimg：**
```python
python3 -c "
import urllib.request, datetime
codes = '{逗号分隔的 symbol，格式 sh688120,sz300394,hk09988}'
r = urllib.request.urlopen(f'https://qt.gtimg.cn/q={codes}', timeout=10).read().decode('gbk')
for line in r.strip().split('\n'):
    if '~' not in line: continue
    f = line.split('~')
    print(f[2], f[1], float(f[3]), float(f[32]), float(f[34]))
    # symbol, 名称, 现价, 涨跌额, 涨跌%
"
```

### 第二步：比对两源数据

对每个标的，计算两源现价差异：

```
差异率 = |价格1 - 价格2| / max(价格1, 价格2)
```

- **差异率 ≤ 0.5%** → 双源一致，直接采用，标注 `✅ 双源验证`
- **差异率 > 0.5%** → 进入第三步裁决

### 第三步：裁决（源1/源2 不一致时）

调用源3 — 新浪财经：
```python
python3 -c "
import urllib.request
symbols = '{逗号分隔，格式 sh688120,sz300394,hk_09988}'
url = f'https://hq.sinajs.cn/list={symbols}'
req = urllib.request.Request(url, headers={'Referer': 'https://finance.sina.com.cn'})
r = urllib.request.urlopen(req, timeout=10).read().decode('gbk')
for line in r.strip().split('\n'):
    if ',' not in line: continue
    name_part = line.split('=\"')[0].split('_')[-1]
    fields = line.split('\"')[1].split(',')
    if len(fields) > 3:
        print(name_part, fields[0], float(fields[3]))
        # symbol, 名称, 现价
"
```

**裁决规则：**
- 三个价格中，找到差异率 ≤ 0.5% 的两个 → 以这两个的均值为准，标注 `⚠️ 三源裁决，源N 为异常值（{价格}）`
- 三个价格均不一致（两两差异 > 0.5%）→ 进入第四步

### 第四步：三源均不一致——告警用户

停止自动处理，直接报告：

```
⚠️ 行情数据三源不一致，无法自动确认，请手动核实后提供

标的：{symbol} {name}
源1（东方财富）：{price1}，涨跌 {change_pct1}%
源2（腾讯）：{price2}，涨跌 {change_pct2}%
源3（新浪）：{price3}

请告知正确价格，或稍后重试。
```

**不得用不一致的数据继续后续分析或决策。**

---

## Symbol 格式

| 市场 | 格式 | 示例 |
|------|------|------|
| 上交所 | sh + 6位 | sh688120 |
| 深交所 | sz + 6位 | sz300394 |
| 港股（gtimg） | hk + 5位 | hk09988 |
| 港股（sina） | hk_ + 5位 | hk_09988 |

---

## 输出格式

验证通过后，统一格式输出：
```
{名称}（{symbol}）  {现价}  {涨跌幅}%  [{验证状态}]
```

示例：
```
阿里巴巴（hk09988）  80.35  +1.23%  [✅ 双源验证]
中科飞测（sh688120）  156.20  -0.45%  [⚠️ 三源裁决，源2 为异常值（159.80）]
```
