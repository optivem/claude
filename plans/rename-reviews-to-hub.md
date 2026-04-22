# Plan: Rename optivem/reviews → optivem/hub

## Decisions confirmed

- **New name**: `optivem/hub` (local folder: `academy/hub`)
- **Visibility**: stays public
- **Architecture**: single shared hub for all courses (not per-course split) — per-course split tracked in optivem/courses#85
- **Scope bundled**: also finish the incomplete prior sandbox→reviews rename in this same pass (do not leave two in-flight renames overlapping)
- **Rename reviews-admin agent**: yes, → `hub-admin`

## Resolved decisions

- Course lesson files (`*-sandbox-project.md` ~20 files): **leave filenames AND content completely untouched**. They will keep referencing "sandbox" / "reviews" — student confusion noted and accepted.
- `sync-sandbox` command → rename to **`sync-hub`**
- `reviews/config/sandbox.json` → rename to **`board.json`**

## Phase 1 — Pre-flight

- [ ] Verify working tree is clean in all affected repos (claude, reviews, courses)
- [ ] `gh repo view optivem/reviews` — confirm current state before rename
- [ ] Re-run sandbox + reviews reference counts to catch any drift from earlier scan

## Phase 2 — Finish sandbox cleanup inside reviews repo (56 references across 20 files)

Do this BEFORE the GitHub rename so the rename commit is clean.

- [ ] `reviews/README.md` — remove "Sandbox Project Reviews" line
- [ ] `reviews/config/sandbox.json` — rename file (per open question above), update `"title": "Optivem Sandbox"`
- [ ] `reviews/config/projects.json` — scan for sandbox references (key `CTF` has repo `ctf-sandbox` — that's an external student repo, leave alone)
- [ ] `reviews/scripts/sync.mjs` (2 refs), `sync-student-urls.mjs` (1), `sync-issue-template.mjs` (1), `sync-course-structure.mjs` (11), `sync-checklists.mjs` (8), `pipeline-setup.sh` (1), `load-config.mjs` (4), `load-config.cjs` (4), `generate-dashboard.mjs` (1), `dashboard-template.html` (2)
- [ ] `reviews/docs/submission-guide.md` (7 refs)
- [ ] `reviews/.github/workflows/auto-on-closed.yml` (1)
- [ ] `reviews/.github/ISSUE_TEMPLATE/review-request.yml` (1)
- [ ] `reviews/.github/actions/validate-issue/action.yml` (1)
- [ ] Commit via `/commit`

## Phase 3 — GitHub repo rename

- [ ] Update GitHub description (currently still "Optivem Sandbox"): `gh repo edit optivem/reviews --description "Optivem Academy Hub — project submissions, reviews, and discussions"`
- [ ] Rename repo: `gh repo rename hub --repo optivem/reviews`
- [ ] Verify redirect works: `gh repo view optivem/hub` + old URL `https://github.com/optivem/reviews` redirects
- [ ] GitHub Pages URL moves from `optivem.github.io/reviews` → `optivem.github.io/hub` — update README badge link + dashboard link
- [ ] Update Pages workflow if it references old name

## Phase 4 — Local folder rename

- [ ] Close VS Code if it has the folder open
- [ ] Rename: `mv academy/reviews academy/hub`
- [ ] Update remote: `gh repo set-default optivem/hub` inside the renamed folder (or manually update `.git/config` origin URL if needed — GitHub's redirect makes this optional but explicit is better)
- [ ] Update `academy/academy.code-workspace` — change `"path": "reviews"` → `"path": "hub"`, update any name fields

## Phase 5 — Rename reviews-admin agent

- [ ] `mv academy/hub/.claude/agents/reviews-admin.md academy/hub/.claude/agents/hub-admin.md`
- [ ] Update agent's `name:` frontmatter + internal references to "reviews" → "hub"
- [ ] Update description to reflect new scope
- [ ] Search for `reviews-admin` invocations across all repos — update any found

## Phase 6 — Rename sync-sandbox command

- [ ] `mv claude/.claude/commands/sync-sandbox.md claude/.claude/commands/sync-hub.md`
- [ ] Update command body: `sandbox` → `hub` references
- [ ] Search for `/sync-sandbox` invocations in other files — update any found

## Phase 7 — Update references outside the renamed repo (43 "reviews" refs across 30 files)

- [ ] `courses/docs/strategy/repo-types.md` (1)
- [ ] `courses/docs/strategy/completion-rates.md` (1)
- [ ] `courses/docs/rules/01-pipeline.md` (1)
- [ ] `courses/docs/rules/00-shared.md` (1)
- [ ] `courses/docs/plans/submission-pattern.md` (5) — verify if this plan is still active or can be removed
- [ ] `courses/02-atdd/accelerator/course/16-adoption-guide/*.md` (4 files, 7+ refs)
- [ ] `courses/02-atdd/accelerator/course/12-atdd-acceptance-criteria/03-three-amigos-session.md` (6 refs)
- [ ] `courses/02-atdd/accelerator/course/01-getting-started/00-overview.md` (1)
- [ ] `courses/01-pipeline/accelerator/course/07-adoption-guides/02-metrics-alignment-meeting.md` (1)
- [ ] `courses/.claude/agents/course-tester.md` (1 — was found with "sandbox" refs)
- [ ] `actions/.claude/agents/docs/devops-rubric.md` (1)
- [ ] `actions/.claude/agents/actions-auditor-reviewer.md` (1)
- [ ] `gh-optivem/BACKLOG.md` (2)
- [ ] `academy.code-workspace` (already covered in Phase 4)

## Phase 8 — Rename course lesson files (pending Option selection above)

~20 files across pipeline + atdd modules, all named `*-sandbox-project.md`. Example paths:
- `courses/01-pipeline/accelerator/course/{01..07}/0{4..9}-sandbox-project.md`
- `courses/02-atdd/accelerator/course/{01..15}/0{4..10}-sandbox-project.md`

- [ ] List exact file set with Glob
- [ ] Batch rename per chosen convention (e.g. `*-sandbox-project.md` → `*-project-submission.md`)
- [ ] Update internal file references (cross-links between lesson files, table-of-contents if any, module indexes)

## Phase 9 — Update memory

Three memory files need edits after the rename:

- [ ] `project_sandbox_renamed_to_reviews.md` — replace with a new memory: `project_reviews_renamed_to_hub.md` reflecting the final state (or consolidate history)
- [ ] `project_sandbox_scope.md` — update terminology: "sandbox" → "hub"
- [ ] `project_reviews_privacy_parked.md` — rename + update references to the new repo name
- [ ] `MEMORY.md` index — update pointers

## Phase 10 — Verify

- [ ] Re-run grep for `sandbox|Sandbox|SANDBOX` across all repos — should be zero or only in external student repo references (e.g. `ctf-sandbox`)
- [ ] Re-run grep for `optivem/reviews` or `academy/reviews` — should be zero
- [ ] Dashboard URL resolves: `https://optivem.github.io/hub/`
- [ ] Issue template works: open a test issue on `optivem/hub`, verify workflows fire correctly, delete test issue
- [ ] Run `/check-actions` across workspace to confirm no broken workflows
- [ ] Verify student-facing links in the course content all resolve (old reviews URLs redirect, but better to update them)

## Phase 11 — Commit + push

- [ ] `/commit` in claude, courses, hub (new name), actions, gh-optivem
- [ ] Announce the rename (if there's a student channel / doc / onboarding doc, update it)

## Out of scope (tracked separately)

- Per-course repo split → optivem/courses#85
- Labels / issue templates / dashboard redesign for per-course organization — follow-on after rename stabilizes
- GitHub Teams for course enrollment tracking — follow-on
- Privacy downgrade plan (Reviews privacy parked, Team→Free 2026-07-02) — tracked in memory
