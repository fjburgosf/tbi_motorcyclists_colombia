# DECISIONS.md

## D001 — 2026-08-20 — Medicina Legal como fuente primaria de tendencia temporal; DANE como fuente de codificación CIE-10 de TCE

**Decisión:** Para cualquier análisis de tendencia temporal 2015-2024 de mortalidad de motociclistas, usar la serie de **Medicina Legal** (`s65h-7665`) como fuente primaria. DANE-EEVV se usa para la **definición operacional de TCE por CIE-10 (S06)**, no como serie de tendencia sin ajustar.

**Motivo:** auditoría de linkage (`scripts/06_link_data.py`, FASE 3) mostró que DANE subestimaba sistemáticamente a Medicina Legal en 2015-2021 (-10% a -25%) y convergió casi exactamente desde 2022 (<2% de diferencia). Se verificó con fuente primaria oficial de DANE (https://microdatos.dane.gov.co/index.php/catalog/807/study-description) que desde la base 2022 se integraron directamente registros de la Registraduría Nacional que antes no se capturaban vía RUAF-ND por no tener contacto con el sector salud — es decir, un **cambio real de cobertura/completitud**, no solo un aumento real de mortalidad.

**Evidencia:** `results/exploratory/linkage_audit_dane_medlegal.json`, `ANALYSIS_LOG.md` (entradas 2026-08-20).

**Alternativa descartada:** usar DANE tal cual como serie de tendencia 2015-2024 sin corrección — descartada porque generaría una sobreestimación artificial del crecimiento en 2021-2022, mezclando aumento real con mejora de captura administrativa.

**Consecuencias:**
- Si se necesita usar DANE en un modelo de tendencia, debe incluirse explícitamente un corte estructural / dummy de periodo (pre/post 2022) o restringirse el panel a 2022-2024.
- La definición operacional de TCE (S06 en DANE `CAUSA_MULT`/campos Era A) permanece válida transversalmente año a año; el problema es solo de comparabilidad temporal en los CONTEOS/tendencia, no en la variable en sí.
