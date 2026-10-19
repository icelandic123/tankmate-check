"""Static site generator. Usage: SITE_URL=https://example.com AMAZON_TAG=xxx-20 python3 build.py
Writes ../site/. Pure standard library."""
import os, sys, json, html, itertools, re, shutil, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "data")); sys.path.insert(0, HERE)
from species import S, BY_ID
from compat import check, gal

SITE = os.environ.get("SITE_URL", "https://tankmatecheck.example").rstrip("/")
BASE = os.environ.get("BASE_PATH", "").rstrip("/")   # e.g. "/tankmates" on a GitHub project page
TAG = os.environ.get("AMAZON_TAG", "")
NAME = "Tankmate Check"
OUT = os.environ.get("OUT_DIR", os.path.join(ROOT, "site"))
TODAY = datetime.date.today().isoformat()
POP = [s for s in S if s.get("popular")]
e = html.escape

def f(c): return round(c * 9 / 5 + 32)
def trange(t): return f"{f(t[0])}–{f(t[1])} °F ({t[0]}–{t[1]} °C)"
def prange(p): return f"{p[0]:g}–{p[1]:g}"
def tank(l): return f"{gal(l)} gallons ({l} L)"
def size(cm): return f"{cm/2.54:.1f} in ({cm:g} cm)".replace(".0 in", " in")
def u(path): return f"{BASE}{path}"
def plural(n):
    if n.lower().endswith(("fish", "shrimp", "s")): return n
    if n.endswith(("sh", "ch")): return n + "es"
    if n.endswith("y") and n[-2] not in "aeiou": return n[:-1] + "ies"
    return n + "s"
def species_url(i): return u(f"/species/{i}/")
def pair_id(a, b): return "-and-".join(sorted((a, b)))
def pair_url(a, b): return u(f"/pairs/{pair_id(a, b)}/")
PAIRS = set()  # standalone "can X live with Y" pages dropped 2026-10-19: informational queries lose clicks to AI Overviews
def has_pair(a, b): return pair_id(a, b) in PAIRS
TEMPER = {"peaceful": "Peaceful", "semi": "Semi-aggressive", "aggressive": "Aggressive"}
LEVEL = {"top": "Top", "mid": "Middle", "bottom": "Bottom", "all": "All levels"}
VERDICT = {"yes": ("Yes", "good"), "caution": ("With caution", "warn"), "no": ("No", "bad")}

def md(text):
    out, para, items = [], [], []
    def flush():
        if para: out.append("<p>" + inline(" ".join(para)) + "</p>"); para.clear()
        if items: out.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul>"); items.clear()
    for line in text.splitlines():
        line = line.rstrip()
        if line.startswith("## "): flush(); out.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith(("- ", "* ")): (para and flush()); items.append(line[2:])
        elif not line.strip(): flush()
        else: (items and flush()); para.append(line.strip())
    flush(); return "\n".join(out)
def inline(t): return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", e(t))

def amazon(q):
    from urllib.parse import quote_plus
    t = f"&tag={TAG}" if TAG else ""
    return f"https://www.amazon.com/s?k={quote_plus(q)}{t}"

def gear(s):
    g = [(f"{gal(max(s['tank_l'], 38))}-gallon aquarium kit", f"A starting point for {s['name'].lower()}s"),
         ("liquid aquarium water test kit", "Test strips are less accurate; a liquid kit catches ammonia and nitrite early")]
    if s["temp"][0] >= 22: g.append(("adjustable aquarium heater", f"Holds the {trange(s['temp'])} this species needs"))
    if s["size_cm"] <= 4 or s["kind"] == "invert" or s["id"] in ("betta", "axolotl"):
        g.append(("aquarium sponge filter", "Gentle flow that won't trap small or weak swimmers"))
    if s["level"] == "bottom" and s["kind"] == "fish": g.append(("sinking wafers aquarium", "Food that reaches bottom feeders before others take it"))
    if s["diet"] == "carnivore": g.append(("frozen bloodworms fish food", "A meaty food for carnivores"))
    if s["id"] in ("hatchetfish", "betta", "zebra-danio", "kuhli-loach", "african-dwarf-frog", "axolotl"):
        g.append(("aquarium glass lid", "This species jumps or climbs out of open tanks"))
    if s["id"] == "axolotl": g.append(("aquarium chiller fan", "Helps keep the water under 68 °F (20 °C) in warm rooms"))
    rows = "".join(f'<li><a href="{amazon(q)}" rel="sponsored nofollow noopener" target="_blank">{e(q.title())}</a><span>{e(why)}</span></li>' for q, why in g)
    return f'<aside class="gear"><h2>Gear for this setup</h2><ul>{rows}</ul><p class="fine">As an Amazon Associate this site earns from qualifying purchases. Links search Amazon, so you choose the product.</p></aside>'

CSS = """
:root{--bg:#f7fafa;--fg:#13232b;--muted:#506570;--card:#fff;--line:#d9e4e6;--accent:#0b7a75;--good:#1f7a3a;--warn:#9a6400;--bad:#b3261e;--goodbg:#e5f4e9;--warnbg:#fdf1dc;--badbg:#fbe4e2}
@media (prefers-color-scheme:dark){:root{--bg:#0e1719;--fg:#e4eef0;--muted:#9bb0b6;--card:#152226;--line:#28393e;--accent:#4fc2bb;--good:#7fd396;--warn:#f0b75a;--bad:#ff8a80;--goodbg:#173323;--warnbg:#3a2c12;--badbg:#3d1d1a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:17px/1.6 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
a{color:var(--accent)}header,main,footer{max-width:860px;margin:0 auto;padding:0 16px}
header{display:flex;justify-content:space-between;align-items:center;padding-top:14px;padding-bottom:14px;flex-wrap:wrap;gap:8px}
header a.logo{font-weight:700;text-decoration:none;color:var(--fg);font-size:20px}header nav a{margin-left:14px;font-size:15px}
h1{font-size:clamp(26px,5vw,36px);line-height:1.2;margin:.6em 0 .3em}h2{margin-top:1.6em}
.answer{border-radius:12px;padding:16px 18px;margin:16px 0;border:1px solid var(--line)}
.answer.good{background:var(--goodbg)}.answer.warn{background:var(--warnbg)}.answer.bad{background:var(--badbg)}
.badge{display:inline-block;font-weight:700;border-radius:999px;padding:2px 10px;font-size:14px}
.badge.good{color:var(--good);background:var(--goodbg)}.badge.warn{color:var(--warn);background:var(--warnbg)}.badge.bad{color:var(--bad);background:var(--badbg)}
table{border-collapse:collapse;width:100%;background:var(--card);border-radius:10px;overflow:hidden;font-size:15px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--muted);font-weight:600}
.scroll{overflow-x:auto}.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:12px 0}
ul.mates{list-style:none;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:8px}
ul.mates li{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px 12px;font-size:15px}ul.mates li small{display:block;color:var(--muted)}
.gear{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:4px 16px 8px;margin:24px 0}.gear ul{padding-left:18px}.gear li span{display:block;color:var(--muted);font-size:14px}
.fine{color:var(--muted);font-size:13px}footer{color:var(--muted);font-size:14px;padding-top:24px;padding-bottom:40px;border-top:1px solid var(--line);margin-top:40px}
.chips{display:flex;flex-wrap:wrap;gap:6px}.chips button{border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:999px;padding:5px 11px;font-size:14px;cursor:pointer}
.chips button.on{background:var(--accent);color:#fff;border-color:var(--accent)}input[type=search]{width:100%;padding:10px 12px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--fg);font-size:16px;margin-bottom:10px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px}.grid a{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px;text-decoration:none}
"""

def page(path, title, desc, body, extra_head=""):
    canon = SITE + u(path)
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{canon}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="article">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%90%9F%3C/text%3E%3C/svg%3E"><link rel="stylesheet" href="{u('/style.css')}">{extra_head}</head><body>
<header><a class="logo" href="{u('/')}">🐟 {NAME}</a><nav><a href="{u('/species/')}">Species</a><a href="{u('/stocking/')}">Stocking ideas</a><a href="{u('/compare/')}">Compare</a><a href="{u('/#checker')}">Tank checker</a><a href="{u('/about/')}">How it works</a></nav></header>
<main>{body}</main>
<footer><p>{NAME} checks freshwater aquarium compatibility from each species' temperature, pH, size, temperament and diet. It is a starting point, not a guarantee: individual fish vary, so watch new tankmates closely.</p>
<p><a href="{u('/about/')}">How the checks work</a> · <a href="{u('/disclosure/')}">Affiliate disclosure and privacy</a> · Updated {TODAY}</p></footer></body></html>"""
    d = os.path.join(OUT, path.strip("/"))
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "index.html") if not path.endswith(".html") else os.path.join(OUT, path.strip("/")), "w") as fh: fh.write(doc)
    if not path.endswith(".html"): URLS.append(canon)

URLS = []

def stat_table(s):
    rows = [("Adult size", size(s["size_cm"])), ("Minimum tank", tank(s["tank_l"])), ("Temperature", trange(s["temp"])),
            ("pH", prange(s["ph"])), ("Temperament", TEMPER[s["temperament"]]), ("Group size", "Alone or a pair" if s["group"] == 1 else f"{s['group']} or more"),
            ("Swims at", LEVEL[s["level"]]), ("Diet", s["diet"].title()), ("Care level", s["care"].title()), ("Scientific name", f"<em>{e(s['sci'])}</em>")]
    return '<div class="scroll"><table>' + "".join(f"<tr><th>{k}</th><td>{v if k=='Scientific name' else e(v)}</td></tr>" for k, v in rows) + "</table></div>"

def mate_li(s, o, r):
    href = pair_url(s["id"], o["id"]) if has_pair(s["id"], o["id"]) else species_url(o["id"])
    why = f"<small>{e(r['reasons'][0][1])}</small>" if r["reasons"] else f"<small>{TEMPER[o['temperament']]}, {LEVEL[o['level']].lower()} level, {size(o['size_cm'])}</small>"
    return f'<li><a href="{href}">{e(o["name"])}</a>{why}</li>'

def species_pages():
    for s in S:
        res = [(o, check(s["id"], o["id"])) for o in S if o["id"] != s["id"]]
        order = lambda x: (not x[0].get("popular"), x[0]["name"])
        yes = sorted([x for x in res if x[1]["verdict"] == "yes"], key=order)
        cau = sorted([x for x in res if x[1]["verdict"] == "caution"], key=order)
        no = sorted([x for x in res if x[1]["verdict"] == "no"], key=order)
        p = os.path.join(ROOT, "content", "species", s["id"] + ".md")
        prose = md(open(p).read()) if os.path.exists(p) else ""
        top = ", ".join(o["name"].lower() + "s" if not o["name"].endswith("s") else o["name"].lower() for o, _ in yes[:4])
        summary = (f"Good tank mates for a {s['name'].lower()} include {top}." if yes else f"The {s['name'].lower()} does best in a tank of its own kind.")
        body = f"""<h1>Best Tank Mates for {e(plural(s['name']))}</h1>
<p><strong>{e(summary)}</strong> {e(s['note'])}</p>{stat_table(s)}
<h2>Best tank mates for a {e(s['name'].lower())}</h2>{('<ul class="mates">' + "".join(mate_li(s, o, r) for o, r in yes) + '</ul>') if yes else '<p>None of the species we cover are a safe match. Keep it with its own kind.</p>'}
{('<h2>Possible, with caution</h2><ul class="mates">' + "".join(mate_li(s, o, r) for o, r in cau) + '</ul>') if cau else ''}
{('<h2>Avoid</h2><ul class="mates">' + "".join(mate_li(s, o, r) for o, r in no) + '</ul>') if no else ''}
{vs_links(s["id"])}
<p class="fine">Verdicts come from comparing temperature, pH, adult size, temperament, diet and fin-nipping behavior. <a href="{u('/about/')}">How the checks work</a>.</p>
{gear(s)}"""
        desc = f"{s['name']} tank mates ranked from {len(S) - 1} species. Needs {trange(s['temp'])}, pH {prange(s['ph'])}, {tank(s['tank_l'])} minimum, plus {len(yes)} compatible tank mates and {len(no)} to avoid."
        title = f"Best Tank Mates for {plural(s['name'])}: {len(yes)} Compatible Species" if len(yes) >= 5 else f"{s['name']} Tank Mates: What Can Live With {plural(s['name'])}?"
        page(f"/species/{s['id']}/", title, desc, body)
    grid = "".join(f'<a href="{species_url(s["id"])}">{e(s["name"])}</a>' for s in sorted(S, key=lambda s: s["name"]))
    page("/species/", "Freshwater Aquarium Species: Care and Tank Mates", f"Care sheets and tank-mate lists for {len(S)} popular freshwater aquarium species.",
         f"<h1>All species</h1><p>Care sheets and tank-mate lists for {len(S)} freshwater fish, shrimp, snails and amphibians.</p><div class='grid'>{grid}</div>")



def pair_pages():
    for pid in sorted(PAIRS):
        a_id, b_id = pid.split("-and-") if pid.count("-and-") == 1 else None
        a, b = BY_ID[a_id], BY_ID[b_id]
        r = check(a_id, b_id)
        label, cls = VERDICT[r["verdict"]]
        A, B = a["name"], b["name"]
        if r["verdict"] == "yes":
            ans = f"Yes. {plural(A)} and {plural(B).lower()} can live together. Their water needs overlap and neither is a threat to the other."
        elif r["verdict"] == "caution":
            ans = f"Sometimes. {plural(A)} and {plural(B).lower()} can share a tank, but there are real risks to plan around."
        else:
            ans = f"No. {plural(A)} and {plural(B).lower()} shouldn't be kept together."
        reasons = "".join(f'<li><span class="badge {VERDICT[s][1]}">{VERDICT[s][0] if s!="yes" else "OK"}</span> {e(t)}</li>' for s, t in r["reasons"])
        rows = [("Adult size", size(a["size_cm"]), size(b["size_cm"])), ("Temperature", trange(a["temp"]), trange(b["temp"])), ("pH", prange(a["ph"]), prange(b["ph"])),
                ("Temperament", TEMPER[a["temperament"]], TEMPER[b["temperament"]]), ("Swims at", LEVEL[a["level"]], LEVEL[b["level"]]),
                ("Group size", "1–2" if a["group"] == 1 else f"{a['group']}+", "1–2" if b["group"] == 1 else f"{b['group']}+"), ("Minimum tank", tank(a["tank_l"]), tank(b["tank_l"])),
                ("Diet", a["diet"].title(), b["diet"].title())]
        table = f'<div class="scroll"><table><tr><th></th><th>{e(A)}</th><th>{e(B)}</th></tr>' + "".join(f"<tr><th>{k}</th><td>{e(x)}</td><td>{e(y)}</td></tr>" for k, x, y in rows) + "</table></div>"
        setup = ""
        if r["verdict"] != "no" and r["temp"] and r["ph"]:
            first = None
            for x, y in ((a, b), (b, a)):
                if {"peaceful": 0, "semi": 1, "aggressive": 2}[x["temperament"]] < {"peaceful": 0, "semi": 1, "aggressive": 2}[y["temperament"]]: first = (x, y)
            order = f"<li>Add the {plural(first[0]['name']).lower()} first and let them settle before the {plural(first[1]['name']).lower()}, so the more assertive fish doesn't claim the whole tank.</li>" if first else ""
            setup = f"""<h2>If you keep them together</h2><ul>
<li>Keep the water at {trange(r['temp'])}, the range both are comfortable in.</li><li>Aim for pH {prange(r['ph'])}.</li>
<li>Start with at least {tank(r['tank_l'])}, the larger of their two minimums. Each extra fish adds waste, so size up for a full community.</li>
<li>Keep {('a single ' + A.lower()) if a['group']==1 else f"{a['group']} or more {plural(A).lower()}"} and {('a single ' + B.lower()) if b['group']==1 else f"{b['group']} or more {plural(B).lower()}"}.</li>{order}</ul>"""
        alts = ""
        for x, y in ((a, b), (b, a)):
            better = [o for o in POP if o["id"] not in (a_id, b_id) and check(x["id"], o["id"])["verdict"] == "yes"][:6]
            if better:
                alts += f"<p><strong>Safer tank mates for a {e(x['name'].lower())}:</strong> " + ", ".join(f'<a href="{pair_url(x["id"], o["id"]) if has_pair(x["id"], o["id"]) else species_url(o["id"])}">{e(o["name"])}</a>' for o in better) + "</p>"
        body = f"""<h1>Can {e(plural(A))} Live With {e(plural(B))}?</h1>
<div class="answer {cls}"><span class="badge {cls}">{label}</span><p><strong>{e(ans)}</strong></p>{('<ul>' + reasons + '</ul>') if reasons else ''}</div>
<h2>Side by side</h2>{table}{setup}
<h2>About each species</h2><div class="card"><p><a href="{species_url(a_id)}"><strong>{e(A)}</strong></a>: {e(a['note'])}</p></div><div class="card"><p><a href="{species_url(b_id)}"><strong>{e(B)}</strong></a>: {e(b['note'])}</p></div>
{('<h2>Better matches</h2>' + alts) if r['verdict'] != 'yes' and alts else ''}
<p class="fine">Check a whole tank at once with the <a href="{u('/#checker')}">tank checker</a>.</p>"""
        desc = f"{label}: {ans} Temperature, pH, size and temperament compared side by side."
        page(f"/pairs/{pid}/", f"Can {plural(A)} Live With {plural(B)}? Compatibility Check", desc[:300], body)

TANKS = [5, 10, 20, 40, 55]  # 29 and 75 produced near-duplicates of 20 and 55
def roles(s):
    if s["kind"] == "invert": return "crew"
    if s["level"] in ("bottom",) or s["id"] in ("otocinclus",): return "bottom"
    if s["group"] >= 5: return "school"
    return "center"

def stockings(g):
    """Up to three fully compatible stocking plans for a tank of g gallons, best-known species first."""
    L = g * 3.785
    fit = [s for s in S if s["tank_l"] <= L + 1 and not s.get("species_only") and s["id"] != "axolotl" and not s.get("rift_lake")]
    key = lambda s: (not s.get("popular"), s["care"] == "hard", -s["tank_l"], s["name"])
    by = {r: sorted([s for s in fit if roles(s) == r], key=key) for r in ("center", "school", "bottom", "crew")}
    def ok(xs):
        load = sum(x["size_cm"] * x["group"] for x in xs if x["kind"] != "invert")  # adult cm of fish
        if load > L: return False
        if g >= 40 and max(x["tank_l"] for x in xs) < 0.5 * L: return False  # make use of the bigger tank
        return all(check(a["id"], b["id"])["verdict"] == "yes" for a, b in itertools.combinations(xs, 2)) and \
            min(x["temp"][1] for x in xs) - max(x["temp"][0] for x in xs) >= 2
    plans, used = [], set()
    for c in by["center"] + [None]:
        if len(plans) >= 3: break
        found = None
        for sc in by["school"]:
            if sc["id"] in used: continue
            for bt in by["bottom"] + [None]:
                if bt and bt["id"] in used: continue
                for cr in sorted(by["crew"], key=lambda x: x["id"] in used) + [None]:
                    xs = [x for x in (c, sc, bt, cr) if x]
                    if len(xs) >= (3 if g >= 10 else 2) and ok(xs): found = (c, sc, bt, cr); break
                if found: break
            if found: break
        if found:
            plans.append(found); used.update(x["id"] for x in found[1:] if x)
    return plans

def stocking_pages():
    links = []
    for g in TANKS:
        plans = stockings(g)
        if not plans: continue
        cards = ""
        for n, (c, sc, bt, cr) in enumerate(plans, 1):
            xs = [x for x in (c, sc, bt, cr) if x]
            lo = max(x["temp"][0] for x in xs); hi = min(x["temp"][1] for x in xs)
            pl = max(x["ph"][0] for x in xs); ph = min(x["ph"][1] for x in xs)
            def line(x, role):
                cnt = "1" if x["group"] == 1 else (f"{x['group']}" if g < 30 else f"{x['group']}–{x['group'] + 4}")
                return f'<li><strong>{cnt} × <a href="{species_url(x["id"])}">{e(x["name"])}</a></strong> ({role}): {e(x["note"])}</li>'
            items = (line(c, "centerpiece") if c else "") + line(sc, "school") + (line(bt, "bottom") if bt else "") + (line(cr, "cleanup crew") if cr else "")
            title = " + ".join(x["name"] for x in xs)
            cards += f'<div class="card"><h3>Plan {n}: {e(title)}</h3><ul>{items}</ul><p class="fine">Every pair in this plan checks out as compatible. Shared water: {trange((lo, hi))}, pH {prange((pl, ph))}.</p></div>'
        lit = round(g * 3.785)
        body = f"""<h1>{g}-Gallon Tank Stocking Ideas</h1>
<p><strong>A {g}-gallon ({lit} L) tank can hold {len(plans)} different community setups that all pass our compatibility checks.</strong> Each plan lists a centerpiece, a school, and a bottom or cleanup crew, with the shared temperature and pH that suit every species in it.</p>
{cards}
<h2>Before you buy</h2><ul><li>Cycle the tank first. Add fish over several weeks, starting with the hardiest group, so the filter bacteria keep up.</li>
<li>The counts are the minimum group sizes. In a {g}-gallon tank, stick close to them rather than adding extra species.</li>
<li>Quarantine new fish if you can, and watch the first two weeks closely.</li></ul>
<p class="fine">Want a different mix? Try the <a href="{u('/#checker')}">tank checker</a>.</p>
{gear({"name": f"{g}-gallon community", "tank_l": lit, "temp": (24, 26), "size_cm": 5, "kind": "fish", "id": "", "level": "mid", "diet": "omnivore"})}"""
        page(f"/stocking/{g}-gallon/", f"{g}-Gallon Fish Tank Stocking Ideas ({len(plans)} Compatible Plans)", f"{len(plans)} compatible stocking plans for a {g}-gallon ({lit} L) aquarium, with fish counts, shared temperature and pH, and why each species fits.", body)
        links.append(f'<a href="{u(f"/stocking/{g}-gallon/")}">{g}-gallon tank ideas</a>')
    page("/stocking/", "Fish Tank Stocking Ideas by Tank Size", "Compatible community stocking plans for 5 to 75 gallon aquariums.", "<h1>Stocking ideas by tank size</h1><div class='grid'>" + "".join(links) + "</div>")
    return links

from versus import VS
def vs_id(a, b): return f"{a}-vs-{b}"
def vs_links(i):
    xs = [(a, b) for a, b, _ in VS if i in (a, b)]
    if not xs: return ""
    return "<h2>Compare before you buy</h2><ul>" + "".join(f'<li><a href="{u(f"/compare/{vs_id(a, b)}/")}">{e(BY_ID[a]["name"])} vs {e(BY_ID[b]["name"])}</a></li>' for a, b in xs) + "</ul>"

def compat_count(i): return sum(1 for o in S if o["id"] != i and check(i, o["id"])["verdict"] == "yes")

def pick_reasons(x, y):
    r = []
    if x["tank_l"] < y["tank_l"]: r.append(f"you have a smaller tank: it needs {tank(x['tank_l'])} against {tank(y['tank_l'])}")
    CARE = {"easy": 0, "moderate": 1, "hard": 2}
    if CARE[x["care"]] < CARE[y["care"]]: r.append(f"you want an easier fish ({x['care']} care, against {y['care']})")
    if x["temp"][0] < y["temp"][0] - 1: r.append(f"your tank runs cooler: it is comfortable down to {f(x['temp'][0])} °F ({x['temp'][0]} °C)")
    if x["temp"][1] > y["temp"][1] + 1: r.append(f"your tank runs warm: it is comfortable up to {f(x['temp'][1])} °F ({x['temp'][1]} °C)")
    if x["ph"][1] > y["ph"][1] + 0.2: r.append(f"your tap water is hard or alkaline (it handles pH up to {x['ph'][1]:g})")
    if x["ph"][0] < y["ph"][0] - 0.2: r.append(f"your water is soft or acidic (it handles pH down to {x['ph'][0]:g})")
    cx, cy = compat_count(x["id"]), compat_count(y["id"])
    if cx > cy + 2: r.append(f"you want more tankmate options: {cx} of the {len(S) - 1} species we cover are a safe match, against {cy}")
    SH = {"no": 0, "babies": 1, "yes": 2}
    if x["kind"] == "fish" and SH[x["shrimp"]] < SH[y["shrimp"]]: r.append("you keep or plan to keep shrimp")
    if not x["nipper"] and y["nipper"]: r.append("you want long-finned tankmates, since it doesn't nip fins")
    if x["size_cm"] > y["size_cm"] * 1.4: r.append(f"you want a bigger, more visible animal ({size(x['size_cm'])} against {size(y['size_cm'])})")
    if x["size_cm"] * 1.4 < y["size_cm"]: r.append(f"you're stocking a small or nano tank ({size(x['size_cm'])} adult size)")
    if x["group"] < y["group"] and y["group"] >= 5: r.append(f"you want fewer animals: {('one or a pair' if x['group'] == 1 else str(x['group']))} instead of {y['group']}+")
    return r

def compare_pages():
    links = []
    for a_id, b_id, bottom in VS:
        a, b = BY_ID[a_id], BY_ID[b_id]
        r = check(a_id, b_id)
        rows = [("Adult size", size(a["size_cm"]), size(b["size_cm"])), ("Minimum tank", tank(a["tank_l"]), tank(b["tank_l"])),
                ("Temperature", trange(a["temp"]), trange(b["temp"])), ("pH", prange(a["ph"]), prange(b["ph"])),
                ("Care level", a["care"].title(), b["care"].title()), ("Temperament", TEMPER[a["temperament"]], TEMPER[b["temperament"]]),
                ("Group size", "1–2" if a["group"] == 1 else f"{a['group']}+", "1–2" if b["group"] == 1 else f"{b['group']}+"),
                ("Swims at", LEVEL[a["level"]], LEVEL[b["level"]]), ("Diet", a["diet"].title(), b["diet"].title()),
                ("Safe tank mates (of %d)" % (len(S) - 1), str(compat_count(a_id)), str(compat_count(b_id))),
                ("Shrimp-safe", {"no": "Yes", "babies": "Adults only", "yes": "No"}[a["shrimp"]] if a["kind"] == "fish" else "n/a", {"no": "Yes", "babies": "Adults only", "yes": "No"}[b["shrimp"]] if b["kind"] == "fish" else "n/a")]
        table = f'<div class="scroll"><table><tr><th></th><th>{e(a["name"])}</th><th>{e(b["name"])}</th></tr>' + "".join(f"<tr><th>{k}</th><td>{e(x)}</td><td>{e(y)}</td></tr>" for k, x, y in rows) + "</table></div>"
        picks = ""
        for x, y in ((a, b), (b, a)):
            rs = pick_reasons(x, y)
            if rs: picks += f"<h3>Pick the {e(x['name'].lower())} if</h3><ul>" + "".join(f"<li>{e(t)}.</li>" for t in rs) + "</ul>"
        lab, cls = VERDICT[r["verdict"]]
        together = f'<p><span class="badge {cls}">{lab}</span> ' + (e(r["reasons"][0][1]) if r["reasons"] else "Their needs overlap, so you could keep both.") + "</p>"
        body = f"""<h1>{e(a['name'])} vs {e(b['name'])}: Which Should You Buy?</h1>
<div class="answer good"><p><strong>Bottom line:</strong> {e(bottom)}</p></div>
<h2>Side by side</h2>{table}
<p class="fine">"Safe tank mates" counts how many of the {len(S) - 1} other species in our data are a clean match, with no cautions.</p>
{picks}<h2>Can you keep both?</h2>{together}
<h2>See each one's tank mates</h2><ul><li><a href="{species_url(a_id)}">Best tank mates for {e(plural(a['name']))}</a></li><li><a href="{species_url(b_id)}">Best tank mates for {e(plural(b['name']))}</a></li></ul>
{gear(a if a['tank_l'] >= b['tank_l'] else b)}"""
        page(f"/compare/{vs_id(a_id, b_id)}/", f"{a['name']} vs {b['name']}: Which to Buy? (Side-by-Side)", f"{a['name']} vs {b['name']} compared on tank size, temperature, pH, care level and tank-mate options. {bottom}"[:300], body)
        links.append(f'<a href="{u(f"/compare/{vs_id(a_id, b_id)}/")}">{e(a["name"])} vs {e(b["name"])}</a>')
    page("/compare/", "Aquarium Fish Comparisons: Which to Buy?", "Side-by-side buying comparisons of popular aquarium fish, shrimp and snails.", "<h1>Which should you buy?</h1><div class='grid'>" + "".join(links) + "</div>")
    return links

def home():
    data = {"species": [{k: s[k] for k in ("id", "name", "temp", "ph", "tank_l", "group", "kind")} for s in S], "pairs": {}}
    for a, b in itertools.combinations(S, 2):
        r = check(a["id"], b["id"])
        if r["verdict"] != "yes": data["pairs"][a["id"] + "|" + b["id"]] = [r["verdict"], [t for _, t in r["reasons"]]]
    with open(os.path.join(OUT, "compat.json"), "w") as fh: json.dump(data, fh, separators=(",", ":"))
    pop = "".join(f'<a href="{species_url(s["id"])}">{e(s["name"])} tank mates</a>' for s in POP)
    body = f"""<h1>Which fish can live together?</h1>
<p>Pick the fish, shrimp and snails you have or want. {NAME} compares temperature, pH, adult size, temperament, diet and fin-nipping for every pair and tells you what will clash.</p>
<section id="checker" class="card"><input type="search" id="q" placeholder="Search species, e.g. betta" aria-label="Search species"><div class="chips" id="chips"></div>
<div id="result" aria-live="polite"><p class="fine">Select two or more species.</p></div></section>
<h2>Stocking ideas by tank size</h2><div class="grid">{"".join(f'<a href="{u(f"/stocking/{g}-gallon/")}">{g}-gallon tank</a>' for g in TANKS)}</div>
<h2>Which should you buy?</h2><div class="grid">{"".join(f'<a href="{u(f"/compare/{vs_id(a, b)}/")}">{e(BY_ID[a]["name"])} vs {e(BY_ID[b]["name"])}</a>' for a, b, _ in VS)}</div>
<h2>Best tank mates for popular fish</h2><div class="grid">{pop}</div>
<script>window.BASE={json.dumps(BASE)}</script><script src="{u('/checker.js')}" defer></script>"""
    page("/", f"{NAME}: Aquarium Fish Compatibility Checker", "Free freshwater aquarium compatibility checker. Pick your fish and see which tank mates clash on temperature, pH, size or temperament, and why.", body)

JS = r"""
(async function(){
 const r=await fetch((window.BASE||'')+'/compat.json');const D=await r.json();const sel=new Set();
 const chips=document.getElementById('chips'),q=document.getElementById('q'),out=document.getElementById('result');
 const by=Object.fromEntries(D.species.map(s=>[s.id,s]));const F=c=>Math.round(c*9/5+32);
 function draw(){const t=q.value.toLowerCase();chips.innerHTML='';
  D.species.filter(s=>sel.has(s.id)||!t||s.name.toLowerCase().includes(t)).sort((a,b)=>a.name.localeCompare(b.name)).forEach(s=>{
   const b=document.createElement('button');b.textContent=s.name;b.className=sel.has(s.id)?'on':'';b.onclick=()=>{sel.has(s.id)?sel.delete(s.id):sel.add(s.id);draw();calc()};chips.appendChild(b)})}
 function esc(x){return x.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
 function calc(){const ids=[...sel];if(ids.length<2){out.innerHTML='<p class="fine">Select two or more species.</p>';return}
  let worst=0,items=[];const R={yes:0,caution:1,no:2};
  for(let i=0;i<ids.length;i++)for(let j=i+1;j<ids.length;j++){const k=[ids[i],ids[j]];const key=D.pairs[k[0]+'|'+k[1]]?k[0]+'|'+k[1]:k[1]+'|'+k[0];const p=D.pairs[key];
   if(p){worst=Math.max(worst,R[p[0]]);items.push('<li><span class="badge '+(p[0]=='no'?'bad':'warn')+'">'+(p[0]=='no'?'No':'Caution')+'</span> <strong>'+esc(by[k[0]].name)+' + '+esc(by[k[1]].name)+'</strong>: '+p[1].map(esc).join(' ')+'</li>')}}
  const S=ids.map(i=>by[i]);const tl=Math.max(...S.map(s=>s.temp[0])),th=Math.min(...S.map(s=>s.temp[1])),pl=Math.max(...S.map(s=>s.ph[0])),ph=Math.min(...S.map(s=>s.ph[1]));const tk=Math.max(...S.map(s=>s.tank_l));
  const cls=['good','warn','bad'][worst],lab=['Looks compatible','Possible, with caution','Not compatible'][worst];
  let h='<div class="answer '+cls+'"><span class="badge '+cls+'">'+lab+'</span>';
  h+='<ul>'+(tl<=th?'<li>Shared temperature: '+F(tl)+'–'+F(th)+' °F ('+tl+'–'+th+' °C)</li>':'<li>No temperature suits them all.</li>')+(pl<=ph?'<li>Shared pH: '+pl+'–'+ph+'</li>':'<li>No pH suits them all.</li>')+'<li>Tank: at least '+Math.round(tk/3.785)+' gallons ('+tk+' L), more for a full stock.</li></ul></div>';
  if(items.length)h+='<ul>'+items.join('')+'</ul>';out.innerHTML=h}
 q.oninput=draw;draw()})();
"""

def static():
    with open(os.path.join(OUT, "style.css"), "w") as fh: fh.write(CSS)
    with open(os.path.join(OUT, "checker.js"), "w") as fh: fh.write(JS)
    page("/about/", f"How {NAME} Works", "How the aquarium compatibility checks are made: the data, the rules, and their limits.", f"""<h1>How the checks work</h1>
<p>Every species has a profile: adult size, minimum tank, temperature range, pH range, temperament, group size, swimming level, diet, and flags for fin nipping, long fins, and eating shrimp or snails. For each pair, {NAME} checks:</p><ul>
<li><strong>Water:</strong> whether their temperature and pH ranges overlap, and by how much.</li>
<li><strong>Predation:</strong> whether one grows big enough to swallow the other, and whether it eats shrimp or snails.</li>
<li><strong>Fins:</strong> whether a known fin nipper would share a tank with long-finned or slow fish.</li>
<li><strong>Temperament and territory:</strong> aggressive fish with peaceful ones, and territorial fish that claim the same part of the tank.</li>
<li><strong>Feeding:</strong> slow eaters that would be out-competed.</li></ul>
<p>Some well-known pairs, like bettas with gouramis, get a hand-written verdict where the general rules are too blunt. When the rules are unsure, they say "with caution" rather than "yes".</p>
<p>Fish are individuals. A peaceful species can still produce a bully, and a semi-aggressive one can be fine in a large, planted tank. Use the verdicts as a starting point, quarantine new arrivals, and watch new tankmates closely for the first weeks.</p>
<p>Found a verdict you disagree with? That feedback is what improves the data.</p>""")
    page("/disclosure/", "Affiliate Disclosure and Privacy", "Affiliate disclosure and privacy policy.", f"""<h1>Affiliate disclosure and privacy</h1>
<p>{NAME} is free to use. Some links go to Amazon. As an Amazon Associate this site earns from qualifying purchases, at no extra cost to you. Those links never affect a compatibility verdict, which comes only from the species data.</p>
<p>This site sets no cookies of its own and runs no ads. Amazon may set cookies when you follow a link to its site; see Amazon's own privacy notice for details. The site host may keep standard server logs.</p>""")
    with open(os.path.join(OUT, "404.html"), "w") as fh:
        fh.write(f'<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Not found</title><link rel=stylesheet href="{u("/style.css")}"><main><h1>Page not found</h1><p><a href="{u("/")}">Back to the tank checker</a></p></main>')

def finish():
    with open(os.path.join(OUT, "sitemap.xml"), "w") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{x}</loc><lastmod>{TODAY}</lastmod></url>" for x in URLS) + "</urlset>")
    with open(os.path.join(OUT, "robots.txt"), "w") as fh: fh.write(f"User-agent: *\nAllow: /\nSitemap: {SITE}{u('/sitemap.xml')}\n")
    open(os.path.join(OUT, ".nojekyll"), "w").close()

if __name__ == "__main__":
    shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
    static(); stocking_pages(); compare_pages(); home(); species_pages(); finish()
    print(f"{len(URLS)} pages -> {OUT}")
