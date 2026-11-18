# 从零复现

> 目标：在一台干净机器上重跑 smoke → small → medium，并重新生成 PDF。

## 1. 准备目录

```bash
mkdir -p ~/rsi-work && cd ~/rsi-work

# 交付仓库
git clone https://github.com/H-wonder/RSI_learn.git automationbench-baseline

# 上游数据集（本仓库不重复打包数据集和模型客户端）
mkdir -p datasets
git clone https://github.com/zapier/AutomationBench.git datasets/AutomationBench
```

## 2. 安装依赖

```bash
export PATH="$HOME/.local/bin:$PATH"
cd datasets/AutomationBench
uv sync
```

需要 Python 3.13 与 uv；`scripts/analyze_results.py` 等分析脚本只用标准库。

## 3. 配置模型 key

```bash
cd ../../automationbench-baseline
cat > .env <<'EOF'
OPENAI_API_KEY=你的key
OPENAI_BASE_URL=https://intlapi.thingo.com.cn/v1
EOF
chmod 600 .env
```

`.env` 已被 `.gitignore` 忽略，不要提交。

## 4. 运行前清代理

系统若设置了 `ALL_PROXY=socks5://...`，Python httpx 会报缺 `socksio`。中转站可直连，所以：

```bash
unset ALL_PROXY HTTP_PROXY HTTPS_PROXY all_proxy http_proxy https_proxy
set -a; . ./.env; set +a
```

## 5. 跑实验

```bash
# 烟测（只验证链路，simple 域不计入 benchmark 分数）
python scripts/run_batch.py --name smoke --domains simple --per-domain 5

# 18 题小批量（低成本的流程演练）
python scripts/run_batch.py --name small \
  --tasks-file data/tasks/small_from_annotation.csv

# 60 题正式实验：max reasoning effort，60 题全部重跑
python scripts/run_batch.py --name medium-max --config configs/medium.json \
  --tasks-file data/tasks/medium_from_annotation.csv
```

历史对照（default effort，12 题复用 + 48 题补跑）仍保留在仓库里：

```bash
python scripts/run_batch.py --name medium --tasks-file data/tasks/medium_missing.csv
```

## 6. 分析与完整性检查

```bash
# 先确认没有中途中断的任务（--tasks 模式不会自动补跑）
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
  --out-md reports/compare-default-vs-max.md \
  --out-csv reports/compare-default-vs-max.csv \
  --out-tex reports/tex/compare.tex

python scripts/make_compact_results.py
```

## 7. 重新生成 PDF

```bash
# build_report.py 读取 medium-60.*，先把 max 结果复制过去
cp reports/medium-max.tasks.csv  reports/medium-60.tasks.csv
cp reports/medium-max.issues.csv reports/medium-60.issues.csv
cp reports/medium-max.by_type.md reports/medium-60.by_type.md
cp reports/medium-max.by_type.csv reports/medium-60.by_type.csv

python scripts/build_report.py
scripts/build_pdf.sh
```

产物：仓库根目录 `AutomationBench-Baseline-Report.pdf`。

## 8. 成本提示

60 题 max effort 的框架上界是 **$120.41**；cached input 占 92.6%，
按缓存价 10% 估算约 **$34.63**（以中转站账单为准）。全量 600 题按上界约 **$1,200**，
按缓存折扣估算约 **$350**。放量前先确认预算，并先跑 10 题检查单题成本。

## 9. 任务二：结构化 Agent

任务二的完整说明、结果与消融见
[../reports/structured-three-tasks.md](../reports/structured-three-tasks.md)
和根目录 `Task2-Structured-Agent-Report.pdf`。最短复现路径：

```bash
# 1) 启动某个任务的 WorldState bridge（每次运行前重启，重置初始状态）
cd automationbench-baseline
uv run --project ../datasets/AutomationBench python scripts/world_bridge.py \
  --domain operations \
  --task operations.generator_load_testing_schedule --port 8765

# 2) 构建一次依赖 classpath
cd ../rsi-flow
../scripts/mvn-rsi.sh -q -pl flow-test dependency:build-classpath \
  -Dmdep.outputFile=/tmp/rsi-cp.txt

# 3) 运行 flow（需先 export OPENAI_BASE_URL / OPENAI_API_KEY）
CP="flow-test/target/test-classes:flow-test/target/classes:\
flow-core/target/classes:flow-route/target/classes:$(cat /tmp/rsi-cp.txt)"
$JAVA_HOME/bin/java -cp "$CP" -Dbridge.url=http://127.0.0.1:8765 \
  -Dtask.name=operations.generator_load_testing_schedule \
  -Dflow.id=FLOW_AGENT_OPS -Dresult.path=/tmp/ops-result.json \
  cc.eamon.open.flow.FLOW_AGENT.UltraAgentRunner
```

三个任务的 `-Dflow.id`：`FLOW_AGENT_ULTRA`（sales）、`FLOW_AGENT_OPS`
（operations）、`FLOW_AGENT_SUPPORT`（support）。消融变体：`_NOREPAIR`、`_OPS_SEQ`。

重新生成任务二 PDF：

```bash
scripts/build_task2_pdf.sh    # -> Task2-Structured-Agent-Report.pdf
```
