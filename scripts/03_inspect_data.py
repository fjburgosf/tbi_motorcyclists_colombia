"""
FASE 1/2 - Auditoria de valores reales: DANE EEVV Defunciones no fetales 2024.

Objetivo (segun CLAUDE.md seccion 10): distinguir "la documentacion afirma que existe"
de "la variable esta realmente presente y poblada en el archivo analizable".

Verifica, con el archivo real descargado por el investigador:
  1. Frecuencia real de causa externa V20-V29 (motociclista) en C_BAS1.
  2. Frecuencia real de TCE (S06) en CAUSA_MULT (causas antecedentes/multiples).
  3. Cruce: cuantas muertes con causa basica V20-V29 tienen ademas S06 en CAUSA_MULT.
  4. Completitud (missing) de CAUSA_MULT, C_BAS1, geografia de ocurrencia.

No inventa nada: si un valor no aparece, se reporta como 0 / NO ENCONTRADO, no se asume.
"""

import pyreadstat
import pandas as pd
import re
import json
from pathlib import Path

RAW_DIR = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis/data/raw/dane_eevv_2024/BD-EEVV-Defuncionesnofetales-2024")
DTA_FILE = RAW_DIR / "BD-EEVV-Defuncionesnofetales-2024.dta"
OUT_DIR = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis/results/exploratory")
LOG_DIR = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis/logs")

COLS_NEEDED = [
    "ANO", "MES", "SEXO", "GRU_ED1", "GRU_ED2",
    "COD_DPTO", "COD_MUNIC", "CODOCUR", "CODMUNOC",
    "C_BAS1", "CAUSA_MULT", "CAUSA_667", "CAU_HOMOL",
    "P_PMAN_IRIS", "TIPO_DEFUN",
]

MOTO_VCODE_RE = re.compile(r"V2[0-9]")   # V20-V29 = accidente de transporte de motociclista (CIE-10)
TCE_S06_RE = re.compile(r"S06")          # S06 = traumatismo intracraneal (CIE-10)


def main():
    print(f"Leyendo {DTA_FILE} (solo columnas necesarias)...")
    df, meta = pyreadstat.read_dta(str(DTA_FILE), usecols=COLS_NEEDED)
    n_total = len(df)
    print(f"N total de defunciones no fetales 2024: {n_total}")

    report = {"n_total_defunciones_2024": n_total, "fuente": str(DTA_FILE)}

    # 1. Completitud de las columnas clave
    completeness = {}
    for col in ["C_BAS1", "CAUSA_MULT", "CODOCUR", "CODMUNOC"]:
        non_null = df[col].notna().sum()
        non_empty = df[col].astype(str).str.strip().replace({"nan": ""}).ne("").sum()
        completeness[col] = {
            "non_null": int(non_null),
            "non_empty_str": int(non_empty),
            "pct_populated": round(100 * non_empty / n_total, 2),
        }
    report["completitud"] = completeness
    print("Completitud:", json.dumps(completeness, indent=2, ensure_ascii=False))

    # 2. C_BAS1 con V20-V29 (motociclista, causa basica)
    c_bas1 = df["C_BAS1"].astype(str)
    is_moto_basica = c_bas1.str.contains(MOTO_VCODE_RE, na=False)
    n_moto_basica = int(is_moto_basica.sum())
    report["n_causa_basica_V20_V29_motociclista"] = n_moto_basica
    print(f"Defunciones con causa BASICA V20-V29 (motociclista): {n_moto_basica}")

    # Desglose por codigo especifico V20-V29
    moto_breakdown = c_bas1[is_moto_basica].value_counts().to_dict()
    report["desglose_causa_basica_moto"] = {k: int(v) for k, v in moto_breakdown.items()}

    # 3. CAUSA_MULT con S06 (TCE) en cualquier posicion (campo texto con multiples codigos)
    causa_mult = df["CAUSA_MULT"].astype(str)
    has_s06 = causa_mult.str.contains(TCE_S06_RE, na=False)
    n_s06_total = int(has_s06.sum())
    report["n_causa_multiple_S06_TCE_total"] = n_s06_total
    print(f"Defunciones con S06 (TCE) en CAUSA_MULT (cualquier causa de muerte): {n_s06_total}")

    # 4. Cruce clave: motociclista (causa basica) Y TCE (causa multiple)
    cross = is_moto_basica & has_s06
    n_cross = int(cross.sum())
    report["n_moto_Y_S06_cruce"] = n_cross
    print(f"CRUCE: causa basica V20-V29 (moto) Y S06 (TCE) en causa multiple: {n_cross}")

    if n_moto_basica > 0:
        pct = round(100 * n_cross / n_moto_basica, 2)
        report["pct_moto_con_S06"] = pct
        print(f"  -> {pct}% de las muertes de motociclistas (V20-V29) registran S06 como causa asociada")

    # 5. Muestra de valores crudos de CAUSA_MULT para muertes de motociclistas (para inspeccion manual)
    sample = causa_mult[is_moto_basica].head(30).tolist()
    report["muestra_causa_mult_moto_raw"] = sample

    # 6. Guardar outputs
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    out_json = OUT_DIR / "audit_dane_eevv_2024_tce_moto.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nReporte guardado en: {out_json}")

    df_moto = df[is_moto_basica].copy()
    df_moto["tiene_S06_causa_mult"] = has_s06[is_moto_basica]
    csv_out = OUT_DIR / "defunciones_motociclistas_2024_dane.csv"
    df_moto.to_csv(csv_out, index=False, encoding="utf-8")
    print(f"Subconjunto de muertes de motociclistas guardado en: {csv_out}")


if __name__ == "__main__":
    main()
