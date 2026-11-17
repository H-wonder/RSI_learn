# 失败分类标准

分析脚本会按断言类型自动归类。**自动归类只是初稿，必须人工复核。**

## 先分清正断言和负断言

| 类型 | 含义 | 失败意味着 |
|---|---|---|
| 正断言 | “应该发生” | **漏做**或**做错** |
| 负断言（type 里含 `not`） | “不能发生” | **多做了**（广撒网、误操作） |

AutomationBench 里负断言占 38.5%，所以“多做”是主要失败来源之一。

## 自动分类

| 类别 | 触发条件 | 典型断言 | 人话 |
|---|---|---|---|
| `extra_or_unwanted_action` | 断言 type 含 `not` | `gmail_message_not_sent_to`、`google_sheets_row_not_exists` | 做了不该做的事 |
| `missing_record` | type 以 `_exists` 结尾或含 `_exists_` | `salesforce_contact_exists_with_field`、`zendesk_ticket_exists` | 该建的记录没建，或建错 key |
| `missing_message_or_note` | type 含 `sent/message/in_channel/comment` | `gmail_message_sent`、`slack_message_in_channel` | 该发的消息/评论没发 |
| `wrong_value_or_state` | type 含 `equals` 或 `has_priority/has_tag` | `salesforce_field_equals`、`google_sheets_row_cell_equals` | 记录在，但字段值错 |
| `wrong_count` | type 含 `count` + `equals` | `salesforce_collection_count_equals` | 数量不对（多建/少建） |
| `missing_content` | type 含 `contains` | `gmail_message_sent_to_with_body_contains` | 消息发了，但正文缺关键内容 |
| `other` | 以上都不匹配 | — | 需要人工看 |

## 人工复核时看什么

对每个失败任务，打开结果 JSON 的 `messages`，回答：

1. **它做了什么？**（调了哪些工具、参数是什么）
2. **它漏了什么？**（对比任务里的 `assertions`）
3. **它多做了什么？**（负断言）
4. **是模型决策错，还是工具/环境错？**
   - 模型错：选错实体、漏步、提前结束
   - 工具错：工具返回异常、参数 schema 不匹配
   - 环境错：初始数据缺失、断言本身有歧义

## 归因标签（人工填）

在 `issues.md` 里给每条失败加一个“根因”：

| 根因 | 说明 |
|---|---|
| `entity_resolution` | 找错实体（同名、相似邮箱） |
| `missing_step` | 漏了任务要求的一步 |
| `extra_action` | 做了不该做的操作 |
| `rule_misread` | 规则/条件读错 |
| `value_error` | 数值/日期/币种/格式算错 |
| `premature_stop` | 没做完就结束 |
| `tool_error` | 工具调用失败/参数错 |
| `task_ambiguity` | 任务本身有歧义或断言不合理 |

## 比例怎么算

- **断言层面**：某类失败的断言数 / 全部失败断言数
- **任务层面**：至少有一条该类失败的任务数 / 总任务数

两个都要报，因为一个任务可能挂多条同类断言。

脚本已经算好，见报告第 4 节。
