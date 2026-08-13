from html.parser import HTMLParser
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []; self.h1 = 0
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "a" and "href" in values: self.links.append(values["href"])
        if tag == "h1": self.h1 += 1

def test_case_studies_links_use_catalogue():
    offenders = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*.html") if p.name != "case-studies.html" and re.search(r'href="[^"]*case-studies\.html', p.read_text(encoding="utf-8"))]
    assert offenders == []

def test_legacy_case_studies_bridge():
    html = (ROOT / "case-studies.html").read_text(encoding="utf-8")
    assert '<link rel="canonical" href="https://cognitivelogic.it/case-studies/">' in html
    assert '<meta name="robots" content="noindex,follow">' in html
    assert '<meta http-equiv="refresh" content="0; url=/case-studies/">' in html
    assert 'href="/case-studies/"' in html

def test_english_homepage_sovereign_positioning():
    html = (ROOT / "index_en.html").read_text(encoding="utf-8"); lower = html.lower()
    for obsolete in ("dual-brain", "dual brain", "claude", "gemini", "mistral"): assert obsolete not in lower
    assert "QEN Sovereign" in html and "human decision authority" in lower
    parser = Parser(); parser.feed(html)
    assert parser.h1 == 1 and "#main" in parser.links and "/case-studies/" in parser.links
