---
name: custom-config-read
description: |
  读取 principal 配置档（CONFIG_{PRINCIPAL_ID}.md，位于该 principal 前端 agent 的工作目录下）的唯一正确方式。
  任何需要读取 profit_target / risk_thresholds / ledger / 输出通道等配置字段的场景都应使用本 SKILL，
  而不是直接 Read 文件或凭记忆/快照取值。强制按 principal 隔离：一次只读取目标 principal 自己的配置档，
  绝不在同一上下文里读取或带出其他 principal 的配置档内容。
---

# custom-config-read · Principal 配置档读取

> **输入**：principal id（小写，如 `towney` / `klaire`）。
> **输出**：该 principal 对应 `CONFIG_{PRINCIPAL_ID}.md` 的字段值。
> **红线**：不读取、不引用、不带出其他 principal 的配置档内容。

---

## 第一步：确认 principal

调用方（Butler / CIO / 任何 Agent）必须已经明确知道当前在为哪个 principal 工作。如果上下文里没有明确的 principal，先停下来确认，不要猜测或默认选一个。

isolated 子 Agent（Research/Industry/News/Risk）的 principal 来自派发时注入的 `context.json`，直接用那个值，不要自己重新判断。

## 隔离边界

本 SKILL 一次只服务一个 principal，且只接受单个 principal 作为输入——不接受"读取所有 principal 配置"这类调用。

如果确实需要跨 principal 比较配置档结构（例如检查模板同步状态），那是 `custom-config-maintain` SKILL 的职责，不是本 SKILL：那个场景比较的是章节结构/字段名，不涉及把一个 principal 的实际业务数据（Bitable 范围、群聊 ID、收益目标等）带入另一个 principal 的处理流程，性质不同。

## 第二步：拼出唯一目标路径

每个 principal 的配置档放在其前端 agent 的工作目录下，不是统一放在 `workspace-cio/`。按以下对照表确定路径：

| principal id | 路径 |
|---|---|
| klaire | `workspace-butler/CONFIG_KLAIRE.md` |
| towney | `workspace-dexter/CONFIG_TOWNEY.md` |

新增 principal 时，在这张表里补一行（`custom-config-maintain` 的发现步骤也用同一张表，两处务必同步更新）。

**只 Read 这一个文件。** 不 Glob `CONFIG_*.md`，不在同一次操作里把多个 principal 的配置档都读出来——即使只是为了"对比格式"，也会导致一个 principal 的数据域/输出通道信息出现在另一个 principal 的处理上下文里，这本身就是一次串账事故，与是否后续误用无关。

`CONFIG_SAMPLE.md` 是模板，不是任何 principal 的真实配置，不在此读取范围内（维护模板见 `custom-config-maintain` SKILL）。

## 第三步：取值

文件内字段均为 YAML/Markdown，直接按需要的字段名取值即可，无需额外解析逻辑：

| 字段路径 | 用途 |
|---------|------|
| `principal.id` / `principal.display_name` | 身份确认 |
| `ledger.*` | Bitable 表名/范围（app_token 仍必须走 `custom-feishu-auth`，配置档里只是占位说明，不存真实 token） |
| `profit_target.*` | 年化目标 |
| `risk_thresholds.veto` / `risk_thresholds.hard_veto` | Risk 委员否决阈值 |
| 仓位体系（如有该节） | 该 principal 的仓位输出格式；没有这节就说明该 principal 不需要特殊格式，按通用规则处理 |
| 输出通道 | 群聊/私聊 ID，决定推送目标；归属永久且排他，不需要每次按消息内容判断 |

字段缺失（如 klaire 没有"仓位体系"节）属于正常情况，不要假设缺的字段应该有值或去 CONFIG_SAMPLE.md / 其他 principal 的文件里找"应该填什么"——没有就是没有，按文件原样为准。

### 输出通道：解析 ID 与频道限制

`输出通道` 这节目前两种写法都可能存在（模板已改为合并格式，但已有的真实配置档可能还没同步，见 `custom-config-maintain`）：

- 合并格式：`ID：{群聊ID}/{单聊ID}`，一行内可能有一个或两个 ID
- 旧格式：分开的"私聊:"/"群聊:"bullet，各自带 ID

两种格式都按同一规则取值，不用关心格式本身：

1. 从该节文字里提取所有形如 `ou_...` / `oc_...` 的 ID
2. `ou_` 开头 = 单聊（`receive_id_type: open_id`），`oc_` 开头 = 群聊（`receive_id_type: chat_id`）——类型从前缀推断，不需要该节额外标注类型
3. 单聊/群聊本身不限制功能——讨论持仓、出建议、写 Bitable 在两种渠道都可以。渠道归属是永久且排他的，不需要按消息内容逐次判断 principal——一个 channel ID 在配置档里填给了谁，就永远归谁，即使另一个 principal 在该渠道发消息也不会改变判定。每个 principal 自己 CONFIG 文件的"输出通道"一节就是该渠道归属的唯一权威来源，不存在独立的绑定文件——若确实存在多个 principal 永久共用同一个渠道的情况，要在涉及的所有 principal 的 CONFIG 文件本节同步加说明，不要在本 SKILL 里临时推断归属——红线始终是不能串 principal，不是渠道类型本身

## 遇到文件不存在

`CONFIG_{PRINCIPAL_ID}.md` 不存在 → 说明该 principal 尚未配置，上报缺失，不回退读取 CONFIG_SAMPLE.md 当作真实配置使用（模板里全是空字段，没有意义）。
