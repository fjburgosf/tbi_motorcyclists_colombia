"""Sensitivity and additional analyses.

  A. Departmental rates as total deaths over accumulated person-years with the
     complete population denominator (department-years with zero deaths included),
     and rank concordance of all-motorcyclist and head-injury rates.
  B. National trend models (full period and 2015-2021) and a formal test of the
     post-2021 change (segmented negative binomial models, likelihood-ratio
     tests) with pandemic-year sensitivity analyses; DANE motorcyclist-TBI trend.
  C. Shared-denominator check for the ecological correlation: partial Spearman
     correlation controlling for population size and a count model with
     log fleet and log population as separate covariates.
  D. Collinearity of the ecological OLS predictors (VIF).
  E. Benjamini-Hochberg correction of the local Moran tests.
  F. Simulated power of global Moran's I with 32 units.
  G. Annual counts by registry, side by side, and the S06 share of DANE
     motorcyclist deaths.
  H. Dispersion diagnostics for the Poisson versus negative binomial family.
  I. Completeness of the forensic fatal records, sensitivity to unspecified
     topographic diagnoses, zone categories and annual non-fatal counts.

Outputs: results/sensitivity/*.csv and results/sensitivity/sensitivity_summary.json
"""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.outliers_influence import variance_inflation_factor

BASE = Path(__file__).resolve().parents[1]
PROC = BASE / "data" / "processed"
INTERIM = BASE / "data" / "interim"
EXPL = BASE / "results" / "exploratory"
SPATIAL = BASE / "results" / "spatial"
ROBUST = BASE / "results" / "robustness"
OUT = BASE / "results" / "sensitivity"
OUT.mkdir(parents=True, exist_ok=True)

RNG = np.random.default_rng(20260925)


def _spatial_module():
    spec = importlib.util.spec_from_file_location("spatial", BASE / "scripts" / "10_spatial_analysis.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _population():
    pop = pd.read_csv(PROC / "population_dept_year.csv")
    return pop[(pop.year >= 2015) & (pop.year <= 2024)]


# ------------------------------------------------------------------ A
def departmental_rates():
    panel = pd.read_csv(PROC / "rq1_panel_dept_year.csv")
    pop = _population()
    deaths = panel.groupby("cod_dpto")[["n_fatal_moto", "n_fatal_moto_tce"]].sum()
    names = panel.sort_values("year").groupby("cod_dpto")["depto_nombre_medlegal"].last()
    py = pop.groupby("cod_dpto")["poblacion_total"].sum()
    d = pd.DataFrame({"department": names, "deaths_all": deaths.n_fatal_moto,
                      "deaths_tbi": deaths.n_fatal_moto_tce, "person_years": py}).dropna()
    d["rate_all_x100k"] = d.deaths_all / d.person_years * 1e5
    d["rate_tbi_x100k"] = d.deaths_tbi / d.person_years * 1e5
    d = d.sort_values("rate_all_x100k")
    d.to_csv(OUT / "A_departmental_rates_persontime.csv")

    lo = d.head(4)
    return {"lowest_four": {r.department: round(r.rate_all_x100k, 8) for r in lo.itertuples()},
            "highest_two": {r.department: round(r.rate_all_x100k, 8) for r in d.tail(2).itertuples()},
            "method": "total deaths / total person-years 2015-2024 (complete denominator)",
            "spearman_all_vs_head_injury_rates": {
                "rho": round(float(stats.spearmanr(d.rate_all_x100k, d.rate_tbi_x100k).statistic), 8),
                "p": float(stats.spearmanr(d.rate_all_x100k, d.rate_tbi_x100k).pvalue), "n": int(len(d))},
            "deaths_with_department": int(d.deaths_all.sum())}


# ------------------------------------------------------------------ B
def _national():
    df = pd.read_csv(PROC / "rq1_panel_dept_year.csv").dropna(subset=["poblacion_total"])
    nat = df.groupby("year").agg(n_all=("n_fatal_moto", "sum"), n_tbi=("n_fatal_moto_tce", "sum"),
                                 pop=("poblacion_total", "sum")).reset_index()
    nat["log_pop"] = np.log(nat["pop"])
    nat["year_c"] = nat["year"] - nat["year"].min()
    nat["post2022"] = (nat.year >= 2022).astype(float)
    nat["post_slope"] = nat.post2022 * (nat.year - 2021)
    nat["pandemic"] = nat.year.isin([2020, 2021]).astype(float)
    return nat


def _nb(sub, y, cols):
    X = sm.add_constant(sub[cols])
    m = sm.NegativeBinomial(sub[y], X, offset=sub["log_pop"], loglike_method="nb2")
    try:
        r = m.fit(disp=0, maxiter=500)
        if not r.mle_retvals.get("converged", True):
            raise RuntimeError
    except Exception:
        r = m.fit(disp=0, method="nm", maxiter=20000)
    return r


def _irr(r, term):
    ci = np.exp(r.conf_int().loc[term])
    return {"IRR": round(float(np.exp(r.params[term])), 8), "CI95": [round(float(ci[0]), 8), round(float(ci[1]), 8)],
            "p": float(r.pvalues[term])}


def _lr(r0, r1, df):
    lr = max(0.0, 2 * (r1.llf - r0.llf))
    return {"LR": round(lr, 6), "df": df, "p": float(stats.chi2.sf(lr, df))}


def segmented_trend():
    nat = _national()
    out = {}
    for y in ("n_tbi", "n_all"):
        m0 = _nb(nat, y, ["year_c"])
        m0r = _nb(nat[nat.year <= 2021], y, ["year_c"])
        m1 = _nb(nat, y, ["year_c", "post2022"])
        m2 = _nb(nat, y, ["year_c", "post2022", "post_slope"])
        ex = nat[~nat.year.isin([2020, 2021])]
        e0 = _nb(ex, y, ["year_c"])
        e1 = _nb(ex, y, ["year_c", "post2022"])
        pdm = _nb(nat, y, ["year_c", "pandemic"])
        pd1 = _nb(nat, y, ["year_c", "post2022", "pandemic"])
        out[y] = {
            "reproduced_linear_full": _irr(m0, "year_c"),
            "reproduced_linear_2015_2021": _irr(m0r, "year_c"),
            "level_shift_model": {"year_c": _irr(m1, "year_c"), "post2022": _irr(m1, "post2022"),
                                  "LR_vs_linear": _lr(m0, m1, 1)},
            "level_and_slope_model": {"post2022": _irr(m2, "post2022"), "post_slope": _irr(m2, "post_slope"),
                                      "LR_vs_linear": _lr(m0, m2, 2)},
            "excluding_2020_2021": {"linear": _irr(e0, "year_c"), "post2022": _irr(e1, "post2022"),
                                    "LR_vs_linear": _lr(e0, e1, 1), "n_years": int(len(ex))},
            "pandemic_indicator": {"year_c": _irr(pdm, "year_c"), "pandemic": _irr(pdm, "pandemic")},
            "level_shift_with_pandemic_indicator": {"year_c": _irr(pd1, "year_c"), "post2022": _irr(pd1, "post2022"),
                                                    "pandemic": _irr(pd1, "pandemic"),
                                                    "LR_vs_pandemic_indicator": _lr(pdm, pd1, 1)},
            "alpha_linear": float(m0.params["alpha"]),
        }
    return out


def dane_trend():
    """DANE motorcyclist deaths with an S06 code: trend over 2015-2024 and 2015-2021."""
    nat = _national()
    dane = pd.read_csv(EXPL / "panel_dane_eevv_2015_2024_tce_moto.csv")
    d = dane.merge(nat[["year", "log_pop", "year_c"]], on="year")
    return {"full_2015_2024": _irr(_nb(d, "n_moto_Y_S06", ["year_c"]), "year_c"),
            "2015_2021": _irr(_nb(d[d.year <= 2021], "n_moto_Y_S06", ["year_c"]), "year_c")}


# ------------------------------------------------------------------ C, D
def ecological_checks():
    sp = pd.read_csv(SPATIAL / "spatial_departments.csv")
    runt = pd.read_csv(ROBUST / "runt_denominator_sensitivity.csv")[["cod_dpto", "motos"]]
    panel = pd.read_csv(PROC / "rq1_panel_dept_year.csv")
    tbi = panel.groupby("cod_dpto")["n_fatal_moto_tce"].sum().rename("deaths_tbi")
    popm = _population().groupby("cod_dpto")["poblacion_total"].mean().rename("pop_mean")
    d = sp.merge(runt, on="cod_dpto", how="left").merge(tbi, on="cod_dpto").merge(popm, on="cod_dpto")
    d = d.dropna(subset=["motos_x1000hab", "pop_density"]).copy()
    n = len(d)

    ry, rx, rz = (stats.rankdata(d[c]) for c in ("rate_tbi", "motos_x1000hab", "pop_mean"))
    rxy, rxz, ryz = np.corrcoef(rx, ry)[0, 1], np.corrcoef(rx, rz)[0, 1], np.corrcoef(ry, rz)[0, 1]
    pr = (rxy - rxz * ryz) / np.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))
    t = pr * np.sqrt((n - 3) / (1 - pr ** 2))
    p_pr = 2 * stats.t.sf(abs(t), n - 3)

    X = sm.add_constant(pd.DataFrame({"log_motos": np.log(d.motos), "log_pop": np.log(d.pop_mean)}))
    cm = sm.NegativeBinomial(d.deaths_tbi, X, loglike_method="nb2").fit(disp=0, maxiter=500)
    ci = cm.conf_int().loc["log_motos"]

    Z = pd.DataFrame({"moto_per_1000_std": (d.motos_x1000hab - d.motos_x1000hab.mean()) / d.motos_x1000hab.std(ddof=0),
                      "pop_density_std": (d.pop_density - d.pop_density.mean()) / d.pop_density.std(ddof=0)})
    Zc = sm.add_constant(Z)
    vif = {c: round(float(variance_inflation_factor(Zc.values, i)), 8) for i, c in enumerate(Zc.columns) if c != "const"}
    r_pred = stats.spearmanr(d.motos_x1000hab, d.pop_density)

    return {
        "n": int(n),
        "spearman_rate_vs_motos": {"rho": round(float(rxy), 8), "p": float(stats.spearmanr(d.rate_tbi, d.motos_x1000hab).pvalue)},
        "spearman_rate_vs_population": {"rho": round(float(ryz), 8), "p": float(stats.spearmanr(d.rate_tbi, d.pop_mean).pvalue)},
        "spearman_motos_vs_population": {"rho": round(float(rxz), 8), "p": float(stats.spearmanr(d.motos_x1000hab, d.pop_mean).pvalue)},
        "partial_spearman_rate_motos_given_population": {"rho": round(float(pr), 8), "p": float(p_pr), "df": n - 3},
        "count_model_logdeaths_on_logmotos_logpop": {
            "elasticity_log_motos": round(float(cm.params["log_motos"]), 8),
            "CI95": [round(float(ci[0]), 8), round(float(ci[1]), 8)], "p": float(cm.pvalues["log_motos"]),
            "coef_log_pop": round(float(cm.params["log_pop"]), 8), "p_log_pop": float(cm.pvalues["log_pop"])},
        "VIF": vif,
        "spearman_between_predictors": {"rho": round(float(r_pred.statistic), 8), "p": float(r_pred.pvalue)},
    }


# ------------------------------------------------------------------ E, F
def spatial_checks():
    sp = pd.read_csv(SPATIAL / "spatial_departments.csv")
    lp = sp.dropna(subset=["local_p"])
    rej, q, _, _ = multipletests(lp.local_p, alpha=0.05, method="fdr_bh")
    lp = lp.assign(q_bh=q, significant_bh=rej)
    lp[["depto_nombre", "local_p", "q_bh", "significant_bh", "lisa_cluster"]].to_csv(OUT / "E_lisa_fdr.csv", index=False)
    nominal = lp[lp.local_p < 0.05][["depto_nombre", "local_p"]]
    nominal = nominal.assign(q_bh=lp.loc[nominal.index, "q_bh"])

    mod = _spatial_module()
    gdf = mod.build_dataset().reset_index(drop=True)
    neigh = mod.queen_weights(gdf)
    counts = np.array([len(nb) for nb in neigh])
    idx = np.where(counts > 0)[0]
    W = mod.row_standardized(neigh)[np.ix_(idx, idx)]
    W = W / W.sum(axis=1, keepdims=True)
    n = W.shape[0]
    n_sim, n_perm = 1000, 199

    def moran_batch(X):
        Z = X - X.mean(axis=1, keepdims=True)
        return np.einsum("ij,ij->i", Z, Z @ W.T) / np.einsum("ij,ij->i", Z, Z)

    power = {}
    for rho in (0.0, 0.2, 0.4, 0.6, 0.8):
        A = np.linalg.inv(np.eye(n) - rho * W)
        rej_count = 0
        for _ in range(n_sim):
            y = A @ RNG.standard_normal(n)
            obs = moran_batch(y[None, :])[0]
            perm = moran_batch(np.array([RNG.permutation(y) for _ in range(n_perm)]))
            p = (np.sum(perm >= obs) + 1) / (n_perm + 1)
            rej_count += p <= 0.05
        power[str(rho)] = round(rej_count / n_sim, 3)
    return {"lisa_tests": int(len(lp)), "lisa_nominal_p_lt_0.05": nominal.round(3).to_dict("records"),
            "lisa_significant_after_BH": int(rej.sum()),
            "moran_power_queen_n": int(n), "moran_power_sims": n_sim, "moran_power_perms": n_perm,
            "moran_power_by_SAR_rho": power}


# ------------------------------------------------------------------ G, H
def registry_counts_and_dispersion():
    link = pd.read_csv(EXPL / "linkage_audit_dane_medlegal_series.csv")
    dane = pd.read_csv(EXPL / "panel_dane_eevv_2015_2024_tce_moto.csv")
    nat = _national()
    # complete annual counts (no department-year dropped)
    counts = (pd.read_csv(PROC / "rq1_panel_dept_year.csv").groupby("year")["n_fatal_moto_tce"].sum()
              .rename("n_tbi").reset_index())
    t = link.merge(dane[["year", "n_moto_Y_S06", "pct_moto_con_S06"]], on="year").merge(counts, on="year")
    t = t.rename(columns={"medicina_legal_moto_fatal": "ML_all", "n_tbi": "ML_head_injury",
                          "dane_eevv_moto_V20_V29": "DANE_V20_V29", "n_moto_Y_S06": "DANE_V20_V29_with_S06",
                          "pct_moto_con_S06": "DANE_pct_S06", "diferencia_pct_dane_vs_medlegal": "pct_diff_all"})
    # shares from counts, stored unrounded
    t["DANE_pct_S06"] = (100 * t.DANE_V20_V29_with_S06 / t.DANE_V20_V29).round(8)
    t["ML_pct_head_injury"] = (100 * t.ML_head_injury / t.ML_all).round(8)
    t["pct_diff_head_injury_vs_S06"] = (100 * (t.DANE_V20_V29_with_S06 - t.ML_head_injury) / t.ML_head_injury).round(6)
    cols = ["year", "ML_all", "DANE_V20_V29", "pct_diff_all", "ML_head_injury", "ML_pct_head_injury",
            "DANE_V20_V29_with_S06", "DANE_pct_S06", "pct_diff_head_injury_vs_S06"]
    t[cols].to_csv(OUT / "G_annual_counts_by_registry.csv", index=False)

    disp = {}
    for y in ("n_all", "n_tbi"):
        g = sm.GLM(nat[y], sm.add_constant(nat[["year_c"]]), family=sm.families.Poisson(), offset=nat.log_pop).fit()
        disp[y + "_national"] = {"mean": round(float(nat[y].mean()), 6), "variance": round(float(nat[y].var()), 6),
                                 "poisson_pearson_chi2_df": round(float(g.pearson_chi2 / g.df_resid), 6)}
    panel = pd.read_csv(PROC / "rq1_panel_dept_year.csv")[["cod_dpto", "year", "n_fatal_moto"]]
    full = _population()[["cod_dpto", "year", "poblacion_total"]].merge(panel, on=["cod_dpto", "year"], how="left")
    full["n_fatal_moto"] = full.n_fatal_moto.fillna(0)
    full["log_pop"] = np.log(full.poblacion_total)
    full["year_c"] = full.year - 2015
    Xf = pd.get_dummies(full[["year_c", "cod_dpto"]].astype({"cod_dpto": str}), drop_first=True, dtype=float)
    Xf = sm.add_constant(Xf)
    Xr = sm.add_constant(full[["year_c"]])
    gp_full = sm.GLM(full.n_fatal_moto, Xf, family=sm.families.Poisson(), offset=full.log_pop).fit()
    nb_full = sm.NegativeBinomial(full.n_fatal_moto, Xf, offset=full.log_pop, loglike_method="nb2").fit(disp=0, maxiter=2000)
    nb_red = sm.NegativeBinomial(full.n_fatal_moto, Xr, offset=full.log_pop, loglike_method="nb2").fit(disp=0, maxiter=2000)
    gp_red = sm.GLM(full.n_fatal_moto, Xr, family=sm.families.Poisson(), offset=full.log_pop).fit()
    k = Xf.shape[1] - Xr.shape[1]
    disp["department_year"] = {
        "n_cells": int(len(full)), "zero_cells": int((full.n_fatal_moto == 0).sum()),
        "mean": round(float(full.n_fatal_moto.mean()), 6), "variance": round(float(full.n_fatal_moto.var()), 6),
        "poisson_dept_year_pearson_chi2_df": round(float(gp_full.pearson_chi2 / gp_full.df_resid), 6),
        "nb_dept_heterogeneity_LR": _lr(nb_red, nb_full, k),
        "poisson_dept_heterogeneity_LR": _lr(gp_red, gp_full, k),
        "nb_alpha_full": round(float(nb_full.params["alpha"]), 6)}
    return {"annual_counts_file": "G_annual_counts_by_registry.csv",
            "DANE_pct_S06_range": [float(t.DANE_pct_S06.min()), float(t.DANE_pct_S06.max())],
            "ML_pct_head_injury_range": [float(t.ML_pct_head_injury.min()), float(t.ML_pct_head_injury.max())],
            "dispersion": disp}


# ------------------------------------------------------------------ I
def record_completeness():
    f = pd.read_csv(INTERIM / "medlegal_moto_fatal.csv", low_memory=False)
    n = len(f)
    miss = {"sin información", "sin informacion", "por determinar", "no sabe / no informa"}

    def share(col):
        s = f[col].astype(str).str.strip().str.lower()
        return round(100 * float(s.isin(miss).mean() + f[col].isna().mean()), 6)

    comp = {"n_fatal_records": int(n),
            "pct_missing": {c: share(c) for c in ["sexo_de_la_victima", "grupo_de_edad_quinquenal", "zona_del_hecho",
                                                 "condicion_de_la_victima_at", "codigo_dane_departamento",
                                                 "diagnostico_topografico_de_la_lesion_fatal",
                                                 "rango_de_hora_del_hecho_x_3_horas"]}}
    topo = f.diagnostico_topografico_de_la_lesion_fatal.str.strip()
    comp["topographic_distribution_pct"] = (100 * topo.value_counts(normalize=True)).round(6).head(6).to_dict()
    by_year = f.assign(u=topo.str.lower().isin(miss)).groupby("a_o_del_hecho").u.mean().mul(100).round(6)
    comp["topographic_unspecified_by_year_pct"] = {int(k): float(v) for k, v in by_year.items()}

    # Sensitivity: unspecified topographic diagnoses fell to zero in 2022-2024. Reallocate the
    # unspecified records of each year to head injury in proportion to the specified share and
    # refit the national head-injury trend, so that a coding shift cannot drive the increase.
    g = f.assign(tbi=topo.eq("Trauma craneano"), u=topo.str.lower().isin(miss)).groupby("a_o_del_hecho") \
         .agg(n=("tbi", "size"), tbi=("tbi", "sum"), u=("u", "sum"))
    g["share_specified"] = g.tbi / (g.n - g.u)
    g["tbi_realloc"] = g.tbi + g.u * g.share_specified
    nat = _national().set_index("year")
    # scale reallocation to the model's case base (which drops the few records without a department)
    nat["n_tbi_realloc"] = (nat.n_tbi * g.tbi_realloc / g.tbi).round()
    nat = nat.reset_index()
    comp["head_injury_share_among_specified_by_year_pct"] = {int(k): round(100 * float(v), 6)
                                                           for k, v in g.share_specified.items()}
    comp["trend_with_reallocated_unspecified"] = {
        "linear": _irr(_nb(nat, "n_tbi_realloc", ["year_c"]), "year_c"),
        "post2022_level_shift": _irr(_nb(nat, "n_tbi_realloc", ["year_c", "post2022"]), "post2022"),
        "LR_level_shift": _lr(_nb(nat, "n_tbi_realloc", ["year_c"]), _nb(nat, "n_tbi_realloc", ["year_c", "post2022"]), 1)}

    r = pd.read_csv(PROC / "rq2_individual_moto_tce.csv")
    zone = {}
    for lab, sub in (("pooled_fatal_nonfatal", r), ("fatal_only", r[r.outcome_fatal == 1])):
        vc = sub.zona.value_counts()
        zone[lab] = {k: {"n": int(v), "pct": round(100 * v / len(sub), 1)} for k, v in vc.items()}
    comp["zone_categories"] = zone
    rq2 = pd.read_csv(PROC / "rq2_individual_moto_tce.csv")
    comp["nonfatal_head_injury_by_year"] = {int(k): int(v) for k, v in
                                           rq2[rq2.outcome_fatal == 0].groupby("year").size().items()}
    return comp


def main():
    summary = {"A_departmental_rates": departmental_rates()}
    print("A done", summary["A_departmental_rates"]["lowest_four"])
    summary["B_segmented_trend"] = segmented_trend()
    summary["B2_dane_trend"] = dane_trend()
    print("B done")
    summary["CD_ecological"] = ecological_checks()
    print("C/D done")
    summary["EF_spatial"] = spatial_checks()
    print("E/F done")
    summary["GH_registry_dispersion"] = registry_counts_and_dispersion()
    print("G/H done")
    summary["I_completeness"] = record_completeness()
    with open(OUT / "sensitivity_summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1, ensure_ascii=False, default=float)
    print(json.dumps(summary, indent=1, ensure_ascii=False, default=float))


if __name__ == "__main__":
    main()
