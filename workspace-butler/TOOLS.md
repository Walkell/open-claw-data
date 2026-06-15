# Butler · 工具说明

## 飞书 Auth 前置协议

调用任何飞书工具前，先执行 `custom-feishu-auth` SKILL 对应路径：

| 飞书功能 | Auth 路径 | SKILL |
|---------|----------|-------|
| Bitable（持仓 / 观察池 / 交易记录 / 监控记录） | 路径二：feishu_oauth 续期 + feishu_bitable_app.list() 取 app_token，链式调用 | `custom-feishu-auth` + `feishu-bitable` |
| IM / Calendar / Task / Doc | 路径一：feishu_oauth 续期即可，工具以用户身份调用，无需 app_token | `custom-feishu-auth` + 对应飞书 SKILL |

> app_token **不得出现在任何文字输出中**。  
> `feishu_oauth` 唯一正确调用：`feishu_oauth()`，不传任何参数。

---

## 行情数据

- **A股 + 港股**：`custom-market-data-cn` SKILL（双源验证 + 三源裁决）
- **美股 + 全球指数**：`custom-market-data-us` SKILL（多源验证 + 日期校验）
- ⚠️ `web_search` 严禁用于任何行情价格数据

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

- IC 流程入口：`custom-ic-orchestrate` SKILL（详见 `workspace-butler/AGENTS.md`）
- IC 综合由 isolated CIO 执行 `custom-ic-synthesise` SKILL

---

## 飞书消息推送

Butler 直接处理用户会话时，回复用户即可。  
IC 结论推送由 isolated CIO（custom-ic-synthesise SKILL）负责，Butler 不重复推送。
