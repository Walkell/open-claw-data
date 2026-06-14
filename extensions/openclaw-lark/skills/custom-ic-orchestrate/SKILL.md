---
name: custom-ic-orchestrate
description: |
  Butler 专用：IC 投委会编排执行流程。Butler 收到 IC 触发后调用此 SKILL。
  负责 spawn 委员、sessions_yield、收集输出、spawn CIO 综合。
  不做投资判断——判断是 CIO 的工作。
---

# custom-ic-orchestrate · Butler IC 编排

> **你的工作**：编排委员 → 收集输出 → 交给 CIO 综合。  
> **不属于你的工作**：分析行情、评估风险、出买卖建议。

参见 `workspace-butler/AGENTS.md` 中的 IC 编排流程（完整协议在那里维护，本 SKILL 是执行入口提示）。

---

## 执行步骤速查

### 第一步：Principal 锁定 + cycle_id + context.json

**cron 触发**：消息直接含 `flow_type` 和 `principal`，直接写 context.json。

**用户触发**（消息只含 cycle_id）：先读 `~/.openclaw/shared/cycles/{cycle_id}/ic_request.json`，从中获取 `flow_type`、`principal`、`symbol`，再写 context.json。

```
cycle_id = {principal}-{YYYYMMDD}-{HHMM}-{场景}
```

写 `~/.openclaw/shared/cycles/{cycle_id}/context.json`（principal / flow_type / table_id）。

输出：`🔔 Butler IC 启动，flow_type={X}，principal={X}，cycle_id={X}`

---

### 第二步：按 flow_type 编排委员

**四委员**
1. 并行 spawn Research + Industry + News（isolated, delivery:none，只注入 cycle_id）
2. **sessions_yield** ← 必须等全部完成
3. ✅ `Research/Industry/News yield 完成`
4. spawn Risk（inline 三份输出，只注入 cycle_id）
5. **sessions_yield**
6. ✅ `Risk yield 完成，risk_score={X}`

**三委员**
1. 并行 spawn Research + Industry
2. **sessions_yield**
3. ✅ 检查点
4. spawn Risk（News 标注"未参与，默认0"）
5. **sessions_yield**
6. ✅ 检查点

**精简两委员**
1. spawn Research
2. **sessions_yield**
3. ✅ 检查点
4. spawn Risk（Industry/News 标注"未参与，默认5/0"）
5. **sessions_yield**
6. ✅ 检查点

子 Agent 失败 → 立即停止，输出 `"{委员名}执行失败，IC 中止"`，通知用户。

---

### 第三步：读取输出文件

```
~/.openclaw/shared/cycles/{cycle_id}/research_output.json
~/.openclaw/shared/cycles/{cycle_id}/industry_output.json
~/.openclaw/shared/cycles/{cycle_id}/news_output.json
~/.openclaw/shared/cycles/{cycle_id}/risk_output.json
```

---

### 第四步：spawn CIO 综合

```
sessions_spawn agentId=cio（isolated, delivery:none）
prompt：cycle_id={cycle_id}，读取委员输出文件，执行 custom-ic-synthesise SKILL
```

**sessions_yield** ← 等 CIO 完成

✅ `CIO yield 完成，cycle_id={cycle_id}，IC 结束`
