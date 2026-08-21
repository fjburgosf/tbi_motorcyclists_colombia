"""
FASE 1/2 - Auditoria de valores reales, PANEL 2015-2024: DANE EEVV Defunciones no fetales.

Extiende scripts/03_inspect_data.py (que solo cubria 2024) a los 10 anos descargados.

HALLAZGO ESTRUCTURAL DOCUMENTADO (no asumido, verificado columna por columna):
  - Era A (2015-2018): el archivo NO tiene un campo unico "CAUSA_MULT". Las causas
    antecedentes/directas/patologicas estan repartidas en:
    C_ANT1, C_ANT12, C_ANT2, C_ANT22, C_ANT3, C_ANT32, C_DIR1, C_DIR12, C_MCM1,
    C_PAT1, C_PAT2
  - Era B (2019-2024): existe el campo unico "CAUSA_MULT" (texto con multiples
    codigos CIE-10 separados por "/").

Para que el panel sea comparable, se construye una variable derivada
`tiene_S06_causa_asociada` que:
  - En Era A: es True si S06 aparece en CUALQUIERA de los 11 campos de causa listados.
  - En Era B: es True si S06 aparece en CAUSA_MULT.

Esto es una armonizacion METODOLOGICA EXPLICITA, no una invencion de datos: cada
codigo se lee tal cual esta en el archivo original. La diferencia estructural entre
eras queda documentada en el output y debe declararse en el manuscrito como limitacion
/ threat to validity (posible diferencia en captura de causas asociadas entre eras).

C_BAS1 (causa basica) SI es comparable en todos los anos: mismo campo, mismo formato
CIE-10, en todos los archivos 2015-2024.
"""

import pyreadstat
import pandas as pd
import re
import json
from pathlib import Path

PROJECT = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis")
RAW_DIR = PROJECT / "data" / "raw"
OUT_DIR = PROJECT / "results" / "exploratory"
LOG_DIR = PROJECT / "logs"

MOTO_VCODE_RE = re.compile(r"V2[0-9]")
TCE_S06_RE = re.compile(r"S06")

# Archivo real por anio (nombre verificado en disco, no asumido)
YEAR_FILES = {
    2015: "data/raw/dane_eevv_2015/BD-EEVV-Defuncionesnofetales-2015/nofetal2015.dta",
    2016: "data/raw/dane_eevv_2016/BD-EEVV-Defuncionesnofetales-2016/nofetal2016.dta",
    2017: "data/raw/dane_eevv_2017/BD-EEVV-Defuncionesnofetales-2017/nofetal2017.dta",
    2018: "data/raw/dane_eevv_2018/BD-EEVV-Defuncionesnofetales-2018/nofetal2018.dta",
    2019: "data/raw/dane_eevv_2019/BD-EEVV-Defuncionesnofetales-2019/nofetal2019.dta",
    2020: "data/raw/dane_eevv_2020/BD-EEVV-Defuncionesnofetales-2020/nofetal2020.dta",
    2021: "data/raw/dane_eevv_2021/BD-EEVV-Defuncionesnofetales-2021/nofetal2021.stata",
    2022: "data/raw/dane_eevv_2022/BD-EEVV-Defuncionesnofetales-2022/nofetal2022.dta",
    2023: "data/raw/dane_eevv_2023/BD-EEVV-Defuncionesnofetales-2023/BD-EEVV-Defuncionesnofetales-2023.dta",
    2024: "data/raw/dane_eevv_2024/BD-EEVV-Defuncionesnofetales-2024/BD-EEVV-Defuncionesnofetales-2024.dta",
}

ERA_A_YEARS = {2015, 2016, 2017, 2018}  # sin CAUSA_MULT
ERA_A_CAUSE_FIELDS = [
    "C_ANT1", "C_ANT12", "C_ANT2", "C_ANT22", "C_ANT3", "C_ANT32",
    "C_DIR1", "C_DIR12", "C_MCM1", "C_PAT1", "C_PAT2",
]

BASE_COLS_NEEDED_UPPER = [
    "ANO", "MES", "SEXO", "GRU_ED1", "GRU_ED2",
    "COD_DPTO", "COD_MUNIC", "CODOCUR", "CODMUNOC",
    "C_BAS1", "CAUSA_667", "CAU_HOMOL", "TIPO_DEFUN", "SIT_DEFUN",
]


def load_year(year, path):
    full_path = PROJECT / path
    df, meta = pyreadstat.read_dta(str(full_path))
    df.columns = [c.upper() for c in df.columns]
    return df, meta


def process_year(year, path):
    print(f"\n--- Procesando {year} ({path}) ---")
    df, meta = load_year(year, path)
    n_total = len(df)
    era = "A_sin_causa_mult" if year in ERA_A_YEARS else "B_con_causa_mult"

    c_bas1 = df["C_BAS1"].astype(str)
    is_moto = c_bas1.str.contains(MOTO_VCODE_RE, na=False)
    n_moto = int(is_moto.sum())

    if year in ERA_A_YEARS:
        present_fields = [f for f in ERA_A_CAUSE_FIELDS if f in df.columns]
        combined = df[present_fields].astype(str).agg("/".join, axis=1)
        has_s06 = combined.str.contains(TCE_S06_RE, na=False)
    else:
        combined = df["CAUSA_MULT"].astype(str)
        has_s06 = combined.str.contains(TCE_S06_RE, na=False)

    n_s06_total = int(has_s06.sum())
    cross = is_moto & has_s06
    n_cross = int(cross.sum())
    pct_cross = round(100 * n_cross / n_moto, 2) if n_moto else None

    # completitud geografica dentro del subgrupo moto
    geo_col = "CODOCUR" if "CODOCUR" in df.columns else None
    geo_pct = None
    if geo_col:
        moto_geo = df.loc[is_moto, geo_col].astype(str).str.strip()
        geo_pct = round(100 * moto_geo.ne("").mean(), 2) if n_moto else None

    result = {
        "year": year,
        "era_causa_asociada": era,
        "n_total_defunciones": n_total,
        "n_causa_basica_moto_V20_V29": n_moto,
        "n_S06_causa_asociada_total": n_s06_total,
        "n_moto_Y_S06": n_cross,
        "pct_moto_con_S06": pct_cross,
        "pct_geografia_hecho_poblada_en_moto": geo_pct,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    all_results = []
    for year, path in YEAR_FILES.items():
        full_path = PROJECT / path
        if not full_path.exists():
            print(f"AVISO: archivo NO ENCONTRADO para {year}: {path} -- se omite, NO se inventa.")
            continue
        try:
            res = process_year(year, path)
            all_results.append(res)
        except Exception as e:
            print(f"ERROR procesando {year}: {e}")
            all_results.append({"year": year, "error": str(e)})

    panel = pd.DataFrame(all_results)
    out_csv = OUT_DIR / "panel_dane_eevv_2015_2024_tce_moto.csv"
    panel.to_csv(out_csv, index=False, encoding="utf-8")

    out_json = OUT_DIR / "panel_dane_eevv_2015_2024_tce_moto.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n\n=== PANEL COMPLETO ===")
    print(panel.to_string(index=False))
    print(f"\nGuardado en: {out_csv}")
    print(f"Guardado en: {out_json}")


if __name__ == "__main__":
    main()
