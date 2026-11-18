# rsi-flow patch：任务二结构化 Agent 实现

> 这个目录是任务二在 **rsi-flow 本地 `test` 分支**上的源码镜像。
> 官方 rsi-flow 仓库没有写权限，改动没有推送到官方远程；为了让评分人
> 不切换仓库也能直接阅读实现，这里按原路径镜像了全部新增/修改的源码、
> 测试与 flow JSON。

- 基线分支：`dev_rsi`
- 实现分支：`test`
- 最新提交：`afc979b`（`3eff87e`、`2b7beab` 为前两步）
- 来源仓库：`/home/wonder/work/xinren/multi_agent/rsi-flow`

## 1. 目录内容

目录结构与 rsi-flow 仓库一致，可直接对照：

```text
rsi-flow-patch/
├── README.md
├── core-fixes.diff                     # 4 个已有文件的修改（unified diff）
├── flow-core/src/main/java/cc/eamon/open/flow/
│   ├── agent/                          # 新增的 19 个节点/工具类
│   │   ├── LlmNode.java
│   │   ├── ToolNode.java / ToolRegistry.java / ToolHandler.java
│   │   ├── FinalActionNode.java / FinalActionRegistry.java / FinalActionHandler.java
│   │   ├── VerifierNode.java
│   │   ├── RuleNode.java / FilterNode.java
│   │   ├── RowsNode.java / WhereNode.java
│   │   ├── AuditNode.java / AuditStore.java
│   │   ├── ContextSnapshotNode.java / JsonFieldNode.java
│   │   ├── Template.java
│   │   └── BridgeToolHandler.java / BridgeScoreHandler.java
│   ├── core/context/FlowScopeContext.java          # 修改：ConcurrentHashMap
│   └── core/stereotype/support/route/Executor.java # 修改：整队去重
└── flow-test/src/test/
    ├── java/cc/eamon/open/flow/FLOW_AGENT/
    │   ├── FlowAgentTest.java           # 5 个测试（tool / LLM mock / final+verifier /
    │   │                                #   rule+filter+audit / rows+where）
    │   └── UltraAgentRunner.java        # 运行器，支持 -Dflow.id
    ├── java/cc/eamon/open/flow/testng.xml
    ├── java/cc/eamon/open/flow/FLOW_SCHEDULE/FlowScheduleTest.java
    │                                    # 仅禁用（Spring 注入依赖，与 Agent 逻辑无关）
    └── resources/flow/FLOW_AGENT/       # 7 个 flow JSON（3 个任务 + 2 个消融 + 2 个冒烟）
```

`flow-agent-ultra.json`、`flow-agent-ops.json`、`flow-agent-support.json` 以及两个消融
变体在 `experiments/exp-004-structured/flows/` 下还有一份镜像，可以直接阅读。

## 2. 每个节点解决什么问题

| 节点 | 对应失败机制 | 作用 |
|---|---|---|
| `LlmNode` | — | 唯一允许调用模型的节点；输出 JSON 语义字段 |
| `ToolNode` + registry | M1 | 固定 app/action，模型不生成完整 tool 参数 |
| `FinalActionNode` | M4 | 必须执行最终动作，否则流程失败 |
| `VerifierNode` | M6 | 检查期望片段，返回 `{passed, missing}` |
| `RuleNode` | M2 | 对 JSON 上下文执行 JEXL 规则 |
| `FilterNode` | M5 | 单字段数组过滤 |
| `RowsNode` | M2 | Sheets `values` → 行对象数组 |
| `WhereNode` | M2/M5 | 行级 JEXL 过滤（列名转下划线，支持模板变量） |
| `AuditNode` | — | 每次运行的阶段审计 |
| `ContextSnapshotNode` | — | 变量快照，供 LLM 证据使用 |
| `JsonFieldNode` | — | 点路径字段提取（支持数组下标） |
| `Template` | — | `{{var}}` 文本/JSON 渲染 |
| `BridgeToolHandler` | M1 | 调本地 WorldState bridge 的工具 |
| `BridgeScoreHandler` | M6 | 读取官方 `partial_credit` 分数 |

## 3. 如何应用

```bash
# 1) 准备官方 rsi-flow，并新建 test 分支
git clone <rsi-flow>
cd rsi-flow
git checkout -b test

# 2) 覆盖/新增文件（镜像里已是修改后的完整文件，目录结构与源仓库一致）
cp -r /path/to/RSI_learn/rsi-flow-patch/flow-core   .
cp -r /path/to/RSI_learn/rsi-flow-patch/flow-test   .

# 3) core-fixes.diff 仅用于查看 4 个已有文件的改动；
#    如果你是从未修改的 dev_rsi 开始、只想要改动，可改为：
#    git apply /path/to/RSI_learn/rsi-flow-patch/core-fixes.diff

# 4) 构建与测试（需要内网 Maven settings）
../scripts/mvn-rsi.sh -pl flow-test -am test
# => Tests run: 22, Failures: 0, Errors: 0
```

复制整个镜像后不需要再执行 `git apply`；`core-fixes.diff` 只是让 4 个已有文件的
改动可审阅、可单独应用。它包含：

- `FlowScopeContext.variableMap`：`HashMap` → `ConcurrentHashMap`（并行分支写变量安全）；
- `Executor.addExecuteNode`：对整队去重（修复 async `close` 汇合点重复入队）；
- `FlowScheduleTest`：`@Test(enabled=false)`（Spring 注入依赖，与 Agent 无关）；
- `testng.xml`：把 `FlowAgentTest` 加入测试套件。

## 4. 运行 flow

见根目录 `Task2-Structured-Agent-Report.pdf` 第 11 节，或
`docs/reproduce.md` 第 9 节。三个任务的 `-Dflow.id`：

- `FLOW_AGENT_ULTRA`（sales）
- `FLOW_AGENT_OPS`（operations）
- `FLOW_AGENT_SUPPORT`（support）

## 5. 配置与安全

- LLM 节点只读环境变量 `OPENAI_BASE_URL` / `OPENAI_API_KEY`，
  key 不写入任何源码或 flow JSON；
- 本目录不包含 `ziyuan/settings.xml`（内网 Maven 凭据），
  也不包含构建产物、日志或数据集；
- 该镜像只用于阅读与复现，不代表官方 rsi-flow 仓库的代码。

## 6. 相关文档

- 设计：[../docs/agent-architecture-design.md](../docs/agent-architecture-design.md)
- 引擎笔记：[../docs/rsi-flow-internals.md](../docs/rsi-flow-internals.md)
- 结果与消融：[../reports/structured-three-tasks.md](../reports/structured-three-tasks.md)
- PDF：[../Task2-Structured-Agent-Report.pdf](../Task2-Structured-Agent-Report.pdf)
