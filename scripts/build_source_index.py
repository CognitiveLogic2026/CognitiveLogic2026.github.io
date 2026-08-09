#!/usr/bin/env python3
"""Generate the versioned deterministic source index from the governed registry."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from source_retrieval import INDEX_PATH, build_index  # noqa: E402


if __name__ == "__main__":
    index = build_index()
    print(f"wrote {INDEX_PATH} ({len(index['documents'])} sources, {index['index_version']})")
