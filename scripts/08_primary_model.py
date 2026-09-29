"""FASE 13 - Analisis principal (confirmatorio, H1-H4 de HYPOTHESES.md)."""
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
from pathlib import Path

pd.set_option("display.width", 120)

PROCESSED = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis/data/processed")
OUT = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis/results/primary")
OUT.mkdir(parents=True, exist_ok=True)


def h1_tendencia_nacional():
    """H1: tendencia temporal, Poisson/NegBin con offset poblacional, nivel nacional."""
    df = pd.read_csv(PROCESSED / "rq1_panel_dept_year.csv").dropna(subset=["poblacion_total"])
    nat = df.groupby("year").agg(n=("n_fatal_moto", "sum"), pop=("poblacion_total", "sum")).reset_index()
    nat["log_pop"] = np.log(nat["pop"])
    nat["year_c"] = nat["year"] - nat["year"].min()

    # NOTA: el chequeo de sobredispersion Poisson a nivel nacional (10 puntos anuales, 8 gl)
    # es poco fiable con tan pocos grados de libertad -- se usa NegBin (alpha estimado por MLE,
    # no fijado a 1) directamente como modelo principal, mas apropiado para conteos de eventos raros.
    X = sm.add_constant(nat["year_c"])
    nb = sm.NegativeBinomial(nat["n"], X, offset=nat["log_pop"], loglike_method="nb2").fit(disp=0)
    irr = np.exp(nb.params["year_c"])
    ci = np.exp(nb.conf_int().loc["year_c"])
    print(f"H1 NegBin (alpha MLE={nb.params['alpha']:.4f}) IRR/anio: {irr:.4f} "
          f"(IC95% {ci[0]:.4f}-{ci[1]:.4f})")

    # Robustez: excluyendo 2022-2024. Este corte es sobre Medicina Legal (numerador), no DANE,
    # pero sirve como chequeo general de sensibilidad temporal de la tendencia (ver DECISIONS.md D001
    # sobre por que Medicina Legal, no DANE, es la serie usada aqui).
    pre2022 = nat[nat["year"] < 2022]
    Xp = sm.add_constant(pre2022["year_c"])
    nb_pre = sm.NegativeBinomial(pre2022["n"], Xp, offset=pre2022["log_pop"], loglike_method="nb2").fit(disp=0)
    irr_pre = np.exp(nb_pre.params["year_c"])
    print(f"H1 robustez NegBin (solo 2015-2021) IRR/anio: {irr_pre:.4f}")

    with open(OUT / "h1_tendencia_nacional.txt", "w", encoding="utf-8") as f:
        f.write(str(nb.summary()))
        f.write(f"\n\nRobustez 2015-2021 IRR/anio: {irr_pre:.4f}\n")
    return nb


def h2_multinivel_departamental():
    """H2: heterogeneidad departamental, Poisson con efecto fijo de depto (proxy de multinivel;
    ver nota de limitacion abajo)."""
    df = pd.read_csv(PROCESSED / "rq1_panel_dept_year.csv").dropna(subset=["poblacion_total"])
    df["log_pop"] = np.log(df["poblacion_total"])
    df["year_c"] = df["year"] - df["year"].min()

    full = smf.glm("n_fatal_moto ~ year_c + C(cod_dpto)", data=df, offset=df["log_pop"],
                    family=sm.families.Poisson()).fit()
    reduced = smf.glm("n_fatal_moto ~ year_c", data=df, offset=df["log_pop"],
                       family=sm.families.Poisson()).fit()
    lr_stat = 2 * (full.llf - reduced.llf)
    df_diff = full.df_model - reduced.df_model
    from scipy import stats
    p_val = stats.chi2.sf(lr_stat, df_diff)
    print(f"H2 heterogeneidad departamental: LR={lr_stat:.1f}, df={df_diff:.0f}, p={p_val:.2e}")
    print("NOTA: efecto fijo usado como proxy computacional; interpretar junto con las tasas "
          "descriptivas de FASE 12 (results/exploratory/rq1_tasas_departamento.csv), no como "
          "sustituto pleno de un modelo multinivel bayesiano con shrinkage.")
    with open(OUT / "h2_heterogeneidad_departamental.txt", "w", encoding="utf-8") as f:
        f.write(f"LR={lr_stat}, df={df_diff}, p={p_val}\n\n")
        f.write(str(full.summary()))


def h3_letalidad():
    """H3: factores asociados a desenlace fatal, logistica multivariable + multinivel (depto)."""
    df = pd.read_csv(PROCESSED / "rq2_individual_moto_tce.csv")
    df["zona_bin"] = np.where(df["zona"].astype(str).str.contains("rural", case=False, na=False),
                               "Rural", np.where(df["zona"].astype(str).str.contains("Cabecera", na=False),
                                                  "Urbano", "Otro/Sin info"))
    df = df[df["zona_bin"] != "Otro/Sin info"]
    df["sexo"] = df["sexo"].replace({"Hombre": "Hombre", "Mujer": "Mujer"})
    df["year_c"] = df["year"] - df["year"].min()

    # AVISO CRITICO: N no-fatal cae de ~200/anio (2015-2018) a ~60-90/anio (2020-2024) mientras
    # N fatal sube -- el denominador no-fatal se encoge en el tiempo (probable artefacto de
    # captura de Medicina Legal, analogo al quiebre DANE de D001), NO evidencia de aumento real
    # de letalidad. year_c se incluye solo como covariable de ajuste, su coeficiente NO debe
    # interpretarse como tendencia epidemiologica real -- ver ANALYSIS_LOG.md.
    logit = smf.glm("outcome_fatal ~ sexo + zona_bin + rol + year_c",
                     data=df, family=sm.families.Binomial()).fit()
    print("\nH3 Logistica multivariable (OR) -- year_c es artefacto de captura, NO interpretar como tendencia:")
    print(np.exp(logit.params))
    with open(OUT / "h3_letalidad_logistica.txt", "w", encoding="utf-8") as f:
        f.write(str(logit.summary()))

    # Multinivel: intercepto aleatorio por departamento
    df_m = df.dropna(subset=["cod_dpto"]).copy()
    df_m["cod_dpto"] = df_m["cod_dpto"].astype(str)
    vc = {"cod_dpto": "0 + C(cod_dpto)"}
    try:
        mixed = BinomialBayesMixedGLM.from_formula(
            "outcome_fatal ~ sexo + zona_bin + rol + year_c", vc,
            data=df_m
        ).fit_vb()
        print("\nH3 multinivel (depto como efecto aleatorio) - resumen:")
        print(mixed.summary())
        with open(OUT / "h3_letalidad_multinivel.txt", "w", encoding="utf-8") as f:
            f.write(str(mixed.summary()))
    except Exception as e:
        print(f"AVISO: multinivel fallo ({e}); se reporta solo el modelo de efectos fijos.")


if __name__ == "__main__":
    h1_tendencia_nacional()
    h2_multinivel_departamental()
    h3_letalidad()
