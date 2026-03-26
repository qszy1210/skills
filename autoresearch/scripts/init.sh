#!/bin/bash
# AutoResearch Project Initializer
# Scaffolds all files needed to run autoresearch in any project.
# Usage: bash ~/.cursor/skills/autoresearch/scripts/init.sh

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_DIR="$(pwd)"

echo "━━━ AutoResearch 初始化 ━━━"
echo "项目目录: $PROJECT_DIR"
echo ""

mkdir -p logs

copy_if_missing() {
    local src="$1" dst="$2"
    if [ -f "$dst" ]; then
        echo "  [skip] $dst (already exists)"
    else
        cp "$src" "$dst"
        echo "  [create] $dst"
    fi
}

echo "创建文件:"
copy_if_missing "$SKILL_DIR/templates/evaluate.py" "evaluate.py"
copy_if_missing "$SKILL_DIR/templates/stop_conditions.json" "stop_conditions.json"
copy_if_missing "$SKILL_DIR/templates/task_prompt.md" "task_prompt.md"

if [ ! -d .git ]; then
    git init -q
    echo "  [create] git repository"
fi

if [ -f .gitignore ]; then
    if ! grep -q "logs/" .gitignore 2>/dev/null; then
        echo "logs/" >> .gitignore
        echo "  [update] .gitignore (added logs/)"
    fi
else
    cat > .gitignore << 'GITIGNORE'
logs/
*.pyc
__pycache__/
.coverage
coverage.json
test-report.json
.best_score
GITIGNORE
    echo "  [create] .gitignore"
fi

echo ""
echo "━━━ 初始化完成 ━━━"
echo ""
echo "下一步:"
echo "  1. 编辑 evaluate.py — 定义你的项目评估维度"
echo "  2. 编辑 task_prompt.md — 描述 Agent 应该做什么"
echo "  3. 编辑 stop_conditions.json — 设置停止条件"
echo "  4. 运行: bash ~/.cursor/skills/autoresearch/scripts/loop.sh"
echo "  或在 Cursor 中说: '开始 autoresearch'"
echo ""
