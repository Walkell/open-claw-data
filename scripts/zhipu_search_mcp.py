#!/usr/bin/env python3
"""
MCP stdio server wrapping Zhipu AI Web Search API.
Reads API key from ~/.openclaw/credentials/zhipu-search-secrets.json
No keys in code, config, or logs.
"""

import json
import os
import sys
import uuid

# Read key from secrets file
SECRETS_PATH = os.path.expanduser("~/.openclaw/credentials/zhipu-search-secrets.json")
try:
    with open(SECRETS_PATH) as f:
        secrets = json.load(f)
    API_KEY = secrets.get("zhipu-search", {}).get("apiKey", "")
except Exception:
    API_KEY = ""

API_URL = "https://open.bigmodel.cn/api/paas/v4/web_search"

# ── MCP stdio protocol ──────────────────────────────────────────────

def send(msg):
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()

def log(msg):
    sys.stderr.write(str(msg) + "\n")
    sys.stderr.flush()

def handle_request(req):
    method = req.get("method", "")
    req_id = req.get("id", 1)

    if method == "tools/list":
        send({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [{
                    "name": "zhipu_web_search",
                    "description": "Search the web using Zhipu AI's Web Search API. Returns titles, URLs, snippets, and content from search results. Supports intent detection, time filtering, and domain whitelisting.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (max 70 characters recommended)"
                            },
                            "engine": {
                                "type": "string",
                                "enum": ["search_std", "search_pro", "search_pro_sogou", "search_pro_quark"],
                                "description": "Search engine. search_std=basic, search_pro=advanced, search_pro_sogou=Sogou, search_pro_quark=Quark",
                                "default": "search_pro"
                            },
                            "count": {
                                "type": "integer",
                                "description": "Number of results (1-50, default 10)",
                                "minimum": 1,
                                "maximum": 50,
                                "default": 10
                            },
                            "recency": {
                                "type": "string",
                                "enum": ["oneDay", "oneWeek", "oneMonth", "oneYear", "noLimit"],
                                "description": "Time filter for results",
                                "default": "noLimit"
                            },
                            "content_size": {
                                "type": "string",
                                "enum": ["medium", "high"],
                                "description": "content detail level: medium=summary, high=full context",
                                "default": "medium"
                            },
                            "domain_filter": {
                                "type": "string",
                                "description": "Whitelist domain filter (e.g. 'www.example.com')"
                            }
                        },
                        "required": ["query"]
                    }
                }]
            }
        })

    elif method == "tools/call":
        params = req.get("params", {})
        args = params.get("arguments", {})
        query = args.get("query", "")
        engine = args.get("engine", "search_pro")
        count = args.get("count", 10)
        recency = args.get("recency", "noLimit")
        content_size = args.get("content_size", "medium")
        domain_filter = args.get("domain_filter") or None

        if not API_KEY:
            send({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": "Error: API key not configured. Set in ~/.openclaw/credentials/zhipu-search-secrets.json"}],
                    "isError": True
                }
            })
            return

        payload = {
            "search_query": query[:70],
            "search_engine": engine,
            "search_intent": True,
            "count": min(max(count, 1), 50),
            "search_recency_filter": recency,
            "content_size": content_size,
            "request_id": str(uuid.uuid4()),
        }
        if domain_filter:
            payload["search_domain_filter"] = domain_filter

        try:
            import urllib.request
            import urllib.error

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                API_URL,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {API_KEY}",
                },
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())

            # Format results as readable text
            lines = []
            search_results = result.get("search_result", [])
            lines.append(f"# Zhipu Web Search Results")
            lines.append(f"Query: {query}")
            lines.append(f"Engine: {engine} | Count: {len(search_results)} | Recency: {recency}")
            lines.append("")

            for i, item in enumerate(search_results, 1):
                title = item.get("title", "No title")
                content = item.get("content", "")
                link = item.get("link", "")
                media = item.get("media", "")
                pub_date = item.get("publish_date", "")
                lines.append(f"## {i}. {title}")
                if media:
                    lines.append(f"Source: {media} | Published: {pub_date}")
                lines.append(f"URL: {link}")
                lines.append(f"{content}")
                lines.append("")

            send({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": "\n".join(lines)}]
                }
            })

        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            send({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": f"Zhipu API error: HTTP {e.code}\n{body}"}],
                    "isError": True
                }
            })

        except Exception as e:
            send({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": f"Zhipu search error: {str(e)}"}],
                    "isError": True
                }
            })

    else:
        send({
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        })

def main():
    send({
        "jsonrpc": "2.0",
        "id": None,
        "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "zhipu-search", "version": "1.0.0"},
            "capabilities": {"tools": {}}
        }
    })
    for line in sys.stdin:
        try:
            req = json.loads(line)
            handle_request(req)
        except json.JSONDecodeError:
            continue
        except Exception as e:
            log(f"Error: {e}")

if __name__ == "__main__":
    main()
