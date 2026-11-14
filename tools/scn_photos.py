#!/usr/bin/env python3
"""Download one photo per Scenarios word from Pexels (free API) into img/scn/.

Run it from the root of the spanish-practice repo:
    PEXELS_KEY=your_key python3 tools/scn_photos.py          # download
    PEXELS_KEY=your_key python3 tools/scn_photos.py --push   # download, then git add / commit / push

Safe to re-run: words that already have a photo are skipped. Delete a file in img/scn/ and
its line in manifest.json (or run with --redo slug) to get a different photo for one word.
Photos are small (about 350 px tall, 20-40 KB). Pexels licence: free to use, credit appreciated.
"""
import json, os, subprocess, sys, time, urllib.parse, urllib.request

KEY = os.environ.get("PEXELS_KEY", "").strip()
if not KEY:
    sys.exit("Set your key first:  PEXELS_KEY=xxxxx python3 tools/scn_photos.py")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "img", "scn"); os.makedirs(OUT, exist_ok=True)
MAN = os.path.join(OUT, "manifest.json")
queries = json.load(open(os.path.join(ROOT, "tools", "scn_queries.json"), encoding="utf8"))
manifest = json.load(open(MAN, encoding="utf8")) if os.path.exists(MAN) else {}
redo = set(sys.argv[sys.argv.index("--redo") + 1:]) if "--redo" in sys.argv else set()

def get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

done = fail = 0
for slug, info in queries.items():
    if slug in manifest and os.path.exists(os.path.join(OUT, manifest[slug]["f"])) and slug not in redo:
        continue
    try:
        url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
            {"query": info["q"], "per_page": 3, "orientation": "square", "size": "medium"})
        res = json.loads(get(url, {"Authorization": KEY, "User-Agent": "practica-diaria"}))
        photos = res.get("photos") or []
        if not photos:
            print("  no result:", slug, "-", info["q"]); fail += 1; continue
        ph = photos[0]
        img = get(ph["src"].get("medium") or ph["src"]["large"], {"User-Agent": "practica-diaria"})
        fn = slug + ".jpg"
        open(os.path.join(OUT, fn), "wb").write(img)
        manifest[slug] = {"f": fn, "by": ph.get("photographer", ""), "u": ph.get("url", "")}
        done += 1; print("  ok:", slug, "-", info["es"], "(", len(img) // 1024, "KB )")
        time.sleep(0.4)
    except Exception as e:
        print("  failed:", slug, e); fail += 1
        if "429" in str(e): print("  rate limit hit; wait a few minutes and run again"); break

json.dump(manifest, open(MAN, "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(f"\nDone: {done} new, {fail} failed, {len(manifest)} photos in total -> img/scn/")
if "--push" in sys.argv:
    run = lambda *a: subprocess.run(a, cwd=ROOT, check=True)
    run("git", "add", "img", "tools")
    run("git", "commit", "-m", "Add Scenarios photos (Pexels)")
    run("git", "push")
    print("Pushed. The app picks the photos up on its next refresh.")
else:
    print("Next: git add img tools && git commit -m 'Scenarios photos' && git push")
