#!/usr/bin/env python3
"""Wikimedia Commons photos for the Scenarios words, picked by eye.

  python3 tools/scn_cands.py            # candidates: up to 8 thumbnails per word -> cand/ + tools/cands.json
  python3 tools/scn_cands.py --pick     # download the one chosen per word in tools/scn_picks.json ({"la-mesa": 3, ...}) -> img/scn/

Every photo keeps its author and licence in img/scn/manifest.json so the app can credit it.
"""
import html, json, os, re, sys, time, urllib.parse, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "img", "scn"); CAND = os.path.join(ROOT, "cand")
Q = {
 "la-mesa": ["restaurant table", "dining table wooden"], "la-silla": ["wooden chair", "chair furniture"],
 "el-camarero": ["waiter restaurant", "waiter serving"], "la-carta": ["restaurant menu", "menu held restaurant"],
 "la-reserva": ["reserved sign table", "reservado table sign"], "la-cuenta": ["restaurant bill receipt", "paying bill restaurant"],
 "la-propina": ["tip jar", "restaurant tip coins bill"], "el-plato": ["empty white plate", "dinner plate table setting"],
 "el-vaso": ["drinking glass tumbler", "glass of water"], "la-copa": ["wine glass", "empty wine glass"],
 "el-tenedor": ["dinner fork", "fork isolated"], "el-cuchillo": ["table knife", "knife cutlery"],
 "la-cuchara": ["spoon", "tablespoon cutlery"], "la-servilleta": ["napkin folded", "paper napkin"],
 "el-agua": ["glass of water", "water pouring glass"], "la-cerveza": ["glass of beer", "beer glass pint"],
 "el-vino": ["glass of red wine", "wine glass red"], "el-cafe": ["cup of coffee", "coffee cup saucer"],
 "el-zumo": ["glass orange juice", "orange juice"], "el-pan": ["bread loaf bakery", "sliced bread"],
 "la-ensalada": ["green salad bowl", "salad"], "la-sopa": ["bowl of soup", "vegetable soup"],
 "la-carne": ["steak plate", "grilled meat"], "el-pollo": ["roast chicken", "grilled chicken"],
 "el-pescado": ["grilled fish plate", "fish dish"], "el-arroz": ["rice dish", "bowl of rice"],
 "las-patatas": ["potatoes", "french fries"], "las-verduras": ["mixed fresh vegetables", "vegetables basket carrots tomatoes"],
 "el-queso": ["cheese wheel", "cheese slices"], "el-huevo": ["fried egg", "egg"],
 "el-postre": ["dessert", "dessert cake plate"], "el-helado": ["ice cream cone", "ice cream"],
 "picante": ["red chili pepper", "chilli peppers pods"], "vegetariano": ["vegetarian food", "vegetable dish plate"]}
def get(url):
    for k in range(5):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "practica-diaria/1.0 (language app; github.com/fynhav/spanish-practice)"}), timeout=40).read()
        except Exception as e:
            if k == 4: raise
            time.sleep(25 if "429" in str(e) else 3)
def search(q):
    u = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
        "gsrsearch": q + " filetype:bitmap", "gsrlimit": 14, "prop": "imageinfo", "iiprop": "url|mime|size|extmetadata", "iiurlwidth": 340,
        "iiextmetadatafilter": "Artist|LicenseShortName|ImageDescription"})
    pages = (json.loads(get(u)).get("query") or {}).get("pages") or {}
    out = []
    for p in sorted(pages.values(), key=lambda p: p.get("index", 0)):
        ii = (p.get("imageinfo") or [{}])[0]
        if ii.get("mime") != "image/jpeg" or ii.get("width", 0) < 500 or not ii.get("thumburl"): continue
        md = ii.get("extmetadata") or {}
        clean = lambda k: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", (md.get(k) or {}).get("value", "")))).strip()
        out.append({"t": p["title"], "thumb": ii["thumburl"], "page": ii.get("descriptionurl", ""), "by": clean("Artist")[:80], "lic": clean("LicenseShortName"), "w": ii["width"], "h": ii["height"]})
    return out
if "--pick" in sys.argv:
    cands = json.load(open(os.path.join(ROOT, "tools", "cands.json"), encoding="utf8"))
    picks = json.load(open(os.path.join(ROOT, "tools", "scn_picks.json"), encoding="utf8"))
    os.makedirs(OUT, exist_ok=True); mp = os.path.join(OUT, "manifest.json")
    man = json.load(open(mp, encoding="utf8")) if os.path.exists(mp) else {}
    for slug, i in picks.items():
        c = cands[slug][i]
        open(os.path.join(OUT, slug + ".jpg"), "wb").write(get(c["thumb"]))
        man[slug] = {"f": slug + ".jpg", "by": c["by"], "u": c["page"], "s": "Wikimedia Commons", "l": c["lic"]}
        print("picked", slug, i, c["t"]); time.sleep(0.5)
    json.dump(man, open(mp, "w", encoding="utf8"), ensure_ascii=False, indent=1)
else:
    os.makedirs(CAND, exist_ok=True)
    only = sys.argv[sys.argv.index("--only") + 1].split() if "--only" in sys.argv else None
    cp = os.path.join(ROOT, "tools", "cands.json"); allc = json.load(open(cp, encoding="utf8")) if only and os.path.exists(cp) else {}
    for slug, qs in Q.items():
        if only and slug not in only: continue
        seen, lst = set(), []
        for q in qs:
            time.sleep(1.5)
            try:
                for c in search(q):
                    if c["t"] not in seen and not re.search(r"\.(svg|tif)|logo|icon|diagram|map|poster|painting|drawing", c["t"], re.I): seen.add(c["t"]); lst.append(c)
            except Exception as e: print("search failed", slug, q, e)
            time.sleep(0.5)
        lst = lst[:8]; allc[slug] = lst
        for i, c in enumerate(lst):
            try: open(os.path.join(CAND, "%s_%d.jpg" % (slug, i)), "wb").write(get(c["thumb"])); time.sleep(0.3)
            except Exception as e: print("thumb failed", slug, i, e)
        print(slug, len(lst))
    json.dump(allc, open(os.path.join(ROOT, "tools", "cands.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
