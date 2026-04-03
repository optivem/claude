# Claude Code Guidelines

## General Rules

- Never use hardcoded local paths (e.g. `C:\Users\...`). Always resolve paths dynamically (e.g. `git rev-parse --show-toplevel`, `$HOME`, environment variables). The user works from different computers.
- Never use `isolation: "worktree"` when spawning agents. Worktrees leave behind orphaned directories that block git operations. Always run agents in the default (non-isolated) mode.

## GitHub Issues

- When implementing a GitHub issue, after the work is done, tell the user it's complete and propose closing the ticket. Only close after the user approves.

## CLI Preferences

- Always use `gh` CLI instead of `git` for GitHub/remote operations (pushing, pulling, cloning, creating repos, etc.).
- For local-only operations with no `gh` equivalent (e.g. finding the repo root with `git rev-parse --show-toplevel`), `git` is acceptable.
- Always use plain `git pull` (merge), never `git pull --rebase`. Rebase can silently drop commits on conflict — merge is safer.
- Never commit, push, or sync repos with ad-hoc commands. Always use the `/commit` skill exclusively for these operations.
- Be conservative with `gh` API calls to avoid rate limiting. When monitoring CI runs, sleep at least 2 minutes between status checks. Prefer single batch queries over multiple parallel `gh` calls.
