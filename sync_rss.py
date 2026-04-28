import urllib.request, json, re, os

url = "https://api.rss2json.com/v1/api.json?rss_url=https%3A%2F%2Ffuorimenu.substack.com%2Ffeed&count=10"

req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

with urllib.request.urlopen(req, timeout=15) as r:
    data = json.loads(r.read())

articoli = []
for item in data.get("items", []):
    desc = re.sub('<[^>]+>', '', item.get("description", "")).strip()[:280]
    articoli.append({
        "titolo": item.get("title", "").strip(),
        "url":    item.get("link", "").strip(),
        "data":   item.get("pubDate", "")[:16],
        "estratto": desc,
        "tag": "Fuorimenu"
    })

os.makedirs("data", exist_ok=True)
with open('data/fuorimenu.json', 'w') as f:
    json.dump({"articoli": articoli}, f, ensure_ascii=False, indent=2)
print(f"OK — {len(articoli)} articoli scritti")
