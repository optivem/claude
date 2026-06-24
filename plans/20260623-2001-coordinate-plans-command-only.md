# 2026-06-23 20:01 UTC — Fold `plan-coordinator` into the `coordinate-plans` command (delete the agent)

## TL;DR

**Why:** `/coordinate-plans` spawns a `plan-coordinator` subagent, but the agent
never syncs to user level while the command does. On 2026-06-23 a real run in the
`shop` repo failed with `Agent type 'plan-coordinator' not found` — the command was
resolvable (synced to `~/.claude/commands/`) but its agent was not (only present in
`academy/claude/.claude/agents/`, never distributed). The coordination was then
produced **inline in the main session** with identical output, proving the subagent
is not required for correctness.

**Decision (made 2026-06-23):** go **command-only** — fold the entire
`plan-coordinator` workflow into `coordinate-plans.md` and **delete the agent**. One
artifact, nothing extra to sync, and the whole "command present / agent absent" class
of breakage disappears. The accepted tradeoff: coordination reads now happen in the
calling session instead of an isolated subagent context (mitigated by an optional
delegate-the-reads escape hatch — see Step 1).

**End result:** `/coordinate-plans <first> [<last>]` reads the in-scope plans, runs
conflict + consolidation analysis, and writes the meta-plan itself — no subagent
dependency. `plan-coordinator.md` is gone. `claude sync` redistributes the updated
command.

## Outcomes

- `coordinate-plans.md` is self-contained: it carries the full workflow (read → extract
  → dependency graph → conflicts → decided consolidations → execution units → waves),
  the per-plan extraction guidance, the conflict taxonomy, the consolidation options,
  the wave-building rules, and the meta-plan output-format block — all previously living
  in the agent body.
- `.claude/agents/plan-coordinator.md` is deleted.
- The command no longer references "spawn the agent" / "relay the 4-line summary";
  instead Claude writes the meta-plan directly in the main session and reports the same
  4-line summary itself.
- An optional escape hatch is documented: for a **large** in-scope set, Claude MAY
  delegate the plan reads + analysis to a single `general-purpose` subagent that returns
  the meta-plan — but the **default is inline**. This keeps the token-isolation benefit
  available without a dedicated, separately-synced agent.
- `claude sync` redistributes the updated command; no stale `plan-coordinator` copy is
  left in `~/.claude/agents/` (there is none today — confirm during execution).
- A re-run of `/coordinate-plans <range>` produces a meta-plan with **no agent error**.

## ▶ Next executable step (resume here)

**Step 4 — Smoke-test (user-driven).** From a repo with multiple plans (e.g. `shop`),
run `/coordinate-plans <first> <last>` over a small range and confirm it writes a
meta-plan with **no `Agent type ... not found` error** and the same section structure as
before. This is an interactive, visible run best done by the user; the `claude` repo has
only one plan, so it can't exercise a multi-plan range here. Steps 1–3 are done and the
agent-spawn code path is fully removed + global copy verified, so this is a final
confirmation, not a blocker.

## Steps

- [ ] **Step 4 — Smoke-test.** From a repo with plans (e.g. `shop`), run
  `/coordinate-plans <first> <last>` over a small range and confirm it writes a
  meta-plan with no `Agent type ... not found` error and the same section structure as
  before.

## Decisions (resolved 2026-06-23)

- **Structure:** Command-only. Delete `plan-coordinator`. (User chose this over
  "keep agent + fix the sync glob" and "keep both, run inline on failure".) Rationale:
  removes the sync-fragility entirely; the command + agent already duplicated ~the same
  workflow, so collapsing them removes duplication too.
- **Tradeoff accepted:** main-session context absorbs the plan reads on every run.
  Mitigated by the optional general-purpose-subagent escape hatch for large sets.

## Open questions

- Should the long **meta-plan output-format block** live inline in the command, or be
  extracted to a shared doc under `docs/` that the command `@`-includes — to keep the
  command lean? (Lean toward inline for now; revisit if the command gets unwieldy.)
- Does the sync script need a fix so **top-level** `.claude/agents/*.md` distribute in
  future (the gap that bit us here), or is command-only enough that this no longer
  matters? If other top-level agents exist or get added, the sync gap is still latent.

## Context / artifacts from this session

- Diagnosis: command synced to `~/.claude/commands/`; `atdd/**` agents synced to
  `~/.claude/agents/atdd/`; top-level `plan-coordinator.md` did **not** sync.
- Proof-of-concept inline output (the meta-plan the agent would have produced) lives at
  `shop/plans/20260623-1955-meta-narrow-integration-cluster.md` — coordinates the four
  `20260623` narrow-integration plans (`1801`, `1939`, `1941`, `1944`).
