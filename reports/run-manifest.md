# 运行清单（Run Manifest）

> 这份文件回答“结果是怎么跑出来的、用了什么配置、花了多少钱”。

## 环境

| 项 | 值 |
|---|---|
| 模型 | `gpt-5.6-sol` |
| 接口 | `https://intlapi.thingo.com.cn/v1` |
| toolset | `api` |
| max_steps | 50 |
| max_concurrent | 5 |
| 数据集 | [zapier/AutomationBench](https://github.com/zapier/AutomationBench) |
| 本地数据集 commit | `4a8e106` |
| 本仓库 commit | 添加本文件时的 `git log -1` |
| 运行日期 | 2026-11-17 |

## 运行记录

### 烟测（smoke）

- 数据：`simple` 域 5 题
- 命令：`python scripts/run_batch.py --name smoke --domains simple --per-domain 5`
- 结果：3/5 通过，部分分 0.600，成本 **$1.56**
- 文件：`reports/smoke.md`、`reports/smoke.issues.csv`

### 小批量（small）

- 数据：6 域 × 3 题 = 18 题（其中 12 题属于 60 题样本）
- 命令：`python scripts/run_batch.py --name small --tasks-file data/tasks/small_from_annotation.csv`
- 结果：3/18 通过，部分分 0.561，成本 **$21.12**
- 文件：`reports/small.md`、`reports/small.tasks.csv`、`reports/small.issues.csv`

### 正式实验（medium）

- 数据：60 题标注样本 = 复用 small 的 12 题 + 补跑 48 题
- 补跑命令：`python scripts/run_batch.py --name medium --tasks-file data/tasks/medium_missing.csv`
- 合并分析命令：

```bash
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
```

- 结果：7/60 通过，通过率 **11.7%**，部分分 **0.509**，60 题成本 **$71.78**
- 分阶段成本：small 18 题 $21.12；medium 48 题 $56.26；全部运行合计约 **$77.38**

## 分析产物

| 产物 | 路径 |
|---|---|
| 23 页 PDF | `AutomationBench-Baseline-Report.pdf` |
| 完整分析 | `reports/medium-60.md` |
| 问题类型表 | `reports/medium-60.by_type.md` |
| 逐题结果 | `reports/medium-60.tasks.csv` |
| 失败断言明细 | `reports/medium-60.issues.csv` |
| 紧凑结果 JSON | `reports/medium-60.compact.json`、`reports/small-18.compact.json` |
| 完整轨迹归档 | `reports/raw-results-2026-11-17.tar.gz`（1.3MB，含完整对话 JSON） |
| 失败案例 | `experiments/exp-002-small/failure-analysis.md` |

## 未入库的内容

- `logs/` 下的运行日志（控制台输出）。
- `.env`（API key）与内网 `settings.xml`。

完整结果已压缩为 `reports/raw-results-2026-11-17.tar.gz`，解压即可看到 `results/small` 与 `results/medium`。

## 复现

见 [docs/reproduce.md](../docs/reproduce.md)。
