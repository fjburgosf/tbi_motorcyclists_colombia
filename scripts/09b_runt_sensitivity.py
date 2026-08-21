# -*- coding: utf-8 -*-
"""
09b_runt_sensitivity.py
-----------------------
ANALISIS DE SENSIBILIDAD (ROBUSTEZ) para RQ1 - desigualdad territorial.

Objetivo: probar si el ranking de mortalidad de motociclistas por departamento
es robusto a la eleccion del denominador de exposicion:
    (a) poblacion total  -> tasa por 100.000 habitantes (PRIMARIO)
    (b) parque de motos   -> tasa por 10.000 motos      (SENSIBILIDAD)

Fuente denominador (b): RUNT2.0 "CRECIMIENTO DEL PARQUE AUTOMOTOR"
    datos.gov.co dataset u3vn-bdcy (snapshot 2026-07, unico disponible).

LIMITACIONES DOCUMENTADAS (no inventar; ver Discusion del manuscrito):
- RUNT cuenta motos por departamento de MATRICULA, no de circulacion.
  -> Municipios-matriculadero (Cundinamarca absorbe Bogota) inflan/desinflan.
  -> Flota informal/contrabando fronterizo (La Guajira) subcontada.
- Snapshot 2026-07: no hay serie historica por anio -> denominador estatico.
- Vaupes (97) no aparece en RUNT -> tasa por-moto no calculable.

NO es un reemplazo del denominador poblacional: es triangulacion.
"""
import json
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "runt"
OUT_ROB = ROOT / "results" / "robustness"
TABLES = ROOT / "tables"
for d in (RAW, OUT_ROB, TABLES):
    d.mkdir(parents=True, exist_ok=True)

RUNT_CSV = RAW / "parque_motos_depto_2026-07.csv"

# Crosswalk nombre RUNT -> codigo DIVIPOLA (verificado contra panel)
XW = {
    'ANTIOQUIA': 5, 'ATLANTICO': 8, 'BOGOTA D.C.': 11, 'BOLIVAR': 13, 'BOYACA': 15,
    'CALDAS': 17, 'CAQUETA': 18, 'CAUCA': 19, 'CESAR': 20, 'CORDOBA': 23,
    'CUNDINAMARCA': 25, 'CHOCO': 27, 'HUILA': 41, 'LA GUAJIRA': 44, 'MAGDALENA': 47,
    'META': 50, 'NARINO': 52, 'NORTE DE SANTANDER': 54, 'QUINDIO': 63, 'RISARALDA': 66,
    'SANTANDER': 68, 'SUCRE': 70, 'TOLIMA': 73, 'VALLE DEL CAUCA': 76, 'ARAUCA': 81,
    'CASANARE': 85, 'PUTUMAYO': 86,
    'ARCHIPIELAGO DE SAN ANDRES, PROVIDENCIA': 88,
    'AMAZONAS': 91, 'GUAINIA': 94, 'GUAVIARE': 95, 'VICHADA': 99,
}


def download_runt():
    """Descarga parque de motos activo por departamento (snapshot RUNT2.0)."""
    url = ("https://www.datos.gov.co/resource/u3vn-bdcy.json?"
           "$select=nombre_departamento,sum(cantidad)"
           "&$where=nombre_de_la_clase='MOTOCICLETA' AND estado_del_vehiculo='ACTIVO'"
           "&$group=nombre_departamento&$limit=100").replace(' ', '%20')
    data = json.load(urllib.request.urlopen(url))
    runt = pd.DataFrame(data)
    runt['motos'] = runt['sum_cantidad'].astype(float).astype(int)
    runt = runt[['nombre_departamento', 'motos']]
    runt.to_csv(RUNT_CSV, index=False, encoding='utf-8')
    return runt


def main():
    if RUNT_CSV.exists():
        runt = pd.read_csv(RUNT_CSV, encoding='utf-8')
    else:
        runt = download_runt()

    runt['cod_dpto'] = runt['nombre_departamento'].map(XW)
    missing_xw = runt[runt['cod_dpto'].isna()]
    if len(missing_xw):
        raise ValueError(f"Nombres RUNT sin crosswalk: {missing_xw['nombre_departamento'].tolist()}")

    # Muertes moto 2015-2024 + poblacion media por depto (excluye cod 999)
    panel = pd.read_csv(ROOT / "data" / "processed" / "rq1_panel_dept_year.csv", encoding='utf-8')
    panel = panel[panel['cod_dpto'] != 999]
    n_years = panel['year'].nunique()
    agg = (panel.groupby('cod_dpto')
           .agg(muertes=('n_fatal_moto', 'sum'),
                pob_media=('poblacion_total', 'mean'),
                depto=('depto_nombre', 'first'))
           .reset_index())

    df = agg.merge(runt[['cod_dpto', 'motos']], on='cod_dpto', how='left')
    df['tasa_x100k_hab'] = df['muertes'] / n_years / df['pob_media'] * 100_000
    df['tasa_x10k_moto'] = df['muertes'] / n_years / df['motos'] * 10_000
    df['motos_x1000hab'] = df['motos'] / df['pob_media'] * 1_000

    # Rankings y correlacion (solo depts con RUNT)
    d2 = df.dropna(subset=['motos']).copy()
    d2['rank_hab'] = d2['tasa_x100k_hab'].rank(ascending=False).astype(int)
    d2['rank_moto'] = d2['tasa_x10k_moto'].rank(ascending=False).astype(int)
    rho = d2['tasa_x100k_hab'].corr(d2['tasa_x10k_moto'], method='spearman')

    # Departamentos robustos: top-tercil en AMBOS denominadores
    n = len(d2)
    thr = max(1, n // 3)
    top_hab = set(d2.nsmallest(thr, 'rank_hab')['cod_dpto'])
    top_moto = set(d2.nsmallest(thr, 'rank_moto')['cod_dpto'])
    robust_high = sorted(top_hab & top_moto)
    df['robusto_alto'] = df['cod_dpto'].isin(robust_high)

    # Guardar tabla de sensibilidad
    cols = ['cod_dpto', 'depto', 'muertes', 'motos', 'tasa_x100k_hab',
            'tasa_x10k_moto', 'motos_x1000hab', 'robusto_alto']
    out = df[cols].sort_values('tasa_x100k_hab', ascending=False)
    out.to_csv(TABLES / "tableS_runt_sensibilidad.csv", index=False, encoding='utf-8')

    summary = {
        "fuente_denominador": "RUNT2.0 u3vn-bdcy snapshot 2026-07 (MOTOCICLETA ACTIVO)",
        "parque_motos_nacional": int(runt['motos'].sum()),
        "n_departamentos_con_runt": int(n),
        "departamentos_sin_runt": df[df['motos'].isna()]['depto'].tolist(),
        "spearman_rho_ranking_hab_vs_moto": round(float(rho), 3),
        "departamentos_robustos_alto_ambos": [
            df.loc[df['cod_dpto'] == c, 'depto'].iloc[0] for c in robust_high
        ],
        "nota_registro_vs_circulacion": (
            "RUNT cuenta por departamento de matricula. Divergencias del ranking "
            "estan dominadas por artefactos de registro (La Guajira: flota informal "
            "subcontada; Bogota-Cundinamarca: transferencia de matricula), no por "
            "senal epidemiologica. Denominador poblacional se mantiene como PRIMARIO."
        ),
    }
    with open(OUT_ROB / "rq1_runt_sensibilidad.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("=== Sensibilidad denominador RQ1 (RUNT) ===")
    print(out.to_string(index=False))
    print(f"\nSpearman rho (hab vs moto) = {rho:.3f}  (n={n})")
    print(f"Robustos alto en ambos: {summary['departamentos_robustos_alto_ambos']}")
    print(f"Sin RUNT: {summary['departamentos_sin_runt']}")
    print(f"\nGuardado: tables/tableS_runt_sensibilidad.csv")
    print(f"Guardado: results/robustness/rq1_runt_sensibilidad.json")


if __name__ == "__main__":
    main()
