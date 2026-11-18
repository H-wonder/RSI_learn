# rsi-flow 引擎内部结构笔记

> 目的：在写任务二的复杂 Agent 结构之前，先把 rsi-flow 的执行模型、flow JSON
> schema、嵌套/分支/async 的真实语义和已知坑读清楚。所有结论都对应源码位置。

## 1. 初始化与执行链路

`FlowEngine` 第一次被访问时触发 `Initializer` 的 pipeline（`FlowEngine` 静态块）：

1. `ConfigLoadPipeline`：扫描 classpath `flow/` 下以 `flow*` / `model*` 开头的 JSON，
   反序列化为 `FlowConfig`；
2. `CodeLoadPipeline`：扫描 `cc.eamon.open.flow` 包，收集带 `@Flow` 方法的
   `FlowCode`；
3. `ModelLoadPipeline` / `ModelAssemblyPipeline`：加载 model JSON（可选）；
4. `FlowAssemblyPipeline`：为每个 `FlowConfig` 构造 `FlowHolder`（节点、路由、
   参数/结果容器）。

运行时：

```text
FlowEngine.run(flowId)
  → FlowHolder.execute()
    → 读取 flow params，构造 paramMap
    → Executor.execute(start, paramMap)
      → 取队首 Source
      → FlowNodeHolder.execute()（event/flow/http）
      → Routes.executeByStrategy(source, variables)
      → RouteExecutor（normal/all/any/async/close）
      → 把下一个节点加入队列
```

关键源码：

- `flow-core/.../core/FlowEngine.java`
- `flow-core/.../core/context/Initializer.java`
- `flow-core/.../core/context/pipeline/*.java`
- `flow-core/.../core/stereotype/execute/holder/FlowHolder.java`
- `flow-core/.../core/stereotype/support/route/Executor.java`

## 2. Flow JSON schema

`FlowConfig`（`flow-config/.../config/flow/FlowConfig.java`）：

| 字段 | 含义 |
|---|---|
| `id` | 流程 ID，也是默认变量域 |
| `name` / `title` / `description` | 展示信息 |
| `type` | 一般为 `flow` |
| `params` | 流程参数（`FlowParamConfig`） |
| `results` | 流程结果（`FlowResultConfig`） |
| `nodes` | 节点列表（`FlowNodeConfig`） |
| `routes` | 路由（`FlowRouteConfig`：source/target/condition/scope） |
| `strategies` | 异步策略（`FlowRouteStrategyConfig`：source/target/strategy） |
| `models` | model 配置（可选） |
| `schedule` | 调度配置（可选） |

`FlowNodeConfig` 的重要字段：

- `id`：节点唯一 ID，参与路由；
- `type`：`event` / `flow` / `http`；
- `reference`：event 对应 `@Flow` 的 value；flow 对应被嵌套 flow 的 `id`；
- `params` / `results`：**按顺序**与 `FlowCode` 方法参数、嵌套 flow 的
  params/results 一一对应；
- `async`：仅 `async` strategy 下使用；
- `name` 不是 `FlowNodeConfig` 字段（示例 JSON 里的 `name` 会被 fastjson 忽略），
  展示名请用 `title`。

`FlowParamConfig` / `FlowResultConfig`：

- `name`、`type`、`scope`、`notnull`、`defaultValue`；
- `notnull` 不写时默认为 **true**；结果缺失会抛异常；
- `scope` 不写时默认是当前 flow 的 `id`。

## 3. 节点类型与执行语义

`ExecutableEnums` 只有三种：

| type | 执行类 | 语义 |
|---|---|---|
| `event` | `EventExecutable` | 按 `reference` 找 `@Flow` 方法，注入 params，执行后校验 results |
| `flow` | `FlowExecutable` | 嵌套另一个 flow；params/results 按下标映射 |
| `http` | `HttpExecutable` | 远程 HTTP（本方案暂不用） |

`EventExecutable`：

- 用 `FlowContextHolder.retrieveVariable(scope, name)` 取参数；
- 用 `ModelEngine.build` 做类型转换；
- 调用 `FlowCode.execute(args)`；
- 节点执行前把 `FlowEngine.flowScope` 设为当前 flow 的 id；
- 执行后 `FlowNodeHolder.verifyResults()` 检查 results 是否存在。

`FlowExecutable`（嵌套）：

- `flowNodeConfig.params` 与嵌套 flow 的 `params` **按下标**对应；
- 先把父 flow 变量复制/转换到嵌套 flow 的 scope；
- 执行嵌套 `FlowHolder`；
- 再把嵌套 results 按 `flowNodeConfig.results` 的 scope/name 复制回父 flow。

## 4. 路由与条件

`FlowHolder` 把 `routes` 转成 `FlowRouteHolder`；`Routes` 按 source 分组。

运行时走 `Routes.executeByStrategy`：

1. `sourceStrategyGroup` 决定 normal/all/any/async/close；
2. normal/all/any/async 都用 `ConditionHelper.JexlEngine` 评估条件；
3. `condition` 默认是 `"true"`；特殊值 `"default"` 表示兜底；
4. 若没有条件命中且有 default，则走 default；否则断言失败；
5. target 不存在的 route 会被当成 `EndNode`（**拼错 target 会静默结束**）。

条件表达式是 **JEXL**（`ConditionHelper.JexlEngine` → `JexlUtils.invokeMethod`），
不是 JSON Logic。示例：

```json
{ "source": "ROUTE", "target": "SEND_EXEC", "condition": "tier == 'Enterprise'" }
{ "source": "ROUTE", "target": "SEND_OPS", "condition": "needsEscalation == true" }
{ "source": "ROUTE", "target": "FALLBACK", "condition": "default" }
```

## 5. async 的真实语义

`strategies` 是“源节点/目标节点 + 策略”：

- 源节点：
  - `all`：所有满足条件的 target 并行执行，全部完成后合并上下文；
  - `any`：并行执行，任意一个完成就继续（其余线程不保证结束）；
  - `async`：对 `async=true` 的节点开线程，**不合并结果**；
  - `close`：把 target 加入父 Executor 的队列（用于并行分支汇合）。
- 目标节点：
  - `close`：分支结束点，汇合到父流程。

典型并行结构：

```json
"strategies": [
  { "source": "FORK", "strategy": "all" },
  { "target": "JOIN", "strategy": "close" }
]
```

含义：`FORK` 的多个 target 并行执行；每个分支的最后节点路由到 `JOIN`，
`JOIN` 在父 Executor 中继续。

### async 的四个已知坑

1. **上下文是浅拷贝**：`FlowContextExtractor` 复制的是
   `Map<String, FlowScopeContext>` 的引用，分支之间共享同一个
   `FlowScopeContext` / `HashMap`，并发写不是线程安全的。
2. **异常被吞**：`FlowSupplier.get()` / `FlowThread.run()` 捕获异常后
   `printStackTrace()`，异步分支失败不一定会让主流程失败；只能靠下游
   `notnull` 结果校验暴露。
3. **close 可能重复入队**：`Executor.addExecuteNode` 只在“等于队首”时去重，
   多个分支同时 close 时可能把 JOIN 入队多次；JOIN 必须幂等。
4. **any 不保证其它分支结束**：不要在 any 分支里做有副作用的写操作。

## 6. 变量域（scope）的真实行为

- `FlowEngine.run(flowId)` 调用 `FlowContext.shareScope(flowId)`：
  `scopeContextMap.put(flowId, scopeContextMap.get(defaultScope))`。
- 也就是说，**默认情况下所有 flow 的 scope 都指向同一个 default map**；
  嵌套 flow 并不是隔离的。
- `FlowEngine.register(name, value)` 写入当前 `flowScope`；由于别名，
  实际写入 default map。
- `FlowScopeContext.retrieveVariable` 用 JEXL 解析变量名，变量名建议只用
  字母/数字/下划线，不要带点或表达式。
- 设计含义：变量名必须**全局唯一**（建议 `stage_node_result` 前缀），
  否则嵌套 flow / 并行分支会互相覆盖。

## 7. 参数与结果校验

- `FlowNodeHolder.verifyParams()` 比较 `FlowCode.getParamTypes().size()` 与
  node `params.size()`；不一致抛 `ParamNotMatchException`。
- 参数按 **顺序** 注入，不按名字匹配；JSON 中 params 的顺序必须与 Java
  方法签名一致。
- `FlowParamHolder.getNotNull()` 默认 true；参数缺失会抛异常。
- `FlowResultHolder.getNotNull()` 默认 true；节点执行后结果缺失会抛异常。
- `FlowHolder.execute()` 末尾会校验 flow results；缺失则抛异常。

## 8. 当前没有的能力 / 设计约束

- **没有循环**：`while/for` 不能直接表达；修复轮次只能用有界分支展开。
- **没有动态扇出**：并行分支数在 JSON 里写死；不能按列表长度动态生成。
- **没有重试/降级**：节点失败即抛异常；需要自己在 FlowCode 里实现 retry/fallback。
- **没有 checkpoint/断点续跑**：长链失败后只能整条重跑。
- **没有静态校验**：`CheckEntrance` 及其策略全部被注释掉；flow 结构错误
  往往在运行时才暴露。
- **没有预算控制**：没有统一的 token/步数预算节点。
- **没有 built-in LLM/Tool 节点**：本仓库已补 `LlmNode`/`ToolNode`/
  `FinalActionNode`/`VerifierNode`，仍是 event 节点，不是引擎级 primitive。

## 9. 对任务二设计的直接影响

1. **用嵌套 flow 做阶段划分**，但变量名要加阶段前缀，避免共享 default map 覆盖。
2. **并行只用于只读取证**，且每个分支写唯一变量名；不要并行写同一业务对象。
3. **JOIN 节点必须幂等**，因为 close 可能重复入队。
4. **修复轮次用有界分支**（如 `REPAIR_1` / `REPAIR_2`），不要写 while。
5. **所有外部调用要有 retry/fallback**，因为引擎不会自动重试。
6. **设计前先写一个 preflight 校验脚本**：检查 node id 唯一、route target 存在、
   params/results 数量匹配、嵌套 flow 存在、变量名不冲突。
7. **评估时必须记录 async 分支的真实完成情况**，不能只看主流程返回值。

## 10. 已实现的 Agent 节点（test 分支）

- `LlmNode`：`LLM_CALL`，OpenAI-compatible Chat Completions；
- `ToolNode` + `ToolRegistry`：`TOOL_CALL`，工具由调用方注册；
- `FinalActionNode` + `FinalActionRegistry`：`FINAL_ACTION`；
- `VerifierNode`：`VERIFY_CONTAINS`，返回 `{passed, missing}`；
- `FLOW_AGENT_TOOL` / `FLOW_AGENT_LLM` 两个 smoke flow；
- `FlowAgentTest` 3 个测试，套件 20/20。

这些是“节点层”；任务二的“结构层”还应在它们之上组织 S0–S7 阶段、
嵌套子流程、并行取证、条件路由、校验与有界修复。
