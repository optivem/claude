Fix all open SonarCloud issues (warnings, code smells, bugs, vulnerabilities) on the SonarCloud project(s) connected to a repository, one issue at a time.

## Input

The target repo is provided as `$ARGUMENTS`. If no argument is given:
1. Default to the repo of the currently open file in the IDE (if any).
2. Else default to the current working directory's repo (`git rev-parse --show-toplevel`).
3. If neither can be resolved, ask the user: "Which repo should I fix SonarCloud warnings for?"

`$ARGUMENTS` may be either:
- A local repo folder name (e.g. `gh-optivem`) — resolved under the academy workspace root.
- An absolute path to a repo directory.

## Prerequisites

Before starting:
1. Verify `SONAR_TOKEN` is set in the environment. If not, stop and tell the user: "SONAR_TOKEN is not set. Generate one at https://sonarcloud.io/account/security and export it."
2. Verify `jq` and `curl` are available.

## Process

### Phase 1: Discover SonarCloud projects for this repo

A repository may publish to **multiple** SonarCloud project keys (e.g. a monorepo with frontend + backend + system-test). Enumerate them all before fetching issues.

1. **Grep the repo** for every `sonar.projectKey` and `sonar.organization` value. Look in:
   - `.github/workflows/*.yml` (search for `-Dsonar.projectKey=` and `sonar.projectKey=`)
   - `build.gradle`, `pom.xml`, `sonar-project.properties`, `SonarScanner*.ps1`, `Run-Sonar.ps1`
   - Any `*.csproj` or `.sonarcloud.properties`

   Use Grep with pattern `sonar\.projectKey|sonar\.organization` across the repo. Record the source file + line for each hit.

   Every SonarCloud project in this workspace is declared in a CI scan job — there are no UI-only bindings — so grep is authoritative. No API fallback needed.

2. **Print what was found** — always, before doing anything else. Format:

   ```
   SonarCloud projects for <repo>:
     ✓ optivem_<key-1>   (from .github/workflows/foo-commit-stage.yml:43)
     ✓ optivem_<key-2>   (from .github/workflows/bar-commit-stage.yml:43)
     ✓ optivem_<key-3>   (from system-test/dotnet/Run-Sonar.ps1:30)

   Total: 3 project keys, organization: optivem
   ```

3. If **zero** project keys are found, stop and ask the user: "No `sonar.projectKey` declaration found in this repo. Does it publish to SonarCloud? Provide a project key, or skip." Do not guess.

### Phase 2: Fetch open issues

For each `(organization, projectKey)` pair, call the SonarCloud issues API:

```bash
curl -s -H "Authorization: Bearer $SONAR_TOKEN" \
  "https://sonarcloud.io/api/issues/search?componentKeys=<projectKey>&resolved=false&ps=500&p=1" \
  | jq '.issues'
```

Paginate if `paging.total > paging.pageSize`. Sleep 2+ seconds between paged requests.

Collect all open issues across all project keys into one list. For each issue, extract:
- `key` (SonarCloud issue id)
- `rule` (e.g. `java:S1192`)
- `severity` (BLOCKER / CRITICAL / MAJOR / MINOR / INFO)
- `type` (BUG / VULNERABILITY / CODE_SMELL / SECURITY_HOTSPOT)
- `component` (file path as `<projectKey>:<repoRelativePath>`) → strip the `<projectKey>:` prefix to get the repo-relative path
- `line` (1-indexed)
- `message`

### Phase 3: Present plan

Summarize to the user:

```
Open SonarCloud issues: N total
  By severity: BLOCKER=x, CRITICAL=x, MAJOR=x, MINOR=x, INFO=x
  By type:     BUG=x, VULNERABILITY=x, CODE_SMELL=x, HOTSPOT=x
  Top rules:   java:S1192 (12), java:S125 (8), ...
```

If the total is zero, report "No open SonarCloud issues for <repo>." and stop.

Otherwise **proceed without asking** (per auto-commit / recommend-and-proceed conventions), processing issues in this order:
1. BLOCKER bugs + vulnerabilities first
2. CRITICAL bugs + vulnerabilities
3. MAJOR → MINOR → INFO
4. Within a severity, group by file to minimize back-and-forth edits on the same file.

### Phase 4 (preferred): Delegate each SonarCloud project to its own subagent

When the repo has multiple SonarCloud project keys, do **not** fix all issues in the main conversation — that bloats context with file reads from every project. Instead, spawn one subagent per project key, each scoped to a single SonarCloud project. The main thread:

1. Writes the fetched issues for each project to `<repo>/.tmp/sonar/<projectKey>.json` (already done in Phase 2).
2. Launches a subagent per project (in parallel where independent) with a self-contained prompt that includes:
   - The project key and the path to its issues JSON.
   - The repo-relative source root (e.g. `system/monolith/java`, `system-test/typescript`).
   - The skip list (e.g. rules already deemed intentional like `typescript:S7739` for the BDD `.then` DSL — pass these in explicitly so the subagent doesn't re-investigate).
   - The deferred-plan path: `<repo>/plans/sonar-deferred.md` — append, do not overwrite.
   - Instructions to fix, run the local build/typecheck for that project once, and **commit** for that project (using the per-project commit pattern in Phase 5). Subagents commit on their own — do not collect changes back to main.
3. Each subagent returns a short structured summary (fixed count, deferred count, commit SHA) — the main thread aggregates these into the final report.

Subagent prompts should be self-contained: include the rule's expected fix where it's a known mechanical pattern (e.g. "`new Error(...)` → `new TypeError(...)` for S7786", "return type `: ClassName` → `: this` for S6565 on fluent builder methods that `return this`"), so the subagent doesn't need to re-fetch rule descriptions.

Use the **general-purpose** agent type with full tool access. Do not use worktree isolation (per CLAUDE.md).

If the repo has only **one** SonarCloud project key, skip subagent delegation and inline the work — Phase 4 (inline) below applies.

### Phase 4 (inline, single-project fallback): Fix issues one by one

For each issue:

1. **Read** the file at `component`:`line` (with a few lines of context).
2. **Understand the rule.** If the rule isn't obvious from `message` + file context, fetch the rule description once:
   ```bash
   curl -s -H "Authorization: Bearer $SONAR_TOKEN" \
     "https://sonarcloud.io/api/rules/show?key=<rule>" | jq '.rule.htmlDesc'
   ```
   Cache rule descriptions in-memory across the run — don't re-fetch for repeated rules.
3. **Apply the fix** with Edit (or Write for new files, e.g. missing `equals`/`hashCode` helper).
4. **Verify locally.** If the repo has a build target that compiles the changed language, run it once per batch (group fixes per-file, then run build after the batch on that file). Do not run a full build after every single issue.
5. **Defer blockers — do not stop the whole run.** If a fix is ambiguous, affects public API, or the build fails after your change, do **not** halt the run waiting for input. Instead, append the issue to a plan file at `<repo>/plans/sonar-deferred-<YYYY-MM-DD-HHMM>.md` (UTC timestamp **in the filename itself**, e.g. `plans/sonar-deferred-2026-04-27-1056.md`) and continue with the remaining issues. Mention the deferred file at the end in the final report.

   Get the timestamp with `date -u +"%Y-%m-%d-%H%M"` so it's reproducible. Each `/fix-sonar-warnings` run gets its own dated file — never overwrite a prior run's deferred file. Inside the file, also include a `**Run started:** YYYY-MM-DD HH:MM UTC` header for human readability. Each issue gets its own section with: rule, file:line, message, what was tried, the open question / decision needed.
6. **Do not mark the issue as resolved via the API.** SonarCloud will auto-resolve issues on the next analysis run after the commit stage executes.

### Phase 5: Commit

**Before committing anything, run compilation / typecheck on EVERY project in the repo — not just the ones you touched.** This is mandatory. A SonarCloud fix in one project (e.g. a shared library or interface) can break a sibling project that depends on it. The user explicitly wants every project verified before a single commit lands.

**Preferred: use the repo's `compile-all.sh` script** (or equivalent if the repo has a different name for it — check the repo root). It walks every system + system-test project and runs the language-appropriate compile/typecheck:
- `./compile-all.sh` from the repo root
- exits non-zero if any project fails

If `compile-all.sh` doesn't exist, fall back to per-language commands (run in parallel where independent):
- Java: `./gradlew compileJava --no-daemon -q` (or `mvn compile -q`)
- TypeScript: `npx tsc --noEmit` (or `npm run type-check` / `npm run lint` if defined)
- .NET: `dotnet build --nologo -v q`

If a project fails to compile, **do not commit anything**. Investigate the failure — most often it's an over-broad `replace_all` that hit a pattern in addition to the intended targets (e.g. a SonarCloud rule asked to change a return type on a fluent method, but `replace_all` of `: ClassName {` also caught a factory method that genuinely returns a different class). Fix the root cause, re-run `compile-all.sh`, and only then commit.

When all fixes for the repo are staged and verified:

1. **One combined commit per repo, not per SonarCloud project.** Even when the repo publishes to multiple SonarCloud project keys (e.g. monolith-java, monolith-typescript, multitier-backend-java, etc.), make a single commit covering all the fixes for the whole run. The commit message must enumerate every SonarCloud project key touched and a per-project rule breakdown so traceability is preserved without splitting commits.
   - Example commit message:
     ```
     fix: resolve N SonarCloud issues across M projects

     - optivem_shop-monolith-java (12): java:S106×3, java:S112×2, java:S2142×1
     - optivem_shop-monolith-typescript (5): typescript:S7721×3, typescript:S7735×1, typescript:S4325×1
     - optivem_shop-tests-typescript (80): typescript:S6565×42, typescript:S2933×13, ...
     ```
   - **Do not use ad-hoc `git add` / `git commit`** (per CLAUDE.md, the commit script is mandatory for all commit/push operations).
   - The `commit.sh --paths` flag exists for other use cases but should NOT be used to split one SonarCloud run into multiple commits — the user prefers one commit for the whole run.
2. **Auto-commit — do not block on the user.** Per the global `feedback_auto_commit` rule, run the commit script without asking. The only things that wait for the user are items written to `<repo>/plans/sonar-deferred.md` (see Phase 4 step 5).
3. Commit via the commit script (per CLAUDE.md — never ad-hoc). To scope a commit to specific paths, pass the paths to the script:
   ```bash
   bash "$(git rev-parse --show-toplevel)/../github-utils/scripts/commit.sh" --repo <repo-name> "<summary>"
   ```

### Phase 6: Report

Produce a final report:

```
SonarCloud fix run — <repo>
  Fixed:    N issues across M files
  Skipped:  K issues (list with reason: needs API change / human judgment / blocked on decision)
  Unclear:  J issues (list with question)
  Commits:  <sha1>, <sha2>
```

## Rules

- Read-only on SonarCloud: never call `projects/delete`, `issues/do_transition`, or any mutating SonarCloud endpoint. The goal is to fix the code — SonarCloud re-analysis will clear the issues.
- Never edit generated code, `.tmp/`, `dist/`, `build/`, `target/`, `node_modules/`, or archived folders.
- Respect the project's existing style — match formatting, indentation, naming conventions of the surrounding file.
- If a rule is disputed or the fix would regress behavior (e.g. the "duplicate string literal" rule asking you to extract a constant that hurts readability), skip and list it under **Skipped** with the reason.
- Sleep 2+ seconds between SonarCloud API calls and 1+ minute between any `gh` status polls (per rate-limit conventions).
- Never use `gh api` to read file contents — all file reads happen locally (repo is already checked out).
- On auth failure (HTTP 401/403), stop immediately and report — do not retry.
