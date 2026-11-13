#!/usr/bin/env bash
# Upload the bundle to Kaggle and start the E11 notebook, with the Kaggle CLI and ~/.kaggle/kaggle.json.
#   kaggle/push.sh datasets   # create (private) or update the trr-code dataset
#   kaggle/push.sh kernel e11_clerc        # push kaggle/<name>.ipynb as private notebook trr-<name-with-dashes>;
#   kaggle/push.sh kernel e12_clerc gpu    # Kaggle runs it on push (Save & Run All); "gpu" turns the GPU on
# Build the bundle first (kaggle/make_bundle.sh). The account name is read from the token file at run time.
set -euo pipefail
cd "$(dirname "$0")/.."
K=.venv/bin/kaggle
user=$(.venv/bin/python -c "import json,os;print(json.load(open(os.path.expanduser('~/.kaggle/kaggle.json')))['username'])")
out=dist/kaggle
hash=$(unzip -p "$out/trr_code.zip" GIT_HASH)

exists() { $K datasets status "$user/$1" >/dev/null 2>&1; }

case "${1:-}" in
  datasets)
    for name in code; do
      d="$out/upload_$name"
      rm -rf "$d" && mkdir -p "$d"
      cp "$out/trr_$name.zip" "$d/"
      printf '{"title": "trr-%s", "id": "%s/trr-%s", "licenses": [{"name": "other"}]}\n' "$name" "$user" "$name" \
        > "$d/dataset-metadata.json"
      if exists "trr-$name"; then
        $K datasets version -p "$d" -m "code $hash"
      else
        $K datasets create -p "$d"            # private unless --public is given
      fi
    done
    ;;
  kernel)
    nb="${2:?notebook name, e.g. e11_clerc}"
    slug="trr-${nb//_/-}"
    gpu=false; [ "${3:-}" = gpu ] && gpu=true
    d="$out/kernel_$nb"
    rm -rf "$d" && mkdir -p "$d"
    cp "kaggle/$nb.ipynb" "$d/"
    cat > "$d/kernel-metadata.json" <<EOF
{"id": "$user/$slug", "title": "$slug", "code_file": "$nb.ipynb",
 "language": "python", "kernel_type": "notebook", "is_private": true, "enable_gpu": $gpu,
 "enable_internet": true, "dataset_sources": ["$user/trr-code"],
 "competition_sources": [], "kernel_sources": []}
EOF
    $K kernels push -p "$d"
    ;;
  *)
    echo "usage: kaggle/push.sh datasets | kernel <notebook> [gpu]" >&2
    exit 1
    ;;
esac
