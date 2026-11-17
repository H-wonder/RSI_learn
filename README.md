# AutomationBench Baseline

AutomationBench 基线实验的代码、运行记录和分析报告。仓库只包含我们自己写的代码与结果摘要，不包含数据集本身。

远程仓库：[https://github.com/H-wonder/RSI_learn](https://github.com/H-wonder/RSI_learn)

## 任务一交付物

- **PDF 报告（根目录）**：[AutomationBench-Baseline-Report.pdf](AutomationBench-Baseline-Report.pdf)（23 页）
- **LaTeX 源码**：[reports/report.tex](reports/report.tex)
- **实验数据**：[reports/medium-60.tasks.csv](reports/medium-60.tasks.csv)、[reports/medium-60.issues.csv](reports/medium-60.issues.csv)
- **重新生成 PDF**：`scripts/build_pdf.sh`（需要 XeLaTeX + ctex）

## 重要说明：与官方榜单的差异

官方 README 的 public 600 题榜单使用**最高 reasoning effort**（GPT-5.6 Sol 45.83%）。
本仓库的 60 题运行**没有显式设置 reasoning effort**，所以 11.7% 不能直接对标官方。

3 题校准（其余配置不变，只加 `--reasoning-effort max`）：

| 任务 | 默认 effort | max effort |
|---|---:|---:|
| multi_hop_lookup | 0.000 | 0.667 |
| sheets_reconciliation | 0.250 | 1.000 |
| vendor_compliance_audit | 0.000 | 0.333 |
| 平均部分分 | 0.083 | **0.667** |
| 通过数 | 0/3 | **1/3** |

因此 11.7% 是**默认 effort 下的下界**。下一步应使用 max effort 重跑 60 题（约 $50–70，1–1.5 小时），
重跑后的数字才能与官方榜单做方向性比较。`configs/` 已默认写入 `reasoning_effort: max`。

## 这个仓库解决什么

基线不是“跑一次拿个分数”，而是：

1. **小批量**跑通，记录每个失败任务卡在哪条断言；
2. **归因**：把失败分成若干类，统计比例；
3. 确认问题后，再**放量**跑，看比例是否稳定；
4. 最后产出**可复现的命令 + 结果表 + 失败分析报告**。

具体流程见 [docs/workflow.md](docs/workflow.md)。

## 基线代码说明

本仓库的 baseline 是官方 AutomationBench 的 direct agent（`auto-bench` CLI），不是我们重写的 agent loop。我们提供的是：

- 按域运行、复用、合并的 wrapper 与 `configs/`；
- 结果分析、失败归类、问题类型汇总；
- 60 题标注、失败案例与报告。

上游代码：[zapier/AutomationBench](https://github.com/zapier/AutomationBench)（本报告基于 commit `4a8e106`）。复现需要 clone 上游数据集仓库；本仓库不重复打包数据集和模型客户端。

## 实验结果在哪里

- **23 页报告**：根目录 [AutomationBench-Baseline-Report.pdf](AutomationBench-Baseline-Report.pdf)
- **完整分析**：[reports/medium-60.md](reports/medium-60.md)
- **逐题结果 / 失败断言**：[medium-60.tasks.csv](reports/medium-60.tasks.csv)、[medium-60.issues.csv](reports/medium-60.issues.csv)
- **紧凑结果 JSON**：[medium-60.compact.json](reports/medium-60.compact.json)、[small-18.compact.json](reports/small-18.compact.json)
- **运行配置与成本**：[reports/run-manifest.md](reports/run-manifest.md)
- **完整轨迹**：[reports/raw-results-2026-11-17.tar.gz](reports/raw-results-2026-11-17.tar.gz)（1.3MB，含 small/medium 的完整对话 JSON）
- **14 个失败案例**：[experiments/exp-002-small/failure-analysis.md](experiments/exp-002-small/failure-analysis.md)

## 目录

```
automationbench-baseline/
├── AutomationBench-Baseline-Report.pdf   # 任务一 PDF 交付物
├── README.md
├── configs/                 # smoke / small / medium / full 配置
├── scripts/
│   ├── check_env.py         # 环境自检（不需要 API）
│   ├── run_batch.py         # 按域批量跑基线，保存 JSON + 日志 + manifest
│   ├── select_tasks.py      # 从数据集里抽样任务
│   ├── analyze_results.py   # 指标、失败类型、问题比例、报告
│   ├── analyze_by_type.py   # 结果 × 标注 → 问题类型 × 通过率（表 2）
│   ├── apply_ai_labels.py   # 合并标注 JSON 到 CSV
│   ├── annotation_summary.py# 标注分布统计
│   ├── export_for_labeling.py # 导出 60 题完整信息
│   ├── dataset_stats.py     # 重算数据集规模/复杂度
│   ├── inspect_task.py      # 查看一道题的 prompt/工具/断言
│   ├── build_report.py      # 从结果 CSV 生成 LaTeX 表格/图
│   └── build_pdf.sh         # 用 XeLaTeX 编译 PDF
├── docs/
│   ├── workflow.md          # 小批量→记录→放量
│   ├── failure-taxonomy.md  # 失败分类标准
│   ├── metrics.md           # 指标与“免费断言”
│   ├── dataset-card.md      # 数据集规模/复杂度
│   ├── problem-taxonomy.md  # P1–P9 问题分类
│   ├── how-to-review-labels.md # 怎么复核 P1–P9 标注
│   ├── experiment-tables.md # 表 1/2/3/4 模板
│   ├── structure-validation-plan.md # 在 rsi-flow 里验证结构的方案
│   ├── reproduce.md         # 从零复现步骤
│   └── report-template.md   # 报告模板
├── experiments/             # smoke / small / medium 的实验记录与失败案例
├── data/annotation/         # 60 题标注表与标签 JSON
├── results/                 # 运行结果 JSON（不入 git）
├── logs/                    # 运行日志（不入 git）
├── reports/                 # markdown / csv / LaTeX / compact JSON / run manifest
└── tests/fixtures/          # 分析脚本测试样本
```

## 前置

- 数据集：`../datasets/AutomationBench`（可用 `--dataset-dir` 指定）
- Python 3.13 + uv
- 模型：`gpt-5.6-sol`，base URL `https://intlapi.thingo.com.cn/v1`
- JDK/Java 与基线无关；rsi-flow 在另一个仓库

```bash
export PATH="$HOME/.local/bin:$PATH"
cd ../datasets/AutomationBench && uv sync
```

从零复现（含 clone 上游、`.env`、代理、完整命令）见 [docs/reproduce.md](docs/reproduce.md)。

运行前加载 key，并清掉会干扰 httpx 的 SOCKS 代理：

```bash
cd ../automationbench-baseline
unset ALL_PROXY HTTP_PROXY HTTPS_PROXY all_proxy http_proxy https_proxy
set -a; . ./.env; set +a
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

### 2）小批量：18 题（与 60 题标注样本对齐）

```bash
python scripts/run_batch.py --name small \
  --tasks-file data/tasks/small_from_annotation.csv
python scripts/analyze_results.py --dir results/small \
  --out-md reports/small.md --out-issues reports/small.issues.csv \
  --out-tasks reports/small.tasks.csv
```

跑完后先看 `experiments/exp-002-small/issues.md`，确认失败原因再放量。

### 3）中批量：60 题（复用 small 的 12 题，只跑缺的 48 题）

```bash
python scripts/run_batch.py --name medium \
  --tasks-file data/tasks/medium_missing.csv

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

### 4）生成 PDF

```bash
python scripts/build_report.py   # 从 CSV 生成 tex 表格/图
scripts/build_pdf.sh             # XeLaTeX 编译并复制到根目录
```

产物：根目录 `AutomationBench-Baseline-Report.pdf`。

### 5）全量（未跑，需预算）

```bash
python scripts/run_batch.py --name full --domains all --per-domain 100
```

按 60 题 $71.78 估算，全量约 $700。

## 结果分析器会输出什么

- 总体：通过率、平均部分分、步数、token、成本
- 分域：每个域的通过率/部分分
- 部分分分布：0、0–0.5、0.5–1、1 各多少
- 失败类型占比：漏建记录、漏发消息、多做、值写错等
- 失败断言 Top N
- 每个失败任务的逐条断言明细（CSV）

## 安全约定

- API key 只放在本地 `.env`（已被 `.gitignore` 忽略），不要提交、不要贴进报告。
- `results/`、`logs/` 默认不入 git（可能很大，且含完整对话）。
- 本仓库不放内网 `settings.xml`、`.env`、私钥。

## 现状

- [x] 仓库结构、运行脚本、分析脚本
- [x] 数据集卡片、P1–P9 分类、60 题标注
- [x] 18 题小批量与失败记录
- [x] 60 题正式基线（11.7% 通过，部分分 0.509）
- [x] 14 个失败案例与根因分析
- [x] 23 页 PDF 报告（根目录）
- [x] 紧凑结果 JSON + 运行清单（run manifest）
- [x] 完整轨迹归档（1.3MB tarball）
- [x] 从零复现文档
- [ ] 全量 600 题（约 $700，待预算）
- [ ] 任务二：rsi-flow 结构实现
