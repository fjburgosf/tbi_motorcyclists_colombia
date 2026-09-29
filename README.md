# TBI Mortality Among Motorcyclists in Colombia, 2015–2024

Analysis scripts for a national study of traumatic brain injury (TBI) mortality
among motorcyclists in Colombia, 2015–2024: national trend, territorial
inequality, spatial autocorrelation and ecological territorial correlates, and
the comparability of forensic and vital-statistics registries.

**Authors:** Alexander Rodríguez-Sanjuán (Universidad del Atlántico) ·
Juan Guillermo Popayán-Hernández (Universidad Nacional de Colombia) ·
Francisco Burgos-Florez (Universidad Nacional de Colombia, Sede La Paz, Cesar ·
fjburgosf@unal.edu.co, corresponding)

---

## Contents

```
scripts/    Analysis scripts, numbered in execution order
README.md   This guide
```

The scripts reproduce the numerical results of the study: counts, rates,
model estimates and test statistics. Data and outputs are not stored in the
repository; the scripts download the public data and write all results to
`results/`.

---

## Data sources (all public)

| Source | Resource ID / URL | Period |
|---|---|---|
| Medicina Legal — fatal injuries | `s65h-7665` (datos.gov.co, Socrata) | 2015–2024 |
| Medicina Legal — non-fatal injuries | `ezhf-hscf` (datos.gov.co, Socrata) | 2015–2024 |
| DANE — vital statistics (non-fetal deaths) | [microdatos.dane.gov.co](https://microdatos.dane.gov.co) | 2015–2024 |
| DANE — departmental population projections | [dane.gov.co](https://www.dane.gov.co) | 2015–2024 |
| RUNT2.0 — registered motorcycle fleet | `u3vn-bdcy` (datos.gov.co, Socrata) | single extract, 2026 |
| Department polygons (DIVIPOLA codes, IGAC areas) | public GeoJSON, pinned commit, downloaded by `10_spatial_analysis.py` | static |

---

## How to run the analyses

### Requirements

- Python 3.12
- Internet access to download the public data (about 3.7 GB)

```bash
pip install pandas numpy scipy statsmodels geopandas pyreadstat openpyxl
```

### Step 1 — Get the scripts and create the folders

```bash
git clone https://github.com/fjburgosf/tbi_motorcyclists_colombia.git
cd tbi_motorcyclists_colombia
mkdir -p data/raw/medicina_legal data/raw/dane_poblacion data/interim data/processed results/exploratory results/primary results/robustness results/spatial results/sensitivity
```

### Step 2 — Download the data

The RUNT fleet and the department polygons are downloaded by the scripts. The
other sources must be downloaded once and saved with the names below.

**Medicina Legal** (datos.gov.co; the full datasets have 73,403 and 342,796 records):

```bash
curl -o data/raw/medicina_legal/muertes_eventos_transporte_2015_2024.csv 'https://www.datos.gov.co/resource/s65h-7665.csv?$limit=100000'
curl -o data/raw/medicina_legal/lesiones_eventos_transporte_2015_2024.csv 'https://www.datos.gov.co/resource/ezhf-hscf.csv?$limit=400000'
```

**DANE population projections** (departmental series):

```bash
curl -o data/raw/dane_poblacion/DCD-area-sexo-edad-proypoblacion-dep-2005-2017_VP.xlsx https://www.dane.gov.co/files/censo2018/proyecciones-de-poblacion/Departamental/DCD-area-sexo-edad-proypoblacion-dep-2005-2017_VP.xlsx
curl -o data/raw/dane_poblacion/PPED-AreaSexoEdadDep-2018-2050_VP.xlsx https://www.dane.gov.co/files/censo2018/proyecciones-de-poblacion/Departamental/PPED-AreaSexoEdadDep-2018-2050_VP.xlsx
```

**DANE vital statistics, non-fetal deaths** (Estadísticas Vitales, EEVV). Download
the Stata file of non-fetal deaths for each year from the DANE microdata catalog
and save it at the path shown:

| Year | Catalog page | Save as |
|---|---|---|
| 2015 | [catalog/475](https://microdatos.dane.gov.co/index.php/catalog/475) | `data/raw/dane_eevv_2015/BD-EEVV-Defuncionesnofetales-2015/nofetal2015.dta` |
| 2016 | [catalog/519](https://microdatos.dane.gov.co/index.php/catalog/519) | `data/raw/dane_eevv_2016/BD-EEVV-Defuncionesnofetales-2016/nofetal2016.dta` |
| 2017 | [catalog/652](https://microdatos.dane.gov.co/index.php/catalog/652) | `data/raw/dane_eevv_2017/BD-EEVV-Defuncionesnofetales-2017/nofetal2017.dta` |
| 2018 | [catalog/652](https://microdatos.dane.gov.co/index.php/catalog/652) | `data/raw/dane_eevv_2018/BD-EEVV-Defuncionesnofetales-2018/nofetal2018.dta` |
| 2019 | [catalog/696](https://microdatos.dane.gov.co/index.php/catalog/696) | `data/raw/dane_eevv_2019/BD-EEVV-Defuncionesnofetales-2019/nofetal2019.dta` |
| 2020 | [catalog/732](https://microdatos.dane.gov.co/index.php/catalog/732) | `data/raw/dane_eevv_2020/BD-EEVV-Defuncionesnofetales-2020/nofetal2020.dta` |
| 2021 | [catalog/775](https://microdatos.dane.gov.co/index.php/catalog/775) | `data/raw/dane_eevv_2021/BD-EEVV-Defuncionesnofetales-2021/nofetal2021.stata` |
| 2022 | [catalog/807](https://microdatos.dane.gov.co/index.php/catalog/807) | `data/raw/dane_eevv_2022/BD-EEVV-Defuncionesnofetales-2022/nofetal2022.dta` |
| 2023 | [catalog/876](https://microdatos.dane.gov.co/index.php/catalog/876) | `data/raw/dane_eevv_2023/BD-EEVV-Defuncionesnofetales-2023/BD-EEVV-Defuncionesnofetales-2023.dta` |
| 2024 | [catalog/878](https://microdatos.dane.gov.co/index.php/catalog/878) | `data/raw/dane_eevv_2024/BD-EEVV-Defuncionesnofetales-2024/BD-EEVV-Defuncionesnofetales-2024.dta` |

### Step 3 — Inspect the raw data

```bash
python scripts/03_inspect_data.py
python scripts/03b_inspect_data_panel_2015_2024.py
```

Audits the DANE variables and builds the annual panel of motorcyclist deaths
with and without an associated S06 code (`results/exploratory/`).

### Step 4 — Clean and filter

```bash
python scripts/04_clean_data.py
```

Filters both Medicina Legal datasets to motorcyclists and standardises the
categorical variables. Outputs: `data/interim/medlegal_moto_fatal.csv` and
`data/interim/medlegal_moto_nofatal.csv`.

### Step 5 — Build the analysis datasets

```bash
python scripts/05_construct_variables.py
```

Adds the DANE population denominators and builds the department-year panel and
the individual-level dataset of forensic head-injury cases (`data/processed/`).

### Step 6 — Registry comparison

```bash
python scripts/06_link_data.py
```

Checks the geographic coding shared by DANE and Medicina Legal and compares
their annual motorcyclist death counts (aggregate comparison only; no
individual linkage). Results go to `results/exploratory/`.

### Step 7 — Descriptive analysis

```bash
python scripts/07_descriptive_analysis.py
```

National annual series, departmental rates and descriptive counts by sex, zone
and role of the forensic head-injury cases (`results/exploratory/`).

### Step 8 — Main models

```bash
python scripts/08_primary_model.py
```

- Negative binomial national trend (2015–2024 and 2015–2021).
- Departmental heterogeneity.
- Logistic and Bayesian mixed models of fatal outcome among forensic cases.

Results go to `results/primary/`.

### Step 9 — Robustness analyses

```bash
python scripts/09b_runt_sensitivity.py
python scripts/09c_rq2_profile_bounding.py
python scripts/09e_hierarchical_shrinkage.py
```

- `09b`: departmental mortality per registered motorcycle and its concordance
  with population-based rates.
- `09c`: demographic profile of the fatal cases and selection bounds for the
  fatal-outcome associations.
- `09e`: empirical-Bayes Poisson–gamma shrinkage of departmental rates, and the
  department random-intercept logistic model refitted by Hamiltonian Monte Carlo
  (four chains, split-R-hat and bulk effective sample size).

Results go to `results/robustness/`.

### Step 10 — Spatial analysis and territorial correlates

```bash
python scripts/10_spatial_analysis.py
```

Global and local Moran's I (queen-contiguity and five-nearest-neighbour weights,
999 permutations), Spearman correlations and an ordinary least-squares model of
the log departmental rate. Results go to `results/spatial/`.

### Step 11 — Sensitivity and additional analyses

```bash
python scripts/12_sensitivity_analyses.py
```

Requires all previous steps. It computes:

- departmental rates over accumulated person-years with the complete population
  denominator, and the concordance of all-motorcyclist and head-injury rates;
- national trend models for 2015–2024 and 2015–2021, segmented models testing a
  2022–2024 level shift, and sensitivity analyses excluding or adjusting for the
  pandemic years; the DANE trend for deaths with an S06 code;
- the ecological correlation adjusted for the shared population denominator,
  and variance inflation factors;
- Benjamini–Hochberg adjustment of the local Moran tests and the simulated power
  of global Moran's I with 32 departments;
- annual counts from both registries and the share of DANE deaths with an S06
  code;
- dispersion diagnostics, record completeness, annual non-fatal counts and a
  reallocation of records with an unspecified topographic diagnosis.

Results go to `results/sensitivity/`.

---

## Inference

All results are descriptive, associational and ecological; no causal claims are
made. Individual-level inference is not supported, because the registries share
no individual identifier.

---

## License

Code released under the [MIT License](https://opensource.org/licenses/MIT).
The underlying microdata belong to their respective Colombian public
institutions (Medicina Legal, DANE, RUNT) and are subject to their own terms of
use.
