# exp-001 烟测（simple 5 题）

## 目的

验证整条链路：API key → 工具调用 → 状态修改 → 断言 → 结果 JSON。**不看分数。**

## 命令

```bash
python scripts/check_env.py
python scripts/run_batch.py --name smoke --domains simple --per-domain 5
python scripts/analyze_results.py --dir results/smoke \
  --out-md reports/smoke.md --out-issues reports/smoke.issues.csv
```

## 检查清单

- [ ] 5 题都有结果
- [ ] 结果 JSON 里有 `assertion_results`
- [ ] `messages` 里能看到工具调用
- [ ] 没有 `errors` / `empty_responses`
- [ ] token 和 cost 有数

## 结果

| 指标 | 值 |
|---|---:|
| n |  |
| 通过率 |  |
| 平均部分分 |  |
| 平均步数 |  |
| token in/out |  |
| 成本 |  |

## 结论

- 链路是否通：
- 异常：
- 是否可以进入小批量：
