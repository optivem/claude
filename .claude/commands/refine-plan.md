Walk a plan file item by item, discuss each item with the user, and update the plan in place based on the discussion. No code changes are made — this command refines the *plan*, not the codebase.

## When to use which plan command

- `/refine-plan` (this one) — you want to **talk through** each item and rewrite the plan based on the conversation. Inputs are the user's judgment, not the codebase.
- `/review-plan` — you want to check the plan against the **current code state** and prune items that are done/obsolete. No discussion per item.
- `/execute-plan` — you want to **implement** the plan. Code changes + commits.
- `/update-plan` — batch sync the plan with decisions already made earlier in *this* conversation. No per-item walk.
- `/explain-plan` — you want a **fast, high-level read** of the plan's *why* and *end result*. No discussion, no edits to items.

If the user invoked `/refine-plan` but the request sounds more like one of the others, point that out before starting.

## Input

The plan file is provided as `$ARGUMENTS`. If no argument is given, use the currently open file in the editor (from the IDE selection context). If no file is open either, ask the user which plan file to refine.

The plan file path can be:
- A filename in the current repo (e.g. `MIGRATION.md`)
- A relative path from the academy workspace root (e.g. `plans/20260518-foo.md`)
- An absolute path

Resolve the academy workspace root dynamically:
```bash
ACADEMY_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
```

## Plan format expectations

The plan file contains numbered or bulleted items (e.g. `## Step 1:`, `### 1.`, `- [ ] Step 1`, or similar). Parse whatever numbering/format is used. Preserve the file's existing structure (phases, headings, principle/target-state sections) — refinement edits items, not the surrounding narrative, unless the user explicitly asks.

## Mark plan as picked up

Before starting the walk, add a marker at the top of the plan file so anyone viewing the file can see an agent is working on it:

> 🤖 **Picked up by agent (refine)** — `<hostname>` at `<ISO-8601 UTC timestamp>`

Obtain the values with:
- Hostname: `hostname`
- Timestamp: `date -u +%Y-%m-%dT%H:%M:%SZ`

Insert the marker as the first line of the file (or immediately after the H1 title, if one exists). If a previous marker is already present (from `/execute-plan` or a prior `/refine-plan` run), replace it with the new one. Remove the marker when refinement finishes.

## Optional pre-pass: index

If the plan has more than ~10 items, before walking, present a short numbered index:

```
The plan has 14 items. I'll walk them in order. You can say:
  - "skip <n>" or "skip to <n>" to jump
  - "stop" at any point to save and exit
  - "next" to keep the current item as-is and move on

Items:
  1. <one-line title>
  2. <one-line title>
  ...
```

For shorter plans, skip the index and go straight to item 1.

## Phase 1: Walk

For each item, in order:

### Step 1 — Present
Show the user the item **verbatim** (the actual text from the file, not a paraphrase). Include the item's number/anchor so the user knows where you are in the file. If the item references other items, surface those references too.

### Step 2 — Offer your read
In one or two sentences, give your own quick read of the item: what looks solid, what looks underspecified, what might conflict with other items. Don't overdo it — this is a hook for discussion, not a review.

### Step 3 — Ask one question
Ask **one** open question at a time, never batched. Per the user's standing preference, sequential design walk-throughs use one `AskUserQuestion` per turn. The default options are:

- **Keep as-is** — no changes; move to next item
- **Edit** — open discussion; user dictates what to change
- **Split** — break this item into multiple items
- **Merge** — fold this item into another (user names which)
- **Delete** — remove this item entirely
- **Defer** — mark with `⏳ Deferred: <reason>` and keep in the plan
- **Skip for now** — leave untouched, return to it at the end

If the user has standing per-item annotations (`VJ:`, `AUTHOR:`, etc.), surface them in Step 2 so the user remembers their own past notes.

### Step 4 — Apply
Once the user has decided:

- **Keep / Skip** → no file edit; move on.
- **Edit / Split / Merge / Delete / Defer** → apply the edit to the plan file immediately via `Edit`. Don't queue edits in memory — write through, item by item, so a mid-walk interruption doesn't lose work.

Preserve the file's existing numbering scheme. If you delete or split an item and the plan uses explicit numbering (`Step 3:`, `### 3.`), renumber subsequent items at the **end** of the walk in a single pass — not mid-walk, which would confuse the user's frame of reference.

### Step 5 — Confirm and advance
Briefly confirm what changed ("Item 4: split into 4a and 4b — moving to item 5") and continue.

## Phase 2: Wrap-up

After the last item (or when the user says "stop"):

1. If the numbering scheme requires it, renumber items in one pass and show the user the renumber diff.
2. If any items were marked "skip for now", offer to return to them: *"3 items were skipped. Walk them now, or save and exit?"*
3. Remove the pickup marker.
4. Summarize what changed: items kept, edited, split, merged, deleted, deferred. One short line per outcome class.
5. **Do not commit.** Leave the refined plan file as an uncommitted change so the user can review the diff. Mention that `/commit` or raw `git` will pick it up — and that `/refine-plan` does not run `git` itself.

## Rules

- **One question per turn.** Never batch. This is a sequential walk-through; the user's standing preference is one `AskUserQuestion` per turn. (See `feedback_open_questions_one_at_a_time` in memory.)
- **No code changes.** This command refines the plan only. If the discussion surfaces something that requires a code change, note it in the plan (as a new item or an annotation) — don't fix it here. Use `/execute-plan` afterward.
- **Write through, not batched.** Apply each item's edit to the file as soon as the user decides. Mid-walk interruptions must not lose prior decisions.
- **Preserve author voice.** Inline author annotations (`VJ:`, `AUTHOR:`, etc.) survive unless the user explicitly rewrites them.
- **Preserve structure.** Headings, phase sections, principle/target-state prose are not refined unless the user asks. Refinement edits items.
- **No silent deletions.** Every deletion was explicitly chosen by the user in the walk — but still surface the list in the Phase 2 summary so it's reviewable in one place.
- **One plan file per invocation.** If the user wants to refine several, run the command once per file.
- **No `/clear` advice mid-walk.** The walk is interactive and stateful; clearing mid-walk loses position. Save and exit first, then `/clear`.
