Run the sync script to pull and push all repos in the academy workspace (no commit).

Execute the following command and report the output:

```bash
bash "$(git rev-parse --show-toplevel)/../github-utils/scripts/sync.sh"
```

Report how many repos were synced and how many were skipped.
