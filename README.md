# Tankmate Check (experiment D: buying-decision comparison site)

Aquarium fish buying-decision site. Every page is generated from one hand-checked dataset, so pages carry original data rather than rewritten articles.

## What's here
- `data/species.py`: 52 species (size, tank, temp, pH, temperament, group, diet, predation, fin-nipping, shrimp/snail safety). Source of truth.
- `data/versus.py`: hand-picked "X vs Y" comparisons with hand-written bottom lines.
- `build/compat.py`: pairwise compatibility rules plus hand overrides for famous pairs.
- `build/build.py`: static site generator, standard library only. Writes `site/`.
- `build/verify_content.py`: checks numbers in prose against the dataset.
- `content/species/*.md`: Haiku-drafted, Opus-reviewed care text. NOT published since the 2026-10-19 pivot (no informational articles). Kept in case it's useful later.

## Pages (79)
- `/species/<id>/` "Best tank mates for X" (ranked, with reasons), spec table, gear links.
- `/stocking/<n>-gallon/` "best fish for an N-gallon tank": up to 3 plans where every pair passes, with a bioload limit.
- `/compare/<a>-vs-<b>/` buying comparisons with "pick X if" lines computed from the data.
- `/` tank compatibility checker (runs on `compat.json`).

## Build
```
cd build
SITE_URL=https://<user>.github.io BASE_PATH=/tankmate-check AMAZON_TAG=<tag-20> python3 build.py
```
Without AMAZON_TAG the Amazon links carry no tag (no earnings, nothing broken).

## Hosting plan
GitHub Pages from the public repo `tankmate-check` (requested via coordinator 2026-10-19). Fallback: Cloudflare Pages direct upload of `site/`.

## Scaling levers
Add species to the dataset (every new species adds a page and enriches all others), add VS pairs, add stocking sizes once Search Console shows which pages get impressions.

## Amazon Associates timing
Sign up only once Search Console shows clicks: the 180-day clock for 3 qualifying sales starts at signup, and a lapsed application can't be reinstated.
