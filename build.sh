#!/bin/sh
# Rebuilds the published site into docs/ (GitHub Pages serves main:/docs).
cd "$(dirname "$0")/build" && SITE_URL=https://icelandic123.github.io BASE_PATH=/tankmate-check OUT_DIR=../docs GSC_VERIFY="${GSC_VERIFY:-$(cat ../gsc-verify.txt 2>/dev/null)}" python3 build.py
