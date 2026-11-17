# 60 题人工标注表

文件：[tasks_to_label.csv](tasks_to_label.csv)

- 6 个计分域 × 10 题 = 60 行
- `simple` 域不计分，没有放进来

## 要填的 4 列

| 列 | 填什么 |
|---|---|
| `primary_type` | P1–P9 选一个 |
| `secondary_types` | 可多个，用 `;` 分隔，如 `P4;P5` |
| `evidence` | 一条支撑判断的断言 `type` |
| `failure_mode` | 一句话：这类任务最容易怎么错 |

## 怎么查看完整任务

```bash
export PATH="$HOME/.local/bin:$PATH"
uv run --project ../datasets/AutomationBench python ../scripts/inspect_task.py \
  --domain sales --index 22
```

（`inspect_task.py` 在主工作区的 `scripts/` 下。）

## 标完之后

1. 统计每类数量；
2. 少于 3 题的类合并或删掉；
3. 更新 `docs/problem-taxonomy.md`；
4. 等基线结果出来后，用 `primary_type` 做“问题类型 × 通过率”表。
