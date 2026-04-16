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

## Execution modes

The skill supports two modes:

### Mode 1: Review (default)
Walk through each incomplete step one at a time, proposing and waiting for approval before executing. This is the default when the plan has no prior decisions recorded.

### Mode 2: Execute approved
If the plan already contains tracked decisions (approved, rejected, skipped, etc. from a prior review pass), only execute steps that were explicitly approved — i.e. steps annotated with approval but not yet implemented (still `- [ ]` with no rejection/skip/defer marker). Skip everything else. This lets the user review the full plan first, mark decisions, then run `/execute-plan` again to carry out only what was approved.

To detect which mode to use: scan the plan file for decision annotations (`⏭️ Skipped`, `❌ Rejected`, `✏️ Modified`, `⏳ Deferred`). If any are found, assume a prior review pass happened and switch to Mode 2. Otherwise use Mode 1.

---

## Execution loop (Mode 1: Review)

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
3. **Mark the step as done in the plan file immediately after committing.** Change `- [ ]` to `- [x]` (or equivalent format). This is mandatory — never move to the next step without updating the plan file first.
4. Report success, then move to the next step.

### Tracking decisions

After each step is resolved (by any outcome), update the plan file to record what happened:

| Outcome | How to mark | Example |
|---------|-------------|---------|
| Approved & committed | `- [x] Step N: ...` | Step done |
| Skipped by user | `- [~] Step N: ... — ⏭️ Skipped` | User chose to skip |
| Rejected / removed | `- [~] Step N: ... — ❌ Rejected: <reason>` | User decided this is not needed |
| Modified | `- [x] Step N: ... — ✏️ Modified: <what changed>` | Approved with changes |
| Deferred | `- [ ] Step N: ... — ⏳ Deferred: <reason>` | Left unchecked, with note |

Always append the annotation on the same line as the step so the plan file is a complete record of decisions. The user should be able to open the plan file at any time and see exactly what was approved, rejected, modified, or deferred — and why.

## Rules

- Only commit the specific repo that was modified, never all repos.
- Never skip the approval gates -- always wait for the user before executing and before committing.
- If a step affects multiple repos, handle them one at a time with separate commit cycles.
- If execution fails, stop and explain the error. Do not auto-fix; propose a solution and wait for approval.
- After the last step, summarize what was completed and what was skipped.
