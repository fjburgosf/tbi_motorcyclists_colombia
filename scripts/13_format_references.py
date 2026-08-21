"""FASE 16 - Genera la seccion de referencias en formato numerado (estilo MDPI/Vancouver)
directamente desde el CSV maestro, para evitar transcripcion manual de 50 referencias."""
import pandas as pd
from pathlib import Path

CSV = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis/docs/literature/master_bibliography_final.csv")
OUT = Path(r"D:/ACADEMICO/Papers/TBI_data_analysis/manuscript/references_formatted.md")


def format_authors(raw):
    """Convierte 'Lastname A.B.; Lastname2 C.D.' (formato Scopus) a lista simple.
    Si hay mas de 6 autores, trunca a 6 + et al. (convencion MDPI)."""
    if pd.isna(raw) or "no extraidos" in str(raw) or "et al." in str(raw):
        return str(raw).replace("[", "").replace("]", "")
    names = [n.strip() for n in str(raw).split(";") if n.strip()]
    if len(names) > 6:
        names = names[:6] + ["et al."]
    return ", ".join(names)


def main():
    df = pd.read_csv(CSV)
    lines = ["# References (auto-generado desde master_bibliography_final.csv — no editar a mano)\n"]
    for _, r in df.iterrows():
        authors = format_authors(r["Authors"])
        lines.append(
            f"{r['n']}. {authors} {r['Title']}. *{r['Source title']}* {r['Year']}. "
            f"https://doi.org/{r['DOI']}"
        )
    OUT.write_text("\n\n".join(lines), encoding="utf-8")
    print(f"{len(df)} referencias formateadas -> {OUT}")


if __name__ == "__main__":
    main()
