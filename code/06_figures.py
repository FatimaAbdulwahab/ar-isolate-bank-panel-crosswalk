#!/usr/bin/env python3
"""
06_figures.py - Draw the two figures.

PLAIN-LANGUAGE NOTE: Figure 1 is the "catalog at a glance": each row is an
Isolate Bank panel, each column a rapid panel target, and each square shows how
many isolates in that panel carry that target (darker = more). Figure 2 puts
the outside check next to Project 1: for each target, the Bank's sensitivity
and specificity (with 95% ranges) beside Project 1's. Figures carry a DRAFT
stamp until you approve them; run with --final to remove it.
You do not need to open this file.
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
FIG = os.path.join(ROOT, "paper", "figures")
FINAL = "--final" in sys.argv
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e1", "#fcfcfb"
BLUE, ORANGE = "#2a78d6", "#eb6834"
SEQ = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6",
       "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "figure.facecolor": SURF, "axes.facecolor": SURF})
TARGETS = ["mecA", "mecC", "vanA", "vanB", "KPC", "NDM", "OXA-48-like", "VIM", "IMP", "CTX-M",
           "OXA-23-like", "OXA-24/40-like", "OXA-58-like", "SME", "mcr-1", "mcr-2", "mcr-3"]


def stamp(fig):
    if not FINAL:
        fig.text(0.99, 0.995, "DRAFT - not yet verified by the author", ha="right", va="top",
                 color=ORANGE, fontsize=9, fontweight="bold")


def fig1():
    g = pd.read_csv(os.path.join(PROC, "panel_target_grid.csv"))
    g = g[g.n_in_scope > 0].copy()
    def short(n, code):
        n = n.replace("(Custom)", "(custom)")
        return n if len(n) <= 58 else n[:50].rstrip(" -(/") + "... (" + code + ")"
    g["label"] = [short(n, c) + "  n=" + str(k) for n, c, k in zip(g.panel_name, g.panel_code, g.n_isolates)]
    order = g[TARGETS].gt(0).dot(range(len(TARGETS), 0, -1))
    g = g.assign(_o=order).sort_values(["_o", "n_isolates"], ascending=[False, False])
    m = g[TARGETS].values
    cmap = LinearSegmentedColormap.from_list("seq", SEQ)
    fig, ax = plt.subplots(figsize=(11, 0.32 * len(g) + 2.2))
    vmax = max(1, m.max())
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            v = m[i, j]
            if v == 0:
                ax.add_patch(plt.Rectangle((j + 0.04, i + 0.04), 0.92, 0.92, color="#f1f0ec", lw=0))
                continue
            c = cmap(0.15 + 0.85 * (v / vmax) ** 0.6)
            ax.add_patch(plt.Rectangle((j + 0.04, i + 0.04), 0.92, 0.92, color=c, lw=0))
            ax.text(j + 0.5, i + 0.52, str(v), ha="center", va="center", fontsize=7.5,
                    color="#ffffff" if (v / vmax) ** 0.6 > 0.45 else INK)
    ax.set_xlim(0, len(TARGETS)); ax.set_ylim(len(g), 0)
    ax.set_xticks([j + 0.5 for j in range(len(TARGETS))]); ax.set_xticklabels(TARGETS, rotation=45, ha="left")
    ax.xaxis.tick_top()
    ax.set_yticks([i + 0.5 for i in range(len(g))]); ax.set_yticklabels(g.label, fontsize=8)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    ax.set_title("Isolate Bank panels by rapid blood culture panel target\n"
                 "Number of isolates in each panel whose CDC gene list includes the target", loc="left",
                 color=INK, fontsize=11, pad=48)
    fig.text(0.01, 0.005, "Source: CDC & FDA Antimicrobial Resistance Isolate Bank, accessed 2026-10-24; "
             "targets grouped with the NCBI AMRFinderPlus gene hierarchy. Panels with no bacteria the rapid "
             "panels test are omitted.", fontsize=7, color=MUTED)
    fig.subplots_adjust(bottom=0.03)
    stamp(fig)
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(FIG, f"fig1_panel_by_target.{ext}"), dpi=200)
    plt.close(fig)


def fig2():
    p = os.path.join(PROC, "external_check_B_concordance.csv")
    if not os.path.exists(p):
        return
    b = pd.read_csv(p)
    left = [("mecA", "oxacillin or cefoxitin"), ("vanA", "vancomycin"), ("vanB", "vancomycin"),
            ("KPC", "meropenem"), ("NDM", "meropenem"), ("OXA-48-like", "meropenem"), ("VIM", "meropenem"),
            ("IMP", "meropenem"), ("CTX-M", "ceftriaxone")]
    right = [("mecA or mecC", "oxacillin or cefoxitin", "mecA or mecC"), ("vanA or vanB", "vancomycin", "vanA or vanB"),
             ("any panel carbapenemase (KPC, NDM, OXA-48-like, VIM, IMP)", "meropenem", "any of 5 carbapenemases"),
             ("CTX-M", "ceftriaxone", "CTX-M")]

    def get(t, d):
        x = b[(b.panel_target == t) & (b.drug == d)]
        return x.iloc[0] if len(x) else None
    L = [(f"{t} | {d}", get(t, d)) for t, d in left]
    R = [(f"{lab} | {d}", get(t, d)) for t, d, lab in right]
    L = [(a, r) for a, r in L if r is not None]
    R = [(a, r) for a, r in R if r is not None]
    fig, axes = plt.subplots(2, 1, figsize=(9.5, 0.36 * (len(L) + len(R)) + 3.2),
                             gridspec_kw={"height_ratios": [len(L), len(R)]})
    for ax, rows, k, ttl, nk in [
            (axes[0], L, "ppv", "Gene present: share of isolates that test resistant (PPV)", ("gene_pos_R", "gene_pos_notR")),
            (axes[1], R, "sensitivity", "Resistant: share of isolates that carry a panel target (sensitivity)",
             ("gene_pos_R", "gene_neg_R"))]:
        for i, (lab, r) in enumerate(rows):
            for off, src, col in [(-0.15, "project1", ORANGE), (0.15, "bank", BLUE)]:
                v, lo, hi = r.get(f"{src}_{k}"), r.get(f"{src}_{k}_lo95"), r.get(f"{src}_{k}_hi95")
                if pd.isna(v) or v == "":
                    continue
                ax.plot([float(lo), float(hi)], [i + off, i + off], color=col, lw=2, solid_capstyle="round")
                ax.plot(float(v), i + off, "o", color=col, ms=6.5, mec=SURF, mew=1.5)
        n = [int(r[f"bank_{nk[0]}"] + r[f"bank_{nk[1]}"]) for _, r in rows]
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels([f"{lab}  (Bank n={m})" for (lab, _), m in zip(rows, n)])
        ax.invert_yaxis()
        ax.set_xlim(0, 1.02)
        ax.set_xticks([0, .25, .5, .75, 1]); ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
        ax.set_title(ttl, loc="left", color=INK, fontsize=10)
        ax.grid(axis="x", color=GRID, lw=0.8); ax.set_axisbelow(True)
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.tick_params(length=0)
    axes[0].plot([], [], "o-", color=ORANGE, label="Project 1 benchmark (U.S. clinical isolates, submitter AST)")
    axes[0].plot([], [], "o-", color=BLUE, label="Isolate Bank (CDC reference broth microdilution)")
    axes[0].legend(loc="lower left", frameon=False, fontsize=8, labelcolor=INK2)
    fig.suptitle("Outside check: Project 1 gene rules applied to Isolate Bank reference results",
                 x=0.01, ha="left", color=INK, fontsize=11)
    fig.text(0.01, 0.005, "Dots = estimate; lines = 95% Wilson range. Genes from NCBI AMRFinderPlus; Project 1 "
             "breakpoints (CLSI M100-Ed35);\nintermediate counted as not resistant; Bank isolates also in Project 1 excluded. "
             "Bank sensitivity reflects a collection built to include hard cases, not a patient population.",
             fontsize=7, color=MUTED)
    stamp(fig)
    fig.tight_layout(rect=(0, 0.045, 1, 0.97))
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(FIG, f"fig2_external_check.{ext}"), dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(FIG, exist_ok=True)
    fig1()
    fig2()
    print("figures written to", FIG)
