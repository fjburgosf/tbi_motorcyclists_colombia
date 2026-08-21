# ANALYSIS_LOG.md

## 2026-08-20 — Auditoría de valores DANE-EEVV 2024 (script 03)

- **Script:** `scripts/03_inspect_data.py`
- **Dataset:** `data/raw/dane_eevv_2024/BD-EEVV-Defuncionesnofetales-2024/BD-EEVV-Defuncionesnofetales-2024.dta`
- **Muestra:** N=275.778 defunciones no fetales, 2024
- **Método:** regex sobre `C_BAS1` (V20-V29) y `CAUSA_MULT` (S06), completitud de geografía del hecho
- **Output:** `results/exploratory/audit_dane_eevv_2024_tce_moto.json`, `results/exploratory/defunciones_motociclistas_2024_dane.csv`
- **Resultado:** 5.156 muertes de motociclistas (causa básica V20-V29); 2.176 (42,2%) con S06 (TCE) como causa asociada; geografía del hecho 99,94% poblada en el subgrupo.

## 2026-08-20 — Panel completo DANE-EEVV 2015-2024 (script 03b)

- **Script:** `scripts/03b_inspect_data_panel_2015_2024.py`
- **Datasets:** 10 archivos anuales `data/raw/dane_eevv_{2015..2024}/.../nofetal*.dta`
- **Método:** mismo enfoque que script 03, pero con manejo explícito de dos estructuras distintas de "causa asociada" (Era A 2015-2018 sin `CAUSA_MULT`, Era B 2019-2024 con `CAUSA_MULT`); ver `DATA_SOURCES.md` para detalle
- **Output:** `results/exploratory/panel_dane_eevv_2015_2024_tce_moto.csv`, `.json`
- **Resultado:** panel de 10 años con N total, N moto, N S06 asociado, N cruce, % geografía poblada. Ver tabla en `DATA_SOURCES.md`.
- **Hallazgo a validar (NO interpretado como causal ni confirmado como tendencia real):** el número de muertes de motociclistas (V20-V29) casi se duplica entre 2021 (3.508) y 2022 (5.081), y el % de esas muertes con S06 asociado sube de ~27-33% (2015-2021) a 36-42% (2022-2024). Posibles explicaciones alternativas no descartadas: (a) aumento real de siniestralidad motociclística pos-pandemia; (b) mejora en la completitud de captura de causas múltiples en el certificado de defunción (RUAF-ND) en años recientes; (c) cambio de metodología/codificación DANE. **Requiere verificación adicional (completitud histórica de CAUSA_MULT, comparación con Medicina Legal y ANSV) antes de cualquier afirmación descriptiva en el manuscrito.**

## 2026-08-20 — Auditoría de linkage DANE ↔ Medicina Legal (script 06, FASE 3)

- **Script:** `scripts/06_link_data.py`
- **Fuentes:** panel DANE-EEVV 2015-2024 (ya construido) vs. Medicina Legal `s65h-7665` (API Socrata en vivo, `medio_de_desplazamiento_o_transporte='Motocicleta'`)
- **Método:** (1) verificación de formato de código geográfico (DIVIPOLA 5 dígitos) en ambas fuentes; (2) comparación año a año de conteos de muertes de motociclistas
- **Output:** `results/exploratory/linkage_audit_dane_medlegal.json`, `.csv`

**Resultado — GATE 3 (linkage):**
- Linkage **individual**: IMPOSIBLE (sin identificador de persona compartido, verificado por diccionarios).
- Linkage **geográfico**: POSIBLE y verificado (ambas usan código DIVIPOLA 5 dígitos; ej. Medicina Legal `codigo_dane_municipio='50223'` = depto 50 Meta + municipio 223, mismo esquema que `COD_DPTO`+`COD_MUNIC` de DANE).
- Linkage **temporal**: POSIBLE a nivel anual en ambas; Medicina Legal permite granularidad diaria, DANE-EEVV solo mensual.
- Linkage **institucional**: no aplica (sin código de institución compartido).
- **Conclusión: solo linkage ECOLÓGICO (año × geografía), nunca individual. Cualquier análisis conjunto debe declarar el riesgo de falacia ecológica.**

**HALLAZGO NO ANTICIPADO (falsación/robustez, sección 8 y 22 CLAUDE.md):**
DANE **subestima sistemáticamente** las muertes de motociclistas frente a Medicina Legal en 2015-2021 (brecha de -9,6% a -24,9%), pero **converge casi exactamente** en 2022-2024 (diferencia de solo 0,1% a 1,5%). Al mismo tiempo, la serie de Medicina Legal —fuente independiente, con metodología presumiblemente estable— **también muestra un salto propio en 2021** (+41,5% interanual, 3.114→4.405), aunque menos extremo que el de DANE (+33,0%) y seguido de +13,6% en 2022 (vs. +44,8% en DANE).

**Interpretación provisional (NO confirmada, requiere más evidencia antes de manuscrito):**
1. El aumento de muertes de motociclistas en 2021-2022 parece ser en parte un fenómeno **real**, porque aparece de forma independiente en Medicina Legal.
2. Pero la magnitud del salto en DANE está probablemente **inflada por una mejora en la completitud de captura** de muertes por causa externa (posible cambio en certificación/codificación RUAF-ND desde 2022), dado que el histórico "descuento" de DANE respecto a Medicina Legal desaparece justo en ese punto.
3. **Implicación para el diseño:** un estudio de tendencia 2015-2024 con DANE como única fuente sería vulnerable a confundir mejora de completitud con aumento real de mortalidad. **Medicina Legal es probablemente la serie más estable para analizar tendencia**, y DANE debe usarse principalmente por su codificación CIE-10 (TCE vía S06), no como serie temporal de conteos.

Pendiente: consultar metadatos/notas metodológicas oficiales de DANE sobre cambios en el proceso de certificación de causa externa 2021-2022 antes de zanjar esta interpretación.

## 2026-08-20 — RESUELTO: causa del quiebre de completitud DANE 2022 (fuente primaria verificada)

**Fuente:** ficha de catálogo oficial DANE, sección "Recolección de Datos" — https://microdatos.dane.gov.co/index.php/catalog/807/study-description (consultado 2026-08-20).

**Cita verbatim:**
> "En la base de datos del año 2022 se integraron directamente los hechos vitales registrados en las bases de datos del registro civil de nacimiento y defunciones de la Registraduría Nacional del Estado Civil, y que no aparecen en el RUAF-ND por cuanto no tuvieron contacto con el sector salud."

**Interpretación (ahora confirmada, no especulativa):** desde la base 2022, DANE integra directamente los registros de la Registraduría Nacional que antes NO se capturaban vía RUAF-ND (por no tener contacto con el sector salud). Esto **confirma la hipótesis** de que la convergencia DANE↔Medicina Legal desde 2022 (ver auditoría de linkage arriba) refleja una **mejora real de completitud/cobertura en DANE**, no necesariamente (o no solo) un aumento real de mortalidad por accidentes de motocicleta.

**Consecuencia metodológica para el diseño (decisión, no solo observación):**
- La serie DANE 2015-2024 **NO es directamente comparable en el tiempo** sin ajustar por este quiebre de cobertura — un análisis de tendencia que use DANE tal cual subestimaría los años 2015-2021 relativo a 2022-2024 y generaría una falsa apariencia de "aumento" que en parte es artefacto de captura.
- **Medicina Legal (`s65h-7665`) es la serie más adecuada para analizar tendencia temporal 2015-2024**, por methodology estable y no depender de contacto con el sector salud.
- DANE sigue siendo la fuente preferida para la **definición CIE-10 de TCE (S06)**, pero su uso en análisis de tendencia temporal requiere: (a) restringir el panel a 2022-2024 (post-quiebre), o (b) tratar el quiebre 2022 explícitamente como corte estructural (dummy de periodo) en cualquier modelo, o (c) usarlo solo de forma transversal (no de tendencia).

Esto se registra como **DECISIÓN METODOLÓGICA** (ver DECISIONS.md).

## 2026-08-20 — Construcción del pipeline (FASE 10, scripts 04-05)

- **04_clean_data.py:** filtra Medicina Legal a motociclistas. Fatal: 73.403→40.318; No-fatal: 342.796→196.330. **Verificación cruzada:** 40.318 = suma exacta de la serie anual ya auditada en FASE 1 (3.234+...+5.152) → confirma que no hay pérdida/duplicación de filas.
- **05_construct_variables.py:**
  - Denominadores poblacionales DANE (departamental, 2015-2024, series 2005-2017 + 2018-2050 combinadas): 330 filas (33 deptos × 10 años), sin duplicados.
  - `rq1_panel_dept_year.csv`: 328 filas depto-año con tasas de mortalidad y % TCE. 6 filas sin población emparejada = los 11 casos (de 40.318, 0,03%) con `codigo_dane_departamento="999"` ("Sin información") en el dato original de Medicina Legal — NO es error de código, es missing real y documentado, se excluye de análisis por tasa pero se reporta en descriptivos de N.
  - `rq2_individual_moto_tce.csv`: 14.487 casos de motociclistas con TCE (13.264 fatales, 1.223 no fatales). **Consistencia:** 13.264/40.318 = 32,9% de letalidad-TCE entre fatales, mismo orden de magnitud que el 42,2% (2024) hallado con la definición DANE S06 — dos definiciones independientes convergen razonablemente.
- **Pendiente antes de modelar:** decidir tratamiento de "Sin información" como categoría propia vs. missing en covariables de RQ2 (no imputar sin justificar).

## 2026-08-20 — FASE 12: exploratorio + 3 correcciones de calidad de datos

- % TCE entre motociclistas fatales es **estable (30-36%) 2015-2024**, sin tendencia — el crecimiento en conteo absoluto no es crecimiento en letalidad-TCE relativa.
- Corregidos en pipeline (`05_construct_variables.py`), no en output: (1) Bogotá partida en 2 filas por cambio de rótulo textual 2017 ("Bogotá D.C."→"Bogotá, D.C.", mismo `cod_dpto`, sin duplicar registros) → unificado por código; (2) "Centro poblado(...)" con/sin espacio → colapsado; (3) "COnductor" (typo, n=1) → fusionado.
- Letalidad bruta: rural 98,2% vs urbano 87,1%; hombre 93,4% vs mujer 81,9%; conductor 93,2% vs pasajero 84,9%.

## 2026-08-20 — FASE 13: análisis principal (script 08)

**H1 (tendencia nacional):** NegBin con alpha estimado por MLE (no fijado — un primer intento con GLM NegativeBinomial usó alpha=1.0 por defecto, se descartó por inválido). IRR/año = **1,041 (IC95% 1,018-1,065), p<0,01**. Robustez restringida a 2015-2021: IRR/año = 1,008 (prácticamente nulo) → **el crecimiento está concentrado en 2022-2024**, no es una tendencia lineal sostenida desde 2015. Esto es consistente con el salto que ya vimos en Medicina Legal en FASE 3 (fuente independiente de DANE, por tanto no es solo el artefacto de cobertura D001) — refuerza que parte del aumento reciente es real.

**H2 (heterogeneidad departamental):** LR=8947, p≈0 — heterogeneidad muy significativa, consistente con el ranking descriptivo de FASE 12. **Limitación declarada:** se usó efecto fijo de departamento como proxy computacional (no un GLMM bayesiano pleno); interpretar junto con las tasas descriptivas, no como estimación con shrinkage.

**H3 (letalidad):** Logística multivariable y multinivel (depto como efecto aleatorio, SD=0,66, IC 0,52-0,84 → heterogeneidad departamental real también en letalidad). Hallazgos estables entre ambos modelos: mujer OR≈0,45-0,50 (menor letalidad que hombre), zona urbana OR≈0,13-0,24 (menor letalidad que rural — protector), pasajero OR≈0,58-0,59 (menor letalidad que conductor).

**HALLAZGO DE INTEGRIDAD (no ocultado):** `year_c` mostró OR=1,22/año (implausible, ~7x en una década). Se investigó ANTES de reportarlo: el N de casos no-fatales cae de ~200/año (2015-2018) a ~60-90/año (2020-2024) mientras el N fatal sube — es un **artefacto de captura decreciente de casos no-fatales por Medicina Legal**, análogo al quiebre DANE (D001), NO evidencia de aumento real de letalidad. Se verificó estabilidad de los coeficientes sustantivos entre 2015-2019 y 2020-2024: sexo y rol estables (cambios <0,1 en OR); zona cambia de magnitud (0,09→0,24) pero mantiene dirección. **Conclusión: los hallazgos de sexo/zona/rol son robustos; el coeficiente de year_c se excluye de cualquier interpretación epidemiológica.**
