"""H1: boilerplate-share analysis and the go/no-go decision (plan Phase 1, Track A).

Writes results/figures/F1_boilerplate_share.{png,pdf}, results/tables/h1_boilerplate.md and
the go/no-go decision (with the numbers behind it) into results/notes/phase1.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trr.analysis.h1_boilerplate import go_no_go, leaf_frame, run_h1, top_shared_leaves  # noqa: E402
from trr.config import load_config  # noqa: E402
from trr.data.load import load_corpus  # noqa: E402


def box_plot(shares: pd.DataFrame, taus: list[float], subsets: list[str], path: Path) -> None:
    fig, axes = plt.subplots(1, len(subsets), figsize=(3.2 * len(subsets), 3.2), sharey=True)
    for ax, subset in zip(axes, subsets):
        data = [shares[(shares.subset == subset) & (shares.tau == tau)]["share"] for tau in taus]
        ax.boxplot(data, tick_labels=[str(t) for t in taus], showfliers=False)
        ax.set_title(subset, fontsize=10)
        ax.set_xlabel("tau")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("boilerplate share")
    axes[0].set_ylim(0, 1)
    fig.suptitle("F1. Boilerplate share per subset x tau", fontsize=11)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(path.with_suffix(f".{ext}"), dpi=200)
    plt.close(fig)


def top_leaf_lines(sections: pd.DataFrame, edges_by: dict, subsets: list[str], go_tau: float,
                   raw: str) -> list[str]:
    """10 most-shared leaves per subset at go_tau, with a short text preview for each."""
    lines = []
    for subset in subsets:
        leaves = leaf_frame(sections, subset)
        top = top_shared_leaves(leaves, edges_by[(subset, go_tau)], n=10)
        if top.empty:
            continue
        doc_text = {d.doc_id: d.text for d in load_corpus(raw, subset)}
        bounds = leaves.set_index("section_id")[["start", "end", "doc_id"]]
        lines.append(f"\n### {subset}\n")
        for _, r in top.iterrows():
            b = bounds.loc[r.section_id]
            preview = doc_text[b.doc_id][b.start:b.end][:80].replace("\n", " ").strip()
            lines.append(f"- {r.doc_count} docs | `{r.section_id}` | {preview}")
    return lines


def main() -> None:
    cfg = load_config()
    cache, tables = Path(cfg["paths"]["cache"]), Path(cfg["paths"]["tables"])
    figures, notes = Path(cfg["paths"]["figures"]), Path(cfg["paths"]["notes"])
    for d in (tables, figures, notes):
        d.mkdir(parents=True, exist_ok=True)

    sections = pd.read_parquet(cache / "sections.parquet")
    subsets, taus = cfg["data"]["subsets"], cfg["h1"]["taus"]
    shares, edges_by = run_h1(sections, subsets, taus, cfg["minhash"]["num_perm"], cfg["seed"])

    box_plot(shares, taus, subsets, figures / "F1_boilerplate_share")

    medians = shares.groupby(["subset", "tau"])["share"].median().unstack("tau").round(3)
    (tables / "h1_boilerplate.md").write_text(
        "# H1: boilerplate share medians\n\n" + medians.to_markdown() + "\n")

    go_tau, go_share = cfg["h1"]["go_tau"], cfg["h1"]["go_median_share"]
    go, go_medians = go_no_go(shares, go_tau, go_share)
    decision = "GO" if go else "NO-GO"

    note = [
        "# Phase 1: H1 boilerplate-share analysis and go/no-go\n",
        f"**Decision: {decision}**\n",
        f"Rule: GO if median share at tau={go_tau} is >= {go_share} on ContractNLI AND on at "
        "least one of CUAD (within contract type) or MAUD.\n",
        f"## Medians at tau={go_tau}\n",
        go_medians.round(3).to_frame("median_share").to_markdown(), "",
        "## Medians at every tau\n",
        medians.to_markdown(), "",
        f"## 10 most-shared leaves per subset (tau={go_tau})",
        *top_leaf_lines(sections, edges_by, subsets, go_tau, cfg["paths"]["raw"]),
    ]
    (notes / "phase1.md").write_text("\n".join(note))

    print(f"decision: {decision}")
    print(go_medians.round(3))
    print(f"wrote {tables / 'h1_boilerplate.md'}, {figures / 'F1_boilerplate_share.png'}, "
          f"{notes / 'phase1.md'}")


if __name__ == "__main__":
    main()
