# AutomationBench Baseline

AutomationBench 基线实验的代码、运行记录和分析报告。仓库只包含我们自己写的代码与结果摘要，不包含数据集本身。

远程仓库：[https://github.com/H-wonder/RSI_learn](https://github.com/H-wonder/RSI_learn)

提交清单（要求 → 文件 → 状态）：[SUBMISSION.md](SUBMISSION.md)

## 任务一交付物

- **PDF 报告（根目录）**：[AutomationBench-Baseline-Report.pdf](AutomationBench-Baseline-Report.pdf)（30 页）
- **LaTeX 源码**：[reports/report.tex](reports/report.tex)
- **主结果**：[reports/medium-max.tasks.csv](reports/medium-max.tasks.csv)、[reports/medium-max.issues.csv](reports/medium-max.issues.csv)
- **默认 vs max**：[reports/compare-default-vs-max.md](reports/compare-default-vs-max.md)
- **机制编码**：[reports/medium-max.mechanisms.md](reports/medium-max.mechanisms.md)
- **重新生成 PDF**：`scripts/build_pdf.sh`（需要 XeLaTeX + ctex）

## 主结果（max effort，60 题）

| 指标 | 默认 effort（A 组） | `max` effort（主结果） |
|---|---:|---:|
| 通过率 | 11.7%（7/60） | **33.3%（20/60，95% CI [22.7, 45.9]）** |
| 平均部分分 | 0.509 | **0.715** |
| 平均步数 | 15.2 | 15.2 |
| 平均输出 token | 2,982 | 9,714 |
| 成本（框架上界） | $71.78 | **$120.41** |

同一批 60 题的配对对比：+21.7 个百分点，McNemar **p = 0.00098**；
14 题失败→通过，1 题通过→失败。部分分配对差 +0.206，95% bootstrap CI [+0.112, +0.303]。

> 成本是“所有 input 按原价”的上界；cached input 占 **92.6%**，按缓存价 10% 估算约 **$34.63**，
> 真实账单以中转站为准。
>
> 1 个任务被中转站安全分类器 refusal（`operations.drive_slack_dock_schedule`），
> 按 0 分计入；单独重跑成功（0.8，无 refusal）。敏感性分析：含 refusal 33.3% / 0.715，
> 排除 33.9% / 0.727，替换 33.3% / 0.728——通过率结论不变。

## 重要说明：与官方参考成绩的差异

官方 README 的 public 600 题榜单使用**最高 reasoning effort**（GPT-5.6 Sol 45.83%）。
需要区分：官方排名榜（zapier.com/benchmarks）用的是**私有 held-out 集**，README 里的
45.83% 是 **public 600 题**成绩；本地只能跑 public，因此只能做方向性比较。

本仓库第一次 60 题运行**没有显式设置 reasoning effort**，得到 11.7%，不能直接对标官方。
之后做了配置核对与校准，并用 `max` 重跑了全部 60 题；**主结果以 max 重跑为准**，
默认 effort 的 11.7% 保留为 A 组对照。配置核对与实测证据见
[docs/config-audit.md](docs/config-audit.md)。

3 题校准（其余配置不变，只加 `--reasoning-effort max`）：

| 任务 | 默认 effort | max effort |
|---|---:|---:|
| multi_hop_lookup | 0.000 | 0.667 |
| sheets_reconciliation | 0.250 | 1.000 |
| vendor_compliance_audit | 0.000 | 0.333 |
| 平均部分分 | 0.083 | **0.667** |
| 通过数 | 0/3 | **1/3** |

3 题样本很小，这组校准只说明**配置差异是主要原因之一**；60 题配对对比才给出主结论。
`configs/` 已默认写入 `reasoning_effort: max` 和 `api: chat_completions`；复现命令见
[docs/reproduce.md](docs/reproduce.md)。

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

- **30 页报告**：根目录 [AutomationBench-Baseline-Report.pdf](AutomationBench-Baseline-Report.pdf)
- **主结果分析**：[reports/medium-max.md](reports/medium-max.md)
- **逐题结果 / 失败断言**：[medium-max.tasks.csv](reports/medium-max.tasks.csv)、[medium-max.issues.csv](reports/medium-max.issues.csv)
- **问题类型（P4a/P4b）**：[reports/medium-max.by_type.md](reports/medium-max.by_type.md)
- **默认 vs max**：[reports/compare-default-vs-max.md](reports/compare-default-vs-max.md)
- **失败机制 M1–M6**：[reports/medium-max.mechanisms.md](reports/medium-max.mechanisms.md)
- **紧凑结果 JSON**：[medium-max-60.compact.json](reports/medium-max-60.compact.json)
- **运行配置与成本**：[reports/run-manifest.md](reports/run-manifest.md)
- **完整轨迹**：[reports/raw-results-2026-11-18.tar.gz](reports/raw-results-2026-11-18.tar.gz)（含 max / calibration / refusal 的完整对话 JSON）
- **14 个失败案例**：PDF 第 8 章
- **任务二最终结果（三个任务 + 消融）**：[reports/structured-three-tasks.md](reports/structured-three-tasks.md)
- **任务二单任务早期记录**：[reports/structured-multi-hop.md](reports/structured-multi-hop.md)

## 任务二交付物（结构化 Agent）

- **任务二 PDF（根目录）**：[Task2-Structured-Agent-Report.pdf](Task2-Structured-Agent-Report.pdf)（19 页）
- **Markdown 版结果与消融**：[reports/structured-three-tasks.md](reports/structured-three-tasks.md)
- **flow JSON 镜像**：[experiments/exp-004-structured/flows/](experiments/exp-004-structured/flows/)（五个 flow，可直接阅读）
- **逐次运行结果**：[experiments/exp-004-structured/](experiments/exp-004-structured/)
- **引擎源码镜像**：[rsi-flow-patch/](rsi-flow-patch/)（19 个节点 + 测试 + flow JSON + 修改 diff）

在 rsi-flow 的 `test` 分支实现，三个 flow 均通过 `scripts/world_bridge.py`
调用官方 WorldState 并用官方 `partial_credit` 评分：

| 任务 | direct（max） | structured | flow |
|---|---:|---:|---|
| `sales.multi_hop_lookup` | 0.333 | **1.000（3/3），×3** | 36 节点 / 44 路由 |
| `operations.generator_load_testing_schedule` | 0.857 | **1.000（7/7）** | 37 节点 / 41 路由 |
| `support.zendesk_sf_case_sync` | 0.750 | **1.000（16/16）** | 60 节点 / 70 路由 |

新增引擎节点 `LlmNode`、`ToolNode`、`FinalActionNode`、`VerifierNode`、
`RuleNode`、`FilterNode`、`RowsNode`、`WhereNode`、`AuditNode` 等；
测试 22/22。设计稿：[docs/agent-architecture-design.md](docs/agent-architecture-design.md)；
结果、消融与限制：[reports/structured-three-tasks.md](reports/structured-three-tasks.md)。

## 目录

```
automationbench-baseline/
├── AutomationBench-Baseline-Report.pdf   # 任务一 PDF 交付物
├── Task2-Structured-Agent-Report.pdf     # 任务二 PDF 交付物
├── rsi-flow-patch/         # 任务二引擎源码镜像（本地 test 分支）
├── README.md
├── configs/                 # smoke / small / medium / full 配置
├── scripts/
│   ├── check_env.py         # 环境自检（不需要 API）
│   ├── run_batch.py         # 按域批量跑基线，保存 JSON + 日志 + manifest
│   ├── select_tasks.py      # 从数据集里抽样任务
│   ├── analyze_results.py   # 指标、失败类型、问题比例、报告
│   ├── analyze_by_type.py   # 结果 × 标注 → 问题类型 × 通过率（表 2）
│   ├── check_aborts.py      # 检查中途中断（--tasks 模式不会自动补跑）
│   ├── compare_runs.py      # 两次运行的配对对比（McNemar + bootstrap CI）
│   ├── show_trace.py        # 查看单题完整轨迹
│   ├── failure_digest.py    # 一屏摘要所有失败任务，便于写案例
│   ├── apply_ai_labels.py   # 合并标注 JSON 到 CSV
│   ├── annotation_summary.py# 标注分布统计
│   ├── export_for_labeling.py # 导出 60 题完整信息
│   ├── dataset_stats.py     # 重算数据集规模/复杂度
│   ├── inspect_task.py      # 查看一道题的 prompt/工具/断言
│   ├── build_report.py      # 从结果 CSV 生成 LaTeX 表格/图
│   ├── build_pdf.sh         # 用 XeLaTeX 编译任务一 PDF
│   ├── build_task2_pdf.sh   # 用 XeLaTeX 编译任务二 PDF
│   ├── build_task2_report.py # 生成任务二节点/断言附录
│   ├── world_bridge.py      # 把 AutomationBench WorldState 暴露为本地 HTTP
│   ├── gen_ultra_flow.py    # 生成 sales 的 S0–S7 flow JSON
│   ├── gen_task_flows.py    # 生成 operations/support 的 flow JSON
│   └── gen_ablation_flows.py # 生成消融变体
├── docs/
│   ├── workflow.md          # 小批量→记录→放量
│   ├── failure-taxonomy.md  # 失败分类标准
│   ├── metrics.md           # 指标与“免费断言”
│   ├── dataset-card.md      # 数据集规模/复杂度
│   ├── problem-taxonomy.md  # P1–P9 问题分类（P4 拆成 P4a/P4b）
│   ├── failure-mechanisms.md # M1–M6 失败机制编码手册
│   ├── how-to-review-labels.md # 怎么复核 P1–P9 标注
│   ├── experiment-tables.md # 表 1/2/3/4 模板
│   ├── structure-validation-plan.md # 在 rsi-flow 里验证结构的方案
│   ├── rsi-flow-internals.md # rsi-flow 引擎结构/路由/async/scope 笔记
│   ├── agent-architecture-design.md # 任务二 S0–S7 设计与三任务落地
│   ├── config-audit.md      # 官方配置 vs 本仓库逐项核对 + 实测证据
│   ├── reproduce.md         # 从零复现步骤
│   └── report-template.md   # 报告模板
├── experiments/             # smoke / small / medium / structured 实验记录
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

### 3）主结果：60 题，max effort

```bash
python scripts/run_batch.py --name medium-max --config configs/medium.json \
  --tasks-file data/tasks/medium_from_annotation.csv

python scripts/check_aborts.py --dir results/medium-max

python scripts/analyze_results.py \
  --dir results/medium-max \
  --tasks-file data/tasks/medium_from_annotation.csv \
  --out-md reports/medium-max.md --out-issues reports/medium-max.issues.csv \
  --out-tasks reports/medium-max.tasks.csv

python scripts/analyze_by_type.py \
  --dir results/medium-max \
  --tasks-file data/tasks/medium_from_annotation.csv \
  --annotation data/annotation/tasks_to_label.csv \
  --out-md reports/medium-max.by_type.md --out-csv reports/medium-max.by_type.csv

python scripts/compare_runs.py \
  --a-dir results/small --a-dir results/medium \
  --b-dir results/medium-max \
  --tasks-file data/tasks/medium_from_annotation.csv \
  --annotation data/annotation/tasks_to_label.csv \
  --out-md reports/compare-default-vs-max.md
```

默认 effort 的旧 60 题保留在 `results/small/` + `results/medium/`，只作 A 组对照。

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

按 max 60 题的成本上界 $120.41 估算，全量 600 题约 $1,200；
按 cached input 10% 估算约 $350。跑之前先做 10 题预算检查。

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
- [x] 数据集卡片、P1–P9 分类（P4 拆成 P4a/P4b）、60 题标注
- [x] 失败机制编码 M1–M6（工具/规则/路由/长链/负约束/收尾）
- [x] 18 题小批量过程记录
- [x] **60 题 max 主结果（33.3% 通过，部分分 0.715；95% CI [22.7, 45.9]）**
- [x] 默认 vs max 配对对比（McNemar p=0.00098）
- [x] 14 个机制案例与 refusal 敏感性分析
- [x] 30 页 PDF 报告（根目录）
- [x] 紧凑结果 JSON + 运行清单（run manifest）
- [x] 完整轨迹归档（max / calibration / refusal）
- [x] 从零复现文档
- [ ] 全量 600 题（上界约 $1,200；缓存折扣后约 $350，待预算）
- [x] 任务二引擎节点：rsi-flow `test` 分支 14 个节点（含 `RowsNode`/`WhereNode`），22/22 测试通过
- [x] 任务二设计稿：S0–S7 超长 Agent 结构、3 任务实例化、H1–H4
- [x] 任务二三个 flow：`FLOW_AGENT_ULTRA`（36 节点）、`FLOW_AGENT_OPS`（37）、`FLOW_AGENT_SUPPORT`（60）
- [x] 三任务结果：direct 0.333/0.857/0.750，structured 全 1.000；sales 3 次重复
- [x] 节点消融：去掉 repair / 串行读取 / 去掉 Case 去重（0.9375）
- [x] 19 页任务二 PDF 报告（根目录）
- [ ] operations/support 各补 2 次重复；等步数对照
