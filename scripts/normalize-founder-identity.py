#!/usr/bin/env python3
"""Give personal Roberto Malini JSON-LD entities one stable identifier."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PERSON_ID = "https://cognitivelogic.it/#founder"


def update(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    updated = re.sub(
        r'("@type"\s*:\s*"Person"\s*,)(\s*)("name"\s*:\s*"Roberto(?: Bob)? Malini")',
        rf'\1\2"@id": "{PERSON_ID}",\2"name": "Roberto Bob Malini"',
        original,
    )
    updated = re.sub(
        r'("@type"\s*:\s*"Person"\s*,\s*"@id"\s*:\s*"https://cognitivelogic\.it/#founder"\s*,\s*"name"\s*:\s*)"Roberto Malini"',
        r'\1"Roberto Bob Malini"',
        updated,
    )
    updated = re.sub(
        r'(<meta\s+name=["\']author["\']\s+content=["\'])Roberto(?: Bob)? Malini(?:\s+[—|-]\s+Cognitive Logic)?(["\'])',
        r'\1Roberto Bob Malini — Cognitive Logic\2',
        updated,
        flags=re.IGNORECASE,
    )
    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def main() -> None:
    changed = [path for path in ROOT.rglob("*.html") if update(path)]
    print(f"Normalized founder identity in {len(changed)} HTML files")


if __name__ == "__main__":
    main()
