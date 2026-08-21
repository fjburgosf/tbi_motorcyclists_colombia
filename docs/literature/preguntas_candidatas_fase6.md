# FASE 6 — Preguntas de investigación candidatas (basadas en FASES 1-5, sin datos nuevos)

## Pregunta A — Tendencia descriptiva nacional

**RQ:** ¿Cómo ha evolucionado la mortalidad por TCE en motociclistas en Colombia, 2015-2024?
**Hipótesis:** H0 descriptiva (sin dirección impuesta): existe variación temporal no explicada solo por artefacto de cobertura.
**Población:** motociclistas fallecidos por evento de transporte, Colombia.
**Exposición:** ser motociclista (vs. otros modos).
**Outcome:** muerte con TCE (Medicina Legal "Trauma craneano"; DANE S06 transversal).
**Unidad de análisis:** individuo (agregado a año).
**Covariables:** sexo, edad, departamento.
**Confusores/mediadores:** cobertura administrativa (DANE, controlado con dummy 2022 por D001), pandemia.
**Fuente por variable:** Medicina Legal `s65h-7665` (serie), DANE-EEVV (definición CIE-10 transversal).
**Periodo:** 2015-2024. **Diseño:** descriptivo/serie temporal.
**Sesgos:** cambio de cobertura DANE (ya documentado y controlable). Falacia ecológica si se interpreta a nivel individual sin cuidado.
**Factibilidad:** ALTA (datos ya en mano). **Novedad:** MEDIA (actualiza Cartagena 2007-2011 a nacional 2015-2024).
**Falsación intentada:** si la tendencia desaparece al excluir 2022-2024 (post-quiebre DANE) o al usar solo Medicina Legal, la "tendencia" es mayormente artefacto — DEBE reportarse como hallazgo, no ocultarse.

## Pregunta B — Desigualdad territorial

**RQ:** ¿Existen diferencias departamentales en la proporción de muertes de motociclistas con TCE en Colombia, 2015-2024?
**Hipótesis:** la proporción varía por departamento más allá del azar.
**Unidad de análisis:** departamento-año (ecológico).
**Covariables:** población DANE (denominador), ruralidad.
**Fuente:** Medicina Legal (numerador, código DIVIPOLA verificado), DANE población (denominador).
**Diseño:** ecológico, posible multinivel (año dentro de departamento).
**Sesgos:** linkage es SOLO ecológico (confirmado FASE 3) — no se puede inferir causalidad individual.
**Factibilidad:** ALTA. **Novedad:** MEDIA-ALTA (nadie ha hecho esto para TCE-moto específicamente; SALURBAL lo hizo a nivel ciudad, no TCE).
**Falsación intentada:** si la variación entre departamentos no supera la esperada por tamaño muestral (prueba de heterogeneidad), la pregunta se descarta como no informativa.

## Pregunta C — Efecto COVID-19 (línea F, sección 14)

**RQ:** ¿Cambió la mortalidad de motociclistas con TCE en Colombia durante 2020-2021 vs. periodo previo?
**Diseño:** pre-post / interrupted time series (con dummy explícito para el quiebre DANE 2022, NO confundir ambos eventos).
**Riesgo mayor:** el quiebre de cobertura DANE (2022) y el efecto COVID (2020-2021) son temporalmente cercanos — **alto riesgo de confusión metodológica** si no se usa Medicina Legal como serie primaria (más estable, ver D001).
**Factibilidad:** MEDIA (requiere diseño cuidadoso de series interrumpidas). **Novedad:** MEDIA-ALTA (Gómez-Niebles 2026 lo hizo solo en 1 hospital hasta 2021; nacional y hasta 2024 es nuevo).
**Falsación intentada:** si el "efecto COVID" no es distinguible estadísticamente del quiebre de cobertura DANE, debe reportarse como indeterminado, no forzar conclusión.

---

## DECISIÓN FINAL FASE 6 (aprobada por investigador, 2026-08-20)

**Un solo estudio integrado**, no tres papers separados. Título de trabajo: *Mortalidad por TCE en motociclistas en Colombia, 2015-2024: tendencia nacional, desigualdad territorial y comparabilidad de las estadísticas vitales.*

Tres RQ dentro del mismo estudio:
- **RQ1 (descriptivo/ecológico):** tendencia nacional 2015-2024 + heterogeneidad territorial departamental de mortalidad por TCE en motociclistas.
- **RQ2 (asociacional multivariable/multinivel):** entre motociclistas con trauma craneano, factores asociados a desenlace fatal (usando split fatal/no-fatal de Medicina Legal como outcome de gravedad).
- **RQ3 (metodológico):** documentar el quiebre de cobertura DANE 2022 y la validación cruzada DANE↔Medicina Legal como advertencia para investigación con estadísticas vitales en LMIC.

**Techo de inferencia CONFIRMADO:** descriptivo + asociacional + ecológico/multinivel. **NO causal.** Verificado (2026-08-20) que no existe shock de política vial limpio 2015-2024: Ley 2251/2022 no tiene mecanismo (solo placa en casco, no uso); restricciones de parrillero son endógenas (motivadas por crimen), intermitentes y costosas de recolectar → no habilitan cuasi-experimento válido. Registrado en DECISIONS.md (D002).

**ML predictivo clínico DESCARTADO:** sin severidad clínica (Glasgow/UCI), un modelo predeciría topografía, no pronóstico → complejidad decorativa prohibida por CLAUDE.md secc. 21.
