#!/usr/bin/env python3
"""Submit current canonical Cognitive Logic URLs to IndexNow."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit, urlunsplit
import xml.etree.ElementTree as ET

HOST = "cognitivelogic.it"
ORIGIN = f"https://{HOST}"
ENDPOINT = "https://api.indexnow.org/indexnow"
KEY = "98a1d7841739b050984005b53993e244"
KEY_LOCATION = f"{ORIGIN}/{KEY}.txt"
MAX_BATCH_SIZE = 10_000
KEY_RE = re.compile(r"^[A-Za-z0-9-]{8,128}$")

# Repository areas which are never directly published as static site content.
INTERNAL_PREFIXES = (
    ".git/", ".github/", ".agents/", ".codex/", "tests/", "scripts/",
    "docs/", "documentation-audit/", "commercial-evolution-1.0/",
    "enterprise-platform-evolution-1.0/", "commercial-platform/",
    "housekeeping-2026/", "qen-sovereign/", "qen-enterprise-assessment/",
    "qen-reconciliation/", "qen-bolkestein/", "qen-horeca-auditor/",
    "wizard-src/", "__pycache__/",
)
PUBLIC_ASSET_SUFFIXES = {
    ".css", ".js", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
    ".ico", ".avif", ".pdf", ".woff", ".woff2", ".webmanifest",
}


class MetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.canonical: str | None = None
        self.noindex = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): (value or "") for key, value in attrs}
        if tag.lower() == "link" and "canonical" in values.get("rel", "").lower().split():
            self.canonical = values.get("href")
        if tag.lower() == "meta" and values.get("name", "").lower() == "robots":
            directives = re.split(r"[\s,]+", values.get("content", "").lower())
            self.noindex = "noindex" in directives


def read_sitemap(path: Path) -> list[str]:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise ValueError(f"cannot read sitemap {path}: {exc}") from exc
    urls: list[str] = []
    for node in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
        location = node.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
        if location is not None and location.text:
            urls.append(validate_url(location.text.strip()))
    if not urls:
        raise ValueError(f"sitemap contains no URLs: {path}")
    return deduplicate(urls)


def file_for_url(url: str, repo: Path) -> Path:
    path = urlsplit(url).path
    if path == "/":
        return repo / "index.html"
    if path.endswith("/"):
        return repo / path.lstrip("/") / "index.html"
    return repo / path.lstrip("/")


def current_sitemap_urls(path: Path, repo: Path) -> list[str]:
    """Keep only sitemap entries backed by a real, indexable canonical page."""
    current: list[str] = []
    for url in read_sitemap(path):
        page = file_for_url(url, repo)
        if page.suffix.lower() != ".html" or not page.is_file():
            continue
        metadata = html_metadata(page)
        if metadata.noindex:
            continue
        if metadata.canonical:
            try:
                if validate_url(metadata.canonical) != url:
                    continue
            except ValueError:
                continue
        current.append(url)
    if not current:
        raise ValueError("sitemap has no current indexable canonical pages")
    return current


def validate_url(value: str) -> str:
    parts = urlsplit(value.strip())
    if parts.scheme != "https" or parts.hostname != HOST or parts.port is not None:
        raise ValueError(f"external or non-HTTPS URL rejected: {value}")
    if parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError(f"non-canonical URL form rejected: {value}")
    if parts.netloc != HOST or not parts.path.startswith("/") or "//" in parts.path:
        raise ValueError(f"non-canonical URL form rejected: {value}")
    return urlunsplit(("https", HOST, parts.path or "/", "", ""))


def deduplicate(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def candidate_url_for_html(relative_path: str) -> str:
    path = PurePosixPath(relative_path)
    if path.name == "index.html":
        parent = path.parent.as_posix()
        suffix = "/" if parent == "." else f"/{parent}/"
    else:
        suffix = f"/{path.as_posix()}"
    return f"{ORIGIN}{suffix}"


def html_metadata(path: Path) -> MetadataParser:
    parser = MetadataParser()
    try:
        parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    except OSError as exc:
        raise ValueError(f"cannot inspect public page {path}: {exc}") from exc
    return parser


def is_internal(path: str) -> bool:
    return path.startswith(INTERNAL_PREFIXES) or path.endswith(".py")


def map_files(paths: list[str], repo: Path, sitemap_urls: list[str]) -> tuple[list[str], bool]:
    """Return canonical URLs and whether an ambiguous public change needs fallback."""
    allowed = set(sitemap_urls)
    mapped: list[str] = []
    fallback = False
    for raw_path in deduplicate(paths):
        relative = raw_path.strip().replace("\\", "/")
        while relative.startswith("./"):
            relative = relative[2:]
        parts = PurePosixPath(relative).parts
        if not relative or relative.startswith("/") or ".." in parts:
            continue
        if not relative or is_internal(relative):
            continue
        if relative == "sitemap.xml":
            fallback = True
            continue
        suffix = PurePosixPath(relative).suffix.lower()
        if suffix == ".html":
            candidate = candidate_url_for_html(relative)
            file_path = repo / relative
            if not file_path.is_file():
                # Deleted pages are intentionally not submitted: only current canonicals qualify.
                continue
            metadata = html_metadata(file_path)
            if metadata.noindex:
                continue
            if metadata.canonical:
                try:
                    canonical = validate_url(metadata.canonical)
                except ValueError:
                    continue
                if canonical != candidate:
                    continue
            if candidate in allowed:
                mapped.append(candidate)
            continue
        if suffix in PUBLIC_ASSET_SUFFIXES or relative in {"_headers", "robots.txt"}:
            fallback = True
    return deduplicate(mapped), fallback


def build_payload(urls: list[str]) -> dict[str, object]:
    return {"host": HOST, "key": KEY, "keyLocation": KEY_LOCATION, "urlList": urls}


def submit_batch(urls: list[str], timeout: float) -> int:
    data = json.dumps(build_payload(urls), ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT, data=data, headers={"Content-Type": "application/json; charset=utf-8"}, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
            body = response.read(1000).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read(1000).decode("utf-8", errors="replace")
        print(f"IndexNow HTTP {exc.code}: {body or exc.reason}", file=sys.stderr)
        return 1
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"IndexNow request failed: {exc}", file=sys.stderr)
        return 1
    if status not in (200, 202):
        print(f"IndexNow unexpected HTTP {status}: {body}", file=sys.stderr)
        return 1
    state = "accepted" if status == 200 else "accepted; key verification pending"
    print(f"IndexNow HTTP {status}: {state} ({len(urls)} URLs)")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="*", help="specific canonical URLs (default: all sitemap URLs)")
    parser.add_argument("--sitemap", type=Path, default=Path("sitemap.xml"))
    parser.add_argument("--files-from", type=Path, help="newline-delimited changed repository paths")
    parser.add_argument("--dry-run", action="store_true", help="print validated payloads without network calls")
    parser.add_argument("--timeout", type=float, default=20.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not KEY_RE.fullmatch(KEY):
        print("configured IndexNow key has an invalid format", file=sys.stderr)
        return 2
    try:
        sitemap_urls = current_sitemap_urls(args.sitemap, Path.cwd())
        allowed = set(sitemap_urls)
        if args.files_from and args.urls:
            raise ValueError("specific URLs and --files-from are mutually exclusive")
        if args.files_from:
            changed = args.files_from.read_text(encoding="utf-8").splitlines()
            urls, fallback = map_files(changed, Path.cwd(), sitemap_urls)
            if fallback:
                print("Ambiguous public change detected; using conservative sitemap fallback.")
                urls = sitemap_urls
        elif args.urls:
            urls = deduplicate([validate_url(url) for url in args.urls])
            unknown = [url for url in urls if url not in allowed]
            if unknown:
                raise ValueError("URL is not a current sitemap canonical: " + ", ".join(unknown))
        else:
            urls = sitemap_urls
    except (OSError, ValueError) as exc:
        print(f"IndexNow input error: {exc}", file=sys.stderr)
        return 2

    if not urls:
        print("No current canonical URLs to submit.")
        return 0
    for start in range(0, len(urls), MAX_BATCH_SIZE):
        batch = urls[start:start + MAX_BATCH_SIZE]
        payload = build_payload(batch)
        if args.dry_run:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        elif submit_batch(batch, args.timeout):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
