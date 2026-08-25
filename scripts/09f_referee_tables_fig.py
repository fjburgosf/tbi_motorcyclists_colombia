# -*- coding: utf-8 -*-
"""
09f_referee_tables_fig.py

Builds the referee-revision supplementary items from 09e outputs:
  * Figure S2  -> figures/figS2_shrinkage.png  (raw vs empirical-Bayes rates)
  * Table S5 markdown (empirical-Bayes shrunken departmental rates)
  * Table S6 markdown (HMC hierarchical-logistic diagnostics: R-hat, ESS)
Prints the two tables to stdout for insertion into the manuscript.
"""
from pathlib import Path
import unicodedata
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis")
ROB = BASE / "results" / "robustness"
FIG = BASE / "figures"


def deaccent(s):
    return "".join(c for c in unicodedata.normalize("NFKD", str(s))
                   if not unicodedata.combining(c))


# ------------------------------------------------------------------ Figure S2
g = pd.read_csv(ROB / "territorial_eb_shrinkage.csv")
g["name"] = g["depto_nombre"].map(deaccent).str.replace(
    "Archipielago de San Andres, Providencia y Santa Catalina", "San Andres", regex=False)
g = g.sort_values("rate_eb", ascending=True).reset_index(drop=True)

fig, ax = plt.subplots(figsize=(7.2, 8.6))
ypos = np.arange(len(g))
# EB posterior with 95% CrI
ax.errorbar(g["rate_eb"], ypos,
            xerr=[g["rate_eb"] - g["eb_lo"], g["eb_hi"] - g["rate_eb"]],
            fmt="o", color="#1f4e79", ecolor="#9db8d2", elinewidth=1.4,
            capsize=2, markersize=4.5, label="Empirical-Bayes rate (95% CrI)", zorder=3)
# raw rates
ax.scatter(g["rate_raw"], ypos, marker="x", color="#c0392b", s=34,
           label="Raw (unshrunk) rate", zorder=4)
prior = float(g["rate_eb"].iloc[len(g) // 2])  # visual ref not used; use JSON mean below
ax.set_yticks(ypos)
ax.set_yticklabels(g["name"], fontsize=7.5)
ax.set_xlabel("Motorcyclist fatality rate per 100,000 population (2015–2024)", fontsize=9)
ax.set_title("Departmental rates: raw vs empirical-Bayes shrinkage", fontsize=10)
ax.legend(loc="lower right", fontsize=8, frameon=True)
ax.grid(axis="x", ls=":", alpha=0.5)
ax.margins(y=0.01)
fig.tight_layout()
fig.savefig(FIG / "figS2_shrinkage.png", dpi=200)
print("Saved figure:", FIG / "figS2_shrinkage.png")

# ------------------------------------------------------------------ Table S5
gt = g.sort_values("rate_eb", ascending=False).reset_index(drop=True)
print("\n===== TABLE S5 (markdown) =====")
print("| Department | Deaths | Raw rate /100k | EB rate /100k (95% CrI) | Top tertile (EB) |")
print("|---|---:|---:|---:|:---:|")
for _, r in gt.iterrows():
    flag = "✔" if r["top_tertile_eb"] else ""
    print(f"| {r['name']} | {int(r['deaths']):,} | {r['rate_raw']:.2f} | "
          f"{r['rate_eb']:.2f} ({r['eb_lo']:.2f}–{r['eb_hi']:.2f}) | {flag} |")

# ------------------------------------------------------------------ Table S6
d = pd.read_csv(ROB / "lethality_hmc_diagnostics.csv")
print("\n===== TABLE S6 (markdown) =====")
print("| Parameter | Posterior mean (log-odds) | OR (95% CrI) | Split-$\\hat{R}$ | ESS (bulk) |")
print("|---|---:|---:|---:|---:|")
for _, r in d.iterrows():
    if r["scale"] == "sd":
        ormcell = "—"
        meancell = f"{r['post_mean']:.3f} (SD)"
    else:
        ormcell = f"{r['OR']:.2f} ({r['OR_lo']:.2f}–{r['OR_hi']:.2f})"
        meancell = f"{r['post_mean']:.3f}"
    print(f"| {r['parameter']} | {meancell} | {ormcell} | {r['rhat']:.3f} | {r['ess_bulk']:.0f} |")
