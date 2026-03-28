Run the check-actions-all script to check GitHub Actions status across all repos in the academy workspace.

Execute the following command and report the output:

```bash
bash "$(git rev-parse --show-toplevel)/../github-utils/scripts/check-actions-all.sh"
```

Report which repos are passing, failing, or have no workflows. For any failures, show the workflow name and the commit that triggered the failure.
