import json
import re
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "manifesto-verita-verificabile" / "index.html"
CANONICAL = "https://cognitivelogic.it/manifesto-verita-verificabile/"


class ManifestoParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1 = 0
        self.ids = set()
        self.links = []
        self.meta = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "h1":
            self.h1 += 1
        if values.get("id"):
            self.ids.add(values["id"])
        if tag == "a" and values.get("href"):
            self.links.append((values["href"], values.get("class", "")))
        if tag == "meta":
            self.meta.append(values)


def test_manifesto_page_metadata_accessibility_and_structure():
    html = PAGE.read_text(encoding="utf-8")
    parser = ManifestoParser()
    parser.feed(html)
    assert parser.h1 == 1
    assert "main" in parser.ids
    assert any(href == "#main" and "skip-link" in classes for href, classes in parser.links)
    assert f'<link rel="canonical" href="{CANONICAL}">' in html
    assert '<meta property="og:url" content="' + CANONICAL + '">' in html
    assert '<meta name="twitter:card" content="summary_large_image">' in html
    assert 'hreflang=' not in html
    assert "DFV-002" in html and "Testo fondativo vigente" in html
    assert "Le dodici tesi della verità verificabile" in html
    assert "Verificabilità = Identità + Provenienza + Evidenze + Metodo + Contesto + Tempo + Limiti" in html
    assert "QEN Sovereign non è l’autorità della verità" in html


def test_manifesto_structured_data_and_required_internal_links():
    html = PAGE.read_text(encoding="utf-8")
    block = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    assert block
    data = json.loads(block.group(1))
    assert data["@type"] == "Article"
    assert data["mainEntityOfPage"] == CANONICAL
    for target in ("/identity.html#manifesto", "/trust.html", "/framework.html", "/operational-record.html", "/resources/"):
        assert f'href="{target}"' in html


def test_manifesto_is_discoverable_without_entering_primary_navigation():
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    trust = (ROOT / "trust.html").read_text(encoding="utf-8")
    assert sitemap.count(CANONICAL) == 1
    main = trust[trust.index('<main id="main">'):]
    assert main.index("Manifesto della Verità Verificabile") < main.index("Governance Framework")
    nav = re.search(r'<nav class="main-nav".*?</nav>', trust, re.S).group(0)
    assert "/manifesto-verita-verificabile/" not in nav
