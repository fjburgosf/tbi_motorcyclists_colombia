# -*- coding: utf-8 -*-
"""
10_spatial_analysis.py  — Spatial-territorial analysis (RQ4)

Adds a spatial-territorial dimension to the departmental motorcyclist TBI
mortality analysis, using only verifiable open data aggregated to the
department level (DIVIPOLA), 2015-2024:

  (A) Global spatial autocorrelation of the departmental TBI mortality rate
      (Moran's I) under a queen-contiguity spatial weights matrix, with a
      permutation-based pseudo p-value.
  (B) Local indicators of spatial association (LISA / local Moran's I) to
      identify department-level high-high and low-low clusters, with
      conditional-permutation pseudo p-values.
  (C) Exploratory ecological correlates of the departmental rate, limited to
      variables reproducibly derivable from open data: motorcycle exposure
      (registered motorcycles per 1,000 inhabitants, RUNT) and population
      density (inhabitants per km^2, DANE population / IGAC department area).

Moran's I and LISA are implemented directly (no libpysal dependency), following
Anselin (1995). No causal claim is made; all associations are ecological.

Geometry: IGAC-derived department polygons (DIVIPOLA `DPTO`), public GeoJSON.
Excluded, per a documented data audit, because reproducible departmental
aggregation from verifiable open data was not achievable in this pipeline:
terrain ruggedness/elevation (IGAC DEM), precipitation (IDEAM), road-network
density (INVIAS). Population density is retained as the standard reproducible
proxy for urbanization/population concentration.

Outputs: results/spatial/*.csv, results/spatial/spatial_summary.json,
figures/figS3_lisa_clusters.png
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
from scipy import stats

BASE = Path(__file__).resolve().parents[1]
PROCESSED = BASE / "data" / "processed"
TABLES = BASE / "tables"
GEO = BASE / "data" / "raw" / "geo" / "colombia_departments.geojson"
OUT = BASE / "results" / "spatial"
OUT.mkdir(parents=True, exist_ok=True)
FIGDIR = BASE / "figures"

RNG = np.random.default_rng(20260904)
N_PERM = 999

# Department polygons (DIVIPOLA codes + IGAC areas). Pinned to an immutable
# commit so the geometry is byte-identical on every run.
GEO_URL = ("https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/"
           "be6a6e239cd5b5b803c6e7c2ec405b793a9064dd/colombia.geo.json")


def ensure_geo():
    """Download the department geometry if it is not present locally."""
    if GEO.exists():
        return GEO
    import urllib.request
    GEO.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading department geometry -> {GEO}")
    urllib.request.urlretrieve(GEO_URL, GEO)
    return GEO


# ----------------------------------------------------------------- assemble data
def build_dataset():
    # deaths + population (person-time) by department, from the RQ1 panel
    panel = pd.read_csv(PROCESSED / "rq1_panel_dept_year.csv").dropna(subset=["poblacion_total"])
    agg = (panel.groupby("cod_dpto", as_index=False)
                 .agg(deaths_all=("n_fatal_moto", "sum"),
                      deaths_tbi=("n_fatal_moto_tce", "sum"),
                      pop_mean=("poblacion_total", "mean"),
                      py=("poblacion_total", "sum")))
    # rates per 100,000 person-years
    agg["rate_all"] = agg["deaths_all"] / agg["py"] * 1e5
    agg["rate_tbi"] = agg["deaths_tbi"] / agg["py"] * 1e5

    # canonical department name (longest label per code)
    name_by_code = (panel.assign(_l=panel["depto_nombre"].astype(str).str.len())
                         .sort_values("_l").groupby("cod_dpto")["depto_nombre"].last())
    agg["depto_nombre"] = agg["cod_dpto"].map(name_by_code)

    # motorcycle exposure (RUNT): motorcycles per 1,000 inhabitants
    runt = pd.read_csv(TABLES / "tableS_runt_sensibilidad.csv")[["cod_dpto", "motos", "motos_x1000hab"]]
    agg = agg.merge(runt, on="cod_dpto", how="left")

    # geometry + official area (IGAC hectares -> km^2)
    g = gpd.read_file(ensure_geo())
    g["cod_dpto"] = g["DPTO"].astype(int)
    g["area_km2"] = g["HECTARES"].astype(float) / 100.0
    g = g[["cod_dpto", "area_km2", "geometry"]]

    gdf = g.merge(agg, on="cod_dpto", how="inner")
    gdf["pop_density"] = gdf["pop_mean"] / gdf["area_km2"]      # inhabitants per km^2
    gdf["moto_density"] = gdf["motos"] / gdf["area_km2"]        # motorcycles per km^2

    # empirical-Bayes shrunken TBI-rate proxy (robustness to small-count noise)
    eb = pd.read_csv(BASE / "results" / "robustness" / "territorial_eb_shrinkage.csv")[["cod_dpto", "rate_eb"]]
    gdf = gdf.merge(eb, on="cod_dpto", how="left")
    return gpd.GeoDataFrame(gdf, geometry="geometry", crs=g.crs)


# ----------------------------------------------------------------- spatial weights
def queen_weights(gdf, buffer_deg=0.01):
    """Row-standardized queen-contiguity weights. Returns W (list of dicts),
    the connected index set, and neighbor counts. Polygons are buffered by a
    small epsilon so that slivers/gaps in the source geometry do not drop true
    adjacencies."""
    geoms = list(gdf.geometry)
    n = len(geoms)
    buf = [gm.buffer(buffer_deg) for gm in geoms]
    neigh = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if buf[i].intersects(buf[j]):
                neigh[i].append(j)
                neigh[j].append(i)
    return neigh


def row_standardized(neigh):
    n = len(neigh)
    W = np.zeros((n, n))
    for i, nb in enumerate(neigh):
        if nb:
            W[i, nb] = 1.0 / len(nb)
    return W


def knn_weights(gdf, k=5):
    """Row-standardized k-nearest-neighbour weights (includes islands).
    Centroids computed in a metric CRS (MAGNA-SIRGAS / Colombia, EPSG:3116)."""
    cen = gdf.to_crs(3116).geometry.centroid
    xy = np.column_stack([cen.x.values, cen.y.values])
    n = len(gdf)
    W = np.zeros((n, n))
    for i in range(n):
        d = np.hypot(xy[:, 0] - xy[i, 0], xy[:, 1] - xy[i, 1])
        d[i] = np.inf
        nn = np.argsort(d)[:k]
        W[i, nn] = 1.0 / k
    return W


# ----------------------------------------------------------------- Moran's I
def morans_I(x, W):
    z = x - x.mean()
    lag = W @ z
    num = np.sum(z * lag)
    den = np.sum(z ** 2)
    return num / den  # row-standardized -> S0 = n cancels


def morans_I_perm(x, W, mask, n_perm=N_PERM, seed=1):
    """Permutation inference on the connected subset (mask = boolean of units
    with >=1 neighbor). Values are permuted among connected units only."""
    rng = np.random.default_rng(seed)
    idx = np.where(mask)[0]
    Wc = W[np.ix_(idx, idx)]
    # re-row-standardize the submatrix
    rs = Wc.sum(axis=1, keepdims=True)
    rs[rs == 0] = 1
    Wc = Wc / rs
    xc = x[idx]
    obs = morans_I(xc, Wc)
    perms = np.empty(n_perm)
    for k in range(n_perm):
        perms[k] = morans_I(rng.permutation(xc), Wc)
    p = (np.sum(perms >= obs) + 1) / (n_perm + 1) if obs >= perms.mean() \
        else (np.sum(perms <= obs) + 1) / (n_perm + 1)
    z_score = (obs - perms.mean()) / perms.std(ddof=1)
    return obs, p, z_score, len(idx)


# ----------------------------------------------------------------- LISA
def local_moran(x, W, mask, n_perm=N_PERM, seed=2):
    rng = np.random.default_rng(seed)
    z = x - x.mean()
    m2 = np.sum(z ** 2) / len(z)
    lag = W @ z
    Ii = z * lag / m2
    n = len(x)
    p = np.full(n, np.nan)
    for i in range(n):
        if not mask[i]:
            continue
        nb = np.where(W[i] > 0)[0]
        if len(nb) == 0:
            continue
        wi = W[i, nb]
        others = np.delete(np.arange(n), i)
        sims = np.empty(n_perm)
        for k in range(n_perm):
            samp = rng.choice(z[others], size=len(nb), replace=False)
            sims[k] = z[i] * np.sum(wi * samp) / m2
        ge = np.sum(sims >= Ii[i]); le = np.sum(sims <= Ii[i])
        p[i] = (min(ge, le) + 1) / (n_perm + 1)
    # quadrant: 1 HH, 2 LH, 3 LL, 4 HL
    lab = np.array(["ns"] * n, dtype=object)
    for i in range(n):
        if not mask[i] or np.isnan(p[i]) or p[i] > 0.05:
            continue
        if z[i] > 0 and lag[i] > 0: lab[i] = "High-High"
        elif z[i] < 0 and lag[i] < 0: lab[i] = "Low-Low"
        elif z[i] > 0 and lag[i] < 0: lab[i] = "High-Low"
        else: lab[i] = "Low-High"
    return Ii, p, lab, lag


# ----------------------------------------------------------------- ecological correlates
def ecological_correlates(gdf):
    d = gdf.dropna(subset=["motos_x1000hab", "pop_density"]).copy()
    d["log_rate_tbi"] = np.log(d["rate_tbi"].clip(lower=0.01))
    corr = {"n": int(len(d))}
    for v in ["motos_x1000hab", "pop_density", "moto_density"]:
        rho, p = stats.spearmanr(d["rate_tbi"], d[v])
        corr[v] = {"spearman_rho": float(rho), "p": float(p)}
    # parsimonious exploratory OLS on log rate (standardized predictors)
    import statsmodels.api as sm
    X = d[["motos_x1000hab", "pop_density"]].copy()
    X = (X - X.mean()) / X.std()
    X = sm.add_constant(X)
    ols = sm.OLS(d["log_rate_tbi"].values, X.values).fit()
    ols_res = {
        "predictors": ["const", "moto_per_1000_std", "pop_density_std"],
        "beta": [float(b) for b in ols.params],
        "p": [float(pp) for pp in ols.pvalues],
        "r2": float(ols.rsquared), "n": int(d.shape[0]),
    }
    return corr, ols_res


# ----------------------------------------------------------------- main
def main():
    gdf = build_dataset().reset_index(drop=True)
    print("departments:", len(gdf))

    neigh = queen_weights(gdf)
    counts = np.array([len(nb) for nb in neigh])
    W = row_standardized(neigh)
    mask = counts > 0
    isolated = gdf.loc[~mask, "depto_nombre"].tolist()
    print("neighbor counts: min %d max %d mean %.1f | isolated: %s"
          % (counts.min(), counts.max(), counts.mean(), isolated))

    # k-nearest-neighbour weights (robustness; includes the island)
    Wk = knn_weights(gdf, k=5)
    maskk = np.ones(len(gdf), bool)

    # --- Global Moran's I: TBI raw rate (primary), plus robustness variants
    res = {}
    specs = [
        ("tbi_queen", "rate_tbi", W, mask),
        ("all_queen", "rate_all", W, mask),
        ("tbi_eb_queen", "rate_eb", W, mask),
        ("tbi_knn5", "rate_tbi", Wk, maskk),
    ]
    for label, col, Wm, mk in specs:
        x = gdf[col].to_numpy(float)
        I, p, zt, ncon = morans_I_perm(x, Wm, mk, seed=10)
        res[label] = {"morans_I": float(I), "p_perm": float(p),
                      "z": float(zt), "n_connected": ncon}
        print(f"Global Moran's I ({label}): I={I:.3f}, p={p:.3f}, z={zt:.2f}, n={ncon}")

    # --- LISA on TBI rate
    x = gdf["rate_tbi"].to_numpy(float)
    Ii, pi, lab, lag = local_moran(x, W, mask, seed=20)
    gdf["local_I"] = Ii
    gdf["local_p"] = pi
    gdf["lisa_cluster"] = lab
    gdf["spatial_lag_rate"] = lag + gdf["rate_tbi"].mean()  # back to rate scale for reference

    out = gdf[["cod_dpto", "depto_nombre", "rate_tbi", "rate_all",
               "motos_x1000hab", "pop_density", "moto_density",
               "local_I", "local_p", "lisa_cluster"]].copy()
    out = out.sort_values("rate_tbi", ascending=False)
    out.to_csv(OUT / "spatial_departments.csv", index=False, encoding="utf-8")
    print("\nLISA clusters (p<0.05):")
    print(out[out["lisa_cluster"] != "ns"][["depto_nombre", "rate_tbi", "lisa_cluster", "local_p"]].to_string(index=False))

    # --- ecological correlates
    corr, ols_res = ecological_correlates(gdf)
    print("\nSpearman correlations with TBI rate (n=%d):" % corr["n"])
    for v, r in corr.items():
        if v == "n":
            continue
        print(f"  {v}: rho={r['spearman_rho']:.3f}, p={r['p']:.3f}")
    print("Exploratory OLS (log TBI rate ~ std predictors): R2=%.3f" % ols_res["r2"])
    for nm, b, pp in zip(ols_res["predictors"], ols_res["beta"], ols_res["p"]):
        print(f"  {nm}: beta={b:.3f}, p={pp:.3f}")

    summary = {
        "n_departments": int(len(gdf)),
        "weights": "queen contiguity, row-standardized (epsilon-buffer 0.01 deg)",
        "neighbor_count_min_max_mean": [int(counts.min()), int(counts.max()), float(counts.mean())],
        "isolated_excluded_from_weights": isolated,
        "n_permutations": N_PERM,
        "global_moran": res,
        "lisa_clusters": {row["depto_nombre"]: row["lisa_cluster"]
                          for _, row in out.iterrows() if row["lisa_cluster"] != "ns"},
        "ecological_spearman": corr,
        "ecological_ols_lograte": ols_res,
        "geometry_source": "IGAC-derived department polygons (DIVIPOLA DPTO), public GeoJSON",
        "excluded_after_audit": {
            "terrain_ruggedness_elevation": "IGAC DEM; no reproducible departmental aggregation available in pipeline",
            "precipitation": "IDEAM; station/raster data not reproducibly aggregable to department here",
            "road_network_density": "INVIAS/Min. Transporte; departmental network length not obtainable as a verifiable open table",
        },
    }
    (OUT / "spatial_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\nSaved:", OUT / "spatial_summary.json")

    make_figure(gdf, W, mask, res["tbi_queen"]["morans_I"], res["tbi_queen"]["p_perm"])
    return gdf, out, summary


def make_figure(gdf, W, mask, I, p):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6.2))

    # (a) choropleth of TBI rate + LISA-significant departments outlined
    gdf.plot(column="rate_tbi", cmap="YlOrRd", legend=True, ax=ax1,
             edgecolor="0.6", linewidth=0.3,
             legend_kwds={"label": "TBI mortality rate per 100,000", "shrink": 0.6})
    sig = gdf[gdf["lisa_cluster"] != "ns"]
    if len(sig):
        sig.boundary.plot(ax=ax1, color="black", linewidth=1.6)
    ax1.set_title("Departmental TBI mortality rate\n(black outline: LISA p<0.05)", fontsize=10)
    ax1.axis("off")

    # (b) Moran scatterplot on TBI rate (connected subset)
    x = gdf["rate_tbi"].to_numpy(float)
    z = (x - x.mean()) / x.std()
    lag = W @ ((x - x.mean()))
    lag = lag / x.std()
    ax2.axhline(0, color="0.7", lw=0.8); ax2.axvline(0, color="0.7", lw=0.8)
    ax2.scatter(z[mask], lag[mask], s=28, color="#1f4e79", zorder=3)
    b = np.polyfit(z[mask], lag[mask], 1)[0]
    xs = np.linspace(z[mask].min(), z[mask].max(), 50)
    ax2.plot(xs, b * xs, color="#c0392b", lw=1.6)
    ax2.set_xlabel("Standardized TBI mortality rate (z)")
    ax2.set_ylabel("Spatial lag (mean of neighbours, z)")
    ax2.set_title("Moran scatterplot\nGlobal Moran's I = %.3f (p = %.2f, ns)" % (I, p), fontsize=10)
    fig.tight_layout()
    fig.savefig(FIGDIR / "figS3_spatial.png", dpi=600, bbox_inches="tight")
    subm = BASE / "figures_submission"
    subm.mkdir(exist_ok=True)
    fig.savefig(subm / "FigureS3.png", dpi=600, bbox_inches="tight")
    fig.savefig(subm / "FigureS3.tif", dpi=600, bbox_inches="tight",
                pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)
    print("Saved figure (600 dpi):", FIGDIR / "figS3_spatial.png")


if __name__ == "__main__":
    main()
