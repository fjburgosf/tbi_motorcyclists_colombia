"""FASE 15 - Tablas generadas por codigo. Ningun numero se escribe a mano."""
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from pathlib import Path

PROCESSED = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis/data/processed")
TABLES = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis/tables")
TABLES.mkdir(parents=True, exist_ok=True)


def table1_descriptivo():
    df = pd.read_csv(PROCESSED / "rq2_individual_moto_tce.csv")
    rows = []
    rows.append(("N total casos moto con TCE", len(df), ""))
    rows.append(("  Fatales", int((df.outcome_fatal == 1).sum()),
                  f"{100*(df.outcome_fatal==1).mean():.1f}%"))
    rows.append(("  No fatales", int((df.outcome_fatal == 0).sum()),
                  f"{100*(df.outcome_fatal==0).mean():.1f}%"))
    for col, label in [("sexo", "Sexo"), ("rol", "Rol"), ("zona", "Zona")]:
        vc = df[col].value_counts()
        rows.append((label, "", ""))
        for k, v in vc.items():
            rows.append((f"  {k}", int(v), f"{100*v/len(df):.1f}%"))
    t1 = pd.DataFrame(rows, columns=["Variable", "N", "%"])
    t1.to_csv(TABLES / "table1_descriptivo.csv", index=False, encoding="utf-8")
    print("Tabla 1 guardada:", len(t1), "filas")


def table2_h1_tendencia():
    df = pd.read_csv(PROCESSED / "rq1_panel_dept_year.csv").dropna(subset=["poblacion_total"])
    nat = df.groupby("year").agg(n=("n_fatal_moto", "sum"), pop=("poblacion_total", "sum")).reset_index()
    nat["log_pop"] = np.log(nat["pop"])
    nat["year_c"] = nat["year"] - nat["year"].min()

    def fit_nb(data):
        X = sm.add_constant(data["year_c"])
        m = sm.NegativeBinomial(data["n"], X, offset=data["log_pop"], loglike_method="nb2").fit(disp=0)
        irr = np.exp(m.params["year_c"]); ci = np.exp(m.conf_int().loc["year_c"])
        return irr, ci[0], ci[1], m.pvalues["year_c"]

    full = fit_nb(nat)
    pre = fit_nb(nat[nat["year"] < 2022])

    rows = [
        ("Serie completa 2015-2024", *full),
        ("Robustez: solo 2015-2021", *pre),
    ]
    t2 = pd.DataFrame(rows, columns=["Especificación", "IRR/año", "IC95% inf", "IC95% sup", "p-valor"])
    t2.to_csv(TABLES / "table2_h1_tendencia.csv", index=False, encoding="utf-8")
    print(t2.to_string(index=False))


def table3_h3_letalidad():
    df = pd.read_csv(PROCESSED / "rq2_individual_moto_tce.csv")
    df["zona_bin"] = np.where(df["zona"].astype(str).str.contains("rural", case=False, na=False), "Rural",
                       np.where(df["zona"].astype(str).str.contains("Cabecera", na=False), "Urbano", "Otro"))
    df = df[df["zona_bin"] != "Otro"]
    df["year_c"] = df["year"] - df["year"].min()
    m = smf.glm("outcome_fatal ~ sexo + zona_bin + rol + year_c", data=df, family=sm.families.Binomial()).fit()
    or_ = np.exp(m.params)
    ci = np.exp(m.conf_int())
    t3 = pd.DataFrame({
        "Variable": or_.index, "OR": or_.values,
        "IC95% inf": ci[0].values, "IC95% sup": ci[1].values, "p-valor": m.pvalues.values,
    })
    t3.loc[t3["Variable"] == "year_c", "Variable"] = "year_c [NO interpretar: artefacto de captura, ver ANALYSIS_LOG.md]"
    t3.to_csv(TABLES / "table3_h3_letalidad.csv", index=False, encoding="utf-8")
    print(t3.to_string(index=False))


if __name__ == "__main__":
    table1_descriptivo()
    table2_h1_tendencia()
    table3_h3_letalidad()
