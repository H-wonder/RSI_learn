# exp-002 小批量（每域 3 题，共 18 题）

## 目的

**暴露问题**，不是拿分数。跑完必须逐题记录失败原因，填 [issues.md](issues.md)。

## 命令

```bash
python scripts/select_tasks.py --per-domain 3 --out data/tasks/small.csv
# 或者直接按每域前 3 题：
python scripts/run_batch.py --name small --domains all --per-domain 3

python scripts/analyze_results.py --dir results/small \
  --out-md reports/small.md --out-issues reports/small.issues.csv
```

## 结果

| 指标 | 值 |
|---|---:|
| n | 18 |
| 通过率 |  |
| 平均部分分 |  |
| 平均步数 |  |
| token in/out |  |
| 成本 |  |

分域：

| 域 | n | 通过率 | 部分分 |
|---|---:|---:|---:|
| sales | 3 |  |  |
| marketing | 3 |  |  |
| operations | 3 |  |  |
| support | 3 |  |  |
| finance | 3 |  |  |
| hr | 3 |  |  |

## 结论

- 失败类型有几种：
- 是否有系统性 bug：
- 是否可以放量到每域 10 题：
