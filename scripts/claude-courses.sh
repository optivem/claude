#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACADEMY_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

ADD_DIRS=()
for dir in "$ACADEMY_ROOT"/*/; do
    name="$(basename "$dir")"
    if [ "$name" != "courses" ] && [ -d "$dir/.git" ]; then
        ADD_DIRS+=(--add-dir "$dir")
    fi
done

cd "$ACADEMY_ROOT/courses"
exec claude "${ADD_DIRS[@]}" "$@"
