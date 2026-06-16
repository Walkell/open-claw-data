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

### Investment Committee (IC) v5.5

**Butler** is the primary agent — first receiver of all **user** requests. **Corona** is the first receiver of all **cron-triggered** tasks (IC orchestration and intraday monitoring), running in persistent per-principal sessions and bridging back to Butler via a status file (`shared/corona-status/{principal}.json`). **CIO** runs only in isolated sessions spawned by Butler or Corona for IC synthesis.

### Agents (defined in `agents/`)

| Agent | Role | Authority |
|-------|------|-----------|
| Butler | Personal assistant — routes all user requests, IC orchestration, Feishu full-domain, market queries | No investment judgment |
| Corona | Cron entry point — IC orchestration + intraday monitoring dispatch, persistent per-principal sessions, pushes results to Feishu directly | No investment judgment |
| CIO | IC synthesis engine — isolated only, §7 formula, issues final recommendations | Sole decision authority |
| Research | Tech/fundamentals/valuation/earnings scoring | Analysis only |
| Industry | Macro + sector analysis | Analysis only |
| News | Event extraction + sentiment + confidence | Analysis only, **never outputs BUY/SELL/HOLD** |
| Risk | Composite risk score (0-10) | **VETO power at ≥7** |
| Monitor | Intraday price monitoring + Bitable writes | Data only |

Sub-agents run in `sessionTarget: "isolated"`. **IC flow must never skip sub-agents** — any decision requires the full committee, enforced by Butler. IC writes go through `custom-ic-write` SKILL (six-gate validation inline).

### Multi-Principal (Tenant Isolation — Highest Priority)

Two principals share the agent infrastructure but have **strictly isolated data domains**:

| Principal | Bitable | Delivery |
|-----------|---------|----------|
| towney | Towney-投资管理 | DM Towney |
| klaire | Klaire-投资管理 | Group chat (see CONFIG_KLAIRE.md) |

**Cross-principal data access = incident.** Every cycle must confirm principal, every sub-agent dispatch injects `principal` + `ledger_ref`. Cycle IDs carry principal prefix: `towney-20260608-1430-688008`.

### Decision Flow

```
Cron-triggered IC → Corona (persistent per-principal session):
  generate cycle_id → write context.json → spawn committees per flow_type
  → yield → spawn isolated CIO (custom-ic-synthesise)
  → §7 formula → push Feishu directly → custom-ic-write SKILL → write Bitable
  → checkpoint status file at each stage

Cron-triggered intraday monitoring → Corona:
  spawn isolated Monitor → yield → read output → push Feishu directly

User message → Butler confirms principal →
  Simple query / Feishu ops / market data → Butler handles directly
  Task-progress query (cron-triggered work) → Butler reads Corona's status file
  Investment decision → Butler writes ic_request.json → IC orchestration
    Butler (custom-ic-orchestrate): committees → isolated CIO (custom-ic-synthesise)
    → §7 formula → push Feishu → custom-ic-write SKILL → write Bitable
```

### Key Workspace Files

| File | Purpose |
|------|---------|
| `workspace-cio/SOUL.md` | Agent personality + IC core rules |
| `workspace-cio/AGENTS.md` | Session protocol, memory system, full IC architecture |
| `workspace-cio/TOOLS.md` | Market data sources, Bitable call protocol, position system rules |
| `workspace-cio/MEMORY.md` | Curated long-term memory (mistakes logged, lessons learned) |
| `workspace-cio/CONFIG_TOWNEY.md` | towney principal config (tables, thresholds, cron schedule) |
| `workspace-cio/CONFIG_KLAIRE.md` | klaire principal config |
| `workspace-*/` | Sub-agent workspaces (each has SOUL/AGENTS/TOOLS/USER/HEARTBEAT/IDENTITY) |

**Before editing `workspace-cio/CONFIG_SAMPLE.md` or any `CONFIG_{PRINCIPAL_ID}.md`:** read `extensions/openclaw-lark/skills/custom-config-maintain/SKILL.md` first — it has the sync checklist for keeping the template and real per-principal files structurally aligned. Skipping this caused repeated template/real-file drift in past sessions.

### Data Sources

- **A-share / HK stocks:** akshare (primary), qt.gtimg.cn (fallback)
- **US stocks / global indices:** Yahoo Finance API (primary), web_search (fallback)
- **Bitable (Feishu):** Single source of truth for positions, watchlists, trades. **Token must be dynamically fetched** via `feishu_bitable_app.list()` every time — never cached or hardcoded. On `permission_denied`, retry the original tool call directly (up to 2x) — auto-auth renews the token in the background; never call any `feishu_oauth`-named tool manually.

### Position System

Each holding has its **own independent full-position line**. Position % is relative to that stock's full-position amount, not total assets.

### Cron Jobs

Defined in `cron/jobs.json`. Cover pre-market briefings, intraday monitoring (every 10-15 min during trading), EOD reviews, weekly/monthly reviews. Each principal has its own set of crons. All cron jobs (IC and monitoring alike) use `sessionTarget: "main"`, routed through Corona's persistent per-principal session (`agentId: "corona"`, `payload.kind: "systemEvent"`); only the sub-agents Corona/Butler spawn from there run `sessionTarget: "isolated"`.

### Extensions

`extensions/openclaw-lark/` — Feishu (Lark) integration plugin providing IM, Bitable, Calendar, and document skills. Bundled with its own `node_modules` (excluded from git via `**/node_modules/`).

## Critical Rules

1. **Bitable = single source of truth.** No static snapshots in any file. Every analysis/report must pull live data from Bitable first.
2. **Tenant isolation.** Never mix towney and klaire data. Violating this is an incident, not a quality issue.
3. **Sub-agent output is internal.** Raw JSON envelopes from Research/Industry/News/Risk are never delivered to users — CIO synthesizes into human-readable conclusions.
4. **Cost values require user confirmation** before writing to Bitable.
5. **No trade execution.** CIO and all sub-agents only issue recommendations. Position status (持有/已卖出/已移除) is only updated by Butler after the user explicitly confirms execution. `custom-ic-write` SKILL writes trade records tagged "建议/待执行" — never as executed.
