#!/usr/bin/env bash
# Build the two files to upload to Kaggle (see kaggle/README.md):
#   dist/kaggle/trr_code.zip   -- the committed code (git archive of HEAD) + GIT_HASH
#   dist/kaggle/trr_data.zip   -- LegalBench-RAG (corpus + benchmarks) + small caches that fix the folds
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

# data: the benchmark, the document MinHash signatures (same folds -> same dev/test split) and the
# routing document embeddings (Parth's router in --dense-baselines; recomputed if missing)
zip -qr "$out/trr_data.zip" data/raw/legalbenchrag data/cache/doc_minhash_*.npy data/cache/routing_emb_docs_*.npy

echo "code $hash -> $out/trr_code.zip ($(du -h "$out/trr_code.zip" | cut -f1))"
echo "data       -> $out/trr_data.zip ($(du -h "$out/trr_data.zip" | cut -f1))"
