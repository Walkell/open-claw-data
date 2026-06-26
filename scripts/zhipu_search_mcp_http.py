#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["fastmcp>=2.0"]
# ///
"""Streamable-HTTP MCP server wrapping Zhipu AI Web Search API."""

import json
import os
import uuid
import urllib.request
import urllib.error

from fastmcp import FastMCP

SECRETS_PATH = os.path.expanduser("~/.openclaw/credentials/zhipu-search-secrets.json")
with open(SECRETS_PATH) as f:
    API_KEY = json.load(f)["zhipu-search"]["apiKey"]

API_URL = "https://open.bigmodel.cn/api/paas/v4/web_search"

mcp = FastMCP("zhipu-search")


@mcp.tool()
def zhipu_web_search(
    query: str,
    engine: str = "search_pro",
    count: int = 10,
    recency: str = "noLimit",
    content_size: str = "medium",
    domain_filter: str | None = None,
) -> str:
    """Search the web using Zhipu AI's Web Search API.

    Args:
        query: Search query (max 70 chars recommended).
        engine: search_std | search_pro | search_pro_sogou | search_pro_quark.
        count: 1-50, default 10.
        recency: oneDay | oneWeek | oneMonth | oneYear | noLimit.
        content_size: medium (summary) | high (full context).
        domain_filter: Whitelist domain (e.g. 'www.example.com').
    """
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

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        return f"Zhipu API error: HTTP {e.code}\n{body}"
    except Exception as e:
        return f"Zhipu search error: {e}"

    search_results = result.get("search_result", [])
    lines = [
        "# Zhipu Web Search Results",
        f"Query: {query}",
        f"Engine: {engine} | Count: {len(search_results)} | Recency: {recency}",
        "",
    ]
    for i, item in enumerate(search_results, 1):
        lines.append(f"## {i}. {item.get('title', 'No title')}")
        media = item.get("media", "")
        pub_date = item.get("publish_date", "")
        if media or pub_date:
            lines.append(f"Source: {media} | Published: {pub_date}")
        lines.append(f"URL: {item.get('link', '')}")
        lines.append(item.get("content", ""))
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8082, path="/mcp")
