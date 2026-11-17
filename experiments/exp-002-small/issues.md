# exp-002 小批量问题记录

> 数据来源：`reports/small.issues.csv`（一行一条失败断言）+ 结果 JSON 的 `messages`。
> 每个失败任务至少记一行；同一个任务多条失败可以合并成一行，写清断言类型。

## 记录表

| # | 域 | 任务 | 分数 | 失败断言 | 自动类别 | 实际做了什么 | 根因 | 系统性? |
|---:|---|---|---:|---|---|---|---|---|
| 1 |  |  |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |  |  |

## 根因选项

`entity_resolution` / `missing_step` / `extra_action` / `rule_misread` /
`value_error` / `premature_stop` / `tool_error` / `task_ambiguity`

## 分类汇总

| 自动类别 | 失败断言数 | 占比 | 涉及任务数 |
|---|---:|---:|---:|
| extra_or_unwanted_action |  |  |  |
| missing_record |  |  |  |
| missing_message_or_note |  |  |  |
| wrong_value_or_state |  |  |  |
| wrong_count |  |  |  |
| missing_content |  |  |  |
| other |  |  |  |

## 系统性问题

> 需要修配置/工具/断言，而不是“模型不行”。

| 问题 | 证据 | 影响 | 处理 |
|---|---|---|---|
|  |  |  |  |

## 结论

- 18 题里能解释清楚原因的：___ / 18
- 失败类型数量：
- 是否进入 medium：
- 需要先修的东西：
