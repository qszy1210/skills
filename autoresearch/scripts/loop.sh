#!/bin/bash
# AutoResearch Loop Controller
# Drives the experiment-evaluate-keep/discard-iterate cycle.
#
# Usage:
#   ./loop.sh                                    # defaults: claude agent, 30 iterations
#   ./loop.sh --agent claude --max-iter 50 --target 85
#   ./loop.sh --agent codex --max-iter 30
#   ./loop.sh --dry-run                          # show config without running
#
# Agents supported: claude, codex
# (Cursor is driven from within the IDE, not via this script)

set -euo pipefail

# ── Defaults ──
AGENT="claude"
MAX_ITER=30
MAX_FAILS=5
TARGET_SCORE=85
MIN_IMPROVE=0.5
MAX_RUNTIME=480  # minutes
DRY_RUN=false
TASK_PROMPT="task_prompt.md"

# ── Parse args ──
while [[ $# -gt 0 ]]; do
    case $1 in
        --agent)       AGENT="$2"; shift 2 ;;
        --max-iter)    MAX_ITER="$2"; shift 2 ;;
        --max-fails)   MAX_FAILS="$2"; shift 2 ;;
        --target)      TARGET_SCORE="$2"; shift 2 ;;
        --min-improve) MIN_IMPROVE="$2"; shift 2 ;;
        --max-runtime) MAX_RUNTIME="$2"; shift 2 ;;
        --task-prompt) TASK_PROMPT="$2"; shift 2 ;;
        --dry-run)     DRY_RUN=true; shift ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "  --agent NAME        Agent to use: claude, codex (default: claude)"
            echo "  --max-iter N        Maximum iterations (default: 30)"
            echo "  --max-fails N       Max consecutive failures before stopping (default: 5)"
            echo "  --target N          Target score to reach (default: 85)"
            echo "  --min-improve N     Minimum score improvement to keep (default: 0.5)"
            echo "  --max-runtime M     Maximum runtime in minutes (default: 480)"
            echo "  --task-prompt FILE  Task prompt file (default: task_prompt.md)"
            echo "  --dry-run           Show config without running"
            exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ── Override from stop_conditions.json if present ──
if [ -f stop_conditions.json ]; then
    _read_json() { python3 -c "import json,sys; d=json.load(open('stop_conditions.json')); print($1)" 2>/dev/null; }
    MAX_ITER=$(_read_json "d.get('hard_limits',{}).get('max_iterations', $MAX_ITER)")
    MAX_FAILS=$(_read_json "d.get('convergence',{}).get('max_consecutive_failures', $MAX_FAILS)")
    TARGET_SCORE=$(_read_json "d.get('convergence',{}).get('target_score', $TARGET_SCORE)")
    MIN_IMPROVE=$(_read_json "d.get('convergence',{}).get('min_improvement_threshold', $MIN_IMPROVE)")
    MAX_RUNTIME=$(_read_json "d.get('hard_limits',{}).get('max_runtime_minutes', $MAX_RUNTIME)")
fi

# ── Config summary ──
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " AutoResearch Loop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Agent:          $AGENT"
echo " Max iterations: $MAX_ITER"
echo " Target score:   $TARGET_SCORE"
echo " Max fails:      $MAX_FAILS"
echo " Min improve:    $MIN_IMPROVE"
echo " Max runtime:    ${MAX_RUNTIME}m"
echo " Task prompt:    $TASK_PROMPT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$DRY_RUN" = true ]; then
    echo "(dry run — not executing)"
    exit 0
fi

# ── Validation ──
if [ ! -f evaluate.py ]; then
    echo "ERROR: evaluate.py not found. Run init.sh first."
    exit 1
fi

if [ ! -f "$TASK_PROMPT" ]; then
    echo "ERROR: $TASK_PROMPT not found."
    exit 1
fi

# ── Agent dispatch function ──
run_agent() {
    local prompt="$1"
    local log_file="$2"

    case $AGENT in
        claude)
            claude -p "$prompt" \
                --allowedTools "Read,Write,Bash" \
                2>&1 | tee "$log_file"
            ;;
        codex)
            codex --approval-mode auto-edit -q "$prompt" \
                2>&1 | tee "$log_file"
            ;;
        *)
            echo "ERROR: Unknown agent: $AGENT"
            exit 1
            ;;
    esac
}

# ── Setup ──
BRANCH_NAME="autoresearch/$(date +%Y%m%d-%H%M%S)"
git checkout -b "$BRANCH_NAME" 2>/dev/null || true
mkdir -p logs

START_TIME=$(date +%s)
MAX_RUNTIME_SEC=$((MAX_RUNTIME * 60))
FAIL_STREAK=0

BEST_SCORE=$(python3 evaluate.py 2>/dev/null | tail -1)
echo "$BEST_SCORE" > .best_score
echo ""
echo "Baseline score: $BEST_SCORE"
echo ""

TASK_CONTENT=$(cat "$TASK_PROMPT")

# ── Main loop ──
for i in $(seq 1 "$MAX_ITER"); do
    ELAPSED=$(( $(date +%s) - START_TIME ))

    # Hard limit: time
    if [ $ELAPSED -gt $MAX_RUNTIME_SEC ]; then
        echo "STOP: max runtime (${MAX_RUNTIME}m) reached"
        break
    fi

    echo ""
    echo "━━━ Iteration $i/$MAX_ITER ━━━ elapsed: $((ELAPSED/60))m"

    # Build prompt with context
    ITER_PROMPT="$TASK_CONTENT

--- AutoResearch Context ---
Current score: $BEST_SCORE / 100
Target score: $TARGET_SCORE
Iteration: $i / $MAX_ITER
Elapsed: $((ELAPSED/60)) minutes

Instructions:
1. Run 'python evaluate.py' to see the detailed score breakdown (on stderr)
2. Identify the dimension with the LOWEST score
3. Make ONE targeted improvement for that dimension
4. Re-run 'python evaluate.py' to verify the score improved
5. Make sure all existing tests still pass

Rules:
- Only change ONE thing per iteration
- Check git log to see what was already tried in previous iterations
- Follow existing project patterns and conventions
- Do not introduce new dependencies unless essential"

    # EXPERIMENT
    run_agent "$ITER_PROMPT" "logs/iteration-$i.log"

    # EVALUATE
    NEW_SCORE=$(python3 evaluate.py 2>/dev/null | tail -1)
    IMPROVEMENT=$(python3 -c "print(round(float('$NEW_SCORE') - float('$BEST_SCORE'), 2))")
    echo "Score: $NEW_SCORE (change: $IMPROVEMENT)"

    # Determine result
    if python3 -c "exit(0 if float('$IMPROVEMENT') >= float('$MIN_IMPROVE') else 1)" 2>/dev/null; then
        RESULT="KEPT"
    else
        RESULT="DISCARDED"
    fi

    # Target reached?
    if python3 -c "exit(0 if float('$NEW_SCORE') >= float('$TARGET_SCORE') else 1)" 2>/dev/null; then
        git add -A && git commit -m "autoresearch: target reached at iteration $i — score $NEW_SCORE"
        echo "TARGET REACHED: $NEW_SCORE >= $TARGET_SCORE"
        break
    fi

    # KEEP or DISCARD
    if [ "$RESULT" = "KEPT" ]; then
        BEST_SCORE=$NEW_SCORE
        echo "$BEST_SCORE" > .best_score
        git add -A && git commit -m "autoresearch: iteration $i — score $NEW_SCORE (+$IMPROVEMENT)"
        echo "KEPT (best: $BEST_SCORE)"
        FAIL_STREAK=0
    else
        git checkout -- . 2>/dev/null || true
        echo "DISCARDED (improvement $IMPROVEMENT < threshold $MIN_IMPROVE)"
        FAIL_STREAK=$((FAIL_STREAK + 1))
    fi

    # Convergence check
    if [ $FAIL_STREAK -ge "$MAX_FAILS" ]; then
        echo "STOP: $MAX_FAILS consecutive failures — converged"
        break
    fi
done

# ── Final report ──
FINAL_ELAPSED=$(( $(date +%s) - START_TIME ))
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " AutoResearch Complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Iterations:  $i"
echo " Final score: $BEST_SCORE"
echo " Runtime:     $((FINAL_ELAPSED/60))m $((FINAL_ELAPSED%60))s"
echo " Branch:      $BRANCH_NAME"
echo ""
echo " Git log:"
git log --oneline "$BRANCH_NAME" 2>/dev/null | head -20
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
