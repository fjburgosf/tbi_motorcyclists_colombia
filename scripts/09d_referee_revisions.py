"""
09d_referee_revisions.py
Cálculos añadidos en respuesta al referee report (Major Revision, estilo Safety Q2).
Todos los números que entran al manuscrito revisado se generan aquí para trazabilidad.

- M1: modelo de tendencia TBI-específico (outcome = fatales moto con 'Trauma craneano'),
       nacional, NegBin offset poblacional. Serie completa + robustez 2015-2021.
- M1-territorial: concordancia (Spearman) entre tasas departamentales total-moto vs TBI-moto.
- M2: IRR DANE restringido a 2015-2021 (ventana pre-integración Registraduría), para
       demostrar que la divergencia de serie completa MedLegal-vs-DANE es el salto de 2022.
- M4: reconciliación del total 40,318 vs suma departamental de la Tabla S1.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import spearmanr

BASE = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis")
PROC = BASE / "data/processed"
EXPL = BASE / "results/exploratory"
OUT = BASE / "results/robustness"
OUT.mkdir(parents=True, exist_ok=True)


def _nb_irr(sub, outcome):
    X = sm.add_constant(sub["year_c"])
    nb = sm.NegativeBinomial(sub[outcome], X, offset=sub["log_pop"],
                             loglike_method="nb2").fit(disp=0)
    irr = float(np.exp(nb.params["year_c"]))
    ci = np.exp(nb.conf_int().loc["year_c"])
    return irr, float(ci[0]), float(ci[1]), float(nb.params["alpha"])


def main():
    res = {}

    # ---- M1: tendencia TBI-específica (Medicina Legal) ----
    df = pd.read_csv(PROC / "rq1_panel_dept_year.csv").dropna(subset=["poblacion_total"])
    nat = df.groupby("year").agg(
        n_tot=("n_fatal_moto", "sum"),
        n_tce=("n_fatal_moto_tce", "sum"),
        pop=("poblacion_total", "sum"),
    ).reset_index()
    nat["log_pop"] = np.log(nat["pop"])
    nat["year_c"] = nat["year"] - nat["year"].min()

    irr_tce = _nb_irr(nat, "n_tce")
    irr_tce_pre = _nb_irr(nat[nat.year < 2022], "n_tce")
    irr_tot = _nb_irr(nat, "n_tot")
    res["M1_tendencia_tbi_especifica"] = {
        "full_2015_2024": {"IRR": irr_tce[0], "IC95": [irr_tce[1], irr_tce[2]], "alpha": irr_tce[3]},
        "robustez_2015_2021": {"IRR": irr_tce_pre[0], "IC95": [irr_tce_pre[1], irr_tce_pre[2]]},
        "comparacion_total": {"IRR_full": irr_tot[0], "IC95": [irr_tot[1], irr_tot[2]]},
    }

    # ---- M1-territorial: concordancia total vs TBI por departamento ----
    g = df.groupby("cod_dpto").agg(
        tot=("n_fatal_moto", "sum"), tce=("n_fatal_moto_tce", "sum"),
        pop=("poblacion_total", "mean")).reset_index()
    g["rate_tot"] = g["tot"] / g["pop"] * 1e5
    g["rate_tce"] = g["tce"] / g["pop"] * 1e5
    rho, p = spearmanr(g["rate_tot"], g["rate_tce"])
    res["M1_territorial_concordancia"] = {"spearman_rho": float(rho), "p": float(p), "n": int(len(g))}

    # ---- M2: DANE pre-2022 vs serie completa ----
    dane = pd.read_csv(EXPL / "panel_dane_eevv_2015_2024_tce_moto.csv")
    d = dane.merge(nat[["year", "pop", "log_pop", "year_c"]], on="year")
    irr_dane_full = _nb_irr(d, "n_moto_Y_S06")
    irr_dane_pre = _nb_irr(d[d.year < 2022], "n_moto_Y_S06")
    res["M2_dane_segmentacion"] = {
        "dane_full_2015_2024": {"IRR": irr_dane_full[0], "IC95": [irr_dane_full[1], irr_dane_full[2]]},
        "dane_2015_2021": {"IRR": irr_dane_pre[0], "IC95": [irr_dane_pre[1], irr_dane_pre[2]]},
        "medlegal_2015_2021_ref": {"IRR": 1.0078, "nota": "de 08_primary_model.py"},
    }

    # ---- M4: reconciliación Tabla S1 ----
    ts1 = pd.read_csv(BASE / "tables/tableS_runt_sensibilidad.csv")
    suma = int(ts1["muertes"].sum())
    res["M4_reconciliacion_tablaS1"] = {
        "total_nacional_moto_fatales": 40318,
        "suma_departamental_tablaS1": suma,
        "registros_sin_departamento": 40318 - suma,
    }

    with open(OUT / "referee_revisions.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
