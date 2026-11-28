#!/usr/bin/env bash
set -euo pipefail

PUBLIC_ROOT="${1:-/var/www/cognitivelogic-public}"
MANIFEST="ops/public-static-manifest.txt"

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

[ -f "$MANIFEST" ] || {
    echo "ERROR: missing $MANIFEST"
    exit 1
}

RETIRED="ops/retired-public-files.txt"

while IFS= read -r rel
do
    [[ "$rel" =~ ^(coste360\.html|case-studies/coste360/index\.html|img/og/coste360-case-study\.png|resources/documents/coste360-[a-z0-9-]+/index\.html)$ ]] || {
        echo "ERROR: invalid retired public path: $rel"
        exit 1
    }
    if [ -e "$rel" ] || git ls-files --error-unmatch "$rel" >/dev/null 2>&1; then
        echo "ERROR: retired public file is still in the repository: $rel"
        exit 1
    fi
done < "$RETIRED"

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
rsync -a --delete --exclude='*.bak*' international-watch/ "$PUBLIC_ROOT/international-watch/"

while IFS= read -r rel
do
    rm -f -- "$PUBLIC_ROOT/$rel"
    if [[ "$rel" == */index.html ]]; then
        retired_directory="$PUBLIC_ROOT/${rel%/index.html}"
        if [ -d "$retired_directory" ] && [ ! -L "$retired_directory" ]; then
            rmdir --ignore-fail-on-non-empty -- "$retired_directory"
        fi
    fi
done < "$RETIRED"

echo "Static synchronization completed: $updated manifest files."
