# 基线实验报告模板

> 复制本文件到 `reports/final-report.md` 后填写。每个数字都必须能追到 `results/` 下的 JSON。

## 1. 实验目的

- 要回答的问题：
- 预期：

## 2. 环境与配置

| 项 | 值 |
|---|---|
| 模型 |  |
| base_url |  |
| toolset | api |
| max_steps | 50 |
| max_concurrent |  |
| benchmark 版本 | 结果 JSON 的 `meta.benchmark_version` |
| 运行日期 |  |
| 命令 | 见 `results/<name>/manifest.json` |

## 3. 数据切片

| 项 | 值 |
|---|---|
| 域 | sales, marketing, ... |
| 每域题数 |  |
| 总题数 |  |
| 是否包含 simple | 否（不计分） |
| 抽样方式 | 前 N / 均匀抽样 / 指定任务 |

## 4. 总体结果

| 指标 | 值 |
|---|---:|
| 通过率 |  |
| 平均部分分 |  |
| 平均步数 |  |
| input tokens |  |
| output tokens |  |
| 成本 |  |

## 5. 分域结果

| 域 | n | 通过率 | 部分分 | 平均步数 |
|---|---:|---:|---:|---:|
| sales |  |  |  |  |
| marketing |  |  |  |  |
| operations |  |  |  |  |
| support |  |  |  |  |
| finance |  |  |  |  |
| hr |  |  |  |  |

## 6. 失败分析

### 6.1 失败类型占比

| 类别 | 失败断言数 | 占比 | 受影响任务数 | 任务占比 |
|---|---:|---:|---:|---:|
| extra_or_unwanted_action |  |  |  |  |
| missing_record |  |  |  |  |
| missing_message_or_note |  |  |  |  |
| wrong_value_or_state |  |  |  |  |
| wrong_count |  |  |  |  |
| missing_content |  |  |  |  |
| other |  |  |  |  |

### 6.2 高频失败断言

| 断言类型 | 次数 | 说明 |
|---|---:|---|
|  |  |  |

### 6.3 典型失败案例

| 任务 | 现象 | 根因 | 证据（断言/工具调用） |
|---|---|---|---|
|  |  |  |  |

## 7. 小批量 vs 放量

| 阶段 | n | 通过率 | 部分分 | 主要失败类型 |
|---|---:|---:|---:|---|
| small（3/域） | 18 |  |  |  |
| medium（10/域） | 60 |  |  |  |
| full（100/域） | 600 |  |  |  |

> 如果 small 和 full 的失败类型比例差异很大，说明样本不稳，需要增加样本或检查数据切片。

## 8. 结论

- 基线是否达到预期：
- 最大的 3 个问题：
- 对后续“结构化流程”的启示：
- 下一步：

## 9. 附录

- 结果文件清单
- 问题记录：`reports/<name>.issues.csv`
- 运行日志：`logs/<name>/`
