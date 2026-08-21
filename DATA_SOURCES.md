# DATA_SOURCES.md

Registro de fuentes de datos auditadas y/o descargadas. Ver también `docs/` (pendiente de crear) y memoria del proyecto.

---

## 1. DANE — Estadísticas Vitales (EEVV), Defunciones no fetales, 2015–2024

- **Fuente:** DANE, microdatos.dane.gov.co (Catálogo Central de Datos)
- **Fecha de acceso:** 2026-08-20
- **Tipo de acceso:** Público, gratuito, descarga manual (portal exige reCAPTCHA — no automatizable)
- **Cobertura temporal:** 2015–2024 (10 archivos anuales, todos descargados)
- **Cobertura geográfica:** Nacional (Colombia), con desagregación departamento/municipio
- **Unidad de observación:** 1 fila = 1 defunción no fetal
- **Formatos disponibles:** CSV, DTA (Stata), SAV (SPSS)
- **Restricciones:** Ninguna para uso público estadístico; secreto estadístico (Ley 79/1993)

### Catálogos y archivos por año

| Año | Catalog ID | URL | Archivo local |
|---|---|---|---|
| 2015 | 475 | microdatos.dane.gov.co/index.php/catalog/475 | `data/raw/dane_eevv_2015/BD-EEVV-Defuncionesnofetales-2015/nofetal2015.dta` |
| 2016 | 519 | microdatos.dane.gov.co/index.php/catalog/519 | `data/raw/dane_eevv_2016/.../nofetal2016.dta` |
| 2017 | 652 (combinado 2017-2018) | microdatos.dane.gov.co/index.php/catalog/652 | `data/raw/dane_eevv_2017/.../nofetal2017.dta` |
| 2018 | 652 (combinado 2017-2018) | microdatos.dane.gov.co/index.php/catalog/652 | `data/raw/dane_eevv_2018/.../nofetal2018.dta` |
| 2019 | 696 | microdatos.dane.gov.co/index.php/catalog/696 | `data/raw/dane_eevv_2019/.../nofetal2019.dta` |
| 2020 | 732 | microdatos.dane.gov.co/index.php/catalog/732 | `data/raw/dane_eevv_2020/.../nofetal2020.dta` |
| 2021 | 775 | microdatos.dane.gov.co/index.php/catalog/775 | `data/raw/dane_eevv_2021/.../nofetal2021.stata` |
| 2022 | 807 | microdatos.dane.gov.co/index.php/catalog/807 | `data/raw/dane_eevv_2022/.../nofetal2022.dta` |
| 2023 | 876 | microdatos.dane.gov.co/index.php/catalog/876 | `data/raw/dane_eevv_2023/.../BD-EEVV-Defuncionesnofetales-2023.dta` |
| 2024 | 878 | microdatos.dane.gov.co/index.php/catalog/878 | `data/raw/dane_eevv_2024/.../BD-EEVV-Defuncionesnofetales-2024.dta` |

### Variables clave verificadas (ver docs/definitions/TCE_definition.md — pendiente de crear)

- `C_BAS1`: causa básica de defunción (CIE-10). **Comparable en todos los años 2015-2024** (mismo nombre y formato). Motociclista = V20–V29.
- Causa(s) asociada(s)/antecedente(s):
  - **Era B (2019–2024):** campo único `CAUSA_MULT` (texto, múltiples códigos CIE-10 separados por "/").
  - **Era A (2015–2018):** SIN campo unificado. Repartido en 11 campos: `C_ANT1, C_ANT12, C_ANT2, C_ANT22, C_ANT3, C_ANT32, C_DIR1, C_DIR12, C_MCM1, C_PAT1, C_PAT2`.
  - **Implicación:** la detección de TCE (S06) como causa asociada usa una lógica distinta por era (concatenación de campos en Era A vs. lectura directa en Era B). Ver `results/exploratory/panel_dane_eevv_2015_2024_tce_moto.json` para el detalle y `scripts/03b_inspect_data_panel_2015_2024.py` para el código. **Esto es una diferencia estructural real del instrumento, no un artefacto de nuestro procesamiento — debe declararse como limitación/threat to validity si se usa la serie completa.**
- Geografía del hecho: `CODOCUR`/`CODMUNOC` (ocurrencia, muertes no naturales) — poblada 99.9–100% dentro del subgrupo de motociclistas en todos los años.
- `SEXO`, `GRU_ED1`, `GRU_ED2`: sexo y edad.

### Resultados de auditoría de valores (ejecutados, no estimados)

Ver `results/exploratory/panel_dane_eevv_2015_2024_tce_moto.csv` (tabla completa). Resumen:

| Año | N defunciones totales | N moto (V20-V29) | N con S06 asociado (total) | N moto ∩ S06 | % moto con S06 |
|---|---:|---:|---:|---:|---:|
| 2015 | 219.472 | 3.139 | 7.329 | 1.030 | 32,81% |
| 2016 | 223.078 | 3.373 | 7.293 | 1.045 | 30,98% |
| 2017 | 227.624 | 2.518 | 6.821 | 678 | 26,93% |
| 2018 | 236.932 | 2.909 | 6.968 | 819 | 28,15% |
| 2019 | 244.355 | 2.920 | 7.589 | 965 | 33,05% |
| 2020 | 300.853 | 2.637 | 7.245 | 833 | 31,59% |
| 2021 | 363.089 | 3.508 | 8.859 | 1.134 | 32,33% |
| 2022 | 287.251 | 5.081 | 9.948 | 1.852 | 36,45% |
| 2023 | 268.411 | 5.296 | 10.553 | 2.085 | 39,37% |
| 2024 | 275.778 | 5.156 | 10.948 | 2.176 | 42,20% |

**Fecha de auditoría:** 2026-08-20. **Script:** `scripts/03b_inspect_data_panel_2015_2024.py`.

---

## 2. Instituto Nacional de Medicina Legal y Ciencias Forenses — microdatos abiertos

- **Fuente:** datos.gov.co (API Socrata)
- **Fecha de acceso:** 2026-08-20
- **Tipo de acceso:** Público, sin restricción, API abierta (sin descarga manual necesaria)
- **Cobertura temporal:** 2015–2024
- **Unidad de observación:** 1 fila = 1 víctima

| Dataset | ID Socrata | N columnas | Notas |
|---|---|---|---|
| Muertes por eventos de transporte | `s65h-7665` | 38 | `diagnostico_topografico_de_la_lesion_fatal` incluye "Trauma craneano" = 22.436 (2015-2024) |
| Lesiones (no fatales) por eventos de transporte | `ezhf-hscf` | 39 | "Trauma craneano" = 4.485; dominado por "Politraumatismo" |

No descargado a disco todavía (consultado vía API); pendiente de descarga si se usa como fuente primaria.

---

## 3. RUNT2.0 — Parque automotor (denominador de exposición, sensibilidad RQ1)

- **Fuente:** datos.gov.co (API Socrata), dataset `u3vn-bdcy` "CRECIMIENTO DEL PARQUE AUTOMOTOR RUNT2.0"
- **Fecha de acceso:** 2026-08-21
- **Tipo de acceso:** Público, API abierta
- **Cobertura temporal:** snapshot único, publicación 2026-07 (NO hay serie histórica por año)
- **Unidad:** fila = combinación depto×municipio×servicio×estado×clase×año-registro; `cantidad` = conteo
- **Uso:** parque de motos activo por departamento (`nombre_de_la_clase='MOTOCICLETA'`, `estado_del_vehiculo='ACTIVO'`). Total nacional ~14,26M. 32 deptos (Vaupés ausente).
- **Restricciones/sesgos DOCUMENTADOS:** conteo por departamento de MATRÍCULA, no de circulación → distorsión en municipios-matriculadero (Cundinamarca) y flota informal fronteriza (La Guajira). **No apto como denominador primario**; usado solo como triangulación de robustez (ver D006).
- **Archivo:** `data/raw/runt/parque_motos_depto_2026-07.csv`. **Script:** `scripts/09b_runt_sensitivity.py`.

---

## 4. RIPS agregado público — EVALUADO Y DESCARTADO (2026-08-21)

- **Fuente:** datos.gov.co `4k9h-8qiu` "Registros Individuales de Prestación de Servicios de Salud – RIPS"
- **Realidad:** pese al nombre, es **agregado** (no individual): conteos por `depto×municipio×año×tipoatencion×diagnóstico CIE-10`. 38M filas, cobertura **2009–2021**. Sí trae S06 (hospitalizaciones 84.965; urgencias 112.153; 2009–2021).
- **Motivo de descarte:** (1) **no moto-específico** — el campo diagnóstico lleva la lesión (S06), no la causa externa; V20–V29 prácticamente ausentes → imposible cruzar moto × TCE; (2) agregado → no arregla sesgo de selección de RQ2; (3) termina 2021 y serie anual errática (artefacto de reporte, no epidemiología). **No sustituye al RIPS individual restringido de SISPRO** (ese sí tendría causa externa + registros individuales).

## 5. ANSV Geoportal (Observatorio Nacional de Seguridad Vial) — EVALUADO Y DESCARTADO (2026-08-21)

- **Fuente:** `geoportal-ansv-ansv.hub.arcgis.com` (ArcGIS Hub, org `onsv.ansv`, 261 ítems).
- **Realidad:** capa de visualización/GIS operativo **sobre datos de Medicina Legal** (misma fuente primaria que ya usamos directo). Activo distintivo: capas de fallecidos **georreferenciados X/Y** sub-municipales (campos: AnoHecho, X, Y, ActorVial, TipoVehiculo, Edad, Sexo, Circunstancia…).
- **Motivo de descarte:** (1) **sin campo de TCE/lesión** → no identifica trauma craneoencefálico; (2) capas geocodificadas son **por corredor** (Pacífico, Villavicencio, sectores críticos), 2012–2022, no microdato nacional descargable; (3) deriva de Medicina Legal → no aporta triangulación independiente.
- **Uso admisible:** citar el **Anuario Nacional de Siniestralidad Vial** como contexto (Introducción/Discusión). Reserva para un eventual paper espacial de hotspots (otro estudio).

## Fuentes auditadas pero NO incorporadas aún (ver informe completo de FASE 1)

- **SISPRO/RIPS individual:** microdato restringido, requiere solicitud formal a MinSalud. Daría denominador no-fatal real (S06 + causa externa V20–V29) + morbilidad → mitigaría sesgo de selección de RQ2. **Único candidato que llenaría el vacío moto × TCE.** NO trae Glasgow.
- Policía Nacional: solo agregados verificados; microdato víctima-nivel NO VERIFICADO como público.
- GCS/severidad clínica nacional: NO DISPONIBLE en datos abiertos ni por registro.
