# 怎么复核 P1–P9 标注

> 目标：不需要看懂整个数据集，只要会回答三个问题，就能判断一道题的标签对不对。

## P1–P9 速查表

| 编号 | 一句话 | 看到这些就选它 |
|---|---|---|
| P1 | 单工具状态更新 | 用户直接给了 ID，只改一个应用的一条记录 |
| P2 | 多跳检索 | 任务只给线索（人名/公司名），要先查 A 拿 ID，再查 B，最后操作 C |
| P3 | 跨应用对账/同步 | 两个地方有同一份数据，要以一方为准合并 |
| P4 | 条件路由/规则推理 | 有 tier/金额/优先级/日期阈值/资格规则，按规则决定做什么 |
| P5 | 排除/冲突消解 | 有“不能做”的检查，或“总数必须等于 N”，或按最新/最高优先级选 |
| P6 | 模糊匹配/脏数据 | 名字拼错、电话/日期格式不一致、字段缺失 |
| P7 | 时间/日程 | 排会、改期、时区、冲突、缓冲 |
| P8 | 聚合/计算 | 加权、排序、分组、汇总、算百分比/金额 |
| P9 | 长链编排 | 5+ 步互相依赖，覆盖多个应用，任意一步错后面全错 |

## 复核一道题的三步

```bash
uv run --project ../datasets/AutomationBench python scripts/inspect_task.py \
  --domain sales --index 44
```

看输出里的三块：

1. **`## user`（用户请求）**
   - 有没有直接给出人名/邮箱/ID？
   - 没有 → 先考虑 P2。
2. **`## tools`（工具）**
   - 跨了几个应用？两个以上 → P2 / P3。
3. **`## assertions`（断言）**
   - 有 `[NEG]` 或“不能/总数等于 N” → P5 是重要约束。
   - 有 `*_exists` / `*_equals` / `gmail_message_sent` → 看最终动作是什么。
   - 有条件词（tier、priority、before today、eligible）→ P4。

**主类选择规则**：选“最耗步骤、最容易失败”的那一步，不是选最后一步。

## 复核 CSV 的方法

打开 [tasks_to_label.csv](../data/annotation/tasks_to_label.csv)，找到对应行：

- `primary_type`：我标的主类，你可以直接改。
- `secondary_types`：次类，可多个，用 `;` 分隔。
- `evidence`：我引用的一条断言，用来支撑判断。
- `failure_mode`：一句话，说明这类任务最容易怎么错。
- `notes`：现在写着“AI 初标，待人工复核”，你复核完可以改成“已复核”。

**改完不需要重新跑脚本**，CSV 就是最终结果。

## 建议先复核这 5 题

这 5 题覆盖不同类别，其中 3 题是 P4（占比最高，最需要检查）：

| # | 任务 | 域 | index | 我标的 |
|---:|---|---|---:|---|
| 1 | `sales.multi_hop_lookup` | sales | 0 | P2 |
| 2 | `sales.sheets_reconciliation` | sales | 11 | P3 |
| 3 | `sales.calendly_sla_monitoring` | sales | 44 | P4 |
| 4 | `operations.generator_load_testing_schedule` | operations | 99 | P4 |
| 5 | `hr.quarterly_termination_queue` | hr | 99 | P4 |

命令（在仓库根目录）：

```bash
uv run --project ../datasets/AutomationBench python scripts/inspect_task.py --domain sales --index 0
uv run --project ../datasets/AutomationBench python scripts/inspect_task.py --domain sales --index 11
uv run --project ../datasets/AutomationBench python scripts/inspect_task.py --domain sales --index 44
uv run --project ../datasets/AutomationBench python scripts/inspect_task.py --domain operations --index 99
uv run --project ../datasets/AutomationBench python scripts/inspect_task.py --domain hr --index 99
```

## 复核时只问三个问题

1. **信息是不是用户直接给的？** 不是 → P2 可能性大。
2. **有没有规则/阈值/资格判断？** 有 → P4 可能性大。
3. **有没有“不能做/只能做 N 个/取最新”的约束？** 有 → P5 是重要次类。

三个问题答完，主类基本就定了。拿不准就写在 `notes` 里，不要卡住。

## 一个已核对的例子：`hr.quarterly_termination_queue`

- 用户请求：处理本季度终止名单，发通知、通知 IT、邮件经理。
- 断言：**所有** `gmail_message_not_sent_to` / `row_not_updated` 都是“不要做”，Slack 只要 `pause`。
- 结论：这是一道**“读最新公告后暂停”**的反直觉任务，主类 P4（规则覆盖字面指令），次类 P5。
- 所以：不要看用户请求说“处理”就标成 P1/P9，要看断言实际要求什么。

## P1–P9 的完整定义

- [problem-taxonomy.md](problem-taxonomy.md)：分类表、判定顺序、与流程结构的映射
- [../reports/annotation-distribution.md](../reports/annotation-distribution.md)：60 题分布
