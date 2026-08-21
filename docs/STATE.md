# STATE.md — Estado operativo del proyecto

**Última actualización:** 2026-08-21

## Objetivo actual
Manuscrito de investigación reproducible sobre **mortalidad por TCE en motociclistas en Colombia, 2015–2024**, dirigido a **Safety (MDPI, Q2)**. Estudio integrado con 3 preguntas: RQ1 (tendencia + desigualdad territorial, descriptivo/ecológico), RQ2 (factores asociados a letalidad, asociacional), RQ3 (quiebre de comparabilidad DANE, metodológico). Techo de inferencia: descriptivo + asociacional + ecológico. **No causal.**

## Tareas completadas (FASES 1–16)
- FASE 1–3: auditoría de fuentes, variables y linkage. Datos descargados y verificados.
- FASE 4–6: estado del arte (PubMed + Scopus), gap identificado, 3 RQ definidas.
- FASE 7: plan estadístico (Python/statsmodels).
- FASE 10–12: pipeline de limpieza/construcción + análisis exploratorio.
- FASE 13–14: modelos principales (H1–H3) + falsación/robustez.
- FASE 15: 3 figuras + 3 tablas (generadas por código).
- FASE 16: borrador de manuscrito con 50 referencias verificadas (DOI reales).
- Revista objetivo decidida: Safety.

## Tareas en progreso
Ninguna en ejecución. El manuscrito está en borrador completo, pendiente de mejoras de calidad (ver abajo).

## Tareas pendientes (para publicación)
1. ~~[ALTA] Denominador RUNT por-moto para RQ1.~~ **HECHO (2026-08-21).** Resuelto como análisis de sensibilidad (no reemplazo): RUNT cuenta por matrícula, no circulación → contaminado. Robustos en ambos denominadores: Casanare/Arauca/Cesar/Huila/Tolima/San Andrés. Integrado a Métodos, Resultados 3.2, Limitación 7, Fig S1, Tabla S1. Ver DECISIONS D006.
2. ~~[ALTA] Degradar RQ2 a case-fatality forense.~~ **HECHO (2026-08-21, D007).** RQ2 reencuadrado: pilar primario = perfil descriptivo de 13.264 fatales (sin sesgo); secundario = case-fatality forense (estimando renombrado) + bounding de selección (urbano 7,9× frágil; sexo/rol robustos). Integrado a Abstract, RQ2, Métodos, Resultados 3.3, Limitación, Discusión, Conclusión, Tablas S2/S3.
3. ~~[MEDIA] Elevar RQ3 a co-protagonista.~~ **HECHO (2026-08-21).** Encuadre dual explícito ("dos contribuciones de peso comparable"): Abstract Conclusions (con dato concreto 9,2% vs 4,1%/año), Introducción (párrafo "RQ3 no es robustez ancilar sino aim co-primario"), Conclusión del paper. Título ya lo co-anunciaba.
4. **[CIERRE, EN PROGRESO]** Metadatos de envío (2026-08-21):
   - ✅ Autoría/afiliación: Francisco Burgos-Florez, Universidad Nacional de Colombia Sede La Paz, Cesar. Corresponsal fjburgosf@unal.edu.co.
   - ✅ Declaraciones MDPI FINALIZADAS: Funding = "no external funding"; COI = "no conflicts"; IRB = "not applicable" (datos secundarios anonimizados/públicos — confirmado contra política MDPI/Safety: la oficina editorial puede pedir aclaración pero "not applicable" es correcto); Informed Consent = "not applicable"; Data Availability completa; Author Contributions (autor único).
   - ✅ Estructura MDPI confirmada: Article + Título + Autoría + Abstract(285w) + Keywords + 1.Introduction / 2.Materials and Methods(2.1-2.5) / 3.Results(3.1-3.4) / 4.Discussion(4.1-4.5) / 5.Conclusions + Back Matter + References. Coincide con plantilla Safety.
   - ✅ Figuras/tablas verificadas: 4 PNG válidos (fig1-3 + figS1), 6 tablas CSV; números cuadran con el texto (IRR 1.041/1.008; OR 0.48/0.13/0.59; 91.6%; perfil fatales 85.7%/81.4%/54.1%). Todas citadas en el texto (Fig 1-3, S1; Tabla 1-3, S1-S3).
   - ✅ 4 referencias incompletas resueltas vía Crossref [10,20,26,49] (eran 4, no 6). Cero placeholders.
   - ✅ Abstract condensado a 285 palabras (límite 300).
   - ✅ Plantilla Safety auditada (`safety-template.dot` = docx; estructura y estilo de referencias extraídos).
   - ✅ Manuscrito final en inglés generado: `manuscript/manuscript_safety_final_EN.md` (2026-08-21). Cuerpo completo, tablas markdown en inglés (Tabla 1-3, S1-S4), figuras en inglés enlazadas.
   - ✅ **Revisiones referee report ejecutadas (2026-08-21, D008):** M1 (tendencia TBI-específica IRR 1.035 + territorial rho 0.92), M2 (DANE 2015-2021 vs MedLegal, rechaza ITS frágil), M3 (Bayes variacional documentado, Tabla S4), M4 (nota 11 registros), M5 (refs huérfanas [4][42] eliminadas, renumerado 50→48), M6/m1/m2/m3/m4. Script `09d_referee_revisions.py`. 4 figuras regeneradas en inglés (`10_figures.py`).
   - ⏳ PENDIENTE: (a) convertir las 50 referencias al estilo MDPI completo (revista abreviada + volumen + páginas) — PI lo hará; (b) confirmar coautores; (c) volcar a plantilla Safety .docx oficial.

## Fuentes de datos por explorar (registro/solicitud) — pendiente decisión del PI
- **RIPS vía SISPRO (MinSalud)** [ALTO impacto]: denominador no-fatal real (S06) + morbilidad/hospitalización → ataca sesgo RQ2. Restringido pero solicitable. NOTA: RIPS NO trae Glasgow.
- **Observatorio ANSV** [medio]: microdatos siniestros/víctimas moto.
- **GBD/IHME** [contexto]: carga TCE Colombia (modelado, cuenta gratis).
- GCS/severidad clínica nacional: **NO DISPONIBLE** en datos abiertos/registrables (solo RIPS restringido sin GCS, o registros institucionales cerrados).

## Problemas conocidos / errores pendientes
- **RQ2 sesgo de selección:** el denominador no-fatal (Medicina Legal) solo capta lesionados que llegan a valoración forense → "91,6% letalidad" es artefacto, no letalidad real. Los OR sexo/zona/rol pueden estar confundidos por referencia forense diferencial. **Riesgo de rechazo si no se aborda.**
- **`year_c` en RQ2:** excluido de interpretación (artefacto de captura decreciente de no-fatales). Documentado.
- **Definición TCE topográfica** ("Trauma craneano") subcaptura TCE oculto en "Politraumatismo" (216k). Mitigado con triangulación DANE-S06.
- **6 referencias** sin lista de autores completa (marcadas, no inventadas).

## Restricciones y supuestos
- No linkage individual entre DANE y Medicina Legal (solo ecológico, año × departamento DIVIPOLA).
- Sin severidad clínica (Glasgow/UCI) en datos abiertos → no viable estudio de gravedad clínica.
- Sin shock de política vial limpio 2015–2024 → no viable diseño causal/cuasi-experimental.
- Regla del proyecto: no inventar datos; marcar NO VERIFICADO cuando aplique.

## Próximos pasos concretos (retomar aquí)
1. **Descargar parque de motos por departamento (RUNT / datos.gov.co)** y recalcular tasas de RQ1 con denominador de motos. Actualizar `scripts/05_construct_variables.py` y `08_primary_model.py`, regenerar Figura 2 y Tabla 2.
2. Reescribir la sección RQ2 del manuscrito degradándola a case-fatality forense (o retirarla).
3. Ajustar abstract/conclusión para elevar RQ3.
4. Rematar metadatos de envío.
