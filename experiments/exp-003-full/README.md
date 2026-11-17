# exp-003 放量（每域 10 → 100）

## 目的

在 small 阶段确认问题后，放量验证问题比例是否稳定，产出正式实验表。

## 命令

```bash
# 中批量：每域 10 题，共 60
python scripts/run_batch.py --name medium --domains all --per-domain 10

# 全量：每域 100 题，共 600
python scripts/run_batch.py --name full --domains all --per-domain 100

python scripts/analyze_results.py --dir results/full \
  --out-md reports/full.md --out-issues reports/full.issues.csv \
  --out-tasks reports/full.tasks.csv
```

## 放量前检查

- [ ] small 阶段每个失败都能解释
- [ ] 没有未处理的系统性问题
- [ ] 同一配置重复跑一次结果大致稳定
- [ ] 预算足够（先看 medium 的 token/cost）

## 结果

| 阶段 | n | 通过率 | 部分分 | 主要失败类型 |
|---|---:|---:|---:|---|
| medium | 60 |  |  |  |
| full | 600 |  |  |  |

## 与 small 的对比

| 失败类别 | small 占比 | full 占比 | 是否稳定 |
|---|---:|---:|---|
|  |  |  |  |

## 结论

- 稳定 / 不稳定：
- 正式表是否可以定稿：
- 下一步：
