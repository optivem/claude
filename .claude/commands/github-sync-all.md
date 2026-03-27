Run the github-sync-all script to pull then push all repos in the academy workspace (like VS "Sync").

Execute the following command and report the output:

```bash
bash "$(git rev-parse --show-toplevel)/../github-utils/scripts/github-sync-all.sh"
```

Report which repos were pulled and pushed, and how many were skipped.
