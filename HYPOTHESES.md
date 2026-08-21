# HYPOTHESES.md

Registro pre-especificado de hipótesis (antes de ejecutar análisis principal). Confirmatorio vs exploratorio marcado explícitamente (CLAUDE.md secc. 23).

## H1 — Tendencia temporal (RQ1) — CONFIRMATORIO
- **Hipótesis:** la mortalidad por TCE en motociclistas (serie Medicina Legal, estable) muestra variación temporal 2015-2024, con un aumento en el periodo post-2020.
- **Variables:** outcome = muerte de motociclista con trauma craneano (Med. Legal `s65h-7665`); tiempo = año.
- **Análisis previsto:** serie anual + modelo de tendencia (Poisson/negative binomial sobre conteos con denominador poblacional DANE).
- **Resultado:** [PENDIENTE DE EJECUCIÓN]
- **Soporte/no soporte:** [PENDIENTE]

## H2 — Desigualdad territorial (RQ1) — CONFIRMATORIO
- **Hipótesis:** existe heterogeneidad departamental en la tasa de mortalidad por TCE en motociclistas que excede la esperada por azar/tamaño muestral.
- **Variables:** tasa = casos Med. Legal / población DANE por departamento-año; nivel = departamento.
- **Análisis previsto:** modelo multinivel (año dentro de departamento) o Poisson con efectos aleatorios de departamento; prueba de heterogeneidad; posible mapa de SMR bayesiano empírico.
- **Resultado:** [PENDIENTE]

## H3 — Factores asociados a letalidad (RQ2) — CONFIRMATORIO
- **Hipótesis:** entre motociclistas con trauma craneano, la zona rural, la mayor edad y ciertos tipos de colisión se asocian con mayor probabilidad de desenlace fatal.
- **Variables:** outcome = fatal (dataset `s65h-7665`) vs no-fatal (`ezhf-hscf`); predictores = edad, sexo, zona urbano/rural, rol (conductor/pasajero), clase de accidente, objeto de colisión, departamento.
- **Análisis previsto:** regresión logística multivariable; versión multinivel con departamento como nivel 2.
- **Sesgo pre-declarado:** el dataset no-fatal solo captura lesionados examinados por Medicina Legal (subconjunto) → posible sesgo de selección en el denominador de "no-fatal". Se analizará como amenaza a la validez, no se ocultará.
- **Resultado:** [PENDIENTE]

## H4 — Quiebre de comparabilidad DANE (RQ3) — CONFIRMATORIO (ya con evidencia parcial de FASE 3)
- **Hipótesis:** la serie DANE-EEVV 2015-2024 no es directamente comparable en el tiempo por el cambio de cobertura de 2022 (integración Registraduría); ignorarlo infla la tendencia estimada.
- **Análisis previsto:** comparación DANE vs Med. Legal ya ejecutada (FASE 3); cuantificar el sesgo con/sin dummy 2022; mostrar sensibilidad de la tendencia H1 según fuente.
- **Resultado:** evidencia preliminar YA OBTENIDA (convergencia post-2022, ver `results/exploratory/linkage_audit_dane_medlegal.json`); falta formalizar.

## Exploratorio (no confirmatorio, declarado como tal)
- Diferencias por sexo, grupo etario específico, franja horaria, mecanismo de colisión: se explorarán pero se reportarán como **exploratorios**, con corrección por multiplicidad (FDR) si se hacen múltiples pruebas.
