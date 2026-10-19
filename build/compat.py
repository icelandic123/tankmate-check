"""Pairwise compatibility rules. Conservative on purpose: when in doubt, say 'caution'."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data"))
from species import BY_ID

RANK = {"yes": 0, "caution": 1, "no": 2}
MILD_NIPPERS = {"zebra-danio"}
SHRIMP = {"cherry-shrimp", "amano-shrimp"}
SNAILS = {"nerite-snail", "mystery-snail"}
LABYRINTH = {"betta", "dwarf-gourami", "honey-gourami", "pearl-gourami"}

# Hand-checked judgements for well-known pairs where the general rules are too blunt.
OVERRIDES = {
    ("betta", "dwarf-gourami"): ("no", "Bettas and dwarf gouramis are both territorial labyrinth fish that claim the surface; males commonly fight."),
    ("betta", "pearl-gourami"): ("no", "Pearl gouramis are territorial surface fish and larger than a betta; the two often fight over the top of the tank."),
    ("betta", "honey-gourami"): ("caution", "Honey gouramis are gentle, but both fish want the surface. It can work in a long, well-planted tank of 76 L (20 gal) or more; have a backup plan."),
    ("dwarf-gourami", "pearl-gourami"): ("caution", "Gouramis of different species still squabble over the surface; give a large, planted tank."),
    ("dwarf-gourami", "honey-gourami"): ("caution", "Male dwarf gouramis can bully the smaller honey gourami."),
    ("guppy", "endler"): ("caution", "They get along, but guppies and Endler's livebearers interbreed. Fine if you don't mind hybrids."),
    ("red-tail-shark", "rainbow-shark"): ("no", "Both are territorial bottom 'sharks' of the same shape; they fight constantly."),
    ("molly", "platy"): ("yes", None),
    ("oscar", "common-pleco"): ("caution", "Common plecos are one of the few fish regularly kept with oscars: armored, fast-growing and too big to swallow once adult. Both are huge waste producers, so the tank needs to be far larger than either needs alone."),
    ("oscar", "bristlenose-pleco"): ("caution", "An adult bristlenose is armored and usually ignored by an oscar, but a small one can be eaten. Add it only fully grown and give it caves the oscar can't reach."),
}
OVERRIDES = {tuple(sorted(k)): v for k, v in OVERRIDES.items()}

def _ov(a, b):
    return min(a[1], b[1]) - max(a[0], b[0])

def gal(l):
    return round(l / 3.785)

def check(a_id, b_id):
    a, b = BY_ID[a_id], BY_ID[b_id]
    reasons = []  # (severity, text)
    def add(sev, text): reasons.append((sev, text))

    t = _ov(a["temp"], b["temp"])
    if t < 0:
        add("no", f"No shared temperature: {a['name']} needs {a['temp'][0]}–{a['temp'][1]} °C, {b['name']} needs {b['temp'][0]}–{b['temp'][1]} °C.")
    elif t < 2:
        add("caution", f"Their temperature ranges barely overlap ({max(a['temp'][0], b['temp'][0])}–{min(a['temp'][1], b['temp'][1])} °C), so you'd keep one of them at the edge of its comfort zone.")
    p = _ov(a["ph"], b["ph"])
    if p < -0.5:
        add("no", f"Very different water chemistry: pH {a['ph'][0]}–{a['ph'][1]} for the {a['name']} versus {b['ph'][0]}–{b['ph'][1]} for the {b['name']}.")
    elif p < 0:
        add("caution", f"Their preferred pH ranges don't quite meet ({a['ph'][0]}–{a['ph'][1]} vs {b['ph'][0]}–{b['ph'][1]}). Both may adapt to water in between, but neither will be at its best.")

    for x, y in ((a, b), (b, a)):
        if x["id"] == "axolotl" or x.get("species_only"):
            add("no", f"The {x['name']} is best kept in a tank of its own kind. " + x["note"])
        # predation
        if y["id"] in SHRIMP:
            if x["shrimp"] == "yes" and (y["id"] == "cherry-shrimp" or x["max_prey_cm"] >= y["size_cm"]):
                add("no", f"The {x['name']} hunts shrimp and will eat {y['name'].lower()}.")
            elif x["shrimp"] == "yes":
                add("caution", f"The {x['name']} picks at shrimp; adult {y['name'].lower()} are big enough to usually survive, but moulting shrimp are at risk.")
            elif x["shrimp"] == "babies":
                add("caution", f"Adult {y['name'].lower()} are usually safe, but the {x['name']} will eat baby shrimp, so the colony won't grow much without dense plants or moss.")
        elif y["id"] in SNAILS:
            if x["snails"]:
                add("no", f"The {x['name']} eats snails.")
            if y.get("has_tentacles") and x["nipper"]:
                add("caution", f"The {x['name']} tends to nip at the {y['name'].lower()}'s long feelers.")
        elif x["max_prey_cm"] > 0:
            if y["size_cm"] <= x["max_prey_cm"]:
                add("no", f"An adult {x['name']} can swallow a {y['name']} (about {y['size_cm']:g} cm), and will.")
            elif y["size_cm"] <= x["max_prey_cm"] * 1.3:
                add("caution", f"A {y['name']} is close to bite-size for an adult {x['name']}; young or small individuals are at risk.")
        # fins
        if x["nipper"] and (y["longfin"] or y.get("slow")) and y["kind"] != "invert":
            if x["id"] in MILD_NIPPERS:
                add("caution", f"The {x['name']} is fast and may nip the {y['name']}'s long fins, especially in a small group.")
            else:
                add("no", f"The {x['name']} is a fin nipper, and the {y['name']}'s long, slow fins make an easy target.")
        elif x["nipper"] and y.get("shy"):
            add("caution", f"The boisterous {x['name']} will stress the shy {y['name']}.")
        if x.get("attacks_longfin") and y["longfin"] and y["kind"] == "fish":
            add("caution", f"The {x['name']} may see the {y['name']}'s bright, flowing fins as a rival and attack. Many pairings work, some don't; watch closely for the first weeks.")
        # temperament
        if x["temperament"] == "aggressive" and y["temperament"] == "peaceful" and y["kind"] != "invert":
            add("no", f"The {x['name']} is aggressive and will bully or kill a peaceful {y['name']}.")
        if x.get("bottom_bully") and y["level"] in ("bottom", "all") and y["kind"] == "fish":
            add("caution", f"The {x['name']} chases other bottom dwellers like the {y['name']} away from food and cover.")
        if x.get("slime_grazer") and (y.get("slow") or y["id"] in ("angelfish", "discus")):
            add("caution", f"Adult {x['name']}s sometimes latch onto slow, flat-sided fish like the {y['name']} at night to graze their slime coat.")
        if x.get("slow") and not y.get("slow") and y["kind"] == "fish" and y["temperament"] != "aggressive":
            add("caution", f"The {x['name']} is a slow eater; the faster {y['name']} will take most of the food unless you target-feed.")
        if x.get("rift_lake") and not y.get("rift_lake") and y["kind"] == "fish":
            add("no", f"The {x['name']} is a Lake Malawi cichlid and belongs in a rift-lake tank with similar cichlids.")
    if a["temperament"] == "aggressive" and b["temperament"] in ("aggressive", "semi") and a["kind"] == b["kind"] == "fish":
        add("caution", "Two assertive fish: expect fights unless the tank is large with broken lines of sight.")
    if b["temperament"] == "aggressive" and a["temperament"] == "semi" and a["kind"] == b["kind"] == "fish":
        add("caution", "Two assertive fish: expect fights unless the tank is large with broken lines of sight.")
    if a.get("territorial") and b.get("territorial") and a["level"] == b["level"] and a["level"] == "bottom":
        add("caution", f"Both fish claim territory on the bottom; give each its own cave and plenty of floor space.")

    key = tuple(sorted((a_id, b_id)))
    if key in OVERRIDES:
        sev, text = OVERRIDES[key]
        reasons = [r for r in reasons if RANK[r[0]] < RANK[sev]] + ([(sev, text)] if text else [])
    # de-duplicate, worst first
    seen, out = set(), []
    for sev, text in sorted(reasons, key=lambda r: -RANK[r[0]]):
        if text not in seen:
            seen.add(text); out.append((sev, text))
    verdict = max((RANK[s] for s, _ in out), default=0)
    verdict = [k for k, v in RANK.items() if v == verdict][0]
    shared_t = (max(a["temp"][0], b["temp"][0]), min(a["temp"][1], b["temp"][1]))
    shared_p = (max(a["ph"][0], b["ph"][0]), min(a["ph"][1], b["ph"][1]))
    tank = max(a["tank_l"], b["tank_l"])
    return dict(verdict=verdict, reasons=out, temp=shared_t if shared_t[0] <= shared_t[1] else None,
                ph=shared_p if shared_p[0] <= shared_p[1] else None, tank_l=tank)

if __name__ == "__main__":
    from species import S
    import itertools, collections
    c = collections.Counter()
    for a, b in itertools.combinations([s["id"] for s in S], 2):
        c[check(a, b)["verdict"]] += 1
    print(c)
    for pair in sys.argv[1:]:
        a, b = pair.split(":")
        print(pair, check(a, b))
