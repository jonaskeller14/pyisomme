---
description: Commit the currently staged changes with a generated conventional-commit message
argument-hint: "[optional message or hint]"
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git branch:*), Bash(git commit:*)
model: claude-haiku-4-5-20251001
---

Commit the changes that are **already staged**. Do not stage anything yourself.

## Steps
1. Inspect staged changes: `git diff --cached --stat` and `git diff --cached`.
   - If nothing is staged, STOP and tell the user there is nothing to commit (do not run `git add`).
   - Scan the staged diff for obvious (major) errors or typos — e.g. syntax errors, broken/leftover debug code, obviously wrong identifiers, or misspellings in user-facing strings. If any exist, STOP and return the list of errors to the user (do not commit). Ignore stylistic nitpicks.
2. If `$ARGUMENTS` is provided, use it as the commit message (or as a strong subject/hint).
   Otherwise write a message in this repo's Conventional Commit style:
   `type(scope): summary` where `type` ∈ feat | fix | refactor | docs | chore | test | perf |
   style | build. Derive it from the staged diff; keep the summary in the imperative mood.

   **When the changeset includes multiple sub-changes** (new files, refactors across multiple files, mixed types of changes, etc.), use multiple `-m` flags to break them down:
   - First `-m`: concise subject line
   - Subsequent `-m` flags: bullet-point list of all specific changes (e.g., "- Add widget.dart", "- Update ComponentType with maxCount", "- Refactor preset picker")
3. Commit ONLY the staged changes: `git commit -m "<message>"` (use multiple `-m` flags for a body).
4. Print the result: `git log -1 --format='%h %s'`.

## Constraints
- Never `git add`, `git push`, or `git commit --amend`.
- Never add a `Co-Authored-By` line.
- Use multiple `-m` flags for multi-paragraph messages (avoid PowerShell here-strings).
- If the current branch is `main` or `master`, warn the user and ask for confirmation before committing.
