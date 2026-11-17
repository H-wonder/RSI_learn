# 实验表模板

> 每个数字都必须能追到 `results/<name>/` 下的 JSON。空白表示未跑，不要填估算值。

## 表 1：基线主表（按域）

| Model | Toolset | max_steps | Overall pass | Overall partial | Sales | Marketing | Operations | Support | Finance | HR | Avg steps | Tokens in/out | Cost |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
|  | api | 50 |  |  |  |  |  |  |  |  |  |  |  |
|  | api | 50 |  |  |  |  |  |  |  |  |  |  |  |

规则：

- 各域列填 pass rate，括号里写 `n`；
- 不同模型必须同 toolset、同 max_steps、同数据切片；
- `Overall` 不含 simple。

## 表 2：问题类型 × 通过率

| 问题类 | n | Pass | Partial | 典型失败 | 备注 |
|---|---:|---:|---:|---|---|
| P1 单工具 CRUD |  |  |  |  |  |
| P2 多跳检索 |  |  |  |  |  |
| P3 跨应用对账 |  |  |  |  |  |
| P4a 资格筛选/规则判定 |  |  |  |  |  |
| P4b 分支路由/优先级 |  |  |  |  |  |
| P5 排除/冲突 |  |  |  |  |  |
| P6 模糊匹配 |  |  |  |  |  |
| P7 时间日程 |  |  |  |  |  |
| P8 聚合评分 |  |  |  |  |  |
| P9 长链编排 |  |  |  |  |  |

生成方式：

```bash
python scripts/analyze_by_type.py --dir results/full \
  --annotation data/annotation/tasks_to_label.csv \
  --out-md reports/full.by_type.md --out-csv reports/full.by_type.csv
```

## 表 3：小批量 vs 放量

| 阶段 | n | 通过率 | 部分分 | extra_action | missing_record | wrong_value | 其他 |
|---|---:|---:|---:|---:|---:|---:|---:|
| small | 18 |  |  |  |  |  |  |
| medium | 60 |  |  |  |  |  |  |
| full | 600 |  |  |  |  |  |  |

用途：判断问题比例是否稳定。如果 small 和 full 差异大，样本不够或切片有偏。

## 表 4：失败归因（定性）

| 失败类型 | 例子任务 | 现象 | 归因（模型/工具/结构/评测） | 可改进动作 |
|---|---|---|---|---|
| 找错实体 |  |  |  |  |
| 漏步 |  |  |  |  |
| 多做（负断言失败） |  |  |  |  |
| 规则读错 |  |  |  |  |
| 参数格式错 |  |  |  |  |
| 提前终止 |  |  |  |  |

> 至少覆盖 30 个失败样本，作为报告第 6 节的核心。
