Execute a plan file item by item, either step-by-step (with per-item approval gates) or batch-then-review (execute everything, then one review-and-commit gate at the end).

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

The plan file contains numbered items (e.g. `## Step 1:`, `### 1.`, `- [ ] Step 1`, or similar). Parse whatever numbering/format is used.

## Execution modes

Three possible modes. **Before starting work, pick a mode**:

1. **Auto-detect "Execute approved" first.** Scan the plan for decision annotations (`⏭️ Skipped`, `❌ Rejected`, `✏️ Modified`, `⏳ Deferred`). If any exist, assume a prior review pass happened and switch to **Mode: Execute approved** (see below). Do not ask the user in this case.

2. **Otherwise, ask the user which mode:**

   > Run this plan **step-by-step** (approve each item before and after) or **batch-then-review** (I execute all items, then present everything for review, and commit on your approval)?

   Accept short answers: "step", "step-by-step", "one by one" → **Step-by-step**. "batch", "all", "everything", "batch-then-review" → **Batch-then-review**. If the user has already indicated a preference in their invocation message (e.g. "execute everything and ask me to review at the end"), treat that as the answer and don't re-ask.

3. Respect **pre-approved items** in either mode (see below).

---

## Mark plan as picked up

Before starting execution in any mode (and after the mode is chosen), add a marker at the top of the plan file so anyone viewing the file can see an agent is working on it:

> 🤖 **Picked up by agent** — `<hostname>` at `<ISO-8601 UTC timestamp>`

Obtain the values with:
- Hostname: `hostname`
- Timestamp: `date -u +%Y-%m-%dT%H:%M:%SZ`

Insert the marker as the first line of the file (or immediately after the H1 title, if one exists). If a previous marker is already present, replace it with the new one.

Remove the marker when execution finishes — either the plan file is deleted (all items done) or only deferred items remain (delete just the marker line).

---

## Pre-approved items

Before any approval gate, check whether the item in the plan file already contains a clear author decision — for example, an inline author comment (`VJ:`, `AUTHOR:`, `APPROVED`, etc.) with an explicit instruction like "create a ticket", "add a TODO in X", "yes do it", "reject", "skip". If the decision is unambiguous and the required action is obvious from that decision, treat the item as pre-approved:

- In **Step-by-step mode**: skip both the Phase 1 approval gate and the Phase 2 commit gate. State what you will do in one sentence, execute, summarize, commit.
- In **Batch-then-review mode**: no change — pre-approved items are executed alongside the rest; the single end-of-run review still applies to the batch as a whole.

Only fall back to normal approval gates when:
- The author decision is unclear ("not sure", "maybe", a question back to you, no comment at all).
- The task is ambiguous enough that multiple reasonable approaches exist and the author didn't pick one.
- Something unexpected comes up during execution that changes the plan.

When in doubt, ask. But don't re-ask for approval on something the author already decided.

---

## Mode: Step-by-step

For each incomplete item in the plan:

### Phase 1: Propose
1. Read and display the item description to the user.
2. Analyze what needs to be done: which files to change, in which repo, and how.
3. Present a concrete proposed solution (file changes, commands, etc.).
4. If the item is pre-approved, proceed to Phase 2 without asking. Otherwise ask: **"Approve this approach? (yes / modify / skip)"** and wait for the user's response. If "modify", incorporate their feedback and re-propose. If "skip", move to the next item.

### Phase 2: Execute
1. Implement the approved changes.
2. If the item involves code, run any relevant tests or validation to confirm correctness.
3. Show the user a summary of what was done (changed files, test results).
4. If the item is pre-approved, proceed directly to Phase 3 (commit) without asking. Otherwise ask: **"Review complete. Approve and commit? (yes / redo / skip)"** and wait for the user's response. If "redo", ask what to change and re-execute. If "skip", leave changes uncommitted and move on.

### Phase 3: Commit
1. Determine which repo the changes belong to (from the file paths modified).
2. Commit only that repo using the commit script with `--repo`:
   ```bash
   bash "$(git rev-parse --show-toplevel)/../github-utils/scripts/commit.sh" --repo <repo-name> "<item description>"
   ```
3. **Delete the item from the plan file immediately after committing.** This is mandatory — never move to the next item without removing the completed item first.
4. Report success, then move to the next item.

---

## Mode: Batch-then-review

Execute all incomplete items in sequence without asking per-item. Commit at the very end after one review gate.

### Phase 1: Execute all items
For each incomplete item:
1. Read the item, determine the work (files, commands), and execute the changes directly.
2. Run any relevant tests/validation to confirm correctness. If tests fail, try to fix within the scope of the item. If unfixable, stop and ask the user.
3. **Do not commit yet.** Leave all changes staged in the working tree.
4. **Delete the item from the plan file as soon as its work is done** — do not wait for the commit gate. The plan-file edit is itself an uncommitted change; if the user later chooses `discard`, revert the plan-file deletions along with the code changes.
5. If an item explicitly says "stop and ask user" (or equivalent — e.g. in Open Questions, in Cleanup sections marked destructive, in items marked "needs user decision"), stop at that point, present what you've done so far, and wait for the user. Do not continue past that item without approval.

### Phase 2: Present for review
Once all items in scope are executed (or you hit a stopping point):
1. Summarize by repo: list every file modified, grouped by repository.
2. For each repo, include: item IDs addressed (reference these from the summary, since they've already been removed from the plan file), key changes (not full diffs), test/build results.
3. Mention any items skipped or deferred and why.
4. Ask: **"Review complete. Approve to commit all changes? (yes / redo / ask-per-item / discard)"**
   - `yes` → proceed to Phase 3
   - `redo <item ID>` → roll that item's changes back and re-execute (this includes restoring the item to the plan file and re-deleting it once the redo work completes)
   - `ask-per-item` → drop into Step-by-step mode for the remaining commit gates (still one commit per repo, but ask per commit)
   - `discard` → revert all uncommitted changes, including the plan-file deletions

### Phase 3: Commit all
1. For each repo that has changes, run the commit script once with a message summarizing the items addressed for that repo:
   ```bash
   bash "$(git rev-parse --show-toplevel)/../github-utils/scripts/commit.sh" --repo <repo-name> "<summary of items>"
   ```
   The plan file's deletions (made in Phase 1) are part of these commits — no separate plan-file step is needed here.
2. Report per-repo commit results and summarize what's left in the plan (if anything — e.g. deferred items or items past a stop-gate that weren't executed).

---

## Mode: Execute approved

Only items annotated as approved-but-unimplemented (still `- [ ]` with no rejection/skip/defer marker) are executed. Everything else is skipped. Within this mode, follow **Step-by-step** semantics for each approved item (Phase 1/2/3 with gates, unless pre-approved).

---

## Tracking decisions

After each item is resolved (by any outcome), update the plan file to record what happened:

| Outcome | How to mark |
|---------|-------------|
| Approved & committed | **Delete the item** from the plan file |
| Modified & committed | **Delete the item** |
| Skipped | **Delete the item** |
| Rejected | **Delete the item** — but if the rejection creates new work (e.g. "do the opposite"), add a new item for that work |
| Deferred | `- [ ] Item N: ... — ⏳ Deferred: <reason>` |

**Resolved items are deleted** — the plan file should only show what's left to do. The git history is the record of what was done. Only deferred items remain visible.

Deletions happen **as soon as each item's work is done**, in both modes — Step-by-step deletes after each item's commit; Batch-then-review deletes during Phase 1, before the final commit gate.

## Rules

- Only commit the specific repo that was modified, never all repos. (Batch mode may still commit multiple repos — one commit per repo with changes, still using `--repo` each time.)
- Never bypass a gate a user would reasonably want: explicit "stop and ask user" markers in the plan, destructive operations (release deletion, force-push, dropping data), or actions visible to third parties (published releases, GitHub comments).
- If a item affects multiple repos, handle each repo with its own commit.
- If execution fails and cannot be fixed within the scope of the item, stop and explain the error. Do not auto-fix; propose a solution and wait for approval.
- After the last item, summarize what was completed and what was skipped.
