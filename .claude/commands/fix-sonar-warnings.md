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

### Phase 4: Fix issues one by one

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
5. **Stop on problems.** If a fix is ambiguous, affects public API, or the build fails after your change, **stop** — do not auto-fix or escalate. Report: "Issue <key> (<rule>) at <file>:<line> — <short reason for stopping>. Proposed options: ... Waiting for input."
6. **Do not mark the issue as resolved via the API.** SonarCloud will auto-resolve issues on the next analysis run after the commit stage executes.

### Phase 5: Commit

When all fixes for the repo are staged and verified:

1. Group changes logically. If fixes touched >1 file and cover multiple rules, a single commit with a message like `fix: resolve N SonarCloud issues (java:S1192×12, java:S125×8)` is fine.
2. Commit via the commit script (per CLAUDE.md — never ad-hoc):
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
