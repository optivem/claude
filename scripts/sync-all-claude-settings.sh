#!/bin/bash
# sync-all-claude-settings.sh
# Runs the Claude settings sync script to distribute settings across all workspace repos.
#
# Usage:
#   ./scripts/sync-all-claude-settings.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYNC_SCRIPT="$SCRIPT_DIR/sync-claude-settings.js"

if [[ ! -f "$SYNC_SCRIPT" ]]; then
  echo "Error: sync script not found at $SYNC_SCRIPT"
  exit 1
fi

echo "============================================"
echo "  Sync Claude Settings"
echo "============================================"
node "$SYNC_SCRIPT"
echo "============================================"
