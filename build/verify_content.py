"""Flags numbers in species prose that don't match the dataset."""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data"))
from species import S
ROOT = os.path.join(os.path.dirname(__file__), "..", "content", "species")
bad = 0
for s in S:
    p = os.path.join(ROOT, s["id"] + ".md")
    if not os.path.exists(p): print("MISSING", s["id"]); bad += 1; continue
    t = open(p).read()
    ok_c = set(s["temp"]); ok_f = {round(c*9/5+32) for c in s["temp"]}
    ok_l = {s["tank_l"]}; ok_g = {round(s["tank_l"]/3.785)}
    probs = []
    for n in re.findall(r"(\d+)\s*°C", t):
        if int(n) not in ok_c: probs.append(f"{n}°C")
    for n in re.findall(r"(\d+)\s*°F", t):
        if int(n) not in ok_f: probs.append(f"{n}°F")
    for n in re.findall(r"(\d+)\s*(?:L\b|liters|litres)", t):
        if int(n) not in ok_l: probs.append(f"{n}L")
    for n in re.findall(r"(\d+)\s*-?\s*gallons?", t):
        if int(n) not in ok_g: probs.append(f"{n}gal")
    for n in re.findall(r"pH (?:of )?(\d+\.?\d*)", t):
        if float(n) not in s["ph"]: probs.append(f"pH {n}")
    if "—" in t or "!" in t: probs.append("dash/!")
    heads = re.findall(r"^## (.+)$", t, re.M)
    if heads != ["Overview", "Tank setup", "Feeding", "Common mistakes"]: probs.append(f"heads {heads}")
    words = len(t.split())
    if probs: bad += 1; print(s["id"], words, probs)
print("files with issues:", bad)
