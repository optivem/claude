# Claude Code Guidelines

## General Rules

- Never use hardcoded local paths (e.g. `C:\Users\...`). Always resolve paths dynamically (e.g. `git rev-parse --show-toplevel`, `$HOME`, environment variables). The user works from different computers.
- Never use `isolation: "worktree"` when spawning agents. Worktrees leave behind orphaned directories that block git operations. Always run agents in the default (non-isolated) mode.

## CLI Preferences

- Always use `gh` CLI instead of `git` for GitHub/remote operations (pushing, pulling, cloning, creating repos, etc.).
- For local-only operations with no `gh` equivalent (e.g. finding the repo root with `git rev-parse --show-toplevel`), `git` is acceptable.
- Always use plain `git pull` (merge), never `git pull --rebase`. Rebase can silently drop commits on conflict — merge is safer.
- Never commit, push, or sync repos with ad-hoc commands. Always use the `/github-commit-push-all` and `/github-sync-all` skills exclusively for these operations.
