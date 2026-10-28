"""Download LegalBench-RAG (corpus + benchmarks) into data/raw/legalbenchrag/.

Skips the download if the folder already has both corpus/ and benchmarks/.
If the Dropbox link stops working, download the folder by hand from the link in
github.com/zeroentropy-cc/legalbenchrag and unzip it into paths.raw.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trr.config import load_config  # noqa: E402


def main() -> None:
    cfg = load_config()
    raw = Path(cfg["paths"]["raw"])
    if (raw / "corpus").is_dir() and (raw / "benchmarks").is_dir():
        print(f"data already present in {raw}")
        return
    raw.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "legalbenchrag.zip"
        print("downloading LegalBench-RAG (~90 MB) ...")
        with urllib.request.urlopen(cfg["data"]["download_url"]) as r, open(zip_path, "wb") as f:
            shutil.copyfileobj(r, f)
        with zipfile.ZipFile(zip_path) as z:
            for member in z.infolist():
                target = (raw / member.filename).resolve()
                if not target.is_relative_to(raw.resolve()):  # zip-slip guard
                    raise RuntimeError(f"unsafe path in zip: {member.filename}")
            z.extractall(raw)
    print(f"extracted to {raw}")


if __name__ == "__main__":
    main()
