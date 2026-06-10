# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

OpenClaw investment committee agent configuration. This directory (`~/.openclaw`) IS the runtime state — it is both the git repo and the live agent home. There is no separate build/deploy step.

**Remote:** `git@github.com:Walkell/open-claw-data.git`

## Git Management

Uses a **whitelist `.gitignore`** — `*` ignores everything, specific paths are un-ignored with `!` prefixes. Force-exclude patterns at the bottom override earlier allows.

Key exclusions: `credentials/`, `secrets/`, `identity/`, `**/node_modules/`, `agents/*/sessions/`, `workspace*/.openclaw/`, `*.sqlite-shm`, `*.sqlite-wal`.

**Before committing `openclaw.json`:** Replace plaintext `apiKey` values with `${ENV_VAR}` references.

## Architecture

### Investment Committee (IC) v3.1

The main agent has **dual personality**:
- **Table Desk** (daily operations): Bitable reads/writes, market data pulls, trade logging — no decision authority
- **CIO** (chief investment officer): Convenes investment committee for any buy/sell decision — sole authority to issue recommendations

### Sub-Agents (defined in `agents/`)

| Agent | Role | Authority |
|-------|------|-----------|
| Research | Tech/fundamentals/valuation/earnings scoring | Analysis only |
| Industry | Macro + sector analysis | Analysis only |
| News | Event extraction + sentiment + confidence | Analysis only, **never outputs BUY/SELL/HOLD** |
| Risk | Composite risk score (0-10) | **VETO power at ≥7** |
| Monitor | Intraday price monitoring + Bitable writes | Data only |

Sub-agents run in `sessionTarget: "isolated"`. CIO **must never skip sub-agents** — any decision judgment requires the full IC flow.

### Multi-Principal (Tenant Isolation — Highest Priority)

Two principals share the agent infrastructure but have **strictly isolated data domains**:

| Principal | Bitable | Delivery |
|-----------|---------|----------|
| towney | `towney` (OcmCb7TQYaHqnvsjBjAc0GRdnTb) | DM Towney |
| klaire | Klaire-投资管理 (J5zobSJFwaW4JjsEzLhcTNKTnBc) | Group chat oc_c19042fb899cda7eeca1bbbd7d981d1a |

**Cross-principal data access = incident.** Every cycle must confirm principal, every sub-agent dispatch injects `principal` + `ledger_ref`. Cycle IDs carry principal prefix: `towney-20260608-1430-688008`.

### Decision Flow

```
User instruction → CIO confirms principal →
  Simple query (quotes/table read) → Table Desk handles directly
  Investment decision → CIO convenes IC:
    Research + Industry + News + Risk (or subset per scenario rules)
    → Gate check (principal consistency, risk veto)
    → CIO synthesizes → final recommendation
    → Table Desk writes to principal's Bitable
```

### Key Workspace Files

| File | Purpose |
|------|---------|
| `workspace/SOUL.md` | Agent personality + IC core rules |
| `workspace/AGENTS.md` | Session protocol, memory system, full IC architecture |
| `workspace/TOOLS.md` | Market data sources, Bitable call protocol, position system rules |
| `workspace/MEMORY.md` | Curated long-term memory (mistakes logged, lessons learned) |
| `workspace/TOWNEY_CONFIG.md` | towney principal config (tables, thresholds, cron schedule) |
| `workspace/KLAIRE_CONFIG.md` | klaire principal config |
| `workspace-*/` | Sub-agent workspaces (each has SOUL/AGENTS/TOOLS/USER/HEARTBEAT/IDENTITY) |

### Data Sources

- **A-share / HK stocks:** akshare (primary), qt.gtimg.cn (fallback)
- **US stocks / global indices:** Yahoo Finance API (primary), web_search (fallback)
- **Bitable (Feishu):** Single source of truth for positions, watchlists, trades. **Token must be dynamically fetched** via `feishu_bitable_app.list()` every time — never cached or hardcoded. On `permission_denied`, auto-retry via `feishu_oauth` renewal.

### Position System

Each holding has its **own independent full-position line**. Position % is relative to that stock's full-position amount, not total assets. Never cross-compare positions between stocks, never calculate "total position", never reference dollar amounts.

### Cron Jobs

Defined in `cron/jobs.json`. Cover pre-market briefings, intraday monitoring (every 10-15 min during trading), EOD reviews, weekly/monthly reviews. Each principal has its own set of crons. Investment committee crons use `sessionTarget: "isolated"`.

### Extensions

`extensions/openclaw-lark/` — Feishu (Lark) integration plugin providing IM, Bitable, Calendar, and document skills. Bundled with its own `node_modules` (excluded from git via `**/node_modules/`).

## Critical Rules

1. **Bitable = single source of truth.** No static snapshots in any file. Every analysis/report must pull live data from Bitable first.
2. **Tenant isolation.** Never mix towney and klaire data. Violating this is an incident, not a quality issue.
3. **Sub-agent output is internal.** Raw JSON envelopes from Research/Industry/News/Risk are never delivered to users — CIO synthesizes into human-readable conclusions.
4. **Cost values require user confirmation** before writing to Bitable.
5. **No amount references.** User has never disclosed total capital. Use only position % relative to each stock's own full-position line.
