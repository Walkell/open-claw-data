#!/bin/bash
# 智谱 Web Search API 调用脚本
# 从 credentials 文件安全读取 API Key，走 https://open.bigmodel.cn/api/paas/v4/tools

set -euo pipefail

CRED_FILE="$HOME/.openclaw/credentials/zhipu-search-secrets.json"

# 读取 API Key
API_KEY=$(python3 -c "
import json,sys
with open('$CRED_FILE') as f:
    d = json.load(f)
print(d['zhipu-search']['apiKey'])
")

# 默认参数
ENGINE="${ZHIPU_SEARCH_ENGINE:-search_pro}"
QUERY="${1:?用法: $0 <搜索词> [count] [引擎] [recency] [domain]}"
COUNT="${2:-10}"
ENGINE="${3:-$ENGINE}"
RECENCY="${4:-noLimit}"
DOMAIN="${5:-}"

# 构建请求体
BODY=$(python3 -c "
import json, sys
query = '''$QUERY'''
body = {
    'search_engine': '$ENGINE',
    'search_query': query,
    'count': $COUNT,
    'search_recency_filter': '$RECENCY',
    'content_size': 'medium'
}
if '$DOMAIN':
    body['search_domain_filter'] = '$DOMAIN'
print(json.dumps(body))
")

# 调用 API
RESP=$(curl -s --max-time 30 \
    -X POST "https://open.bigmodel.cn/api/paas/v4/web_search" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "$BODY")

# 输出结构化结果
python3 -c "
import json, sys
try:
    data = json.loads('''$RESP''')
except:
    print('{}')
    sys.exit(1)

results = data.get('search_result', [])
output = {
    'query': data.get('search_intent', [{}])[0].get('query', '$QUERY'),
    'total': len(results),
    'engine': '$ENGINE',
    'results': []
}
for r in results:
    output['results'].append({
        'title': r.get('title', ''),
        'url': r.get('link', ''),
        'summary': r.get('content', ''),
        'source': r.get('media', ''),
        'date': r.get('publish_date', ''),
        'ref': r.get('refer', '')
    })

print(json.dumps(output, ensure_ascii=False, indent=2))
"
