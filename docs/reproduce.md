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
# 烟测
python scripts/run_batch.py --name smoke --domains simple --per-domain 5

# 18 题小批量
python scripts/run_batch.py --name small \
  --tasks-file data/tasks/small_from_annotation.csv

# 60 题正式实验：复用 small 的 12 题，补跑 48 题
python scripts/run_batch.py --name medium \
  --tasks-file data/tasks/medium_missing.csv
```

## 6. 分析

```bash
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

python scripts/make_compact_results.py
```

## 7. 重新生成 PDF

```bash
python scripts/build_report.py
scripts/build_pdf.sh
```

产物：仓库根目录 `AutomationBench-Baseline-Report.pdf`。

## 8. 成本提示

60 题约 **$71.78**；全量 600 题按此估算约 **$700**。放量前先确认预算。
