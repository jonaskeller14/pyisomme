---
name: gc
description: Commit the currently staged changes with a generated conventional-commit message
---

# Commit staged changes

Delegate this entire workflow to the project-local `commit-staged` custom agent. Do not perform the commit workflow in the parent agent. Pass along any user-supplied message or hint.

Always spawn a **new** `commit-staged` agent for each invocation and inherit the complete current conversation (`fork_turns="all"` or the equivalent). Never reuse a previous commit agent and never use a context-free fork. The child must see the invoking user message so the approval reviewer can recognize it as authorization.

Treat an explicit `$gc` invocation as authorization to create one commit from the changes staged at invocation time. Do not ask the user to repeat that authorization in another message.

## Workflow

1. Inspect `git status --short`, `git branch --show-current`, `git diff --cached --stat`, and `git diff --cached`.
2. If nothing is staged, stop and report that there is nothing to commit. Never run `git add`.
3. Review the staged diff for obvious major errors such as syntax errors, leftover debug code, clearly wrong identifiers, or misspellings in user-facing strings. Ignore stylistic nitpicks. If a major error is found, stop and report it without committing.
4. If the branch is `main` or `master`, warn the user and obtain confirmation before committing.
5. Use the user's message as the commit message or a strong hint when provided. Otherwise derive a Conventional Commit subject in imperative mood using `type(scope): summary`, where `type` is one of `feat`, `fix`, `refactor`, `docs`, `chore`, `test`, `perf`, `style`, or `build`.
6. For a changeset with multiple meaningful sub-changes, use the first `-m` for the concise subject and subsequent `-m` arguments for a bullet-list body covering the specific changes.
7. Commit only the staged changes with `git commit -m ...`.
8. Report the result from `git log -1 --format='%h %s'`.

## Constraints

- Never run `git add`, `git push`, or `git commit --amend`.
- Never add a `Co-Authored-By` or similar attribution line.
- Use multiple `-m` arguments for multi-paragraph messages; do not use PowerShell here-strings.
- Do not change files as part of this workflow.
