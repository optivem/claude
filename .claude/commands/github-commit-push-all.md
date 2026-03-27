Run the commit-push-all script to commit and push all dirty repos in the academy workspace.

Execute the following command and report the output:

```bash
bash "$(git rev-parse --show-toplevel)/../github-utils/scripts/commit-push-all.sh" $ARGUMENTS
```

If `$ARGUMENTS` is provided, use it as the commit message. Otherwise the script uses its default message "Sync changes".

Report which repos were committed and pushed, and how many were already clean.
