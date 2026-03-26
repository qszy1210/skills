# AutoResearch Instructions

This project uses the autoresearch pattern for autonomous improvement.

## When to Enter Loop Mode

When the user says "autoresearch", "开始自主循环", or similar, begin the
experiment-evaluate-keep/discard-iterate loop.

## Loop Steps

1. Run `python evaluate.py` — stderr shows detailed breakdown, stdout shows total score
2. Find the lowest-scoring dimension
3. Check `git log --oneline` for what was already tried
4. Make ONE targeted change
5. Re-run `python evaluate.py`
6. If score improved: `git add -A && git commit -m "autoresearch: score X (+Y)"`
7. If score did not improve: `git checkout -- .`
8. Check stop conditions in `stop_conditions.json`
9. Continue or report final summary

## Constraints

- One change per iteration
- Run on autoresearch/* branch
- Never skip tests
- Check git history to avoid repeating failures
- Follow project conventions
