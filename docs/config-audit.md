# 配置核对：官方要求 vs 本仓库

> 这份文档回答一个问题：我们的基线到底有没有对齐官方配置？
> 每个结论都给出源码位置或实测证据，避免再次出现“跑完才发现配置不对”。

## 1. 官方口径

来源：`datasets/AutomationBench`，commit `4a8e106`，benchmark version `1.0.6`。

| 项目 | 官方值 | 依据 |
|---|---|---|
| 公开集规模 | 600 题 = 6 域 × 100 | README「Public vs. Official Scores」 |
| 计分方式 | `task_completed_correctly` 的均值；`simple` 不计分 | README「Scoring」 |
| 参考成绩 | GPT-5.6 Sol **45.83%** | README 的 public 600 表 |
| reasoning effort | 每个模型使用**最高可用** effort；GPT-5.6 Sol 标为 `max` | README 表头与表体 |
| toolset | `api` | `--toolset` 默认值 |
| 最大步数 | 50 | `--max-steps` 默认值 |
| API 路径 | `auto` → 非 Anthropic/Gemini 模型走 **Chat Completions** | `eval.py::_resolve_api` |
| 温度等采样参数 | 未显式设置，使用框架默认 | `eval.py` 只设置 `reasoning_effort` |

**重要区分**：官方排名榜（zapier.com/benchmarks）用的是**私有 held-out 集**；
README 里的 45.83% 是**public 600 题**的成绩。两者不是 1:1，公开集只能做方向性比较。
本地能跑到的上限就是 public 600，本仓库的 60 题又是其中一个子样本。

## 2. 我们的配置

`configs/medium.json`：

```json
{
  "model": "gpt-5.6-sol",
  "base_url": "https://intlapi.thingo.com.cn/v1",
  "api": "chat_completions",
  "toolset": "api",
  "max_steps": 50,
  "max_concurrent": 5,
  "reasoning_effort": "max"
}
```

逐项对齐：

| 项目 | 官方 | 我们 | 是否一致 |
|---|---|---|---|
| 模型 | `gpt-5.6-sol` | `gpt-5.6-sol` | 是 |
| reasoning effort | 最高可用（`max`） | `max` | 是 |
| toolset | `api` | `api` | 是 |
| max_steps | 50 | 50 | 是 |
| 数据集版本 | 1.0.6 / `4a8e106` | 同 | 是 |
| API 路径 | 默认 Chat Completions | 显式 `chat_completions` | 是 |
| 计分 | `task_completed_correctly` | 直接读官方导出的 `score` / `passed` | 是 |
| 题量 | 600 | 60（6 域 × 10，固定间隔） | 否（样本） |
| 服务商 | 官方直连 | 中转站 | 未知（残余风险） |

## 3. 实测：`max` 不是摆设

担心点：CLI 帮助里写“OpenAI: none/minimal/low/medium/high/xhigh”，`max` 只列在
Claude 一侧；如果中转站静默忽略 `max`，校准的提升就可能只是随机波动。

2026-11-17 直接探测 `https://intlapi.thingo.com.cn/v1/chat/completions`（同一模型）：

| `reasoning_effort` | HTTP | reasoning tokens |
|---|---:|---:|
| 不传 | 200 | 21 |
| `low` | 200 | 40 |
| `high` | 200 | 22 |
| `xhigh` | 200 | 40 |
| `max` | 200 | 37 |
| `bogus` | 502 | — |

结论：合法值都被接受，非法值被拒绝（不是静默降级）；`max` 确实被转发。

更强的证据是 3 题校准的同一批任务：

| 任务 | 默认 effort 输出 token / 模型耗时 | max effort 输出 token / 模型耗时 |
|---|---:|---:|
| `sales.multi_hop_lookup` | 1,446 / 66.6s | 6,137 / 175.2s |
| `sales.sheets_reconciliation` | 1,241 / 73.4s | 5,692 / 289.3s |
| `operations.vendor_compliance_audit` | 1,003 / 55.8s | 5,668 / 181.7s |

输出 token 约 4–5 倍、耗时约 3–5 倍，说明 `max` 真正改变了推理预算。

## 4. 实测：Responses API 也可用，但我们不用

中转站同时支持：

- `POST /v1/chat/completions`
- `POST /v1/responses`

官方 CLI 的 `--api` 默认是 `auto`，对本模型解析为 `chat_completions`；
README 的用法示例也没有传 `--api responses`。因此我们显式固定
`chat_completions`，与官方默认路径一致。若未来官方改用 Responses API，
只需把配置里的 `api` 改成 `responses` 并重跑，脚本无需改动。

## 5. `--tasks` 模式的隐患

`auto-bench` 的 `--ensure-complete`（自动补跑中断任务）只在**全量运行**时启用；
用 `--tasks` 跑固定样本时会跳过。也就是说，一次网络中断可能被静默记成 0 分。

处理：

1. 每次跑完执行 `python scripts/check_aborts.py --dir results/<name>`；
2. 健康任务的最后一条消息应是**不带 tool call 的 assistant 文本**；
3. 若发现 abort，用 `--out-csv` 生成重跑清单，再跑一次。

历史 60 题（default effort）检查结果：74 个任务文件、0 个 abort、0 个 refusal。

## 6. 仍未消除的差异

1. **私有榜单**：官方排名榜用私有集，本地 public 集不可能完全复现。
2. **中转站**：模型版本、系统提示、限流、安全过滤都可能与官方直连不同。
3. **60 题样本**：固定间隔抽样，总体结构与 540 题接近，但分域有偏差（见报告表）。
4. **Chat vs Responses**：官方未公布榜单运行所用的 API 路径；我们采用 CLI 默认值。
5. **成本**：`auto-bench` 的定价表含 `gpt-5.6-sol`（\$5/M input，\$30/M output），
   但中转站的实际计费与 reasoning token 上报方式可能不同；报告中的成本是框架估算。
6. **导出字段**：上游 `_perf` 只从 Responses API 的 `output_tokens_details` 读
   reasoning tokens，Chat Completions 路径下任务的 `reasoning_tokens` 字段恒为 0；
   `output_tokens` 仍然包含推理 token（`completion_tokens`）。因此分析里不要用
   `reasoning_tokens` 判断推理量，用 `output_tokens` 与 `model_time_s` 更可靠。
