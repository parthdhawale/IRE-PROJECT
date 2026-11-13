#!/usr/bin/env bash
# Build the file to upload to Kaggle (see kaggle/README.md):
#   dist/kaggle/trr_code.zip   -- the committed code (git archive of HEAD) + GIT_HASH
# Data is not bundled: the CLERC notebook downloads CLERC itself. (A LegalBench run would also need
# data/raw/legalbenchrag and data/cache/doc_minhash_*.npy as a second dataset.)
# The code bundle is made from the last commit only, so a run's git hash always names the exact code:
# commit first, then bundle.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! git diff --quiet HEAD -- src scripts configs tests pyproject.toml kaggle; then
  echo "Uncommitted changes in code/config: commit first, so the bundle's git hash names the code." >&2
  exit 1
fi

out=dist/kaggle
rm -rf "$out" && mkdir -p "$out"
hash=$(git rev-parse --short HEAD)

# code: tracked files at HEAD, plus the hash stamp read by trr.config.git_hash()
git archive --format=zip -o "$out/trr_code.zip" HEAD
tmp=$(mktemp -d)
echo "$hash" > "$tmp/GIT_HASH"
(cd "$tmp" && zip -q "$OLDPWD/$out/trr_code.zip" GIT_HASH)
rm -rf "$tmp"


echo "code $hash -> $out/trr_code.zip ($(du -h "$out/trr_code.zip" | cut -f1))"
