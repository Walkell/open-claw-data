---
name: custom-ic-synthesise
description: |
  CIO 专用：接收 Butler 汇总好的委员报告，运用 §7 公式，出投资决议。
  当 CIO 收到 cycle_id 并被要求综合时调用此 SKILL。
  不做任何编排、不 spawn 委员——编排是 Butler 的工作。
---

# custom-ic-synthesise · CIO 综合决议

> **你的输入**：Butler 已收集好的委员输出文件。  
> **你的工作**：读文件 → §7 公式 → 输出四部分裁决 → 推飞书。  
> **不属于你的工作**：spawn 委员、sessions_yield 等待子 Agent。

---

## 第一步：读取委员输出文件

```
~/.openclaw/shared/cycles/{cycle_id}/research_output.json
~/.openclaw/shared/cycles/{cycle_id}/industry_output.json   （四委员 / 三委员，否则默认5）
~/.openclaw/shared/cycles/{cycle_id}/news_output.json        （四委员，否则默认0）
~/.openclaw/shared/cycles/{cycle_id}/risk_output.json
```

同时读取 `~/.openclaw/shared/cycles/{cycle_id}/context.json` 确认 principal 和 flow_type。

---

## 第二步：§7 公式计算（必须逐步展开）

```
research_composite = 0.30×fundamental + 0.25×financials + 0.25×valuation + 0.20×technical
industry_composite = 0.50×macro_score + 0.50×industry_score   （文件缺失时默认 5）
news_modifier      = sentiment × (event_impact / 10)           （文件缺失时默认 0）

baseline_score = 0.55×research_composite + 0.30×industry_composite + 0.15×(5 + news_modifier×5)
```

| baseline_score | 基线动作 |
|---|---|
| ≥ 7.0 | 支持建仓 / 加仓（仍需 Risk NOC）|
| 4.0 ~ 7.0 | 持有观察 |
| < 4.0 | 建议减仓 / 止损 |

**VETO 阻断**：risk_score ≥ 7 → 禁止建仓/加仓；≥ 9 → 硬否决，不可 override。

---

## 第三步：输出四部分裁决（IC 最终交付物）

**缺任意一部分 = 未完成，不得进入推送步骤。**

**① 委员评分汇总表**

| 委员 | 评分 | 核心判断 |
|------|------|---------|
| Research | tech:X / fund:X / val:X / fin:X | ... |
| Industry | macro:X / industry:X | ... |
| News | sentiment:X / impact:X | ... |
| Risk | X.X / NOC 或 VETO | ... |

未参与委员标注"未参与（默认5/0）"。

**② §7 公式展开**
```
research_composite = [计算过程] = X.XX
industry_composite = [计算过程] = X.XX
news_modifier      = [计算过程] = X.XX
baseline_score     = 0.55×X + 0.30×X + 0.15×X = X.XX
```

**③ CIO 裁决表**

| 项目 | 内容 |
|------|------|
| baseline | X.XX → 持有观察 / 支持加仓 / 建议减仓 |
| Risk | NOC / VETO |
| 结论 | ... |
| 触发条件 | ...（如有）|
| 止损 | ... |
| 失效条件 | ...（如有）|

**④ 核心逻辑**（2-4句）

---

## 第四步：推送飞书 + 写库

1. 从 context.json 确认 principal，读对应配置档获取推送渠道（TOWNEY_CONFIG.md / KLAIRE_CONFIG.md 的「输出通道」字段），将四部分裁决推送飞书
2. 执行 `custom-ic-write` SKILL（传入 cycle_id + 决议单，含 flow_type + report_summary）

✅ 检查点：输出 `CIO 综合完成，cycle_id={cycle_id}，已推飞书，写库完成`
