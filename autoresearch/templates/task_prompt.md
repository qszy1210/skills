# AutoResearch Task Prompt

## Project Goal

<!-- Describe what your project does and what the agent should improve -->
You are improving a [PROJECT TYPE] project.

## Focus Areas (in priority order)

1. **Feature completeness** — implement missing APIs/functions
2. **Test coverage** — write meaningful tests for untested code paths
3. **Error handling** — add proper error handling and edge case coverage
4. **Code quality** — type annotations, documentation, clean patterns

## Constraints

- Make ONE change per iteration
- Do NOT change core architecture
- Do NOT introduce new dependencies unless essential
- Keep ALL existing tests passing
- Follow existing code patterns and conventions

## Context

- Review `.learnings/ITERATIONS.md` for past iteration results
- Avoid approaches that already failed (logged in iterations history)
- Focus on the lowest-scoring evaluation dimension
