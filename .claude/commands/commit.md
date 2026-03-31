Run the commit script to commit, pull, and push all repos in the academy workspace.

Execute the following command and report the output:

```bash
bash "$(git rev-parse --show-toplevel)/../github-utils/scripts/commit.sh" $ARGUMENTS
```

If `$ARGUMENTS` is provided, use it as the commit message. Otherwise the script uses its default message "Sync changes".

Report which repos were committed, how many were synced, and how many were skipped.
