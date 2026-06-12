---
name: custom-ic-write
description: |
  IC 决策写库专用：六闸门校验 + Bitable 写入。
  由 CIO 在 custom-ic-synthesise 综合完成后调用。
  输入：cycle_id + CIO 决议单。输出：Bitable 写入完成或拒绝原因。
---

# custom-ic-write · IC 写库

> **输入**：cycle_id + CIO 决议单（含委员票据、baseline_score、action、flow_type 等字段）。  
> **工作**：六闸门逐门校验 → 全通过后写 Bitable → 输出结果。  
> **红线**：不做任何投资分析，不修改票据内容，不跨 principal 写入。

---

## 六闸门校验（写库前必须全部通过，按顺序执行）

任一门不通过 → 立即拒绝，输出 `❌ 闸门{N}不通过：{原因}`，不执行写入。

### 闸门 1：Principal 一致性

所有**非 null** 委员票据的 `principal` 字段必须与 context.json 的 `principal` 完全一致。

- 检查：对 votes 中每个非 null 的票据，验证 `vote.principal == cycle_principal`
- 不过：`"principal 不一致，疑似串账，整次决策作废"`

### 闸门 2：法定委员数（Quorum）

读决议单 `flow_type` 字段确认本周期委员要求：

| flow_type | 必须非 null |
|-----------|------------|
| 四委员 | research + industry + news + risk |
| 三委员 | research + industry + risk |
| 精简两委员 | research + risk |

`flow_type` 缺失或非法值 → `"flow_type 字段缺失或非法，无法确认 Quorum"`  
委员不足 → `"委员不足，缺少：{列出 null 委员}"`

### 闸门 3：票据 schema 合法性

每份非 null 票据的字段齐全、值域合法：

- research：fundamental / financials / valuation / technical，各 0-10
- industry：macro_score 0-10，industry_score 0-10
- news：sentiment -1~1，event_impact 0-10，confidence 0-1
- risk：risk_score 0-10，verdict ∈ {NOC, VETO}

不过 → `"票据 schema 不合法：{委员名} {具体错误}"`

### 闸门 4：行情数据新鲜度

CIO 决议单中引用的行情数据时间戳，距写入时刻不超过 **30 分钟**（非交易时段豁免）。

不过 → `"行情数据过期，时间戳：{ts}，超出 30 分钟"`

### 闸门 5：baseline_score 复算

按 §7 公式重新计算 baseline_score，与决议单值对比：

- 偏差 ≤ 0.1：通过
- 偏差 > 0.1 且 ≤ 1.0：通过，但在 `deviation_note` 字段注明
- 偏差 > 1.0：`"baseline_score 严重偏差（差值 X.XX），可能存在数据污染"`

### 闸门 6：否决与 Override 一致性

- risk_score ≥ 9（硬否决）→ 直接拒绝，无论是否有 override_reason
- risk_score 7-8 + verdict=VETO（软否决）→ 检查决议单是否有非空 `override_reason`
  - 有 → 通过（CIO 已行使 override 权）
  - 无 → `"软 VETO 未 override，禁止写入"`

---

## 写入内容（六闸门全通过后执行）

写入当前 principal 的 Bitable：

1. **决策复盘表**：cycle_id、decision_time（毫秒时间戳）、baseline_score、cio_action、risk_verdict、override_reason（如有）、各委员关键分值
2. **交易记录表**（决议含建仓/减仓/止损/清仓指令时）：symbol、action、position_pct、price_ref、operator="CIO"、status="建议/待执行"
   > ⚠️ 交易记录此时记录的是 **CIO 建议**，不代表用户已执行。用户确认执行后由 Butler 将 status 更新为"已执行"，并同步更新持仓表。
3. **报告表**（决议单 `report_summary` 非空时）：content、cycle_id，type 按以下优先级推断：
   - cycle_id 含 `premkt` → `盘前简报`
   - cycle_id 含 `monday` → `周一简报`
   - cycle_id 含 `weekly` → `周度复盘`
   - cycle_id 含 `monthly` → `月度复盘`
   - 含 `eod` 或标的为 `全持仓` → `日终复盘`
   - 均不匹配 → `综合复盘`

---

## Bitable 写入规程

> app_token **不得出现在任何文字输出中**。

1. 执行 `custom-feishu-auth` SKILL 路径二 → 续期 + 取 app_token
2. app_token 从工具结果直接传入下一个调用，不经过文字
3. `feishu_bitable_app_table_field.list()` → 确认字段名
4. `batch_create` / `batch_update`
5. 遇 `NOTEXIST` / `permission_denied` → 重新执行 SKILL（最多 2 次）

---

## 完成输出

```
✅ custom-ic-write 完成
cycle_id：{cycle_id}
写入：决策复盘 ✓ / 交易记录（建议）✓（如有）/ 报告表 ✓（如有）
```

或

```
❌ custom-ic-write 拒绝
闸门{N}：{原因}
```
