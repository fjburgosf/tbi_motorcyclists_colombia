# -*- coding: utf-8 -*-
"""
Regenerate the manuscript figures at 600 ppi with submission-ready names.

Output (folder `figures_submission/`):
  Figure1.png/.tif   -> national trend + TBI share (RQ1)
  Figure2.png/.tif   -> departmental rates (RQ1)
  Figure3.png/.tif   -> forest plot case-fatality (RQ2, secondary)
  FigureS1.png/.tif  -> exposure-denominator sensitivity (supplementary)
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

PROCESSED = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis/data/processed")
EXPLORATORY = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis/results/exploratory")
TABLES = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis/tables")
OUT = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis/figures_submission")
OUT.mkdir(parents=True, exist_ok=True)

DPI = 600
plt.rcParams["font.size"] = 10


def save(fig, stem):
    fig.savefig(OUT / ("%s.png" % stem), dpi=DPI, bbox_inches="tight", pad_inches=0.08)
    fig.savefig(OUT / ("%s.tif" % stem), dpi=DPI, bbox_inches="tight", pad_inches=0.08,
                pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)
    print("saved", stem)


def fig1():
    df = pd.read_csv(PROCESSED / "rq1_panel_dept_year.csv").dropna(subset=["poblacion_total"])
    nat = df.groupby("year").agg(n=("n_fatal_moto", "sum"), n_tce=("n_fatal_moto_tce", "sum")).reset_index()
    nat["pct_tce"] = 100 * nat["n_tce"] / nat["n"]

    fig, ax1 = plt.subplots(figsize=(7, 4.5))
    ax1.bar(nat["year"], nat["n"], color="#4C72B0", alpha=0.85, label="Motorcyclist deaths (total)")
    ax1.bar(nat["year"], nat["n_tce"], color="#C44E52", alpha=0.9, label="Motorcyclist deaths with TBI")
    ax1.set_ylabel("Number of deaths")
    ax1.set_xlabel("Year")
    ax1.axvline(2021.5, color="gray", linestyle="--", linewidth=1)
    ax1.text(2021.6, ax1.get_ylim()[1] * 0.92, "DANE 2022\nbreak", fontsize=8, color="gray")
    ax1.legend(loc="upper left", fontsize=8)

    ax2 = ax1.twinx()
    ax2.plot(nat["year"], nat["pct_tce"], color="black", marker="o", markersize=4, linewidth=1.5)
    ax2.set_ylabel("% TBI among motorcyclist deaths")
    ax2.set_ylim(0, 60)

    ax1.set_title("Motorcyclist mortality and share with TBI, Colombia 2015-2024\n(Source: Medicina Legal)")
    fig.tight_layout()
    save(fig, "Figure1")


def fig2():
    rates = pd.read_csv(EXPLORATORY / "rq1_tasas_departamento.csv")
    rates = rates.sort_values("tasa_fatal_moto_x100k", ascending=True)
    fig, ax = plt.subplots(figsize=(6, 9))
    colors = ["#C44E52" if v >= rates["tasa_fatal_moto_x100k"].median() else "#4C72B0"
              for v in rates["tasa_fatal_moto_x100k"]]
    ax.barh(rates["depto_nombre_medlegal"], rates["tasa_fatal_moto_x100k"], color=colors)
    ax.set_xlabel("Mean annual rate 2015-2024 (motorcyclist deaths per 100,000 pop.)")
    ax.set_title("Territorial inequality: motorcyclist mortality by department")
    fig.tight_layout()
    save(fig, "Figure2")


def fig3():
    df = pd.read_csv(PROCESSED / "rq2_individual_moto_tce.csv")
    df["zona_bin"] = np.where(df["zona"].astype(str).str.contains("rural", case=False, na=False), "Rural",
                              np.where(df["zona"].astype(str).str.contains("Cabecera", na=False), "Urbano", "Otro"))
    df = df[df["zona_bin"] != "Otro"]
    df["year_c"] = df["year"] - df["year"].min()
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    m = smf.glm("outcome_fatal ~ sexo + zona_bin + rol + year_c", data=df, family=sm.families.Binomial()).fit()
    ci_df = np.exp(m.conf_int())
    or_df = np.exp(m.params)

    keys = ["sexo[T.Mujer]", "zona_bin[T.Urbano]", "rol[T.Pasajero]"]
    labels = ["Sex: Female\n(vs. Male)", "Zone: Urban\n(vs. Rural)", "Role: Passenger\n(vs. Driver)"]
    or_point = [or_df[k] for k in keys]
    ci_low = [ci_df.loc[k, 0] for k in keys]
    ci_high = [ci_df.loc[k, 1] for k in keys]

    fig, ax = plt.subplots(figsize=(6, 3.5))
    y = np.arange(len(labels))
    ax.errorbar(or_point, y, xerr=[np.array(or_point) - np.array(ci_low), np.array(ci_high) - np.array(or_point)],
                fmt="o", color="black", capsize=4)
    ax.axvline(1, color="gray", linestyle="--")
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Odds ratio (fatal outcome among registered motorcyclist TBI cases)")
    ax.set_title("Factors associated with fatal outcome (RQ2, secondary)")
    fig.tight_layout()
    save(fig, "Figure3")


def figS1():
    df = pd.read_csv(TABLES / "tableS_runt_sensibilidad.csv").dropna(subset=["tasa_x10k_moto"])
    from scipy.stats import spearmanr
    rho, _ = spearmanr(df["tasa_x100k_hab"], df["tasa_x10k_moto"])
    fig, ax = plt.subplots(figsize=(7, 5.5))
    robust = df["robusto_alto"] == True
    ax.scatter(df.loc[~robust, "tasa_x100k_hab"], df.loc[~robust, "tasa_x10k_moto"],
               color="#4C72B0", alpha=0.7, label="Other departments")
    ax.scatter(df.loc[robust, "tasa_x100k_hab"], df.loc[robust, "tasa_x10k_moto"],
               color="#C44E52", s=60, label="Robust (top tertile in both)")
    for _, r in df.iterrows():
        ax.annotate(r["depto"], (r["tasa_x100k_hab"], r["tasa_x10k_moto"]),
                    fontsize=6, alpha=0.75, xytext=(3, 2), textcoords="offset points")
    ax.set_xlabel("Rate per 100,000 population")
    ax.set_ylabel("Rate per 10,000 registered motorcycles")
    ax.set_title("Exposure-denominator sensitivity by department\n(Spearman rho = %.2f, n = %d)" % (rho, int(robust.count())))
    ax.legend(fontsize=8)
    fig.tight_layout()
    save(fig, "FigureS1")


def figS2():
    import unicodedata
    ROB = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis/results/robustness")
    g = pd.read_csv(ROB / "territorial_eb_shrinkage.csv")
    deacc = lambda s: "".join(c for c in unicodedata.normalize("NFKD", str(s))
                              if not unicodedata.combining(c))
    g["name"] = g["depto_nombre"].map(deacc).str.replace(
        "Archipielago de San Andres, Providencia y Santa Catalina", "San Andres", regex=False)
    g = g.sort_values("rate_eb", ascending=True).reset_index(drop=True)
    ypos = np.arange(len(g))
    fig, ax = plt.subplots(figsize=(7.2, 8.6))
    ax.errorbar(g["rate_eb"], ypos,
                xerr=[g["rate_eb"] - g["eb_lo"], g["eb_hi"] - g["rate_eb"]],
                fmt="o", color="#1f4e79", ecolor="#9db8d2", elinewidth=1.4,
                capsize=2, markersize=4.5, label="Empirical-Bayes rate (95% CrI)", zorder=3)
    ax.scatter(g["rate_raw"], ypos, marker="x", color="#c0392b", s=34,
               label="Raw (unshrunk) rate", zorder=4)
    ax.set_yticks(ypos)
    ax.set_yticklabels(g["name"], fontsize=7.5)
    ax.set_xlabel("Motorcyclist fatality rate per 100,000 population (2015-2024)")
    ax.set_title("Departmental rates: raw vs empirical-Bayes shrinkage")
    ax.legend(loc="lower right", fontsize=8, frameon=True)
    ax.grid(axis="x", ls=":", alpha=0.5)
    ax.margins(y=0.01)
    fig.tight_layout()
    save(fig, "FigureS2")


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    figS1()
    figS2()
    print("Done. Output folder:", OUT)
