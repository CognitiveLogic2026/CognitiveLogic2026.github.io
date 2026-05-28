# Copyright (c) 2026 Roberto Malini - Cognitive Logic
# https://www.cognitivelogic.it
# Licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
import urllib.request, urllib.error, json, re, os, sys
import xml.etree.ElementTree as ET

RSS_DIRECT = "https://fuorimenu.substack.com/feed"
RSS_PROXY  = "https://api.rss2json.com/v1/api.json?rss_url=https%3A%2F%2Ffuorimenu.substack.com%2Ffeed&count=10"
OUT_PATH   = "data/fuorimenu.json"

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
