Run the commit script to commit, pull, and push repos in the academy workspace.

Execute the following command and report the output:

```bash
bash "$(git rev-parse --show-toplevel)/../github-utils/scripts/commit.sh" $ARGUMENTS
```

`$ARGUMENTS` supports:
- No arguments: commits all repos with default message "Sync changes"
- `"message"`: commits all repos with a custom message
- `--repo <name>`: commits only the named repo with default message
- `--repo <name> "message"`: commits only the named repo with a custom message

Report which repos were committed, how many were synced, and how many were skipped.
