import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PERSON_ID = "https://cognitivelogic.it/#founder"


def walk(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)


def test_roberto_person_entities_share_one_identity():
    found = 0
    for path in ROOT.rglob("*.html"):
        html = path.read_text(encoding="utf-8")
        for payload in re.findall(
            r'<script\s+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            html,
            re.I | re.S,
        ):
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                continue
            for entity in walk(data):
                kind = entity.get("@type")
                kinds = kind if isinstance(kind, list) else [kind]
                if "Person" in kinds and re.fullmatch(
                    r"Roberto(?: Bob)? Malini", str(entity.get("name", ""))
                ):
                    found += 1
                    assert entity["@id"] == PERSON_ID, path
                    assert entity["name"] == "Roberto Bob Malini", path
                    # The shared @id resolves the author to the complete Person
                    # entity published on about.html without duplicating its profile.
    assert found >= 30


def test_public_aliases_are_present_and_not_indexed():
    expected = {
        "research/index.html": ("https://cognitivelogic.it/research.html", "/research.html"),
        "accessibility.html": ("https://cognitivelogic.it/accessibilita.html", "/accessibilita.html"),
    }
    for relative, (canonical, target) in expected.items():
        html = (ROOT / relative).read_text(encoding="utf-8")
        assert '<meta name="robots" content="noindex,follow">' in html
        assert f'<link rel="canonical" href="{canonical}">' in html
        assert f'url={target}' in html
        assert f'href="{target}"' in html


def test_founder_page_lists_verified_doi_and_external_publications():
    html = (ROOT / "about.html").read_text(encoding="utf-8")
    for value in (
        "https://doi.org/10.5281/zenodo.22850822",
        "https://doi.org/10.5281/zenodo.22850821",
        "https://www.innovationpost.it/tecnologie/industrial-it/perche-quando-lai-decide-in-fabbrica-servono-evidenze-verificabili/",
        "https://www.italiaatavola.net/horeca/2026/9/25/hotel-ristoranti-anche-dato-corretto-puo-portare-decisioni-sbagliate/121545/",
        "https://rivista.camminodiritto.it/articolo.asp?id=11970",
    ):
        assert value in html
    assert "Tech Policy Press" not in html
    assert "European Law Blog" not in html
    assert "id=11964" not in html
