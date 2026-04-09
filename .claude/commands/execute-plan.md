Execute a plan file step by step, with approval gates before and after each step.

## Input

The plan file is provided as `$ARGUMENTS`. If no argument is given, use the currently open file in the editor (from the IDE selection context). If no file is open either, ask the user which plan file to execute.

The plan file path can be:
- A filename in the current repo (e.g. `MIGRATION.md`)
- A relative path from the academy workspace root (e.g. `starter/MIGRATION.md`)
- An absolute path

Resolve the academy workspace root dynamically:
```bash
ACADEMY_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
```

## Plan format expectations

The plan file contains numbered steps (e.g. `## Step 1:`, `### 1.`, `- [ ] Step 1`, or similar). Parse whatever numbering/format is used.

## Execution loop

For each incomplete step in the plan:

### Phase 1: Propose
1. Read and display the step description to the user.
2. Analyze what needs to be done: which files to change, in which repo, and how.
3. Present a concrete proposed solution (file changes, commands, etc.).
4. Ask: **"Approve this approach? (yes / modify / skip)"**
5. Wait for the user's response. If "modify", incorporate their feedback and re-propose. If "skip", move to the next step.

### Phase 2: Execute
1. Implement the approved changes.
2. If the step involves code, run any relevant tests or validation to confirm correctness.
3. Show the user a summary of what was done (changed files, test results).
4. Ask: **"Review complete. Approve and commit? (yes / redo / skip)"**
5. Wait for the user's response. If "redo", ask what to change and re-execute. If "skip", leave changes uncommitted and move on.

### Phase 3: Commit
1. Determine which repo the changes belong to (from the file paths modified).
2. Commit only that repo using the commit script with `--repo`:
   ```bash
   bash "$(git rev-parse --show-toplevel)/../github-utils/scripts/commit.sh" --repo <repo-name> "<step description>"
   ```
3. **Mark the step as done in the plan file immediately after committing.** Use whatever format matches the plan (e.g. change `- [ ]` to `- [x]`, prefix with `~~strikethrough~~`, or append `— ✅ Done`). This is mandatory — never move to the next step without updating the plan file first.
4. Report success, then move to the next step.

## Rules

- Only commit the specific repo that was modified, never all repos.
- Never skip the approval gates -- always wait for the user before executing and before committing.
- If a step affects multiple repos, handle them one at a time with separate commit cycles.
- If execution fails, stop and explain the error. Do not auto-fix; propose a solution and wait for approval.
- After the last step, summarize what was completed and what was skipped.
