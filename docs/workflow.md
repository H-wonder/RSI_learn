# 基线实验流程：小批量 → 记录 → 放量

> 原则：**不要一上来跑全量**。先用小批量暴露问题，记录、归类、修配置，再放量。

## 四个阶段

| 阶段 | 规模 | 命令 | 目的 | 通过条件 |
|---|---|---|---|---|
| 0 环境自检 | 0 | `python scripts/check_env.py` | 确认 Python/uv/数据集/key | 全部 OK |
| 1 烟测 | simple 5 题 | `run_batch.py --name smoke --domains simple --per-domain 5` | 验证链路：工具调用、状态、断言、导出 | 有结果 JSON，能打开 |
| 2 小批量 | 每域 3 题，共 18 | `run_batch.py --name small --domains all --per-domain 3` | **暴露问题**，逐题记录失败原因 | 18 题全部有记录 |
| 3 中批量 | 每域 10 题，共 60 | `run_batch.py --name medium --domains all --per-domain 10` | 看问题比例是否稳定 | 比例与 18 题接近 |
| 4 全量 | 每域 100 题，共 600 | `run_batch.py --name full --domains all --per-domain 100` | 出正式表 | 结果可复现 |

每一阶段都要：

```bash
python scripts/analyze_results.py --dir results/<name> \
  --out-md reports/<name>.md --out-issues reports/<name>.issues.csv
```

标注表填完后，再生成“问题类型 × 通过率”（表 2）：

```bash
python scripts/analyze_by_type.py --dir results/<name> \
  --annotation data/annotation/tasks_to_label.csv \
  --out-md reports/<name>.by_type.md --out-csv reports/<name>.by_type.csv
```

需要重算数据集规模时（不需要 API）：

```bash
uv run --project ../datasets/AutomationBench python scripts/dataset_stats.py
```

## 小批量记录怎么做

1. 跑完 18 题；
2. 打开 `reports/small.issues.csv`，一行是一条失败断言；
3. 对每个失败任务，看完整对话（结果 JSON 的 `messages`），写下：
   - 它本来要做什么；
   - 实际做了什么；
   - 卡在哪条断言；
   - 归类（见 [failure-taxonomy.md](failure-taxonomy.md)）；
   - 是模型问题、工具问题、还是任务本身歧义。
4. 填进 [../experiments/exp-002-small/issues.md](../experiments/exp-002-small/issues.md)。

**只记录事实，不要猜。** 例如：

- ✅ “它给 vp-sales 发了邮件，导致 `gmail_message_not_sent_to` 失败”
- ❌ “模型不够聪明”

## 什么时候可以放量

同时满足：

- 18 题里，每一道失败都能说清原因；
- 失败类型不超过 5–6 类；
- 没有环境/工具/断言的系统性 bug；
- 同一配置重复跑一次，结果大致稳定。

## 变量控制

- 小批量、中批量、全量**必须用同一个模型、同一套参数**；
- 一次只改一个东西（模型、prompt、max_steps、toolset）；
- 每次运行都在 `results/<name>/manifest.json` 里记录了命令和配置，报告里要引用它。

## 成本控制

1. smoke 5 题；
2. small 18 题；
3. 只对失败率最高的 2 个域跑 20 题；
4. 最后才全量 600 题。

每一步都先看 `reports/<name>.md` 的 token 和 cost，再决定是否继续。
