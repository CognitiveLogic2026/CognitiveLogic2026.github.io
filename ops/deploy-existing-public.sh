#!/usr/bin/env bash
set -euo pipefail

PUBLIC_ROOT="${1:-/var/www/cognitivelogic-public}"
MANIFEST="ops/public-static-manifest.txt"

cd /app/cognitivelogic

[ -f "$MANIFEST" ] || {
    echo "ERROR: missing $MANIFEST"
    exit 1
}

updated=0

while IFS= read -r rel
do
    [ -n "$rel" ] || continue

    if [ ! -f "$rel" ]; then
        echo "ERROR: manifest file missing from repository: $rel"
        exit 1
    fi

    git ls-files --error-unmatch "$rel" >/dev/null 2>&1 || {
        echo "ERROR: manifest file is not tracked by git: $rel"
        exit 1
    }

    install -D -m 0644 "$rel" "$PUBLIC_ROOT/$rel"
    echo "UPDATED $rel"
    updated=$((updated + 1))
done < "$MANIFEST"

mkdir -p "$PUBLIC_ROOT/international-watch"
rsync -a --delete international-watch/ "$PUBLIC_ROOT/international-watch/"

echo "Static synchronization completed: $updated manifest files."
