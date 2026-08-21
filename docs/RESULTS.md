# RESULTS.md — Resultados y conclusiones provisionales

**Última actualización:** 2026-08-20. Todos los valores provienen de outputs ejecutados (`results/`, `tables/`). Ninguno transcrito de memoria.

## RQ1 — Tendencia nacional (H1)
- Muertes de motociclistas (Medicina Legal): 3.234 (2015) → 5.152 (2024).
- **% TCE entre fatales: estable, 30,5–35,7%** (sin tendencia; el crecimiento es de volumen, no de proporción TCE).
- Tendencia (NegBin, α MLE): **IRR = 1,041/año (IC95% 1,018–1,065; p = 0,0005)**.
- Robustez 2015–2021: IRR = 1,008 (IC95% 0,973–1,044; **p = 0,667, no significativo**) → el aumento está **concentrado en 2022–2024**, no es lineal sostenido.
- Fuente: `tables/table2_h1_tendencia.csv`, `results/exploratory/rq1_serie_nacional.csv`, Figura 1.

## RQ1 — Desigualdad territorial (H2)
- Departamento altamente significativo: **LR = 8947,2; df = 32; p < 0,001**.
- Tasas medias 2015–2024 (×100.000 hab.): **Casanare 23,1; Arauca 21,6; San Andrés 20,3** (altas) vs **Chocó 2,6; Bogotá 2,7; Vaupés 2,8** (bajas). ~9× de diferencia.
- Fuente: `results/exploratory/rq1_tasas_departamento.csv`, `results/primary/h2_*.txt`, Figura 2.
- **Sensibilidad denominador (RUNT, resuelto):** tasas re-expresadas por 10.000 motos activas (RUNT2.0 `u3vn-bdcy`, snapshot 2026-07). Spearman ranking hab vs moto = **0,34** (n=32) → ranking global sensible al denominador, PERO la divergencia son artefactos de registro RUNT (La Guajira flota informal; Bogotá↔Cundinamarca matriculadero), no señal. **Robustos alto en AMBOS denominadores: Casanare, Arauca, Cesar, Huila, Tolima, San Andrés.** Casanare/Arauca siguen liderando → exceso NO es densidad de motos. Vaupés sin RUNT. Población se mantiene como denominador PRIMARIO; por-moto es triangulación. Fuente: `scripts/09b_runt_sensitivity.py`, `tables/tableS_runt_sensibilidad.csv`, `results/robustness/rq1_runt_sensibilidad.json`, `figures/figS_runt_sensibilidad.png`.

## RQ2 — Perfil de fatalidades (primario) + case-fatality forense (secundario)
**REENCUADRADO (2026-08-21, D007) para blindar sesgo de selección.**
- **PILAR PRIMARIO — perfil descriptivo de los 13.264 fatales con TCE** (estrato casi completo, sin muestra no-fatal → sin sesgo de selección):
  - Sexo: **85,7% hombres**, 14,3% mujeres.
  - Edad: **48,1% en 20–34 años** (modal 20–24 = 19,4%); cola a mayores.
  - Rol: **81,4% conductores**, 18,6% pasajeros.
  - Zona: 54,1% urbano, 37,7% rural, 8,2% ND.
  - Fuente: `tables/tableS_rq2_perfil_fatales.csv`.
- **SECUNDARIO — case-fatality entre casos forenses** (estimando renombrado, NO letalidad poblacional; 91,6% = mezcla de casos forenses):
  - OR logística: Mujer 0,48 (0,40–0,56); Urbano 0,13 (0,10–0,16); Pasajero 0,59 (0,50–0,69). `year_c` excluido (artefacto).
  - **Bounding de selección** (razón de captación no-fatal que anularía el OR bajo letalidad verdadera igual): Urbano **7,9×** (el más frágil), Mujer 3,1×, Pasajero 2,5×. → sexo y rol robustos; urbano-rural sensible.
  - Multinivel: heterogeneidad departamental residual (posterior SD 0,66; IC 0,52–0,84).
  - Fuente: `tables/table3_h3_letalidad.csv`, `results/primary/h3_*.txt`, `tables/tableS_rq2_bounding_seleccion.csv`, `results/robustness/rq2_reframe.json`, Figura 3, script `09c_rq2_profile_bounding.py`.

## RQ3 — Comparabilidad DANE ↔ Medicina Legal
- DANE subestima a Med.Legal **−9,6% a −24,9% (2015–2021)**; converge a **<2% (2022–2024)**.
- Causa verificada (fuente primaria DANE): integración de registros Registraduría desde base 2022.
- Tendencia con definición DANE: IRR = 1,092/año (IC95% 1,039–1,147) ≈ **2,2× la de Med.Legal** → misma dirección, magnitud sensible a fuente.
- Fuente: `results/exploratory/linkage_audit_dane_medlegal.*`.

## Conclusiones provisionales
1. Aumento real de mortalidad de motociclistas concentrado post-2021 (aparece en dos fuentes independientes).
2. Desigualdad territorial marcada y persistente (sujeta a caveat de denominador).
3. Letalidad patronada por sexo, zona y rol (asociacional, con caveat de selección).
4. **Contribución metodológica:** el quiebre de cobertura DANE 2022 sesga tendencias si no se ajusta — advertencia cuantificada para investigación con estadísticas vitales en LMIC.

## Figuras y tablas
- `figures/fig1_tendencia_nacional.png`, `fig2_tasas_departamento.png`, `fig3_forest_letalidad.png`.
- `tables/table1_descriptivo.csv`, `table2_h1_tendencia.csv`, `table3_h3_letalidad.csv`.
