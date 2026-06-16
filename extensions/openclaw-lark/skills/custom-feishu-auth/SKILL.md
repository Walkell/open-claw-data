---
name: custom-feishu-auth
description: |
  飞书统一授权协议。调用任何飞书 API 前先确认是否需要 Bitable 专项步骤。
  覆盖两条路径：
  (1) 通用路径 — 适用于所有非 Bitable 飞书 API（IM / Calendar / Task / Doc），直接调用目标工具即可，授权续期已由系统自动处理
  (2) Bitable 专项 — 额外获取 app_token，解决 token 不能经过文字传递的安全问题
  遇到 permission_denied / NOTEXIST 时也通过此 SKILL 重试，但不通过调用 feishu_oauth 解决。
---

# custom-feishu-auth · 飞书统一授权协议

## 为什么需要这个 SKILL

飞书 API 有两层授权：

1. **用户 OAuth token**（所有 API 共用）：由系统自动续期（auto-auth），与本 SKILL、与 `feishu_oauth` 工具都无关——遇到任何鉴权报错，唯一正确动作是直接重试原工具调用，不调用任何 auth 相关工具。
2. **Bitable app_token**（仅 Bitable API）：每个多维表格应用有独立 token。这个 token **不能出现在任何文字输出**（思考过程、response、spawn prompt），安全策略会将其替换为 `***`，导致后续 API 调用返回 NOTEXIST。

---

## 遇到任何鉴权报错时

授权失败 / 授权过期 / 401 / permission_denied / NOTEXIST —— 不管报错是什么，正确动作只有一种：**直接重试原本想调用的那个工具**（最多 2 次）。系统会在后台自动处理授权（auto-auth），不需要、也不应该调用任何名字里带 oauth 的工具来"修复"或"刷新"。

---

## 路径一：通用路径（IM / Calendar / Task / Doc）

直接调用目标工具（feishu_calendar_event、feishu_im_user_get_messages 等），无需任何前置 auth 调用——授权续期已由系统自动处理。

---

## 路径二：Bitable 专项（Bitable API 前执行）

### 第一步：feishu_bitable_app.list() 取 app_token

调用 `feishu_bitable_app.list()`，从返回结果中找到当前 principal 对应的 Bitable（按名称匹配），取出 `app_token`。

### 第二步：立即链式调用，不经过文字

从工具调用结果中直接提取 `app_token`，**立刻**传入下一个 Bitable 工具调用的参数。

**严禁以下行为：**
- ❌ 把 app_token 值写进任何文字输出（thinking、response、日志）
- ❌ 在 spawn 子 Agent 的 prompt 里包含 app_token 值
- ❌ 把 app_token 写进 context.json 或任何文件

**在文字里提及 Bitable 时，用名称代替 token 值：**
- ✅ "Towney-投资管理"、"Klaire-投资管理"
- ❌ "app_token: OcmCb7TQYaHqnvs..."

---

## 遇到 NOTEXIST / permission_denied 时

直接重新执行对应路径（重新 list() → 重新链式调用即可，不调用 feishu_oauth）。最多重试 2 次。系统的 auto-auth 会在后台处理授权续期，无需 Agent 介入。

两次重试后仍失败，上报错误，不静默失败：
```
⚠️ 飞书授权持续失败 | error: {code} | msg: {msg} | 已重试 2 次
```

---

## spawn 子 Agent 规则

spawn prompt 里只传：
- `principal`（名称，如 "towney"）
- `cycle_id`

**绝不传 app_token**。子 Agent 启动后自己调用本 SKILL 的路径二获取 token。

---

## 各 Principal Bitable 对应关系（备查）

| principal | Bitable 名称 | 持仓表 | 观察池 | 监控记录 |
|-----------|-------------|--------|--------|---------|
| towney | Towney-投资管理 | tblUeTGMf0IKJ8Pk | tblaLlSQp8tEcWgJ | tblFAfrZs4Rz4AOu |
| klaire | Klaire-投资管理 | tbl9xYrGkBDZlnYm | tblaQY1jOFWOXd1U | tblHkc0MfQbe2x37 |

table_id 是稳定标识符，可以安全出现在文字和文件中。app_token 是动态 token，不可以。
