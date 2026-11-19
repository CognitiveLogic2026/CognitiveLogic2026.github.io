import json
import re
from pathlib import Path
from html.parser import HTMLParser


ROOT = Path(__file__).resolve().parents[1]


def page():
    return (ROOT / "fuorimenu" / "index.html").read_text(encoding="utf-8")


def test_fuorimenu_metadata_and_structured_data():
    html = page()
    class RootParser(HTMLParser):
        lang = None

        def handle_starttag(self, tag, attrs):
            if tag == "html":
                self.lang = dict(attrs).get("lang")

    parser = RootParser()
    parser.feed(html)
    assert parser.lang == "it"
    assert '<link rel="canonical" href="https://cognitivelogic.it/fuorimenu/">' in html
    assert '<meta property="og:url" content="https://cognitivelogic.it/fuorimenu/">' in html
    assert '<meta name="twitter:card" content="summary_large_image">' in html
    data = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL).group(1))
    assert data["@type"] == "CollectionPage"
    assert data["breadcrumb"]["@type"] == "BreadcrumbList"


def test_fuorimenu_editorial_boundaries_and_actions():
    html = page()
    assert "progetto editoriale di Cognitive Logic" in html
    assert "DFV-002" in html and "International Watch" in html
    assert "Dossier, assessment, evidenze" in html
    assert ">Leggi FuoriMenù " in html
    assert ">Iscriviti alla newsletter " in html
    external = re.findall(r'<a\b[^>]*href="https://fuorimenu\.substack\.com/[^"]*"[^>]*>', html)
    assert external and all('rel="noopener noreferrer"' in link for link in external)


def test_fuorimenu_uses_existing_feed_and_required_topics():
    html = page()
    script = (ROOT / "js" / "fuorimenu.js").read_text(encoding="utf-8")
    assert 'request.open("GET", "/data/fuorimenu.json"' in script
    assert "substack.com/feed" not in script
    for topic in ("Ristorazione e ospitalità", "QEN e territorio", "AI e governance", "Green claim e Italian sounding", "Dati, responsabilità e decisioni"):
        assert topic in html
    feed = json.loads((ROOT / "data" / "fuorimenu.json").read_text(encoding="utf-8"))
    assert feed["articoli"]
