# AutomationBench 基线实验报告（max 60 题）

> 完整版：根目录 [AutomationBench-Baseline-Report.pdf](../AutomationBench-Baseline-Report.pdf)（30 页，XeLaTeX）。
> 本文是仓库内的 Markdown 摘要；所有数字以 PDF、CSV 和 `results/medium-max/*.json` 为准。

## 1. 配置

| 项 | 值 |
|---|---|
| 模型 | `gpt-5.6-sol` |
| base_url | `https://intlapi.thingo.com.cn/v1` |
| API 路径 | `chat_completions`（官方 CLI 默认） |
| toolset | `api` |
| reasoning effort | `max`（官方要求最高可用） |
| max_steps | 50 |
| 数据 | public，6 域 × 10 题 = 60 |
| benchmark | `1.0.6` / `4a8e106` |

## 2. 主结果

| 指标 | 默认 effort（A 组） | `max` effort（主结果） |
|---|---:|---:|
| 通过率 | 11.7%（7/60） | **33.3%（20/60，95% CI [22.7, 45.9]）** |
| 平均部分分 | 0.509 | **0.715** |
| 平均步数 | 15.2 | 15.2 |
| 平均输出 token | 2,982 | 9,714 |
| 成本（框架上界） | $71.78 | **$120.41** |

配对对比：+21.7 个百分点，McNemar **p = 0.00098**；14 题失败→通过，
1 题通过→失败。部分分配对差 +0.206，95% bootstrap CI [+0.112, +0.303]。
cached input 占 92.6%，按缓存价 10% 估算约 $34.63。
1 个 refusal（`operations.drive_slack_dock_schedule`）按 0 分计入；重跑成功 0.8、无 refusal。
敏感性：含 refusal 33.3% / 0.715，排除 33.9% / 0.727，替换 33.3% / 0.728。

## 3. 分域与问题类型

| 域 | 通过率 | 部分分 |
|---|---:|---:|
| marketing | 50.0% | 0.891 |
| finance | 40.0% | 0.670 |
| hr | 40.0% | 0.677 |
| operations | 30.0% | 0.680 |
| support | 30.0% | 0.865 |
| sales | 10.0% | 0.507 |

P4a 资格筛选 56.2%、P4b 分支路由 33.3%、P8 41.7%、P3 14.3%、P2 10.0%、
P9 0%。完整表见 [medium-max.by_type.md](medium-max.by_type.md)。

## 4. 失败机制

40 个失败任务（含 1 个 refusal）的主机制：

| 机制 | 任务数 | 占失败任务 |
|---|---:|---:|
| M4 长链/最后动作 | 16 | 40.0% |
| M6 收尾校验 | 8 | 20.0% |
| M1 工具/数据源 | 4 | 10.0% |
| M3 路由/优先级 | 4 | 10.0% |
| M5 集合/负约束 | 4 | 10.0% |
| M2 规则/资格 | 3 | 7.5% |
| R refusal | 1 | 2.5% |

M4 + M6 = 60%：先做 FinalActionNode + VerifierNode，再做路由与工具绑定。
逐题编码见 [medium-max.mechanisms.csv](medium-max.mechanisms.csv)。

## 5. 文件索引

- PDF：[../AutomationBench-Baseline-Report.pdf](../AutomationBench-Baseline-Report.pdf)
- 主结果分析：[medium-max.md](medium-max.md)
- 逐题 / 失败断言：[medium-max.tasks.csv](medium-max.tasks.csv)、[medium-max.issues.csv](medium-max.issues.csv)
- 默认 vs max：[compare-default-vs-max.md](compare-default-vs-max.md)
- 运行清单：[run-manifest.md](run-manifest.md)
- 机制编码：[medium-max.mechanisms.csv](medium-max.mechanisms.csv)
