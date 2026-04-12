#!/usr/bin/env bash
# Vallm pre-commit hook: validate each staged .py file individually.
set -euo pipefail

config=""
if [ -f "vallm.toml" ]; then
    config="--config vallm.toml"
fi

failed=0
for file in "$@"; do
    if ! vallm validate -f "$file" $config; then
        failed=1
    fi
done

exit $failed
