# FASE 7 — Plan estadístico detallado

Deriva de: pregunta + unidad de análisis + estructura de datos + outcome + diseño (CLAUDE.md secc. 19). NO se elige técnica por sofisticación.

## Definiciones operacionales (fijadas antes del análisis)

- **Motociclista:** Med. Legal → `medio_de_desplazamiento_o_transporte="Motocicleta"` (roles conductor/pasajero vía `condicion_de_la_victima_at`). DANE → causa básica `C_BAS1 ∈ V20–V29`.
- **TCE:** Med. Legal → `diagnostico_topografico="Trauma craneano"` (definición primaria); DANE → S06 en causas (definición de sensibilidad, CIE-10). Doble definición = análisis de robustez, no debilidad (ver docs/definitions/TCE_definition.md — PENDIENTE crear).
- **Desenlace fatal:** pertenencia al dataset fatal (`s65h-7665`) vs no-fatal (`ezhf-hscf`).

## Análisis por RQ

### RQ1 — Tendencia + territorial
- **Numerador:** conteos Med. Legal por año / departamento.
- **Denominador:** proyecciones de población DANE (PENDIENTE descargar) → tasas por 100.000.
- **Modelo:** regresión de Poisson; si sobredispersión (probable), **negative binomial**. Offset = log(población). Tiempo como término continuo y/o categórico.
- **Territorial:** modelo multinivel (año nivel-1, departamento nivel-2) con intercepto aleatorio; reportar varianza entre departamentos e ICC. Complemento descriptivo: mapa de tasas / SMR.

### RQ2 — Factores asociados a letalidad
- **Diseño:** combinar fatal + no-fatal restringido a motociclistas con trauma craneano → outcome binario fatal.
- **Modelo:** regresión logística multivariable. Extensión: logística multinivel con departamento nivel-2.
- **Covariables:** edad, sexo, zona (urbano/rural), rol, clase de accidente, objeto de colisión, año.
- **Reporte:** OR con IC95%; NO lenguaje causal (solo "asociado a").

### RQ3 — Comparabilidad DANE
- Formalizar la comparación DANE↔Med. Legal (ya en FASE 3); cuantificar sesgo de tendencia con/sin corte 2022.

## Robustez / falsación (secc. 8, 22)
- Definición alt. de TCE (Med. Legal topográfico vs DANE S06).
- Excluir 2022-2024 y re-estimar tendencia (¿persiste sin el quiebre DANE?).
- Serie solo Med. Legal vs solo DANE.
- Subgrupos: sexo, urbano/rural, grupos etarios.
- Sensibilidad a "Politraumatismo" (los que podrían ocultar TCE) — reportar rango.

## Multiplicidad (secc. 24)
- Análisis confirmatorios = H1-H4. Todo lo demás exploratorio con FDR si múltiples pruebas.

## Pendientes de datos antes de ejecutar
1. Descargar proyecciones de población DANE por depto/año/sexo/edad (denominadores).
2. Crear `docs/definitions/TCE_definition.md` con la definición CIE-10 verificada.
3. Descargar los microdatos Med. Legal a disco (hasta ahora solo vía API).

## Software
- **Decisión (2026-08-20):** Python. `statsmodels` (Poisson/NegBin/logística), `statsmodels.MixedLM` o `bambi`/`pymer4` si se requiere multinivel más flexible.
