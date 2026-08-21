"""
FASE 10 - Limpieza: filtra Medicina Legal (fatal/no-fatal) a motociclistas y
estandariza tipos. No inventa columnas ni valores; solo filtra/tipa.
"""
import pandas as pd
from pathlib import Path

RAW = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis/data/raw/medicina_legal")
INTERIM = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis/data/interim")
INTERIM.mkdir(parents=True, exist_ok=True)


def clean(path_in, path_out, label):
    df = pd.read_csv(path_in, dtype=str, low_memory=False)
    n0 = len(df)
    df = df[df["medio_de_desplazamiento_o_transporte"] == "Motocicleta"].copy()
    df["a_o_del_hecho"] = pd.to_numeric(df["a_o_del_hecho"], errors="coerce").astype("Int64")
    df.to_csv(path_out, index=False, encoding="utf-8")
    print(f"{label}: {n0} filas totales -> {len(df)} motociclistas -> {path_out}")


def main():
    clean(RAW / "muertes_eventos_transporte_2015_2024.csv",
          INTERIM / "medlegal_moto_fatal.csv", "FATAL")
    clean(RAW / "lesiones_eventos_transporte_2015_2024.csv",
          INTERIM / "medlegal_moto_nofatal.csv", "NO_FATAL")


if __name__ == "__main__":
    main()
