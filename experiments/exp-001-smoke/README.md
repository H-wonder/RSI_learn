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
| n | 5 |
| 通过率 | 60%（3/5） |
| 平均部分分 | 0.600 |
| 平均步数 | 9.6 |
| token in/out | 293,857 / 2,933 |
| 成本 | $1.56 |

失败任务与原因见 [issues.md](issues.md)。

## 结论

- 链路：通（工具调用、状态修改、断言、导出都正常）。
- 主要问题：
  1. 模型把 `api_fetch` URL 里的 `{userId}` / `{id}` 当字面量，导致 404；
  2. contact 指向的 Account 记录不存在，模型不知道该更新 contact 的冗余字段，最后放弃。
- 是否可以进入小批量：可以，但要重点观察这两类问题是否普遍。
