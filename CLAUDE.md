# Claude Code Guidelines

## General Rules

- Never use hardcoded local paths (e.g. `C:\Users\...`). Always resolve paths dynamically (e.g. `git rev-parse --show-toplevel`, `$HOME`, environment variables). The user works from different computers.
- Never use `isolation: "worktree"` when spawning agents. Worktrees leave behind orphaned directories that block git operations. Always run agents in the default (non-isolated) mode.
- When presenting options or asking for decisions, always mark one as **recommended** and explain why in one sentence. Minimize the number of choices the user needs to make — default to the recommended option and proceed unless the user objects.

## GitHub Issues

- When implementing a GitHub issue, after the work is done, tell the user it's complete and propose closing the ticket. Only close after the user approves.

## CLI Preferences

- Always use `gh` CLI instead of `git` for GitHub/remote operations (pushing, pulling, cloning, creating repos, etc.).
- For local-only operations with no `gh` equivalent (e.g. finding the repo root with `git rev-parse --show-toplevel`), `git` is acceptable.
- Always use plain `git pull` (merge), never `git pull --rebase`. Rebase can silently drop commits on conflict — merge is safer.
- Never commit, push, or sync repos with ad-hoc commands. Always use the `/commit` skill exclusively for these operations.
- Be conservative with `gh` API calls to avoid rate limiting. When monitoring CI runs, sleep at least 2 minutes between status checks. Prefer single batch queries over multiple parallel `gh` calls.

## Consistency Checks

- When checking consistency across files (e.g. latest vs legacy configs), always enumerate concretely before judging. List every item/stage/type in each file, then compare side-by-side and flag anything present in one but missing from the other.
- Never conclude "no changes needed" based on a quick read. Produce a structured comparison (table or list) that makes gaps self-evident before reaching any conclusion.
- "Consistent" means structural parity: every feature/type/stage in one file must have an equivalent in the other, unless explicitly documented otherwise.
