# DECISIONS.md — Decisiones técnicas, metodológicas y de diseño

> Registro consolidado. El archivo raíz `DECISIONS.md` contiene la versión original de D001; este documento lo amplía y agrega las demás.

---

## D001 — 2026-08-20 — Medicina Legal como fuente primaria de tendencia; DANE para codificación CIE-10
- **Contexto:** la auditoría de linkage (FASE 3) mostró que DANE subestimaba a Medicina Legal en 2015–2021 (−10% a −25%) y convergió a <2% desde 2022.
- **Decisión:** usar Medicina Legal (`s65h-7665`) como serie primaria de tendencia; DANE-EEVV para la definición CIE-10 de TCE (S06).
- **Alternativas consideradas:** usar DANE tal cual como serie temporal (descartada: infla el crecimiento 2021–2022 mezclando aumento real con mejora de cobertura).
- **Razón:** verificado con fuente primaria oficial DANE que desde 2022 se integran registros de la Registraduría antes no captados vía RUAF-ND (cambio de cobertura, no de mortalidad real).
- **Impacto:** si se usa DANE en tendencia, requiere dummy de corte 2022 o restringir a 2022–2024. La variable TCE-S06 sigue válida transversalmente.

## D002 — 2026-08-20 — Techo de inferencia: descriptivo/asociacional/ecológico, NO causal
- **Contexto:** se buscó un shock de política vial 2015–2024 para habilitar diseño cuasi-experimental.
- **Decisión:** limitar todas las afirmaciones a descriptivo, asociacional y ecológico/multinivel.
- **Alternativas consideradas:** (a) Ley 2251/2022 (casco) — descartada: solo cambia requisito de placa en casco, no el uso; sin mecanismo ni grupo control. (b) Restricciones municipales de parrillero — descartadas: endógenas (motivadas por crimen), intermitentes, costosas de recolectar.
- **Razón:** ningún instrumento identifica causalmente el efecto de seguridad vial; forzarlo violaría el principio de identificación.
- **Impacto:** RQ2 es asociacional (OR, no efecto causal). Sin ML clínico predictivo (sin severidad clínica → predeciría topografía, no pronóstico).

## D003 — 2026-08-20 — Estudio integrado de 3 RQ en un solo paper
- **Contexto:** A (tendencia), B (territorial), C (COVID) por separado eran demasiado delgadas para Q2.
- **Decisión:** un solo estudio con RQ1 (tendencia+territorial), RQ2 (letalidad), RQ3 (comparabilidad DANE como contribución metodológica). COVID entra como corte dentro de la serie, no como pregunta separada.
- **Razón:** convierte la debilidad (todo descriptivo/ecológico + artefacto de datos) en fortaleza (lección de calidad de datos para vigilancia con estadísticas vitales en LMIC).
- **Impacto:** define la estructura del manuscrito.

## D004 — 2026-08-20 — Doble definición operacional de TCE (triangulación)
- **Decisión:** TCE primario = "Trauma craneano" topográfico (Medicina Legal); TCE de sensibilidad = CIE-10 S06 (DANE).
- **Alternativas consideradas:** usar solo una definición (descartada: ninguna fuente abierta tiene severidad clínica; una sola definición es frágil).
- **Razón:** si ambas coinciden, la conclusión es más robusta; si difieren, se reporta como limitación. Definición en `docs/definitions/TCE_definition.md`.
- **Impacto:** análisis de sensibilidad incorporado; limitación de subcaptura ("Politraumatismo") declarada.

## D005 — 2026-08-20 — Revista objetivo: Safety (MDPI, Q2)
- **Decisión:** dirigir el manuscrito a Safety.
- **Alternativas consideradas:** Epidemiologia (más rápida ~36 vs ~41 días, pero exigiría reenfocar en lo metodológico); IJERPH (descartada: fuera de Web of Science desde 2023); Trauma Care (descartada: sin Q2 confirmado).
- **Razón:** el centro de gravedad del paper es seguridad vial; el match temático supera la ventaja marginal de velocidad de Epidemiologia.
- **Impacto:** manuscrito escrito con estructura y encuadre de Safety.

## D006 — 2026-08-21 — RUNT como análisis de sensibilidad de exposición, NO como denominador primario
- **Contexto:** el hallazgo de desigualdad territorial (RQ1) era vulnerable a la objeción "las tasas por 100k hab confunden mortalidad con densidad de motos". Se obtuvo el parque de motos por depto (RUNT2.0 `u3vn-bdcy`, snapshot 2026-07).
- **Decisión:** usar la tasa por-moto como triangulación de robustez; mantener población como denominador primario.
- **Evidencia:** Spearman ranking hab vs moto = 0,34 (n=32). La discordancia está dominada por artefactos de RUNT (cuenta por matrícula, no circulación): La Guajira (flota informal fronteriza subcontada) salta a 1º por-moto; Bogotá↔Cundinamarca se distorsionan por municipios-matriculadero. 6 deptos robustos en ambos denominadores (Casanare, Arauca, Cesar, Huila, Tolima, San Andrés).
- **Alternativas descartadas:** (a) reemplazar denominador por RUNT (descartada: cambia un sesgo por otro peor); (b) mencionar RUNT solo en Discusión sin tabla (descartada: desaprovecha la robustez demostrada). No existe conteo de motos por circulación en datos abiertos → **NO DISPONIBLE**.
- **Impacto:** Métodos RQ1, Resultados 3.2, Limitación 7, Fig S1, Tabla S1. Refuerza que el exceso de Casanare/Arauca es denominador-independiente.

## D008 — 2026-08-21 — Revisiones tras referee report simulado (Major Revision, Safety Q2)
- **Contexto:** referee report crítico (`review/referee_report_TBI_motorcyclists_Safety.md`). Se validó cada punto con datos/código reales; algunos correctos, otros discutibles/erróneos.
- **Decisiones ejecutadas (script `09d_referee_revisions.py`, outputs en `results/robustness/referee_revisions.json`):**
  - **M1 (correcto):** el modelo de tendencia usaba fatalidades totales, no TBI. Añadido modelo TBI-específico (IRR 1.035, IC 1.009–1.062; 2015–2021 IRR 1.000). Rastrea al total (1.041) → refuerza el share estable. Tabla 2 ahora por outcome. Territorial: rho total-vs-TBI = 0.92 → patrón no depende del numerador (frase en 3.2).
  - **M2 (concern válido, receta del referee frágil):** rechazada la ITS con interacción (n=10, 3 puntos post-quiebre). En su lugar: IRR DANE 2015–2021 = 0.989 vs MedLegal 2015–2021 = 1.008 → ambas planas y convergentes; la divergencia de serie completa es el salto de nivel 2022. Integrado a Métodos RQ3 y Resultados 3.4.
  - **M3 (correcto):** modelo Bayesiano es `BinomialBayesMixedGLM.fit_vb()` (Bayes variacional, NO MCMC → no hay R-hat/ESS). Documentado con veracidad (priors por defecto, aproximación de campo medio) y degradado a sensibilidad; Tabla S4 en suplementario.
  - **M4 (correcto en sustancia, aritmética del referee mal):** brecha real 40,318−40,307 = **11** registros sin departamento (no 17). Nota al pie en Tabla S1.
  - **M5 (correcto):** eliminadas refs huérfanas [4] (gatos) y [42] (neurocirugía espinal); renumeración en cascada 50→48 (script verificó 0 huérfanas, 0 citas colgantes).
  - **M6, m1, m3 (correctos):** "pre-registered"→"prespecified"; IRB "aggregated"→"individual-level microdata + aggregated pop stats"; 4.4 "demographic risk patterns"→"composition of fatalities".
  - **m2, m4 (recomendado/opcional):** abstract RUNT suavizado (rho=0.34 explícito); caveat de cobertura Medicina Legal en 4.5.
- **Figuras (petición PI):** las 4 PNG regeneradas en inglés (`10_figures.py` reescrito; figS ahora también en script).
- **Impacto:** manuscrito `manuscript_safety_final_EN.md` actualizado íntegro. Cierra la brecha título↔modelo (M1) que era el riesgo #1 de rechazo.

## D007 — 2026-08-21 — RQ2 reencuadrado: perfil descriptivo de fatales (primario) + case-fatality forense (secundario, con bounding)
- **Contexto:** el denominador no-fatal de Medicina Legal está seleccionado (solo lesionados que llegan a valoración forense) → "letalidad 91,6%" es artefacto y los OR fatal-vs-nofatal pueden estar sesgados. Riesgo de rechazo si se presenta como letalidad poblacional.
- **Decisión:** (1) pilar PRIMARIO = perfil descriptivo de los 13.264 fatales (necropsia obligatoria → captación casi completa → sin sesgo de selección); (2) los OR se conservan como SECUNDARIO con estimando renombrado ("proporción fatal entre casos forenses"), reportando solo dirección; (3) bounding de selección: bajo letalidad verdadera igual, un OR se explicaría por razón de captación no-fatal = 1/OR.
- **Evidencia:** perfil — 85,7% hombres, 48,1% en 20–34, 81,4% conductores. Bounding — urbano 7,9× (frágil), sexo 3,1×, rol 2,5× (robustos).
- **Alternativas descartadas:** (a) mantener letalidad poblacional (descartada: artefacto, motivo de rechazo); (b) retirar RQ2 por completo (descartada: el perfil de fatales es contenido limpio y valioso); (c) conseguir denominador no-fatal completo vía RIPS individual restringido (NO DISPONIBLE sin solicitud a SISPRO).
- **Impacto:** Abstract, RQ2 (Sec 2), Métodos RQ2, Resultados 3.3, Limitación selección, Discusión, Conclusión, Tablas S2/S3. Convierte el mayor pasivo del paper en análisis defendible.
