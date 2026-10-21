#!/usr/bin/env python3
"""Text-to-image stills on fal.ai (nanoproedit takes reference images via "refs"). Sibling of gen_flux.py.

Backends (prices read from api.fal.ai/v1/models/pricing on 2026-10-18):
  nanopro  fal-ai/nano-banana-pro = Gemini 3 Pro Image, the most photoreal people. $0.15 per image at 2K.
  nano     fal-ai/nano-banana  = Gemini 2.5 Flash Image, the cheapest Gemini image model on fal.
           $0.0398 per image. aspect_ratio "16:9" / "9:16".
  klein    fal-ai/flux-2/klein/9b (text-to-image). $0.006 per megapixel, rounded UP, so
           1280x720 / 720x1280 (0.92 MP) bills as 1 MP = $0.006.

The project folder holds prompts_t2i.json:
  {"styles": {"<id>": "<style block>"},
   "scenes": {"<name>": {"backend": "nano|klein", "style": "<id>", "aspect": "16:9|9:16", "prompt": "<SHOT>"}}}
Images are written to <project>/_images/<name>.png. Every call is logged to <project>/spend.json, so
bin/fal_ledger.py counts it (the project must be a top-level folder in Vibe code).

GATEKEEPING, the same as gen_flux.py: with no --approve <USD> it prints the quote and spends nothing.
The approved figure is a hard cap on this project's total spend; any call that would cross it is refused.
Rishi approves each quoted batch; approval never carries over.

usage: python3 gen_fal_t2i.py --project <dir> [name ...] [--approve <USD>] [--force] [--dry]
"""
import json, os, ssl, sys, time, urllib.request

argv = sys.argv[1:]
val = lambda flag: argv[argv.index(flag) + 1] if flag in argv else None
P = os.path.abspath(val("--project") or sys.exit("--project <dir> is required"))
approved = float(val("--approve")) if val("--approve") else None
force, dry = "--force" in argv, "--dry" in argv
skip = {i + 1 for i, a in enumerate(argv) if a in ("--project", "--approve")}
names = [a for i, a in enumerate(argv) if not a.startswith("--") and i not in skip]

RS = 88
MODEL = {"nano": "fal-ai/nano-banana", "klein": "fal-ai/flux-2/klein/9b", "nanopro": "fal-ai/nano-banana-pro",
         "nanoproedit": "fal-ai/nano-banana-pro/edit"}
RATE = {"nano": 0.0398, "klein": 0.006, "nanopro": 0.15, "nanoproedit": 0.15}   # nanopro: $0.15 at 1K/2K (4K bills double)
SIZE = {"16:9": (1280, 720), "9:16": (720, 1280), "1:1": (960, 960)}
SEED = 77
CTX = ssl.create_default_context(cafile="/etc/ssl/cert.pem" if os.path.exists("/etc/ssl/cert.pem") else None)
KEY = os.environ.get("FAL_KEY") or open(os.path.expanduser("~/.config/fal/key")).read().strip().splitlines()[-1].strip()

D = json.load(open(f"{P}/prompts_t2i.json"))
OUT = f"{P}/_images"; os.makedirs(OUT, exist_ok=True)
ledger = json.load(open(f"{P}/spend.json")) if os.path.exists(f"{P}/spend.json") else {"calls": []}
spent = lambda: round(sum(c["usd"] for c in ledger["calls"]), 4)
CAP = approved if approved is not None else 0.0

def body(sc):
    style = D["styles"][sc["style"]]
    prompt = f"SHOT: {sc['prompt']}\n\nSTYLE: {style}"
    if sc["backend"] == "nano":
        return {"prompt": prompt, "num_images": 1, "aspect_ratio": sc.get("aspect", "16:9"), "output_format": "png"}
    if sc["backend"] == "nanopro":   # photoreal people; added 2026-10-21 for ai-guru-avatar
        return {"prompt": prompt, "num_images": 1, "aspect_ratio": sc.get("aspect", "9:16"), "resolution": "2K",
                "output_format": "png", "seed": sc.get("seed", SEED)}
    if sc["backend"] == "nanoproedit":   # reference images ("refs", paths relative to the project) sent as data URIs
        import base64, mimetypes
        uri = lambda f: f"data:{mimetypes.guess_type(f)[0] or 'image/png'};base64," + base64.b64encode(open(os.path.join(P, f), "rb").read()).decode()
        return {"prompt": prompt, "image_urls": [uri(f) for f in sc["refs"]], "num_images": 1,
                "aspect_ratio": sc.get("aspect", "16:9"), "resolution": "2K", "output_format": "png"}
    w, h = SIZE[sc.get("aspect", "16:9")]
    return {"prompt": prompt, "image_size": {"width": w, "height": h}, "num_images": 1, "seed": SEED,
            "output_format": "png", "enable_safety_checker": False}

def gen(name, sc):
    b = sc["backend"]
    for attempt in range(2):
        if spent() + RATE[b] > CAP + 1e-9:
            print(f"  STOP: ${spent():.4f} spent; ${RATE[b]:.4f} more crosses the ${CAP:.2f} approved cap.")
            return False
        try:
            req = urllib.request.Request(f"https://fal.run/{MODEL[b]}", data=json.dumps(body(sc)).encode(),
                                         headers={"Authorization": f"Key {KEY}", "Content-Type": "application/json"})
            r = json.load(urllib.request.urlopen(req, timeout=300, context=CTX))
            url = r["images"][0]["url"]
            open(f"{OUT}/{name}.png", "wb").write(urllib.request.urlopen(url, timeout=120, context=CTX).read())
            ledger["calls"].append({"name": name, "model": MODEL[b], "usd": RATE[b], "t": time.strftime("%Y-%m-%d %H:%M:%S"), "ok": True})
            json.dump(ledger, open(f"{P}/spend.json", "w"), indent=1)
            print(f"  ok  {name:24s} {b:5s} running ${spent():.4f} (Rs {spent()*RS:.1f})", flush=True)
            return True
        except Exception as e:
            msg = e.read().decode()[:160] if hasattr(e, "read") else str(e)[:160]
            ledger["calls"].append({"name": name, "model": MODEL[b], "usd": 0.0, "t": time.strftime("%Y-%m-%d %H:%M:%S"),
                                    "ok": False, "err": msg[:80]})
            json.dump(ledger, open(f"{P}/spend.json", "w"), indent=1)
            print(f"  .. {name} attempt {attempt + 1}: {msg}", flush=True)
            time.sleep(3)
    return False

todo = names or list(D["scenes"])
todo = [n for n in todo if force or not os.path.exists(f"{OUT}/{n}.png")]
est = sum(RATE[D["scenes"][n]["backend"]] for n in todo)
by = {}
for n in todo:
    by.setdefault(D["scenes"][n]["backend"], []).append(n)
print("\n  ---- COST QUOTE ----------------------------------------------")
for b, ns in by.items():
    print(f"  {MODEL[b]:28s} {len(ns):3d} x ${RATE[b]:.4f} = ${len(ns) * RATE[b]:.3f}")
print(f"  THIS RUN       ${est:.3f}  = Rs {est * RS:.1f}")
print(f"  already spent  ${spent():.3f}  = Rs {spent() * RS:.1f}")
print(f"  approved cap   ${CAP:.3f}  = Rs {CAP * RS:.1f}")
print("  --------------------------------------------------------------\n")
if dry:
    sys.exit(0)
if approved is None:
    sys.exit("NOT SPENDING: no --approve. Show Rishi the quote and get an explicit yes for this batch.")
if spent() + est > CAP + 1e-9:
    sys.exit(f"REFUSING: ${spent():.3f} + ${est:.3f} would cross the ${CAP:.3f} approved cap.")
fails = [n for n in todo if not gen(n, D["scenes"][n])]
print(f"\ndone. spent ${spent():.4f} (Rs {spent() * RS:.1f}) of ${CAP:.2f}" + (f" | FAILED: {fails}" if fails else ""))
