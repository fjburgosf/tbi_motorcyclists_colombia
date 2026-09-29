"""
FASE 10 - Construccion de variables y datasets analiticos.

Outputs:
  data/processed/population_dept_year.csv         -> denominadores DP x ANO x sexo
  data/processed/rq1_panel_dept_year.csv           -> RQ1: tasas fatal/TCE por depto-anio
  data/processed/rq2_individual_moto_tce.csv       -> RQ2: nivel individuo, outcome fatal
"""
import pandas as pd
from pathlib import Path

INTERIM = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis/data/interim")
POP_DIR = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis/data/raw/dane_poblacion")
PROCESSED = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis/data/processed")
PROCESSED.mkdir(parents=True, exist_ok=True)

TCE_TOPOGRAFICO = "Trauma craneano"


def _tidy_old(path):
    """Archivo 2005-2017: columnas finales 'Total Hombres','Total Mujeres','Total general'."""
    df = pd.read_excel(path, header=11)
    df.columns = [str(c).strip() for c in df.columns]
    area_col = [c for c in df.columns if "REA GEOGR" in c.upper()][0]
    year_col = [c for c in df.columns if c.upper().startswith("A") and "O" in c.upper()][0]
    keep = df[df[area_col].astype(str).str.strip().str.lower() == "total"].copy()
    keep = keep.rename(columns={
        "DP": "cod_dpto", "DPNOM": "depto_nombre", year_col: "year",
        "Total general": "poblacion_total", "Total Hombres": "poblacion_hombres",
        "Total Mujeres": "poblacion_mujeres",
    })
    keep["cod_dpto"] = keep["cod_dpto"].astype(str).str.zfill(2)
    keep["year"] = pd.to_numeric(keep["year"], errors="coerce").astype("Int64")
    return keep[["cod_dpto", "depto_nombre", "year", "poblacion_total", "poblacion_hombres", "poblacion_mujeres"]]


def _tidy_new(path):
    """Archivo 2018-2050: bloque TOTAL en columnas 'Total','Hombres','Mujeres' (indices 4-6)."""
    df = pd.read_excel(path, sheet_name=2, header=7)
    cols = list(df.columns)
    area_col = [c for c in cols if "REA GEOGR" in str(c).upper()][0]
    year_col = [c for c in cols if str(c).upper().startswith("A") and "O" in str(c).upper()][0]
    # renombra por posicion las 3 primeras columnas del bloque TOTAL (E,F,G = idx 4,5,6)
    df = df.rename(columns={cols[4]: "poblacion_total", cols[5]: "poblacion_hombres", cols[6]: "poblacion_mujeres"})
    keep = df[df[area_col].astype(str).str.strip().str.lower() == "total"].copy()
    keep = keep.rename(columns={"DP": "cod_dpto", "DPNOM": "depto_nombre", year_col: "year"})
    keep["cod_dpto"] = keep["cod_dpto"].astype(str).str.zfill(2)
    keep["year"] = pd.to_numeric(keep["year"], errors="coerce").astype("Int64")
    return keep[["cod_dpto", "depto_nombre", "year", "poblacion_total", "poblacion_hombres", "poblacion_mujeres"]]


def build_population_denominators():
    """Combina series 2005-2017 y 2018-2050 (departamental), filtra Total (urb+rural),
    restringe a 2015-2024."""
    old_t = _tidy_old(POP_DIR / "DCD-area-sexo-edad-proypoblacion-dep-2005-2017_VP.xlsx")
    new_t = _tidy_new(POP_DIR / "PPED-AreaSexoEdadDep-2018-2050_VP.xlsx")

    old_t = old_t[old_t["year"].between(2015, 2017)]
    new_t = new_t[new_t["year"].between(2018, 2024)]

    pop = pd.concat([old_t, new_t], ignore_index=True).dropna(subset=["cod_dpto", "year"])
    pop = pop.drop_duplicates(subset=["cod_dpto", "year"])
    pop.to_csv(PROCESSED / "population_dept_year.csv", index=False, encoding="utf-8")
    print(f"Poblacion depto-anio: {len(pop)} filas ({pop['year'].min()}-{pop['year'].max()}, "
          f"{pop['cod_dpto'].nunique()} departamentos)")
    return pop


def build_rq1_panel(pop):
    fatal = pd.read_csv(INTERIM / "medlegal_moto_fatal.csv", dtype=str, low_memory=False)
    fatal["tce"] = fatal["diagnostico_topografico_de_la_lesion_fatal"] == TCE_TOPOGRAFICO
    fatal["a_o_del_hecho"] = pd.to_numeric(fatal["a_o_del_hecho"], errors="coerce")

    agg = (
        fatal.groupby(["codigo_dane_departamento", "a_o_del_hecho"])
        .agg(n_fatal_moto=("id", "count"), n_fatal_moto_tce=("tce", "sum"))
        .reset_index()
        .rename(columns={"codigo_dane_departamento": "cod_dpto", "a_o_del_hecho": "year"})
    )
    agg["cod_dpto"] = agg["cod_dpto"].astype(str).str.zfill(2)
    agg["year"] = agg["year"].astype("Int64")

    # El nombre de depto varia de texto entre anios (ej. "Bogota D.C." -> "Bogota, D.C." desde
    # 2017; mismo cod_dpto="11" en ambos casos, sin perdida/duplicacion de registros -- se usa
    # cod_dpto como llave canonica y se anexa el nombre MAS RECIENTE solo para lectura.
    nombre_reciente = (
        fatal.sort_values("a_o_del_hecho")
        .groupby("codigo_dane_departamento")["departamento_del_hecho_dane"]
        .last()
        .rename_axis("cod_dpto").reset_index()
        .rename(columns={"departamento_del_hecho_dane": "depto_nombre_medlegal"})
    )
    nombre_reciente["cod_dpto"] = nombre_reciente["cod_dpto"].astype(str).str.zfill(2)
    agg = agg.merge(nombre_reciente, on="cod_dpto", how="left")

    panel = agg.merge(pop, on=["cod_dpto", "year"], how="left")
    panel["tasa_fatal_moto_x100k"] = 100000 * panel["n_fatal_moto"] / panel["poblacion_total"]
    panel["tasa_fatal_moto_tce_x100k"] = 100000 * panel["n_fatal_moto_tce"] / panel["poblacion_total"]
    panel["pct_tce_entre_fatales"] = 100 * panel["n_fatal_moto_tce"] / panel["n_fatal_moto"]

    missing_pop = panel["poblacion_total"].isna().sum()
    print(f"RQ1 panel: {len(panel)} filas depto-anio. Sin poblacion emparejada: {missing_pop} "
          f"({'OK' if missing_pop == 0 else 'REVISAR codigos DIVIPOLA no coincidentes'})")

    panel.to_csv(PROCESSED / "rq1_panel_dept_year.csv", index=False, encoding="utf-8")
    return panel


def build_rq2_individual():
    fatal = pd.read_csv(INTERIM / "medlegal_moto_fatal.csv", dtype=str, low_memory=False)
    nofatal = pd.read_csv(INTERIM / "medlegal_moto_nofatal.csv", dtype=str, low_memory=False)

    fatal_tce = fatal[fatal["diagnostico_topografico_de_la_lesion_fatal"] == TCE_TOPOGRAFICO].copy()
    fatal_tce["outcome_fatal"] = 1
    fatal_tce = fatal_tce.rename(columns={
        "sexo_de_la_victima": "sexo", "grupo_de_edad_quinquenal": "grupo_edad",
        "zona_del_hecho": "zona", "condicion_de_la_victima_at": "rol",
        "clase_o_tipo_de_accidente_de_transporte": "clase_accidente",
        "objeto_de_colision": "objeto_colision",
        "codigo_dane_departamento": "cod_dpto", "a_o_del_hecho": "year",
    })

    nofatal_tce = nofatal[nofatal["diagnostico_topografico_de_la_lesion_no_fatal"] == TCE_TOPOGRAFICO].copy()
    nofatal_tce["outcome_fatal"] = 0
    nofatal_tce = nofatal_tce.rename(columns={
        "sexo_de_la_victima": "sexo", "grupo_de_edad_quinquenal": "grupo_edad",
        "zona_del_hecho": "zona", "condicion_de_la_victima_at": "rol",
        "clase_o_tipo_de_accidente": "clase_accidente",
        "objeto_de_colision": "objeto_colision",
        "codigo_dane_municipio": "cod_muni", "a_o_del_hecho": "year",
    })
    if "codigo_dane_departamento" in nofatal.columns:
        nofatal_tce = nofatal_tce.rename(columns={"codigo_dane_departamento": "cod_dpto"})

    cols = ["outcome_fatal", "sexo", "grupo_edad", "zona", "rol", "clase_accidente",
            "objeto_colision", "cod_dpto", "year"]
    cols_f = [c for c in cols if c in fatal_tce.columns]
    cols_nf = [c for c in cols if c in nofatal_tce.columns]

    combined = pd.concat([fatal_tce[cols_f], nofatal_tce[cols_nf]], ignore_index=True)
    combined["year"] = pd.to_numeric(combined["year"], errors="coerce").astype("Int64")

    # Normalizacion de inconsistencias detectadas en FASE 12 (typos/espacios en el dato
    # original de Medicina Legal, NO se cambia el significado, solo se colapsan variantes
    # de la misma categoria):
    combined["rol"] = combined["rol"].replace({"COnductor": "Conductor"})
    combined["zona"] = combined["zona"].str.replace(
        "Centro poblado(corregimiento", "Centro poblado (corregimiento", regex=False
    )

    print(f"RQ2 individual: {len(combined)} casos moto con TCE "
          f"(fatales={int(combined['outcome_fatal'].sum())}, "
          f"no fatales={int((combined['outcome_fatal']==0).sum())})")
    combined.to_csv(PROCESSED / "rq2_individual_moto_tce.csv", index=False, encoding="utf-8")
    return combined


def main():
    pop = build_population_denominators()
    build_rq1_panel(pop)
    build_rq2_individual()


if __name__ == "__main__":
    main()
