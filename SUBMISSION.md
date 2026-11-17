# 任务一提交清单

> 用途：让评分人一眼看到“每条要求在哪个文件、哪一章、什么状态”。
> 状态：`完成` / `进行中` / `任务二`。

## 1. 要求 → 交付物

| 要求 | 交付物 | 位置 | 状态 |
|---|---|---|---|
| 分析至少一个数据集 | 数据集卡片、规模/断言统计、public vs private 说明 | [docs/dataset-card.md](docs/dataset-card.md)、PDF 第 3 章 | 完成 |
| 学习书写第一张实验表 | 表 1–4 + “这张表怎么读” | [reports/first-experiment-table.md](reports/first-experiment-table.md)、PDF 实验设计/结果章 | 完成（max 数字） |
| 基线跑起来 | 按域 runner、配置、官方 `auto-bench` 调用、运行清单 | [scripts/run_batch.py](scripts/run_batch.py)、[configs/](configs/)、[reports/run-manifest.md](reports/run-manifest.md) | 完成（max 60 + A 组） |
| 至少 5 类问题 | P1–P9（含 P4a/P4b 拆分）+ 60/60 标注 | [docs/problem-taxonomy.md](docs/problem-taxonomy.md)、[data/annotation/tasks_to_label.csv](data/annotation/tasks_to_label.csv) | 完成 |
| 先小批量、输出记录 | 18 题过程记录（只作方法记录） | [experiments/exp-002-small/issues.md](experiments/exp-002-small/issues.md)、PDF 第 5 章 | 完成 |
| 大规模统计问题比例 | 60 题分域/分类型/失败类别 | [reports/medium-max.tasks.csv](reports/medium-max.tasks.csv)、[reports/medium-max.by_type.md](reports/medium-max.by_type.md)、PDF 结果/失败章 | 完成 |
| 详细分析为什么跑不满 | 断言级分类 + M1–M6 机制编码 + 14 个案例 | PDF 失败分析章、[docs/failure-mechanisms.md](docs/failure-mechanisms.md)、[reports/medium-max.mechanisms.md](reports/medium-max.mechanisms.md) | 完成 |
| 默认 vs max 对照 | 同一批 60 题的配对对比、McNemar、bootstrap CI | [reports/compare-default-vs-max.md](reports/compare-default-vs-max.md) | 完成 |
| refusal 敏感性 | 含 refusal / 排除 / 重跑替换三种口径；重跑 0.8、无 refusal | `results/refusal-retry/`、PDF 失败分析章 | 完成 |
| 熟悉 rsi-flow、下一步验证结构 | 构建/测试记录、3 任务 flow 设计、H1–H4、对比协议 | [docs/structure-validation-plan.md](docs/structure-validation-plan.md) | 方案完成；最小节点已实现（test 分支 20/20），完整对比待做 |
| 配置对齐官方 | public 600 表、max effort、toolset、max_steps、API 路径逐项核对 | [docs/config-audit.md](docs/config-audit.md)、PDF 第 4/7 章 | 完成 |
| 可复现 | 从零复现步骤、run manifest、原始轨迹 | [docs/reproduce.md](docs/reproduce.md)、[reports/raw-results-2026-11-18.tar.gz](reports/raw-results-2026-11-18.tar.gz) | 完成 |

## 2. 基线代码在哪里

- **官方 direct agent**：上游 [`zapier/AutomationBench`](https://github.com/zapier/AutomationBench) 的 `auto-bench` CLI。
  任务一要求“把基线跑起来”，不是重写 agent；
- **我们写的**：
  - [scripts/run_batch.py](scripts/run_batch.py)：按域运行、复用/合并、`max` effort、API 路径、manifest；
  - [configs/](configs/)：smoke/small/medium/full 的精确配置；
  - [scripts/analyze_results.py](scripts/analyze_results.py)、[scripts/analyze_by_type.py](scripts/analyze_by_type.py)：指标、失败类别、P1–P9；
  - [scripts/compare_runs.py](scripts/compare_runs.py)：默认 effort vs max 的配对对比（McNemar + bootstrap CI）；
  - [scripts/check_aborts.py](scripts/check_aborts.py)：中断任务检查；
  - 60 题标注、失败案例、报告与 PDF。
- **任务二**：在 rsi-flow 里实现 `LlmNode`/`ToolNode`/`FinalActionNode`/`VerifierNode`，
  做 direct vs structured 对比；计划见 [docs/structure-validation-plan.md](docs/structure-validation-plan.md)。

## 3. 提交包结构

```text
automationbench-baseline/
├── AutomationBench-Baseline-Report.pdf   # 主报告
├── README.md                             # 导航
├── SUBMISSION.md                         # 本清单
├── configs/                              # 精确配置
├── scripts/                              # runner + 分析 + 对比 + 检查
├── data/annotation/                      # P1–P9（含 P4a/P4b）标注
├── reports/
│   ├── first-experiment-table.md         # 第一张实验表 + 读表说明
│   ├── medium-max/                       # max 60 题结果（生成后）
│   ├── compare-default-vs-max.md         # 配置配对对比
│   ├── run-manifest.md                   # 配置/命令/成本
│   └── raw-results-2026-11-18.tar.gz     # 原始轨迹
├── experiments/exp-002-small/issues.md   # 小批量过程记录
└── docs/
    ├── dataset-card.md
    ├── problem-taxonomy.md               # P1–P9 + P4 子类
    ├── failure-mechanisms.md             # M1–M6 编码手册
    ├── structure-validation-plan.md      # 任务二方案
    ├── config-audit.md                   # 官方配置核对
    └── reproduce.md
```

## 4. 三条结论（写报告时用）

1. **基线不是“跑一次”**：配置对齐（max effort / chat_completions / api / 50 steps）
   是外部效度的前提；默认 effort 的 11.7% 只作对照，不作官方可比基线。
2. **失败不是“模型笨”**：六条机制（M1 工具选择、M2 规则判定、M3 路由、M4 长链、
   M5 负约束、M6 收尾）把断言失败映射到可干预的结构缺口。
3. **结构验证要有假设**：H1–H4 + 步数对照 + 节点消融，避免把“多跑几步”误判成
   “结构有用”。
