---
name: AutoResearch
description: Autonomous experiment-evaluate-iterate loop for AI agents.
---

# AutoResearch Skill

Autonomous experiment-evaluate-iterate loop for AI agents.
Based on Karpathy's autoresearch hill-climbing pattern:
the agent continuously tries improvements, measures results,
keeps what works, discards what doesn't, and iterates.

Use this skill when the user wants to:
- Continuously and autonomously improve a codebase (tests, coverage, performance, features)
- Run overnight experiment loops that keep what works and discard what doesn't
- Set up a project for autonomous iteration with measurable metrics
- Initialize autoresearch in any project (any language, any framework)

## Quick Reference

| User says | Action |
|-----------|--------|
| "初始化 autoresearch" / "setup autoresearch" | Run `scripts/init.sh` to scaffold project |
| "开始 autoresearch" / "start autoresearch" | Execute the experiment loop |
| "autoresearch 状态" / "autoresearch status" | Show current scores and iteration count |
| "设置停止条件" / "set stop conditions" | Edit `stop_conditions.json` |
| "验证停止条件" / "verify stop conditions" | Run completeness verification |

---

## How It Works

```
┌─────────────┐
│  EXPERIMENT  │ ← Agent tries ONE change
└──────┬──────┘
       ▼
┌─────────────┐
│  EVALUATE   │ ← Run evaluate.py, get score
└──────┬──────┘
       ▼
┌─────────────┐     ┌──────────┐
│   BETTER?   │─No─▶│  REVERT  │──┐
└──────┬──────┘     │ git checkout│ │
       │ Yes        └──────────┘  │
       ▼                           │
┌─────────────┐                   │
│ git commit  │                   │
└──────┬──────┘                   │
       │                           │
       ▼                           │
┌─────────────┐                   │
│ CHECK STOPS │◀──────────────────┘
└──────┬──────┘
       │ Not yet
       ▼
    (repeat)
```

Three prerequisites for the loop to work:
1. **Automated experiment** — Agent can modify code and run commands without human input
2. **Quantitative metric** — `evaluate.py` outputs a number, not vibes
3. **Version control** — git commit/revert to cleanly keep or discard each attempt

---

## Platform Setup

### Cursor (Agent Mode)

In Cursor, you drive the loop from within a conversation. The agent executes
each iteration using Shell, Read, Write, and Task tools.

**Approach A — Single-session loop (recommended for < 30 iterations):**

Tell the agent:
```
开始 autoresearch，目标分数 85，最多 20 轮。
每轮：运行 evaluate.py → 找最低维度 → 做一个改进 → 验证 → commit 或 revert。
连续 5 轮无改进时停止。每轮完成后报告分数变化。
```

**Approach B — External script driving Cursor Background Agent:**

Use `scripts/loop.sh` with `cursor` as the agent backend.
The script submits tasks to Background Agent API in a loop.

**Approach C — .cursor/rules/ integration:**

Create a rule file that defines loop behavior (see `templates/cursor-rule.mdc`).

### Claude Code

**Approach A — /loop command (simplest):**
```bash
/loop 5m "运行 python evaluate.py，找到分数最低的维度，做一个改进，
验证分数提升后 git commit，否则 git checkout -- ."
```

**Approach B — Shell script loop (most robust):**
```bash
chmod +x scripts/loop.sh
./scripts/loop.sh --agent claude --max-iter 30 --target 85
```

**Approach C — CLAUDE.md driven:**

Copy `templates/CLAUDE.md` to your project root. Claude Code will
automatically follow the autoresearch instructions.

### OpenAI Codex

```bash
./scripts/loop.sh --agent codex --max-iter 30 --target 85
```

---

## Initialization

Run initialization in your project to scaffold autoresearch files:

```bash
# From your project root
bash ~/.cursor/skills/autoresearch/scripts/init.sh
```

This creates:
```
your-project/
├── evaluate.py              # Evaluation script (customize this!)
├── stop_conditions.json     # Stop conditions config
├── task_prompt.md           # What the agent should work on
└── logs/                    # Per-iteration output logs
```

---

## The Evaluation Script

The evaluation script is the **most important file**. It must:
1. Output a single number (the score) to stdout
2. Be fully automated (no human input needed)
3. Cover multiple dimensions of quality

### Customization Guide

Edit `evaluate.py` dimensions for your project:

| Project Type | Key Dimensions |
|-------------|---------------|
| Library/SDK | API completeness, test coverage, doc coverage, type safety |
| Web App | Route coverage, component tests, lighthouse score, a11y |
| CLI Tool | Command coverage, error handling, help text, integration tests |
| ML Model | Accuracy, F1, inference speed, memory usage |
| Data Pipeline | Correctness, throughput, error recovery, schema validation |

### Minimum Viable Evaluation

Even a simple evaluation is better than none:

```python
#!/usr/bin/env python3
import subprocess, sys

score = 0

# Does it compile/import?
r = subprocess.run(["python", "-c", "import my_project"], capture_output=True)
if r.returncode == 0: score += 30

# Do tests pass?
r = subprocess.run(["python", "-m", "pytest", "-q"], capture_output=True, text=True)
if r.returncode == 0: score += 40
elif "passed" in r.stdout: score += 20

# Is there test coverage?
r = subprocess.run(["python", "-m", "pytest", "--cov=my_project", "-q"],
                    capture_output=True, text=True)
for line in r.stdout.split("\n"):
    if "TOTAL" in line:
        pct = int(line.split()[-1].rstrip("%"))
        score += min(pct // 4, 30)  # max 30 points

print(score)
```

---

## Stop Conditions

### Three-Layer Framework

```
Layer 1: HARD LIMITS (must stop)
  - max_iterations: 50        # prevent infinite loops
  - max_runtime_minutes: 480  # 8-hour cap
  - max_cost_usd: 30.0        # budget ceiling
  - stop_on_compile_failure    # don't pile garbage

Layer 2: CONVERGENCE (should stop)
  - max_consecutive_failures: 5  # plateau detected
  - min_improvement_threshold: 0.5  # ignore tiny gains
  - target_score: 85              # "good enough"

Layer 3: QUALITY GATES (can stop)
  - all_tests_pass: true
  - min_coverage_percent: 70
  - required_features: [...]   # project-specific checklist
```

### Verifying Completeness

Run the verifier to check your stop conditions cover all safety bases:

```bash
python ~/.cursor/skills/autoresearch/scripts/verify_stops.py stop_conditions.json
```

---

## Loop Execution Protocol (For the Agent)

When executing autoresearch, follow this exact protocol per iteration:

### Step 1: Assess
```bash
python evaluate.py 2>/dev/null    # score to stdout
python evaluate.py > /dev/null    # detailed breakdown to stderr
```

### Step 2: Plan
- Identify the dimension with the lowest score
- If a dimension is already at max, skip to the next lowest
- Check git log for what was already tried in previous iterations

### Step 3: Execute
- Make ONE targeted change
- Keep changes small and focused
- Follow existing project patterns and conventions

### Step 4: Verify
```bash
NEW_SCORE=$(python evaluate.py 2>/dev/null)
```

### Step 5: Decide
```
IF new_score > best_score + threshold:
    git add -A && git commit -m "autoresearch: iteration N — score X (+Y)"
    Reset fail counter
ELSE:
    git checkout -- .
    Increment fail counter
```

### Step 6: Check Stop Conditions
```
IF score >= target: STOP (goal reached)
IF fail_streak >= max_fails: STOP (converged)
IF iteration >= max_iter: STOP (budget exhausted)
IF elapsed >= max_time: STOP (time limit)
```

### Step 7: Continue or Report
- If continuing: go to Step 1
- If stopping: output final report with summary stats

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | What To Do Instead |
|-------------|-------------|-------------------|
| Changing multiple things per iteration | Can't attribute improvement | One change per iteration |
| No git branch isolation | Pollutes main branch | Always use `autoresearch/*` branch |
| Single evaluation metric | Goodhart's Law | Multiple orthogonal dimensions |
| No fail counter | Infinite plateau loops | Circuit breaker at 5 consecutive fails |
| Trivial tests to inflate coverage | False sense of quality | Score meaningful test assertions |
| No cost/time limits | Unbounded spending | Always set hard limits |

---

## Files Reference

```
~/.cursor/skills/autoresearch/
├── SKILL.md                      # This file
├── scripts/
│   ├── init.sh                   # Project scaffolding
│   ├── loop.sh                   # Main loop controller (claude/codex)
│   └── verify_stops.py           # Stop condition completeness checker
└── templates/
    ├── evaluate.py               # Evaluation script template
    ├── stop_conditions.json      # Default stop conditions
    ├── task_prompt.md            # Task description template
    ├── cursor-rule.mdc           # Cursor rule template
    └── CLAUDE.md                 # Claude Code instructions template
```
