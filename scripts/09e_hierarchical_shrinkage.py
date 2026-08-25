# -*- coding: utf-8 -*-
"""
09e_hierarchical_shrinkage.py

Referee-revision analyses (methodological robustness):

  (A) Territorial rates with SHRINKAGE.
      Bayesian hierarchical Poisson-gamma (empirical-Bayes) model for
      department-specific motorcyclist fatality rates, 2015-2024. Small-count
      departments (e.g. Vaupes n=6, Guainia n=13) are shrunk toward the national
      mean, stabilizing the raw fixed-effects rates. Replaces the reviewer
      concern about the fixed-effects territorial model lacking shrinkage.

  (B) Lethality hierarchical logistic re-fit by MCMC (Hamiltonian Monte Carlo),
      to check that the variational-Bayes (BinomialBayesMixedGLM) posterior used
      in the manuscript is not distorted by the mean-field approximation. Reports
      split-R-hat and bulk effective sample size (ESS) per parameter (Vehtari et
      al. 2021). Non-centered parameterization; 4 chains; dual-averaging step-size
      adaptation. Pure numpy/scipy (no PyMC dependency).

Outputs:
  results/robustness/territorial_eb_shrinkage.csv
  results/robustness/lethality_hmc_diagnostics.csv
  results/robustness/hierarchical_shrinkage.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import optimize, stats
from scipy.special import gammaln

BASE = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis")
PROCESSED = BASE / "data" / "processed"
OUT = BASE / "results" / "robustness"
OUT.mkdir(parents=True, exist_ok=True)

RNG = np.random.default_rng(20260824)

# =====================================================================
# (A) Empirical-Bayes Poisson-gamma shrinkage for department rates
# =====================================================================
def territorial_eb():
    # Deaths: sum over all department-years (the fatality panel omits zero-death
    # cells, so absent cells contribute zero). Person-time: the COMPLETE decade
    # denominator from the full population panel (all 33 x 10 department-years),
    # not the sparse fatality panel, which would truncate person-time for the
    # smallest departments and inflate their rates.
    fat = pd.read_csv(PROCESSED / "rq1_panel_dept_year.csv")
    deaths = fat.groupby("cod_dpto", as_index=False)["n_fatal_moto"].sum() \
                .rename(columns={"n_fatal_moto": "deaths"})
    pop = pd.read_csv(PROCESSED / "population_dept_year.csv")
    name_by_code = pop.groupby("cod_dpto")["depto_nombre"].first()
    py = pop.groupby("cod_dpto", as_index=False)["poblacion_total"].sum() \
            .rename(columns={"poblacion_total": "py"})
    g = py.merge(deaths, on="cod_dpto", how="left")
    g["deaths"] = g["deaths"].fillna(0.0)
    g["depto_nombre"] = g["cod_dpto"].map(name_by_code)
    g["E"] = g["py"] / 1e5                       # expected units so rate = deaths/E per 100k
    g["rate_raw"] = g["deaths"] / g["E"]
    y = g["deaths"].to_numpy(float)
    E = g["E"].to_numpy(float)

    # NegBin marginal of y_d ~ Poisson(theta_d * E_d), theta_d ~ Gamma(alpha, beta)
    def negloglik(par):
        la, lb = par
        a, b = np.exp(la), np.exp(lb)
        # P(y) = C(y+a-1, y) * (b/(b+E))^a * (E/(b+E))^y
        ll = (gammaln(y + a) - gammaln(a) - gammaln(y + 1)
              + a * (np.log(b) - np.log(b + E))
              + y * (np.log(E) - np.log(b + E)))
        return -ll.sum()

    res = optimize.minimize(negloglik, x0=[np.log(8.0), np.log(1.0)],
                            method="Nelder-Mead",
                            options=dict(xatol=1e-8, fatol=1e-8, maxiter=20000))
    alpha, beta = np.exp(res.x)
    prior_mean_rate = alpha / beta

    # Posterior theta_d | y_d ~ Gamma(alpha + y_d, rate = beta + E_d)
    a_post = alpha + y
    b_post = beta + E
    g["rate_eb"] = a_post / b_post
    g["eb_lo"] = stats.gamma.ppf(0.025, a=a_post, scale=1.0 / b_post)
    g["eb_hi"] = stats.gamma.ppf(0.975, a=a_post, scale=1.0 / b_post)
    g["shrinkage_pct"] = 100.0 * (1.0 - g["rate_eb"] / g["rate_raw"])

    g = g.sort_values("rate_eb", ascending=False).reset_index(drop=True)
    n = len(g)
    tertile_cut = int(np.ceil(n / 3))
    g["top_tertile_eb"] = False
    g.loc[:tertile_cut - 1, "top_tertile_eb"] = True

    # rank concordance raw vs shrunken
    rho = stats.spearmanr(g["rate_raw"], g["rate_eb"]).correlation

    g.to_csv(OUT / "territorial_eb_shrinkage.csv", index=False, encoding="utf-8")

    summary = dict(
        n_departments=int(n),
        alpha=float(alpha), beta=float(beta),
        prior_mean_rate_per100k=float(prior_mean_rate),
        between_dept_sd_rate=float(np.sqrt(alpha) / beta),  # sd of Gamma prior
        spearman_raw_vs_eb=float(rho),
        top2_raw=g.sort_values("rate_raw", ascending=False)["depto_nombre"].head(2).tolist(),
        top2_eb=g["depto_nombre"].head(2).tolist(),
    )
    # highlight the smallest-count departments' shrinkage
    small = g.sort_values("deaths").head(4)[
        ["depto_nombre", "deaths", "rate_raw", "rate_eb", "eb_lo", "eb_hi"]]
    summary["smallest_count_departments"] = small.to_dict("records")
    top = g.head(3)[["depto_nombre", "deaths", "rate_raw", "rate_eb", "eb_lo", "eb_hi"]]
    summary["highest_eb_departments"] = top.to_dict("records")
    print("\n=== (A) Empirical-Bayes territorial shrinkage ===")
    print(f"alpha={alpha:.3f}  beta={beta:.4f}  prior mean rate={prior_mean_rate:.2f}/100k")
    print(f"Spearman raw vs EB = {rho:.3f}")
    print(g[["depto_nombre", "deaths", "rate_raw", "rate_eb", "eb_lo", "eb_hi",
             "shrinkage_pct", "top_tertile_eb"]].to_string(index=False))
    return summary, g


# =====================================================================
# (B) Hierarchical logistic re-fit by Hamiltonian Monte Carlo
# =====================================================================
def build_design():
    df = pd.read_csv(PROCESSED / "rq2_individual_moto_tce.csv")
    z = df["zona"].astype(str)
    df["zona_bin"] = np.where(z.str.contains("rural", case=False, na=False), "Rural",
                       np.where(z.str.contains("Cabecera", na=False), "Urbano", "Otro"))
    df = df[df["zona_bin"] != "Otro"].copy()
    df = df.dropna(subset=["cod_dpto"]).copy()
    # Standardize year for sampling geometry (decorrelates intercept<->year, improves
    # ESS). The reported per-year effect is back-transformed by dividing by year_sd.
    yr = df["year"].to_numpy(float)
    year_mean, year_sd = yr.mean(), yr.std()
    df["year_z"] = (yr - year_mean) / year_sd
    y = df["outcome_fatal"].to_numpy(float)
    # fixed-effects design: Intercept, Female, Urban, Passenger, year_z (standardized)
    X = np.column_stack([
        np.ones(len(df)),
        (df["sexo"] == "Mujer").to_numpy(float),
        (df["zona_bin"] == "Urbano").to_numpy(float),
        (df["rol"] == "Pasajero").to_numpy(float),
        df["year_z"].to_numpy(float),
    ])
    fe_names = ["Intercept", "Sex: Female", "Zone: Urban", "Role: Passenger", "Year (per year)"]
    codes, uniq = pd.factorize(df["cod_dpto"])
    return y, X, codes, len(uniq), fe_names, float(year_sd)


def logpost_and_grad(params, y, X, grp, J, prior_beta_sd=5.0, sigma_prior_scale=1.0):
    """Non-centered hierarchical logistic.
    params = [beta(p), zeta(J), log_sigma]. u_j = sigma * zeta_j.
    Priors: beta ~ N(0, prior_beta_sd^2); zeta ~ N(0,1); sigma ~ HalfNormal(scale).
    """
    p = X.shape[1]
    beta = params[:p]
    zeta = params[p:p + J]
    log_sigma = params[p + J]
    sigma = np.exp(log_sigma)
    u = sigma * zeta

    eta = X @ beta + u[grp]
    # stable log-lik
    # ll_i = y*eta - log(1+exp(eta))
    m = np.maximum(eta, 0.0)
    log1pexp = m + np.log1p(np.exp(-np.abs(eta)))
    ll = np.sum(y * eta - log1pexp)
    prob = 1.0 / (1.0 + np.exp(-eta))
    resid = y - prob                      # d ll / d eta

    # priors
    lp_beta = -0.5 * np.sum((beta / prior_beta_sd) ** 2)
    lp_zeta = -0.5 * np.sum(zeta ** 2)
    # HalfNormal(sigma; scale) on sigma>0, with Jacobian for log_sigma: + log_sigma
    lp_sigma = -0.5 * (sigma / sigma_prior_scale) ** 2 + log_sigma
    logpost = ll + lp_beta + lp_zeta + lp_sigma

    # gradients
    g_beta = X.T @ resid - beta / prior_beta_sd ** 2
    # group residual sums
    gr = np.bincount(grp, weights=resid, minlength=J)
    g_zeta = sigma * gr - zeta
    # d/d log_sigma: chain through u = sigma*zeta, du/dlogsigma = sigma*zeta = u
    dll_dlogsigma = np.sum(resid * u[grp])
    dprior_dlogsigma = -(sigma ** 2) / sigma_prior_scale ** 2 + 1.0  # d lp_sigma/dlogsigma
    g_logsigma = dll_dlogsigma + dprior_dlogsigma

    grad = np.concatenate([g_beta, g_zeta, [g_logsigma]])
    return logpost, grad


def hmc(logpost_grad, init, n_warmup, n_sample, target_accept=0.8, L=25, seed=0):
    rng = np.random.default_rng(seed)
    q = init.copy()
    dim = len(q)
    lp, grad = logpost_grad(q)

    # dual averaging for step size
    eps = 0.02
    mu = np.log(10 * eps)
    log_eps_bar = 0.0
    H_bar = 0.0
    gamma_da, t0, kappa = 0.05, 10.0, 0.75

    draws = np.empty((n_sample, dim))
    accepts = 0
    for it in range(n_warmup + n_sample):
        p0 = rng.standard_normal(dim)
        cur_lp, cur_grad = lp, grad
        q_new = q.copy()
        g = cur_grad.copy()
        p = p0 + 0.5 * eps * g
        for l in range(L):
            q_new = q_new + eps * p
            lp_new, g = logpost_grad(q_new)
            if l != L - 1:
                p = p + eps * g
        p = p + 0.5 * eps * g
        # Hamiltonians (potential = -logpost)
        cur_H = -cur_lp + 0.5 * np.sum(p0 ** 2)
        new_H = -lp_new + 0.5 * np.sum(p ** 2)
        accept_prob = min(1.0, np.exp(cur_H - new_H)) if np.isfinite(new_H) else 0.0
        if rng.random() < accept_prob:
            q = q_new
            lp, grad = lp_new, g
            if it >= n_warmup:
                accepts += 1
        # dual averaging (warmup only)
        if it < n_warmup:
            H_bar = (1 - 1.0 / (it + 1 + t0)) * H_bar + (target_accept - accept_prob) / (it + 1 + t0)
            log_eps = mu - np.sqrt(it + 1) / gamma_da * H_bar
            w = (it + 1) ** (-kappa)
            log_eps_bar = w * log_eps + (1 - w) * log_eps_bar
            eps = np.exp(log_eps)
        elif it == n_warmup:
            eps = np.exp(log_eps_bar)
        if it >= n_warmup:
            draws[it - n_warmup] = q
    return draws, accepts / n_sample, eps


def split_rhat(chains):
    # chains: (n_chains, n_draws)
    m, n = chains.shape
    if n % 2 == 1:
        chains = chains[:, :-1]; n -= 1
    half = n // 2
    s = np.concatenate([chains[:, :half], chains[:, half:half * 2]], axis=0)
    M, N = s.shape
    means = s.mean(axis=1)
    B = N * means.var(ddof=1)
    W = s.var(axis=1, ddof=1).mean()
    var_hat = (N - 1) / N * W + B / N
    return float(np.sqrt(var_hat / W)) if W > 0 else np.nan


def ess_bulk(chains):
    m, n = chains.shape
    means = chains.mean(axis=1)
    W = chains.var(axis=1, ddof=1).mean()
    B = n * means.var(ddof=1)
    var_hat = (n - 1) / n * W + B / n
    # combined autocorrelation via mean of chain autocovariances
    acov = np.zeros(n)
    for c in range(m):
        x = chains[c] - means[c]
        f = np.fft.rfft(x, n=2 * n)
        ac = np.fft.irfft(f * np.conj(f))[:n].real
        acov += ac / n
    acov /= m
    rho = 1.0 - (W - acov) / var_hat
    # Geyer initial monotone sequence
    t = 1
    ess_sum = 0.0
    while t + 1 < n:
        pair = rho[t] + rho[t + 1]
        if pair < 0:
            break
        ess_sum += pair
        t += 2
    tau = 1.0 + 2.0 * ess_sum
    return float(m * n / tau) if tau > 0 else np.nan


def lethality_hmc(n_warmup=1500, n_sample=2500, n_chains=4):
    y, X, grp, J, fe_names, year_sd = build_design()
    p = X.shape[1]
    dim = p + J + 1
    year_col = fe_names.index("Year (per year)")

    def lpg(q):
        return logpost_and_grad(q, y, X, grp, J)

    # ---- gradient check (finite differences) ----
    q0 = np.zeros(dim); q0[p + J] = np.log(0.5)
    _, ga = lpg(q0)
    gnum = np.zeros(dim); h = 1e-5
    for k in [0, 1, 2, 3, 4, p, p + J]:
        qh = q0.copy(); qh[k] += h
        qm = q0.copy(); qm[k] -= h
        gnum[k] = (lpg(qh)[0] - lpg(qm)[0]) / (2 * h)
    gchk = float(np.max(np.abs((ga - gnum)[[0, 1, 2, 3, 4, p, p + J]])))
    print(f"\n=== (B) HMC hierarchical logistic ===\nmax|analytic-numeric grad| = {gchk:.2e}  (n={len(y)}, J={J})")

    all_draws = []
    accs = []
    for c in range(n_chains):
        init = np.zeros(dim)
        init[:p] = RNG.normal(0, 0.5, p)          # dispersed starts
        init[p:p + J] = RNG.normal(0, 0.3, J)
        init[p + J] = np.log(RNG.uniform(0.3, 0.9))
        draws, acc, eps = hmc(lpg, init, n_warmup, n_sample, L=30,
                              target_accept=0.9, seed=1000 + c)
        accs.append(acc)
        all_draws.append(draws)
        print(f"  chain {c+1}: accept={acc:.2f}  step={eps:.4f}")
    D = np.stack(all_draws)  # (chains, draws, dim)

    # transform: betas (p), sigma = exp(log_sigma)
    rows = []
    # fixed effects
    for j, name in enumerate(fe_names):
        ch = D[:, :, j]
        # R-hat/ESS are invariant to linear rescaling; back-transform the
        # standardized year draws to a per-year effect for reporting.
        ch_rep = ch / year_sd if j == year_col else ch
        mean = ch_rep.mean(); sd = ch_rep.std(ddof=1)
        lo, hi = np.percentile(ch_rep, [2.5, 97.5])
        rows.append(dict(parameter=name, scale="log-odds",
                         post_mean=mean, post_sd=sd, ci_lo=lo, ci_hi=hi,
                         OR=np.exp(mean), OR_lo=np.exp(lo), OR_hi=np.exp(hi),
                         rhat=split_rhat(ch), ess_bulk=ess_bulk(ch)))
    # sigma (random-intercept SD)
    sig = np.exp(D[:, :, p + J])
    lo, hi = np.percentile(sig, [2.5, 97.5])
    rows.append(dict(parameter="Department random-intercept SD", scale="sd",
                     post_mean=sig.mean(), post_sd=sig.std(ddof=1), ci_lo=lo, ci_hi=hi,
                     OR=np.nan, OR_lo=np.nan, OR_hi=np.nan,
                     rhat=split_rhat(np.exp(D[:, :, p + J])),
                     ess_bulk=ess_bulk(np.exp(D[:, :, p + J]))))
    tab = pd.DataFrame(rows)
    tab.to_csv(OUT / "lethality_hmc_diagnostics.csv", index=False, encoding="utf-8")
    print(tab.to_string(index=False))
    summary = dict(
        n_obs=int(len(y)), n_departments=int(J),
        n_chains=n_chains, n_warmup=n_warmup, n_sample=n_sample,
        mean_accept=float(np.mean(accs)),
        grad_check_max_abs_err=gchk,
        max_rhat=float(tab["rhat"].max()),
        min_ess_bulk=float(tab["ess_bulk"].min()),
        table=tab.to_dict("records"),
    )
    return summary, tab


if __name__ == "__main__":
    a_sum, a_tab = territorial_eb()
    b_sum, b_tab = lethality_hmc()
    payload = {"territorial_eb": a_sum, "lethality_hmc": b_sum}
    (OUT / "hierarchical_shrinkage.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=float), encoding="utf-8")
    print("\nSaved:", OUT / "hierarchical_shrinkage.json")
