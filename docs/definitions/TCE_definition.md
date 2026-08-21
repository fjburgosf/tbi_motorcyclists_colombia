# Definición operacional de TCE (trauma craneoencefálico)

## Definición primaria (Medicina Legal — usada para RQ1, RQ2)
`diagnostico_topografico_de_la_lesion_fatal` o `..._no_fatal` = **"Trauma craneano"**, en víctimas con `medio_de_desplazamiento_o_transporte = "Motocicleta"`.
**Limitación declarada:** es región topográfica, no diagnóstico clínico CIE-10; probablemente subestima TCE oculto dentro de "Politraumatismo" (mayoría de casos). No permite gradación de severidad.

## Definición de sensibilidad (DANE-EEVV — usada para RQ3 y robustez)
CIE-10 **S06** (traumatismo intracraneal) en causa asociada (`CAUSA_MULT` 2019-2024; campos `C_ANT*/C_DIR*/C_PAT*/C_MCM1` 2015-2018), en defunciones con causa básica `C_BAS1 ∈ V20–V29` (motociclista).
**Verificado con datos reales** (FASE 1-3): 2.176 casos en 2024 (42,2% de motociclistas fallecidos), serie completa 2015-2024 en `results/exploratory/panel_dane_eevv_2015_2024_tce_moto.csv`.

## Por qué dos definiciones (no es inconsistencia, es triangulación)
Ninguna fuente pública tiene Glasgow ni severidad clínica (ver `tce-severity-not-in-open-data` en memoria del proyecto). Usar ambas definiciones permite análisis de sensibilidad: si los resultados son consistentes bajo las dos, la conclusión es más robusta; si difieren, se reporta como limitación explícita, no se oculta.

## Explícitamente NO cubierto
- TCE leve no fatal que no llega a valoración forense.
- Gradación leve/moderado/grave (requiere RIPS o registro de trauma institucional — ver `tce-severity-not-in-open-data`).
