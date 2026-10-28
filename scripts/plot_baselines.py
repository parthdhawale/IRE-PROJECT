"""Mid-report figures from results/tables/baselines_<split>.csv.

F2: DRM@k per subset for the flat baselines (+ doc-first).
F3: char recall@k of dense vs oracle (the gap is what document mismatch costs).
Saved as PNG and PDF in results/figures/.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trr.config import load_config  # noqa: E402

STYLE = {"bm25": ("#1f77b4", "o"), "dense": ("#ff7f0e", "s"), "hybrid": ("#2ca02c", "^"),
         "docfirst": ("#9467bd", "D"), "oracle": ("#7f7f7f", "x")}


def panel_plot(df: pd.DataFrame, methods: list[str], metric: str, ylabel: str, title: str, path: Path) -> None:
    subsets = [s for s in df.subset.unique() if s != "ALL"] + ["ALL"]
    fig, axes = plt.subplots(1, len(subsets), figsize=(3.2 * len(subsets), 3.0), sharey=True)
    for ax, subset in zip(axes, subsets):
        for m in methods:
            g = df[(df.subset == subset) & (df.method == m)].sort_values("k")
            if g.empty:
                continue
            color, marker = STYLE.get(m, (None, "."))
            ax.plot(g.k, g[metric], marker=marker, color=color, label=m, linewidth=1.5, markersize=4)
        ax.set_xscale("log", base=2)
        ax.set_xticks([1, 4, 16, 64], labels=["1", "4", "16", "64"])
        ax.set_title("ALL (macro)" if subset == "ALL" else subset, fontsize=10)
        ax.set_xlabel("k")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel(ylabel)
    axes[0].set_ylim(0, 1)
    axes[-1].legend(fontsize=8, loc="best")
    fig.suptitle(title, fontsize=11)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(path.with_suffix(f".{ext}"), dpi=200)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="mini")
    args = ap.parse_args()
    cfg = load_config()
    df = pd.read_csv(Path(cfg["paths"]["tables"]) / f"baselines_{args.split}.csv")
    fig_dir = Path(cfg["paths"]["figures"])
    fig_dir.mkdir(parents=True, exist_ok=True)
    panel_plot(df, ["bm25", "dense", "hybrid", "docfirst"], "drm", "DRM@k (lower is better)",
               f"F2. Document-level retrieval mismatch of flat baselines ({args.split})",
               fig_dir / f"F2_drm_at_k_{args.split}")
    panel_plot(df, ["dense", "hybrid", "oracle"], "char_r", "char recall@k",
               f"F3. Char recall: flat retrieval vs oracle document ({args.split})",
               fig_dir / f"F3_char_recall_oracle_{args.split}")
    print(f"wrote figures to {fig_dir}")


if __name__ == "__main__":
    main()
