# AutomationBench Baseline

AutomationBench 基线实验的代码、运行记录和分析报告。仓库只包含我们自己写的代码与结果摘要，不包含数据集本身。

## 这个仓库解决什么

基线不是"跑一次拿个分数"，而是：

1. **小批量**跑通，记录每个失败任务卡在哪条断言；
2. **归因**：把失败分成若干类，统计比例；
3. 确认问题后，再**放量**跑，看比例是否稳定；
4. 最后产出**可复现的命令 + 结果表 + 失败分析报告**。

具体流程见 [docs/workflow.md](docs/workflow.md)。

## 目录

```
automationbench-baseline/
├── README.md
├── configs/                 # smoke / small / full 三套配置
├── scripts/
│   ├── check_env.py         # 运行前环境自检（不需要 API）
│   ├── run_batch.py         # 按域批量跑基线，保存 JSON + 日志 + manifest
│   ├── select_tasks.py      # 从数据集里均匀抽样任务，生成任务清单
│   ├── analyze_results.py   # 结果分析：指标、失败类型、问题比例、报告
│   ├── analyze_by_type.py   # 结果 × 标注 → 问题类型 × 通过率（表 2）
│   ├── dataset_stats.py     # 重算数据集规模/复杂度（不需要 API）
│   └── inspect_task.py      # 查看一道题的完整 prompt/工具/断言
├── docs/
│   ├── workflow.md          # 小批量→记录→放量的流程
│   ├── failure-taxonomy.md  # 失败分类标准
│   ├── metrics.md           # 两个指标与"免费断言"的解释
│   ├── dataset-card.md      # 数据集规模/复杂度
│   ├── problem-taxonomy.md  # P1–P9 问题分类
│   ├── how-to-review-labels.md # 怎么复核 P1–P9 标注
│   ├── experiment-tables.md # 表 1/2/3/4 模板
│   └── report-template.md   # 最终报告模板
├── experiments/             # 每次实验的 README 与问题记录
├── data/annotation/         # 60 题人工标注表
├── results/                 # 运行结果 JSON（默认不入 git）
├── logs/                    # 运行日志（默认不入 git）
├── reports/                 # 生成的 markdown / csv 报告（入 git）
└── tests/fixtures/          # 分析脚本的测试样本
```

## 前置

- 数据集：`../datasets/AutomationBench`（可用 `--dataset-dir` 指定）
- Python 3.13 + uv
- JDK/Java 与基线无关；rsi-flow 在另一个仓库

```bash
export PATH="$HOME/.local/bin:$PATH"
cd ../datasets/AutomationBench && uv sync
```

## 快速开始

### 0）环境自检（不需要 API）

```bash
python scripts/check_env.py
```

### 1）烟测：simple 域 5 题

```bash
python scripts/run_batch.py --name smoke --domains simple --per-domain 5
```

### 2）小批量：每域 3 题，共 18 题

```bash
python scripts/run_batch.py --name small --tasks-file data/tasks/small_from_annotation.csv
python scripts/analyze_results.py --dir results/small \
  --out-md reports/small.md --out-issues reports/small.issues.csv
```

小批量跑完，先填 [experiments/exp-002-small/issues.md](experiments/exp-002-small/issues.md)，再决定是否放量。

### 3）中批量 / 全量

```bash
python scripts/run_batch.py --name medium --domains all --per-domain 10
python scripts/run_batch.py --name full --domains all --per-domain 100
```

### 4）生成报告

```bash
python scripts/analyze_results.py --dir results/full \
  --out-md reports/full.md --out-issues reports/full.issues.csv

# 标注表填完后，生成“问题类型 × 通过率”（表 2）
python scripts/analyze_by_type.py --dir results/full \
  --annotation data/annotation/tasks_to_label.csv \
  --out-md reports/full.by_type.md --out-csv reports/full.by_type.csv
```

## 结果分析器会输出什么

- 总体：通过率、平均部分分、步数、token、成本
- 分域：每个域的通过率/部分分
- 部分分分布：0、0–0.5、0.5–1、1 各多少
- 失败类型占比：多做事、漏记录、值写错、漏通知、数量不对等
- 失败断言 Top N
- 每个失败任务的逐条断言明细（CSV，便于人工写原因）

## 安全约定

- **不要把 API key 写进任何文件**；用环境变量 `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`。
- `results/`、`logs/` 默认不入 git（可能很大，且含完整对话）。
- 本仓库不放内网 `settings.xml`、`.env`、私钥。

## 现状

- [x] 仓库结构、运行脚本、分析脚本、报告模板
- [x] 数据集卡片、问题分类、标注表
- [ ] 烟测 / 小批量（等 API key）
- [ ] 失败归因记录、放量、最终报告
