# 运行清单（Run Manifest）

> 这份文件回答“结果是怎么跑出来的、用了什么配置、花了多少钱”。
> 所有数字都能追到 `results/<name>/*.json`。

## 环境

| 项 | 值 |
|---|---|
| 模型 | `gpt-5.6-sol` |
| 接口 | `https://intlapi.thingo.com.cn/v1` |
| API 路径 | `chat_completions`（官方 CLI 默认） |
| toolset | `api`（官方默认） |
| reasoning effort | `max`（官方要求最高可用） |
| max_steps | 50（官方默认） |
| max_concurrent | 5 |
| 数据集 | [zapier/AutomationBench](https://github.com/zapier/AutomationBench) |
| 本地数据集 commit | `4a8e106` |
| benchmark 版本 | `1.0.6` |
| 主运行日期 | 2026-11-17 22:03 – 2026-11-18 00:47 |

## 运行记录

### 烟测（smoke）

- 数据：`simple` 域 5 题（不计分）
- 结果：3/5 通过，部分分 0.600，成本 **$1.56**
- 文件：`reports/smoke.md`

### 小批量（small，过程记录）

- 数据：6 域 × 3 题 = 18 题（默认 effort）
- 结果：3/18 通过，部分分 0.561，成本 **$21.12**
- 用途：只暴露工具/数据源/收尾问题，**不作为最终比例**
- 文件：`reports/small.md`、`experiments/exp-002-small/issues.md`

### A 组：默认 effort 的 60 题

- 数据：60 题标注样本 = 复用 small 的 12 题 + 补跑 48 题
- 配置：**没有显式设置 reasoning effort**
- 结果：7/60 通过，通过率 **11.7%**，部分分 **0.509**，成本 **$71.78**
- 用途：配置失误的对照；**不是官方可比基线**
- 文件：`results/small/`、`results/medium/`

### 校准：max effort（3 题）

- 任务：`sales.multi_hop_lookup`、`sales.sheets_reconciliation`、
  `operations.vendor_compliance_audit`
- 结果：默认 effort 平均部分分 0.083、通过 0/3；max 为 0.667、通过 1/3；
  输出 token 约 4–5 倍、模型耗时 3–5 倍；成本 **$2.59**
- 文件：`results/calibration-max/calib.json`

### 主结果：max effort 的 60 题

- 数据：60 题标注样本，**全部重跑**，不复用默认 effort 的任何一题
- 命令：

```bash
python scripts/run_batch.py \
  --name medium-max --config configs/medium.json \
  --tasks-file data/tasks/medium_from_annotation.csv
```

- 结果：**20/60 通过（33.3%，95% CI [22.7, 45.9]）**，
  部分分 **0.715**，成本上界 **$120.41**
- cached input：19,060,629 / 20,584,480（**92.6%**）；
  若按缓存价 10% 估算，约 **$34.63**
- refusal：1 个（`operations.drive_slack_dock_schedule` 见下）
- 文件：`results/medium-max/`

### 默认 vs max 配对对比

- 同一批 60 题，唯一变化是 reasoning effort
- 通过率 11.7% → 33.3%（+21.7 pp）
- McNemar 精确检验 **p = 0.00098**
- 14 题失败→通过，1 题通过→失败（`finance.revenue_recognition`）
- 部分分 0.509 → 0.715，配对差 +0.206，95% bootstrap CI [+0.112, +0.303]
- 文件：`reports/compare-default-vs-max.md`

### refusal 与重跑

- 任务：`operations.drive_slack_dock_schedule`
- 默认 effort 下得分 0.8；max 运行在第 23 步被中转站安全分类器中断，
  `stop_reason=refusal`，按官方语义记 0
- 单独重跑一次：**成功，0.8，10 步，无 refusal**；成本 $0.97
- 文件：`results/refusal-retry/operations.json`（独立目录，不覆盖主结果）
- 敏感性分析：
  - 含 refusal（n=60）：33.3% / 0.715
  - 排除（n=59）：33.9% / 0.727
  - 重跑替换（n=60）：33.3% / 0.728

## 分析产物

| 产物 | 路径 |
|---|---|
| PDF 报告 | `AutomationBench-Baseline-Report.pdf` |
| 完整分析 | `reports/medium-max.md` |
| 问题类型表 | `reports/medium-max.by_type.md` |
| 逐题结果 | `reports/medium-max.tasks.csv` |
| 失败断言明细 | `reports/medium-max.issues.csv` |
| 机制编码 | `reports/medium-max.mechanisms.csv` |
| 默认 vs max | `reports/compare-default-vs-max.md` |
| 紧凑结果 JSON | `reports/medium-max-60.compact.json` |
| 完整轨迹归档 | `reports/raw-results-2026-11-18.tar.gz` |

## 未入库的内容

- `logs/` 下的运行日志；
- `.env`（API key）与内网 `ziyuan/settings.xml`；
- `results/` 下的完整对话 JSON（已压缩进 raw archive）。

## 复现

见 [docs/reproduce.md](../docs/reproduce.md) 与
[docs/config-audit.md](../docs/config-audit.md)。
