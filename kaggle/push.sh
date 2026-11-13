#!/usr/bin/env bash
# Upload the bundle to Kaggle and start the E11 notebook, with the Kaggle CLI and ~/.kaggle/kaggle.json.
#   kaggle/push.sh datasets   # create (private) or update trr-code; create trr-data once
#   kaggle/push.sh kernel     # push kaggle/e11_clerc.ipynb as a private notebook: Kaggle runs it (Save & Run All)
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
    for name in code data; do
      d="$out/upload_$name"
      rm -rf "$d" && mkdir -p "$d"
      cp "$out/trr_$name.zip" "$d/"
      printf '{"title": "trr-%s", "id": "%s/trr-%s", "licenses": [{"name": "other"}]}\n' "$name" "$user" "$name" \
        > "$d/dataset-metadata.json"
      if exists "trr-$name"; then
        if [ "$name" = code ]; then
          $K datasets version -p "$d" -m "code $hash"
        else
          echo "trr-data already exists: not re-uploaded"
        fi
      else
        $K datasets create -p "$d"            # private unless --public is given
      fi
    done
    ;;
  kernel)
    d="$out/kernel"
    rm -rf "$d" && mkdir -p "$d"
    cp kaggle/e11_clerc.ipynb "$d/"
    cat > "$d/kernel-metadata.json" <<EOF
{"id": "$user/trr-e11-clerc", "title": "trr-e11-clerc", "code_file": "e11_clerc.ipynb",
 "language": "python", "kernel_type": "notebook", "is_private": true, "enable_gpu": false,
 "enable_internet": true, "dataset_sources": ["$user/trr-code", "$user/trr-data"],
 "competition_sources": [], "kernel_sources": []}
EOF
    $K kernels push -p "$d"
    ;;
  *)
    echo "usage: kaggle/push.sh datasets|kernel" >&2
    exit 1
    ;;
esac
