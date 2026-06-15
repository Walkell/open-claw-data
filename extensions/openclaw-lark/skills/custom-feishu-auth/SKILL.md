---
name: custom-feishu-auth
description: |
  飞书统一授权协议。调用任何飞书 API 前必须通过此 SKILL 完成 auth 前置步骤。
  覆盖两条路径：
  (1) 通用 OAuth 续期 — 适用于所有飞书 API（IM / Calendar / Task / Doc / Bitable）
  (2) Bitable 专项 — 在通用续期基础上额外获取 app_token，解决 token 不能经过文字传递的安全问题
  遇到 permission_denied / NOTEXIST 时也通过此 SKILL 重新授权后重试。
---

# custom-feishu-auth · 飞书统一授权协议

## 为什么需要这个 SKILL

飞书 API 有两层授权：

1. **用户 OAuth token**（所有 API 共用）：需要定期续期，否则工具调用返回 401。
2. **Bitable app_token**（仅 Bitable API）：每个多维表格应用有独立 token。这个 token **不能出现在任何文字输出**（思考过程、response、spawn prompt），安全策略会将其替换为 `***`，导致后续 API 调用返回 NOTEXIST。

---

## 路径一：通用 OAuth 续期（IM / Calendar / Task / Doc）

调用任何飞书非 Bitable API 之前执行：

```
feishu_oauth()   ← 正确且完整的续期调用，不需要传任何参数
```

续期完成后直接调用目标工具（feishu_calendar_event、feishu_im_user_get_messages 等），无需其他操作。

---

## 路径二：Bitable 专项（Bitable API 前执行）

在路径一的基础上，额外执行以下步骤：

### 第一步：feishu_oauth 续期（同路径一）

### 第二步：feishu_bitable_app.list() 取 app_token

调用 `feishu_bitable_app.list()`，从返回结果中找到当前 principal 对应的 Bitable（按名称匹配），取出 `app_token`。

### 第三步：立即链式调用，不经过文字

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

重新执行对应路径（重新续期 → 重新 list() → 重新链式调用）。最多重试 2 次。

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
