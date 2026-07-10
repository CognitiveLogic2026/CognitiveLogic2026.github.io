# Copyright (c) 2026 Roberto Malini - Cognitive Logic
# https://www.cognitivelogic.it
# Licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
import urllib.request, urllib.error, json, re, os, sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html import escape

RSS_DIRECT = "https://fuorimenu.substack.com/feed"
RSS_PROXY  = "https://api.rss2json.com/v1/api.json?rss_url=https%3A%2F%2Ffuorimenu.substack.com%2Ffeed&count=10"
OUT_PATH   = "data/fuorimenu.json"
MD_PATH    = "fuorimenu.md"
HTML_PATH  = "fuorimenu.html"
MD_MARKER_START   = "<!-- FUORIMENU:ARTICLES:START -->"
MD_MARKER_END     = "<!-- FUORIMENU:ARTICLES:END -->"
HTML_MARKER_START = "<!-- FUORIMENU:ARTICLES:START -->"
HTML_MARKER_END   = "<!-- FUORIMENU:ARTICLES:END -->"

def strip_html(text):
    return re.sub(r'<[^>]+>', '', text or '').strip()

def fetch(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()

def parse_xml(raw):
    root = ET.fromstring(raw)
    channel = root.find('channel')
    if channel is None:
        raise ValueError("Nessun <channel> nel feed RSS")
    articoli = []
    for item in list(channel.findall('item'))[:10]:
        desc = strip_html(
            item.findtext('{http://purl.org/rss/1.0/modules/content/}encoded')
            or item.findtext('description') or ''
        )[:280]
        articoli.append({
            "titolo":   (item.findtext('title') or '').strip(),
            "url":      (item.findtext('link') or '').strip(),
            "data":     (item.findtext('pubDate') or '')[:16],
            "estratto": desc,
            "tag":      "Fuorimenu"
        })
    return articoli

def parse_json_proxy(raw):
    data = json.loads(raw)
    if data.get('status') != 'ok':
        raise ValueError(f"rss2json error: {data.get('message','unknown')}")
    articoli = []
    for item in data.get('items', [])[:10]:
        desc = strip_html(item.get('description', ''))[:280]
        articoli.append({
            "titolo":   item.get('title', '').strip(),
            "url":      item.get('link', '').strip(),
            "data":     item.get('pubDate', '')[:16],
            "estratto": desc,
            "tag":      "Fuorimenu"
        })
    return articoli

def render_md_list(articoli):
    lines = []
    for i, a in enumerate(articoli, 1):
        titolo = a['titolo'].replace('[', '(').replace(']', ')')
        lines.append(f"{i}. **[{titolo}]({a['url']})** — {a['data']} — {a['estratto']}")
    return "\n".join(lines)

def render_html_cards(articoli):
    cards = []
    for a in articoli:
        cards.append(f"""          <div class="ed">
            <div class="ed-tag">{escape(a['tag'])} · {escape(a['data'])}</div>
            <div class="ed-title">{escape(a['titolo'])}</div>
            <div class="ed-quote">{escape(a['estratto'])}</div>
            <div class="ed-meta"><span>Roberto Bob Malini · Fuorimenu</span><a href="{escape(a['url'])}" target="_blank" rel="noopener">→ Leggi su Substack</a></div>
          </div>""")
    return '        <div class="ed-grid">\n' + "\n".join(cards) + "\n        </div>"

def replace_between_markers(text, start_marker, end_marker, new_inner):
    pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.DOTALL)
    replacement = f"{start_marker}\n{new_inner}\n{end_marker}"
    return pattern.sub(lambda _: replacement, text, count=1)

def sync_markdown_file(path, articoli, sync_ts):
    if not os.path.exists(path):
        return False
    text = open(path, 'r', encoding='utf-8').read()
    if MD_MARKER_START not in text or MD_MARKER_END not in text:
        return False
    body = (
        "## Ultimi articoli\n\n"
        f"_Aggiornato automaticamente ogni 6 ore da `sync_rss.py` via GitHub Actions · "
        f"fonte: [fuorimenu.substack.com/feed](https://fuorimenu.substack.com/feed) · "
        f"ultimo sync: {sync_ts}_\n\n"
        + render_md_list(articoli)
    )
    new_text = replace_between_markers(text, MD_MARKER_START, MD_MARKER_END, body)
    if new_text != text:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_text)
        return True
    return False

def sync_html_file(path, articoli, sync_ts):
    if not os.path.exists(path):
        return False
    text = open(path, 'r', encoding='utf-8').read()
    if HTML_MARKER_START not in text or HTML_MARKER_END not in text:
        return False
    new_text = replace_between_markers(text, HTML_MARKER_START, HTML_MARKER_END, render_html_cards(articoli))
    new_text = re.sub(
        r'(<span id="fm-sync-ts">)[^<]*(</span>)',
        lambda m: f"{m.group(1)}{sync_ts}{m.group(2)}",
        new_text, count=1
    )
    if new_text != text:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_text)
        return True
    return False

articoli = None
errors = []

# Tentativo 1: feed RSS diretto (più affidabile, nessuna dipendenza esterna)
try:
    ua = "Mozilla/5.0 (compatible; CognitiveLogicBot/1.0; +https://www.cognitivelogic.it)"
    raw = fetch(RSS_DIRECT, {"User-Agent": ua, "Accept": "application/rss+xml, application/xml, text/xml"})
    articoli = parse_xml(raw)
    print(f"Feed diretto OK — {len(articoli)} articoli")
except Exception as e:
    errors.append(f"feed diretto: {e}")

# Tentativo 2: proxy rss2json.com
if articoli is None:
    try:
        raw = fetch(RSS_PROXY, {"User-Agent": "Mozilla/5.0"})
        articoli = parse_json_proxy(raw)
        print(f"Proxy rss2json OK — {len(articoli)} articoli")
    except Exception as e:
        errors.append(f"proxy rss2json: {e}")

# Se entrambi falliscono: uscita 0 (nessuna email di fail, JSON precedente rimane valido)
if articoli is None:
    for err in errors:
        print(f"WARN: {err}", file=sys.stderr)
    print("WARN: feed non aggiornato, JSON precedente conservato.", file=sys.stderr)
    sys.exit(0)

os.makedirs("data", exist_ok=True)
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    json.dump({"articoli": articoli}, f, ensure_ascii=False, indent=2)

print(f"OK — {len(articoli)} articoli scritti in {OUT_PATH}")

sync_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")

if sync_markdown_file(MD_PATH, articoli, sync_ts):
    print(f"OK — {MD_PATH} rigenerato (Semantic Markdown feed)")
else:
    print(f"WARN: {MD_PATH} non aggiornato (marker assenti o nessuna modifica)", file=sys.stderr)

if sync_html_file(HTML_PATH, articoli, sync_ts):
    print(f"OK — {HTML_PATH} rigenerato (feed statico per crawler)")
else:
    print(f"WARN: {HTML_PATH} non aggiornato (marker assenti o nessuna modifica)", file=sys.stderr)
