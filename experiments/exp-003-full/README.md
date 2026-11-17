# exp-003 放量（每域 10 → 100）

## 目的

在 small 阶段确认问题后，放量验证问题比例是否稳定，产出正式实验表。

## 命令

```bash
# 中批量：60 题标注样本；复用 small 已跑的 12 题，只跑缺的 48 题
python scripts/run_batch.py --name medium --tasks-file data/tasks/medium_missing.csv

# 合并 small + medium，只统计 60 题标注样本
python scripts/analyze_results.py \
  --dir results/small --dir results/medium \
  --tasks-file data/tasks/medium_from_annotation.csv \
  --out-md reports/medium-60.md --out-issues reports/medium-60.issues.csv \
  --out-tasks reports/medium-60.tasks.csv

python scripts/analyze_by_type.py \
  --dir results/small --dir results/medium \
  --tasks-file data/tasks/medium_from_annotation.csv \
  --annotation data/annotation/tasks_to_label.csv \
  --out-md reports/medium-60.by_type.md --out-csv reports/medium-60.by_type.csv

# 全量：每域 100 题，共 600（未跑）
python scripts/run_batch.py --name full --domains all --per-domain 100
```

## 放量前检查

- [x] small 阶段每个失败都能解释（4 个 0 分任务已分析）
- [x] 没有未处理的系统性问题（采样已对齐）
- [ ] 同一配置重复跑一次结果大致稳定
- [ ] 预算足够（medium 已花 $71.78，full 预计约 $700）

## 结果

| 阶段 | n | 通过率 | 部分分 | 成本 |
|---|---:|---:|---:|---:|
| medium（60 题） | 60 | **11.7%** | **0.509** | **$71.78** |
| full（600 题） | 600 | 未跑 | — | — |

分域：

| 域 | n | 通过率 | 部分分 |
|---|---:|---:|---:|
| sales | 10 | 0% | 0.396 |
| marketing | 10 | 10.0% | 0.614 |
| operations | 10 | 10.0% | 0.458 |
| support | 10 | 0% | 0.506 |
| finance | 10 | 30.0% | 0.586 |
| hr | 10 | 20.0% | 0.495 |

类型：

| 类型 | n | 通过率 | 部分分 |
|---|---:|---:|---:|
| P2 | 10 | 10.0% | 0.415 |
| P3 | 7 | 0% | 0.436 |
| P4 | 25 | 12.0% | 0.505 |
| P5 | 3 | 33.3% | 0.630 |
| P7 | 1 | 0% | 0.667 |
| P8 | 12 | 16.7% | 0.632 |
| P9 | 2 | 0% | 0.286 |

## 与 small 的对比

| 指标 | small（18） | medium（60） |
|---|---:|---:|
| 通过率 | 16.7% | 11.7% |
| 部分分 | 0.562 | 0.509 |
| 漏建记录 | 45.6% | 42.6% |
| 漏发消息 | 35.3% | 29.1% |
| 多做 | 11.8% | 10.9% |

失败类型比例基本稳定；“漏做”仍然是主因。

## 结论

- 60 题结果可作为第一张正式表；full 600 未跑，论文里要写明“60 题分层样本”。
- 成本：60 题 $71.78，按此估算 full 约 $700，需要预算决策。
- 下一步：结构验证（见 [structure-validation-plan.md](../../docs/structure-validation-plan.md)）。
