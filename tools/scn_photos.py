#!/usr/bin/env python3
"""Download one photo per Scenarios word into img/scn/ (small files, about 340 px).

Run it from the root of the spanish-practice repo. Pick a source:
    PIXABAY_KEY=xxxx python3 tools/scn_photos.py --push     # Pixabay (free key: pixabay.com/api/docs, sign up and the key is shown)
    PEXELS_KEY=xxxx  python3 tools/scn_photos.py --push     # Pexels (when they issue keys again)
    python3 tools/scn_photos.py --source openverse --push   # no key: public-domain photos from Openverse (fewer, less reliable)

Leave out --push to only download. Safe to re-run: words that already have a photo are skipped.
For a different photo of one word: python3 tools/scn_photos.py --redo la-mesa (edit its search in tools/scn_queries.json first).
"""
import json, os, subprocess, sys, time, urllib.parse, urllib.request

ARGS = sys.argv[1:]
SRC = ARGS[ARGS.index("--source") + 1] if "--source" in ARGS else ("pixabay" if os.environ.get("PIXABAY_KEY") else "pexels" if os.environ.get("PEXELS_KEY") else "openverse")
KEY = os.environ.get({"pixabay": "PIXABAY_KEY", "pexels": "PEXELS_KEY"}.get(SRC, "_"), "").strip()
if SRC in ("pixabay", "pexels") and not KEY:
    sys.exit("Set your key first, e.g.  %s_KEY=xxxxx python3 tools/scn_photos.py" % SRC.upper())
print("Source:", SRC)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "img", "scn"); os.makedirs(OUT, exist_ok=True)
MAN = os.path.join(OUT, "manifest.json")
queries = json.load(open(os.path.join(ROOT, "tools", "scn_queries.json"), encoding="utf8"))
manifest = json.load(open(MAN, encoding="utf8")) if os.path.exists(MAN) else {}
redo = set(a for a in ARGS[ARGS.index("--redo") + 1:] if not a.startswith("--")) if "--redo" in ARGS else set()

def get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

done = fail = 0
for slug, info in queries.items():
    if slug in manifest and os.path.exists(os.path.join(OUT, manifest[slug]["f"])) and slug not in redo:
        continue
    try:
        q = urllib.parse.quote_plus(info["q"])
        if SRC == "pexels":
            res = json.loads(get("https://api.pexels.com/v1/search?query=%s&per_page=3&orientation=square&size=medium" % q,
                                 {"Authorization": KEY, "User-Agent": "practica-diaria"}))
            hits = [(p["src"].get("medium") or p["src"]["large"], p.get("photographer", ""), p.get("url", "")) for p in res.get("photos") or []]
        elif SRC == "pixabay":
            res = json.loads(get("https://pixabay.com/api/?key=%s&q=%s&image_type=photo&per_page=3&safesearch=true" % (KEY, q), {"User-Agent": "practica-diaria"}))
            hits = [(p["webformatURL"].replace("_640", "_340"), p.get("user", ""), p.get("pageURL", "")) for p in res.get("hits") or []]
        else:  # openverse, public domain / CC0 only so no per-photo credit is needed
            res = json.loads(get("https://api.openverse.org/v1/images/?q=%s&license=cc0,pdm&page_size=3&aspect_ratio=square" % q, {"User-Agent": "practica-diaria"}))
            hits = [(p.get("thumbnail") or p["url"], p.get("creator") or "", p.get("foreign_landing_url") or "") for p in res.get("results") or []]
        if not hits:
            print("  no result:", slug, "-", info["q"]); fail += 1; continue
        src, by, page = hits[0]
        img = get(src, {"User-Agent": "practica-diaria"})
        fn = slug + ".jpg"
        open(os.path.join(OUT, fn), "wb").write(img)
        manifest[slug] = {"f": fn, "by": by, "u": page, "s": {"pixabay": "Pixabay", "pexels": "Pexels"}.get(SRC, "Openverse")}
        done += 1; print("  ok:", slug, "-", info["es"], "(", len(img) // 1024, "KB )")
        time.sleep(0.6)
    except Exception as e:
        print("  failed:", slug, e); fail += 1
        if "429" in str(e): print("  rate limit hit; wait a few minutes and run again"); break

json.dump(manifest, open(MAN, "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(f"\nDone: {done} new, {fail} failed, {len(manifest)} photos in total -> img/scn/")
if "--push" in ARGS:
    run = lambda *a: subprocess.run(a, cwd=ROOT, check=True)
    run("git", "add", "img", "tools")
    run("git", "commit", "-m", "Add Scenarios photos")
    run("git", "push")
    print("Pushed. The app picks the photos up on its next refresh.")
else:
    print("Next: git add img tools && git commit -m 'Scenarios photos' && git push")
