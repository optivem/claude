Spawn the `plan-coordinator` agent against the in-flight plan files and write a coordination meta-plan: dependency graph, conflicts, consolidation findings (each with a decided resolution), execution units, and execution waves (parallel-safe batches) — so the user knows which agent sessions to spin up in parallel.

This command is read-only on the plans themselves. The agent never edits a plan, never invokes `/execute-plan`, never commits.

## Input

The scope is provided as `$ARGUMENTS`. The contract is **required first plan, optional last plan**:

- **Required:** the first plan to coordinate. Either a full filename (`20260518-1144-atdd-bpmn-orchestration.md`) or a date/slug prefix that uniquely identifies one file (`20260518-1144`).
- **Optional:** the last plan, given the same way. When present, the range is **inclusive on both ends** — `[first..last]` by filename sort order.

Accepted argument shapes:

- `<first>` — coordinate from `<first>` onwards (every `*.md` directly under `plans/` whose filename sorts ≥ `<first>`, skip `plans/deferred/`).
- `<first> <last>` (space-separated) or `<first>..<last>` (range syntax) — coordinate the inclusive range `[first..last]`.

**If `$ARGUMENTS` is empty, do NOT default to "everything".** Stop and ask the user: "Which plan should coordination start from? (filename or date prefix; optionally pass a last plan to bound the range.)" — then re-enter with the answer. Empty input is treated as missing required argument, not as "coordinate everything".

**Resolve and validate the inputs** before spawning the agent:

1. Resolve the plans directory dynamically from the current repo root (`git rev-parse --show-toplevel`). Never hardcode absolute paths.
2. `Glob` `plans/*.md`, sort lexicographically.
3. Resolve `<first>` to a real file. If `<first>` is a prefix, expect exactly one match — multiple matches or zero matches is an error; report the candidates (or "no match") and stop.
4. If `<last>` is given, resolve it the same way; require `<last> >= <first>` in sort order.
5. Compute the in-scope list as the contiguous slice. Pass this resolved list to the agent, not the raw `$ARGUMENTS` string, so the agent doesn't have to re-resolve the prefix.

Plans referenced as dependencies by in-scope plans but sitting *outside* the `[first..last]` range are still **read by the agent for graph completeness** (marked "referenced-only" in the meta-plan) — the range bounds the *coordination scope*, not the *reading scope*.

## What to do

Spawn the `plan-coordinator` agent in the foreground (subagent_type = `plan-coordinator`) with a self-contained brief:

- The **resolved list** of in-scope plan filenames (the contiguous `[first..last]` slice computed above).
- The original first/last arguments, for traceability in the meta-plan header.
- A reminder that the agent must complete conflict + consolidation analysis BEFORE building the wave plan, and that consolidations must be *decided* in the meta-plan (not left as open questions) so the wave plan operates on a stable post-consolidation unit set.
- The output path convention: `plans/{YYYYMMDD-HHMM}-meta-{slug}.md`.

When the agent returns, relay its 4-line chat summary (meta-plan path, plans analysed, conflict/consolidation/needs-decision counts, wave 1 batch summary) to the user. Do not re-summarise the meta-plan inline — the user reads the file.

## After

Suggest the natural follow-ups in one short line:

- `/refine-plan plans/{path}` — walk the meta-plan and tweak any decisions before acting on them.
- For each wave-1 batch in the meta-plan, the user can spawn a fresh agent session per batch member (the meta-plan names the files each session should touch).

## Rules

- One agent invocation per command run. Do not loop or chain.
- Never edit a plan file. Never invoke `/execute-plan`. Never commit.
- If the agent reports "no findings — all plans in a single wave, no conflicts, no consolidations," surface that message and do not write a meta-plan file.
