# AutomationBench 数据卡片

> 数字来自运行时 dataset（`get_<domain>_dataset()`），不是静态代码统计。

## 规模

| 项 | 值 |
|---|---|
| 计分任务 | 600（6 域 × 100） |
| 调试任务 | 200（`simple`，不计分） |
| 总任务数 | 800 |
| 总断言数 | 9,855 |
| 负断言占比 | 38.5% |
| 实际使用的断言类型 | 337 种 |
| 模拟 SaaS 应用 | 47 个 |
| 公开集 vs 私有集 | 本地只能跑 public；官方榜单用私有集 |

## 分域复杂度

| 域 | n | 工具/任务 | 断言/任务 | 初始状态 | 负断言占比 |
|---|---:|---:|---:|---:|---:|
| sales | 100 | 9.8 | 10.9 | 45 KB | 31.3% |
| marketing | 100 | 9.3 | 19.5 | 13 KB | 34.4% |
| operations | 100 | 9.2 | 14.0 | 19 KB | 52.8% |
| support | 100 | 12.0 | 34.9 | 8 KB | 40.8% |
| finance | 100 | 7.8 | 7.1 | 3 KB | 29.2% |
| hr | 100 | 7.3 | 9.7 | 4 KB | 42.4% |
| simple | 200 | 2.0 | 1.2 | 0.4 KB | 0% |

## 三个关键结论

1. **support 最严格**：平均 34.9 条断言/任务，漏一条就失败。
2. **sales 信息量最大**：初始状态平均 45 KB（邮件 + 表格 + CRM），多跳检索成本最高。
3. **负断言占 38.5%**，operations 高达 52.8%——“不做错”和“做对”同样重要。

## 任务结构

每个任务包含：

```json
{
  "example_id": 501,
  "prompt": [{"role": "system", ...}, {"role": "user", ...}],
  "info": {
    "task_name": "sales.multi_hop_lookup",
    "zapier_tools": ["salesforce_find_records", "..."],
    "initial_state": {"gmail": {...}, "salesforce": {...}},
    "assertions": [{"type": "salesforce_field_equals", "...": "..."}]
  }
}
```

- `answer` 为空：评分不靠文本匹配，靠最终环境状态。
- `assertions` 是验收标准，分正断言和负断言。

## 坑

- 任务由 Python 代码生成，没有静态 JSONL。
- `sales/tasks.py` 有 106 个函数定义，运行时只选 100 个。
- 函数名和任务名不一定对应（如 `get_multi_hop_contact_update_task` → `sales.multi_hop_lookup`）。
- 运行时没有顶层 `task` 字段，任务名在 `info.task_name`。
