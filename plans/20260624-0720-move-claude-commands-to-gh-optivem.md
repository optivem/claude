# 2026-06-24 07:20:00 UTC — Move Claude commands into gh-optivem for global install


## TL;DR

**Why:** Claude slash commands currently live in `optivem/claude`, a repo that exists solely to distribute them. Anyone who wants the commands must know to clone or sync that repo separately — there is no self-contained install story.
**End result:** The 13 slash commands, `settings.json`, and `CLAUDE.md` rules are embedded via `go:embed` inside `optivem/gh-optivem`. `gh optivem claude install` copies commands to `~/.claude/commands/`; `gh optivem claude configure` merges settings and CLAUDE.md rules into `~/.claude/` non-destructively (never deletes user's own entries); `gh optivem claude setup` runs both. Per-repo `.claude/settings.json` files are deleted across all workspace repos. The `optivem/claude` GitHub repo is archived and removed from the workspace.

## Outcomes

- Anyone who runs `gh extension install optivem/gh-optivem` can set up Claude with two focused commands: `gh optivem claude install` (commands only) and `gh optivem claude configure` (settings only), or `gh optivem claude setup` for both at once.
- Users who manage their own `~/.claude/settings.json` can skip `configure` — commands and settings are fully independent.
- Per-repo `.claude/settings.json` files are deleted from all workspace repos; settings live globally in `~/.claude/settings.json` only.
- `optivem/claude` is archived and removed from the workspace; the academy workspace has one fewer repo to maintain.
- The `sync-claude` and `claude-sync-settings` skills are removed (replaced by `gh optivem claude install`).

## ▶ Next executable step (resume here)

Resolve the open questions below, then begin Step 1: embed the 13 command files into `gh-optivem` using `go:embed` and add the `gh optivem claude install`, `configure`, and `setup` subcommands.

## Steps

- [ ] Step 1: Add `claude/commands/` directory to `gh-optivem`, copy the 13 `.md` files from `optivem/claude/.claude/commands/`, and embed them with `go:embed`
- [ ] Step 2: Add `gh optivem claude install` subcommand — writes embedded command files to `~/.claude/commands/` (skip-if-same, overwrite-if-different, print changed files)
- [ ] Step 3: Add `gh optivem claude configure` subcommand — merges two things into global Claude config, both non-destructively:
  - `settings.json` → `~/.claude/settings.json`: union `permissions.allow` lists, merge hooks additively, never delete user's own entries
  - `CLAUDE.md` rules → `~/.claude/CLAUDE.md`: append sections not already present, never overwrite existing content
- [ ] Step 4: Add `gh optivem claude setup` convenience subcommand — runs `install` then `configure`
- [ ] Step 5: Delete `.claude/settings.json` from all workspace repos (actions, claude, courses, gh-optivem, github-utils, hub, etc.) — global settings replace them
- [ ] Step 6: Remove `scripts/sync-claude-settings.js`, `scripts/sync-all-claude-settings.sh`, `.claude/commands/`, and `.claude/settings.json` from `optivem/claude`; remove `sync-claude` and `claude-sync-settings` skills
- [ ] Step 7: Move `docs/` from `optivem/claude` to `gh-optivem/docs/claude/`; embed `CLAUDE.md` into `gh-optivem` source (used by `configure`) then delete it from `optivem/claude`
- [ ] Step 8: Remove `optivem/claude` from `academy.code-workspace` and archive the GitHub repo
- [ ] Step 9: Update README in `gh-optivem` with install + setup instructions (`gh optivem claude install`, `gh optivem claude configure`, `gh optivem claude setup`)

## Resolved decisions

- **Embedding strategy:** `go:embed` — bake command files and CLAUDE.md into the binary at compile time. Self-contained install, no external path assumptions.
- **Archive vs delete:** Archive the `optivem/claude` GitHub repo — keeps history accessible, marks it read-only.
