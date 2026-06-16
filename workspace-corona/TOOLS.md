# Corona · 工具说明

## 飞书 Auth 前置协议

调用任何飞书工具前，先执行 `custom-feishu-auth` SKILL 对应路径：

| 飞书功能 | Auth 路径 | SKILL |
|---------|----------|-------|
| Bitable（持仓 / 观察池 / 交易记录 / 监控记录） | 路径二：直接调用 feishu_bitable_app.list() 取 app_token，链式调用 | `custom-feishu-auth` + `feishu-bitable` |
| IM 推送（盘中监控预警） | 路径一：直接调用目标工具，无需 app_token | `custom-feishu-auth` + `feishu-im-read` / 对应 IM SKILL |

> app_token **不得出现在任何文字输出中**。
> ⚠️ 遇到 401 / permission_denied / NOTEXIST 等任何鉴权报错，唯一正确动作是直接重试原工具调用（最多 2 次）——系统的 auto-auth 会在后台自动处理授权，不需要调用任何 auth 相关工具。

---

## Bitable Table ID 速查

```
towney（Towney-投资管理）:
  持仓表:    tblUeTGMf0IKJ8Pk
  观察池:    tblaLlSQp8tEcWgJ
  监控记录:  tblFAfrZs4Rz4AOu

klaire（Klaire-投资管理）:
  持仓表:    tbl9xYrGkBDZlnYm
  观察池:    tblaQY1jOFWOXd1U
  监控记录:  tblHkc0MfQbe2x37
```

遇 NOTEXIST → 重新执行 `custom-feishu-auth` SKILL（最多 2 次）。

---

## IC 编排

- IC 流程入口：`custom-ic-orchestrate` SKILL（详见 `workspace-corona/AGENTS.md`）——cron 触发分支
- IC 综合由 isolated CIO 执行 `custom-ic-synthesise` SKILL，CIO 直接推飞书，Corona 不重复推送

---

## 盘中监控

- Monitor 任务入口：spawn agentId=monitor（isolated），见 `workspace-monitor/AGENTS.md`
- Monitor 只读行情、写监控记录表，不推送——推送由 Corona 在 yield 之后显式调用 feishu_im 完成

---

## 推送渠道

Corona 的常驻会话（`agent:corona:cron:{principal}`）**没有挂任何聊天频道**，会话内输出对用户不可见。所有需要让人看到的内容，必须显式调用飞书工具推送：

- IC 结论 → 由 CIO 推送，Corona 不经手
- 盘中监控预警 → Corona 显式调用 feishu_im 推送到对应 DM / 群

---

## 状态文件

- 路径：`~/.openclaw/shared/corona-status/{principal}.json`
- 协议详见 `workspace-corona/AGENTS.md` 顶部「状态文件协议」一节
- 这是 Butler 查询你执行状态的唯一接口，每一步都要写
