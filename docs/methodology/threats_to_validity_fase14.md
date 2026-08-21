# FASE 14 — Threats to validity / Falsification checks

Consolidado de todos los chequeos de robustez y falsación ejecutados en FASES 1-13. Ninguno se ejecutó para confirmar una conclusión ya decidida — cada uno se hizo antes de aceptar el resultado correspondiente.

## 1. Definición de TCE (sensibilidad de medición)
**Chequeo:** replicar la tendencia nacional (H1) con la definición alternativa DANE-S06 en vez de Medicina Legal-topográfico.
**Resultado:** DANE-S06 → IRR/año = 1,092 (IC95% 1,039-1,147); Medicina Legal → IRR/año = 1,041 (IC95% 1,018-1,065). **Misma dirección, magnitud DANE ~2,2x mayor.**
**Interpretación:** consistente con el quiebre de cobertura DANE 2022 (D001) — DANE infla la tendencia. Ambas fuentes confirman dirección positiva, lo que da soporte a que el aumento es parcialmente real, pero **la magnitud reportada en el manuscrito debe basarse en Medicina Legal** (fuente primaria, más estable) y declarar el rango DANE solo como sensibilidad.

## 2. Ventana temporal (¿tendencia sostenida o concentrada?)
**Chequeo:** IRR/año restringido a 2015-2021 (excluyendo el salto reciente).
**Resultado:** IRR/año = 1,008 (prácticamente nulo) vs. 1,041 en la serie completa.
**Interpretación:** el aumento NO es una tendencia lineal sostenida — está concentrado en 2022-2024. Debe reportarse así explícitamente, no como "aumento constante desde 2015".

## 3. Artefacto de captura en el modelo de letalidad (H3)
**Chequeo:** año como covariable dio OR implausible (1,22/año); se investigó la distribución de N fatal/no-fatal por año antes de aceptar el coeficiente.
**Resultado:** N no-fatal cae de ~200/año a ~60-90/año mientras N fatal sube — **artefacto de captura decreciente**, no cambio real de letalidad.
**Acción:** `year_c` excluido de interpretación epidemiológica en H3; se verificó estabilidad de sexo/zona/rol entre 2015-2019 y 2020-2024 (estables, con zona variando en magnitud pero no en dirección) antes de reportarlos como robustos.

## 4. Especificación del modelo de conteo (H1)
**Chequeo:** un primer ajuste NegBin usó `alpha=1.0` fijo (default de statsmodels GLM) en vez de estimado por MLE.
**Resultado:** se detectó y corrigió — el alpha real estimado es 0,011 (mucho menor dispersión real de la que sugería el chequeo naive con solo 10 puntos anuales/8 gl).
**Lección:** el chequeo de sobredispersión a nivel nacional (n=10 años) es poco fiable por pocos grados de libertad; no usar como único criterio.

## 5. Heterogeneidad geográfica (H2) — limitación de método declarada
Efecto fijo de departamento usado como proxy computacional, no GLMM bayesiano pleno con shrinkage. La significancia (LR=8947, p≈0) es robusta a este approach, pero las tasas puntuales por departamento (FASE 12) no tienen corrección de shrinkage — departamentos con N pequeño pueden tener tasas ruidosas. **Pendiente para versión final:** modelo bayesiano jerárquico con shrinkage si el manuscrito reporta tasas específicas por departamento.

## 6. Calidad de datos categóricos (RQ2)
Tres inconsistencias textuales detectadas y corregidas en el pipeline antes de modelar (Bogotá con 2 rótulos, "Centro poblado" con/sin espacio, typo "COnductor") — de no corregirse, habrían fragmentado categorías y sesgado los efectos estimados hacia el nulo (dilución, no inflación).

## 7. Linkage — recordatorio de límite estructural (de FASE 3)
Todo lo anterior es válido a nivel ecológico/individual-dentro-de-fuente. **No existe linkage individual entre DANE y Medicina Legal** (D001, FASE 3) — nunca se combinan registros individuo a individuo entre ambas fuentes; la comparación siempre es agregada (año/departamento).

## Conclusión de FASE 14
Ningún hallazgo confirmatorio (H1-H3) se sostiene sin matices — todos tienen una limitación declarada y cuantificada, no oculta. Esto es consistente con el principio de falsación del proyecto: se buscó activamente evidencia que debilitara cada conclusión antes de aceptarla, y en dos casos (H1 alpha, H3 year_c) esa búsqueda cambió el resultado reportado.
