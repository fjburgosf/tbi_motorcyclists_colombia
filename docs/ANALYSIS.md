# ANALYSIS.md — Métodos, scripts y procedimientos

**Última actualización:** 2026-08-20. Log cronológico detallado en `ANALYSIS_LOG.md` (raíz). Plan completo en `docs/methodology/plan_estadistico_fase7.md`. Robustez en `docs/methodology/threats_to_validity_fase14.md`.

## Fuentes de datos (detalle en `DATA_SOURCES.md`)
- **Medicina Legal fatal** `s65h-7665` (Socrata) — 73.403 registros; 40.318 motociclistas.
- **Medicina Legal no fatal** `ezhf-hscf` (Socrata) — 342.796; 196.330 motociclistas.
- **DANE-EEVV** defunciones no fetales 2015–2024 (10 archivos, `data/raw/dane_eevv_*`).
- **DANE proyecciones de población** departamental/municipal (`data/raw/dane_poblacion/`), denominadores.

## Definiciones operacionales (`docs/definitions/TCE_definition.md`)
- Motociclista: Med.Legal `medio="Motocicleta"`; DANE `C_BAS1 ∈ V20–V29`.
- TCE primario: `diagnostico_topografico="Trauma craneano"`. TCE sensibilidad: CIE-10 S06 (DANE, `CAUSA_MULT` 2019–2024 / 11 campos separados 2015–2018).
- Outcome de letalidad: pertenencia a dataset fatal vs no-fatal.

## Pipeline de scripts
| Script | Función | Output |
|---|---|---|
| `03_inspect_data.py` | Auditoría valores DANE 2024 | `results/exploratory/audit_dane_eevv_2024_*` |
| `03b_inspect_data_panel_2015_2024.py` | Panel DANE 10 años (maneja Era A/B de causa múltiple) | `panel_dane_eevv_2015_2024_tce_moto.*` |
| `04_clean_data.py` | Filtra Med.Legal a motociclistas | `data/interim/medlegal_moto_{fatal,nofatal}.csv` |
| `05_construct_variables.py` | Denominadores pobl. + datasets RQ1/RQ2 | `data/processed/{population_dept_year, rq1_panel_dept_year, rq2_individual_moto_tce}.csv` |
| `06_link_data.py` | Auditoría linkage DANE↔Med.Legal | `linkage_audit_dane_medlegal.*` |
| `07_descriptive_analysis.py` | Exploratorio RQ1/RQ2 | `rq1_serie_nacional.csv`, `rq1_tasas_departamento.csv` |
| `08_primary_model.py` | Modelos H1–H3 | `results/primary/*.txt` |
| `09b_runt_sensitivity.py` | Sensibilidad denominador RQ1 (por-moto, RUNT) | `tables/tableS_runt_sensibilidad.csv`, `results/robustness/rq1_runt_sensibilidad.json`, `figures/figS_runt_sensibilidad.png` |
| `09c_rq2_profile_bounding.py` | Reencuadre RQ2: perfil descriptivo de fatales + bounding de selección | `tables/tableS_rq2_perfil_fatales.csv`, `tables/tableS_rq2_bounding_seleccion.csv`, `results/robustness/rq2_reframe.json` |
| `09d_referee_revisions.py` | Revisiones referee: tendencia TBI-específica (M1), concordancia territorial total-vs-TBI, IRR DANE 2015-2021 (M2), reconciliación Tabla S1 (M4) | `results/robustness/referee_revisions.json` |
| `10_figures.py` | 3 figuras | `figures/*.png` |
| `11_tables.py` | 3 tablas | `tables/*.csv` |
| `13_format_references.py` | Referencias formateadas | `manuscript/references_formatted.md` |

*(No existen scripts 01, 02, 09, 12; numeración según plantilla CLAUDE.md, no todos los pasos requirieron script propio.)*

## Modelos estadísticos (Python 3.12, statsmodels 0.14.6)
- **H1 tendencia (RQ1):** Negative Binomial (α por MLE), offset log-población, año centrado. Robustez: solo 2015–2021.
- **H2 territorial (RQ1):** Poisson con departamento categórico vs reducido, LR test. + tasas descriptivas por depto. **Sensibilidad denominador:** tasa por 10.000 motos (RUNT2.0 `u3vn-bdcy`); concordancia de rankings por Spearman; robustos = top-tercil en ambos denominadores. Limitación: RUNT por matrícula, no circulación.
- **H3 letalidad (RQ2):** logística multivariable (sexo, zona, rol, año) + Bayesian mixed GLM con intercepto aleatorio de departamento.
- **RQ3:** comparación año a año DANE vs Med.Legal + re-estimación de tendencia con definición DANE.

## Verificaciones de integridad realizadas
- Truncamiento silencioso de descarga Socrata (50k/300k) detectado y corregido vía `count(id)`.
- 3 inconsistencias categóricas corregidas en pipeline (Bogotá doble rótulo, "Centro poblado" espacio, "COnductor" typo).
- α NegBin fijado por defecto → corregido a MLE.
- `year_c` en RQ2 con OR implausible → trazado a artefacto de captura decreciente de no-fatales, excluido de interpretación.
- Auditoría de 50 citas del manuscrito: 4 lugares con mala atribución corregidos.

## Limitaciones metodológicas conocidas
Ver `docs/methodology/threats_to_validity_fase14.md` (7 chequeos). Las más críticas: sesgo de selección del denominador no-fatal (RQ2); tasas sin denominador de exposición (parque de motos); definición topográfica de TCE subcaptura; linkage solo ecológico.
