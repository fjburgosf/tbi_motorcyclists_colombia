# -*- coding: utf-8 -*-
"""
09c_rq2_profile_bounding.py
---------------------------
RE-ENCUADRE DE RQ2 (letalidad) para blindar contra sesgo de seleccion forense.

Contexto del problema:
  El denominador NO-FATAL de Medicina Legal (valoracion de lesionados) capta solo
  un subconjunto SELECCIONADO de los motociclistas lesionados. Los fatales
  (necropsia obligatoria por causa externa) tienen captacion casi completa.
  -> La "letalidad" absoluta (91,6%) es un artefacto y los OR fatal-vs-nofatal
     pueden estar sesgados por seleccion diferencial.

Estrategia (acordada con el PI):
  (A) PILAR PRIMARIO: perfil DESCRIPTIVO de las defunciones con TCE (outcome_fatal==1),
      que NO usa la muestra no-fatal seleccionada -> libre de sesgo de seleccion.
  (B) SUPLEMENTARIO: conservar los OR de case-fatality, RENOMBRADOS como
      "case-fatality entre casos forenses", con un BOUNDING de seleccion:
      bajo letalidad verdadera igual entre grupos, un OR observado se explicaria
      enteramente por una razon de captacion no-fatal = 1/OR entre grupos.

Salidas:
  tables/tableS_rq2_perfil_fatales.csv
  tables/tableS_rq2_bounding_seleccion.csv
  results/robustness/rq2_reframe.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "rq2_individual_moto_tce.csv"
TABLES = ROOT / "tables"
OUT_ROB = ROOT / "results" / "robustness"
for d in (TABLES, OUT_ROB):
    d.mkdir(parents=True, exist_ok=True)


def zona_bin(s):
    s = str(s).lower()
    if "rural" in s or "vereda" in s or "campo" in s:
        return "Rural"
    if "urban" in s or "cabecera" in s or "ciudad" in s:
        return "Urbano"
    return "Otro/ND"


def profile_block(df, col, label):
    """Distribucion de fatales por categoria: n y %."""
    vc = df[col].value_counts(dropna=False)
    tot = vc.sum()
    rows = []
    for cat, n in vc.items():
        rows.append({"variable": label, "categoria": str(cat),
                     "n_fatales": int(n), "pct": round(100 * n / tot, 1)})
    return rows


def main():
    df = pd.read_csv(DATA, encoding="utf-8")
    df["zona_bin"] = df["zona"].map(zona_bin)

    fatal = df[df["outcome_fatal"] == 1].copy()
    n_fatal = len(fatal)
    n_total = len(df)
    n_nofatal = n_total - n_fatal

    # -------- (A) PERFIL DESCRIPTIVO DE FATALES (pilar limpio) --------
    prof = []
    prof += profile_block(fatal, "sexo", "Sexo")
    prof += profile_block(fatal, "grupo_edad", "Grupo de edad")
    prof += profile_block(fatal, "zona_bin", "Zona")
    prof += profile_block(fatal, "rol", "Rol")
    prof_df = pd.DataFrame(prof)
    prof_df.to_csv(TABLES / "tableS_rq2_perfil_fatales.csv", index=False, encoding="utf-8")

    # -------- (B) BOUNDING DE SELECCION sobre los OR --------
    # OR de case-fatality (modelo logistico principal, ver 08_primary_model.py):
    #   fatal ~ sexo + zona_bin + rol + year_c
    # Reproducimos los OR crudos por celda 2x2 para el bounding interpretable.
    def cell_or(col, ref, idx):
        sub = df[df[col].isin([ref, idx])]
        tab = pd.crosstab(sub[col], sub["outcome_fatal"])
        # OR = (fatal_idx/nofatal_idx)/(fatal_ref/nofatal_ref)
        f_i, nf_i = tab.loc[idx, 1], tab.loc[idx, 0]
        f_r, nf_r = tab.loc[ref, 1], tab.loc[ref, 0]
        orv = (f_i / nf_i) / (f_r / nf_r)
        return orv, dict(f_i=int(f_i), nf_i=int(nf_i), f_r=int(f_r), nf_r=int(nf_r))

    contrasts = [
        ("Sexo", "sexo", "Hombre", "Mujer"),
        ("Zona", "zona_bin", "Rural", "Urbano"),
        ("Rol", "rol", "Conductor", "Pasajero"),
    ]
    bound = []
    for label, col, ref, idx in contrasts:
        orv, cells = cell_or(col, ref, idx)
        sel_ratio = 1.0 / orv  # captacion no-fatal (idx vs ref) que anularia el OR
        bound.append({
            "contraste": f"{label}: {idx} vs {ref}",
            "OR_case_fatality_crudo": round(orv, 3),
            "razon_captacion_nofatal_que_explicaria_OR": round(sel_ratio, 2),
            "interpretacion": (
                f"Un OR de {orv:.2f} se explicaria enteramente si los lesionados "
                f"'{idx}' llegaran a valoracion forense {sel_ratio:.1f}x mas que "
                f"'{ref}', aun con letalidad verdadera IGUAL."
            ),
            **cells,
        })
    bound_df = pd.DataFrame(bound)
    bound_df.to_csv(TABLES / "tableS_rq2_bounding_seleccion.csv", index=False, encoding="utf-8")

    summary = {
        "n_total": n_total,
        "n_fatal": n_fatal,
        "n_nofatal": n_nofatal,
        "case_fatality_forense_pct": round(100 * n_fatal / n_total, 1),
        "advertencia": (
            "case-fatality forense NO es letalidad poblacional; denominador no-fatal "
            "esta seleccionado (solo lesionados que llegan a valoracion forense)."
        ),
        "pilar_primario": "perfil descriptivo de defunciones con TCE (sin muestra no-fatal)",
        "bounding": bound_df.to_dict(orient="records"),
    }
    with open(OUT_ROB / "rq2_reframe.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"=== RQ2 re-encuadre ===")
    print(f"n total {n_total} | fatales {n_fatal} | no-fatales {n_nofatal} "
          f"| case-fatality forense {100*n_fatal/n_total:.1f}%\n")
    print("--- (A) Perfil descriptivo de FATALES (pilar limpio) ---")
    print(prof_df.to_string(index=False))
    print("\n--- (B) Bounding de seleccion sobre OR ---")
    print(bound_df[["contraste", "OR_case_fatality_crudo",
                    "razon_captacion_nofatal_que_explicaria_OR"]].to_string(index=False))
    print("\nGuardado: tables/tableS_rq2_perfil_fatales.csv, "
          "tables/tableS_rq2_bounding_seleccion.csv, results/robustness/rq2_reframe.json")


if __name__ == "__main__":
    main()
