"""FASE 12 - Analisis exploratorio sobre datasets procesados (RQ1, RQ2)."""
import pandas as pd
from pathlib import Path

PROCESSED = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis/data/processed")
OUT = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis/results/exploratory")
OUT.mkdir(parents=True, exist_ok=True)


def explore_rq1():
    df = pd.read_csv(PROCESSED / "rq1_panel_dept_year.csv")
    nat = df.groupby("year")[["n_fatal_moto", "n_fatal_moto_tce"]].sum()
    nat["pct_tce"] = 100 * nat["n_fatal_moto_tce"] / nat["n_fatal_moto"]
    print("=== RQ1: serie nacional (agregada desde panel depto-año) ===")
    print(nat)

    valid = df.dropna(subset=["poblacion_total"])
    avg_rate = valid.groupby("depto_nombre_medlegal")["tasa_fatal_moto_x100k"].mean().sort_values(ascending=False)
    print("\n=== Top 5 deptos por tasa promedio fatal-moto x100k (2015-2024) ===")
    print(avg_rate.head(5))
    print("\n=== Bottom 5 ===")
    print(avg_rate.tail(5))
    nat.to_csv(OUT / "rq1_serie_nacional.csv")
    avg_rate.to_csv(OUT / "rq1_tasas_departamento.csv")


def explore_rq2():
    df = pd.read_csv(PROCESSED / "rq2_individual_moto_tce.csv")
    print("\n=== RQ2: N por covariable, con % 'Sin informacion' ===")
    for col in ["sexo", "grupo_edad", "zona", "rol", "clase_accidente", "objeto_colision"]:
        vc = df[col].value_counts(dropna=False)
        pct_missing = 100 * vc.filter(like="Sin inf", axis=0).sum() / len(df) if any(vc.index.astype(str).str.contains("Sin inf", na=False)) else 0.0
        print(f"\n--- {col} (Sin informacion: {pct_missing:.1f}%) ---")
        print(vc.head(8))

    print("\n=== Letalidad (%% fatal) por sexo ===")
    print(100 * df.groupby("sexo")["outcome_fatal"].mean())
    print("\n=== Letalidad (%% fatal) por zona ===")
    print(100 * df.groupby("zona")["outcome_fatal"].mean())
    print("\n=== Letalidad (%% fatal) por rol ===")
    print(100 * df.groupby("rol")["outcome_fatal"].mean())


if __name__ == "__main__":
    explore_rq1()
    explore_rq2()
