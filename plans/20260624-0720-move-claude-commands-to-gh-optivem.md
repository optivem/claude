# 2026-06-24 07:20:00 UTC — Move Claude commands into gh-optivem for global install

🤖 **Picked up by agent** — `ValentinaLaptop` at `2026-06-24T08:31:15Z`


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

Step 6: Remove `scripts/sync-claude-settings.js`, `scripts/sync-all-claude-settings.sh`, `.claude/commands/`, and `.claude/settings.json` from `optivem/claude`; remove `sync-claude` and `claude-sync-settings` skills.

## Steps

- [ ] Step 6: Remove `scripts/sync-claude-settings.js`, `scripts/sync-all-claude-settings.sh`, `.claude/commands/`, and `.claude/settings.json` from `optivem/claude`; remove `sync-claude` and `claude-sync-settings` skills
- [ ] Step 7: Move `docs/` from `optivem/claude` to `gh-optivem/docs/claude/`; embed `CLAUDE.md` into `gh-optivem` source (used by `configure`) then delete it from `optivem/claude`
- [ ] Step 8: Remove `optivem/claude` from `academy.code-workspace` and archive the GitHub repo
- [ ] Step 9: Update README in `gh-optivem` with install + setup instructions (`gh optivem claude install`, `gh optivem claude configure`, `gh optivem claude setup`)

## Resolved decisions

- **Embedding strategy:** `go:embed` — bake command files and CLAUDE.md into the binary at compile time. Self-contained install, no external path assumptions.
- **Archive vs delete:** Archive the `optivem/claude` GitHub repo — keeps history accessible, marks it read-only.
