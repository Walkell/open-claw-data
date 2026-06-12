---
name: feishu-bitable-auth
description: |
  飞书 Bitable token 获取与授权续期协议。所有 Agent（主 Agent 和子 Agent）在访问 Bitable 前必须通过此 Skill 获取 token，避免因 token 出现在文字输出中被安全策略替换为 *** 导致的 NOTEXIST 错误。
  遇到 permission_denied / NOTEXIST 时也通过此 Skill 续期重试。
---

# Feishu Bitable Token 获取协议

## 为什么需要这个 SKILL

**根本原因**：app_token 一旦出现在任何文字输出（思考过程、response、spawn prompt）中，安全策略会将其替换为 `***`。后续 API 调用若使用 `***` 会返回 NOTEXIST。

这不是 token 过期的问题，是 token 值**不能经过文字**传递的问题。

---

## 获取 Token 的正确步骤

### 第一步：feishu_oauth 续期

调用 `feishu_oauth` 刷新授权（每次会话主动执行，不等报错）。

> ⚠️ 绝不传 `action="revoke"`——revoke 会清除用户授权凭据，不是刷新 token。

### 第二步：feishu_bitable_app.list() 取 token

调用 `feishu_bitable_app.list()`，从返回结果中找到当前 principal 对应的 Bitable，取出 `app_token`。

### 第三步：立即链式调用，不经过文字

从工具调用结果中直接提取 `app_token`，**立刻**传入下一个工具调用的参数。

**严禁以下行为：**
- ❌ 把 app_token 值写进任何文字输出（thinking、response、日志）
- ❌ 在 spawn 子 Agent 的 prompt 里包含 app_token 值
- ❌ 把 app_token 写进 context.json 或任何文件

**在文字里提及 Bitable 时，用名称代替 token 值：**
- ✅ "Towney-投资管理"、"Klaire-投资管理"
- ❌ "app_token: OcmCb7TQYaHqnvsjBjAc0GRdnTb"

---

## 遇到 NOTEXIST / permission_denied 时

重新执行上述三步（重新续期 → 重新 list() → 重新链式调用）。最多重试 2 次。

两次重试后仍失败，上报错误，不静默失败：
```
⚠️ Bitable 授权持续失败 | error: {code} | msg: {msg} | 已重试 2 次
```

---

## spawn 子 Agent 规则

spawn prompt 里只传：
- `principal`（名称，如 "towney"）
- `cycle_id`

**绝不传 app_token**。子 Agent 启动后自己调用本 SKILL 获取 token。

---

## 各 Principal 对应关系（备查）

| principal | Bitable 名称 | 持仓表 | 观察池 | 监控记录 |
|-----------|-------------|--------|--------|---------|
| towney | Towney-投资管理 | tblUeTGMf0IKJ8Pk | tblaLlSQp8tEcWgJ | tblFAfrZs4Rz4AOu |
| klaire | Klaire-投资管理 | tbl9xYrGkBDZlnYm | tblaQY1jOFWOXd1U | tblHkc0MfQbe2x37 |

table_id 是稳定标识符，可以安全出现在文字和文件中。app_token 是动态 token，不可以。
