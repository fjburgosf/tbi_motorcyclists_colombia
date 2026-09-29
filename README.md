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
- Internet access (the scripts download the raw data; about 3.7 GB)

```bash
pip install pandas numpy statsmodels scipy sodapy requests openpyxl pyreadstat geopandas shapely
```

### Step 1 — Get the scripts and create the folders

```bash
git clone https://github.com/fjburgosf/tbi_motorcyclists_colombia.git
cd tbi_motorcyclists_colombia
mkdir -p data/raw data/interim data/processed results/exploratory results/primary results/robustness results/spatial results/sensitivity
```

### Step 2 — Download and inspect the raw data

```bash
python scripts/03_inspect_data.py
python scripts/03b_inspect_data_panel_2015_2024.py
```

Downloads the Medicina Legal and DANE microdata into `data/raw/`, audits the
variables and builds the DANE annual panel of motorcyclist deaths with and
without an associated S06 code.

### Step 3 — Clean and filter

```bash
python scripts/04_clean_data.py
```

Filters both Medicina Legal datasets to motorcyclists and standardises the
categorical variables. Outputs: `data/interim/medlegal_moto_fatal.csv` and
`data/interim/medlegal_moto_nofatal.csv`.

### Step 4 — Build the analysis datasets

```bash
python scripts/05_construct_variables.py
```

Adds the DANE population denominators and builds the department-year panel and
the individual-level dataset of forensic head-injury cases (`data/processed/`).

### Step 5 — Registry comparison

```bash
python scripts/06_link_data.py
```

Checks the geographic coding shared by DANE and Medicina Legal and compares
their annual motorcyclist death counts (aggregate comparison only; no
individual linkage). Results go to `results/exploratory/`.

### Step 6 — Descriptive analysis

```bash
python scripts/07_descriptive_analysis.py
```

National annual series, departmental rates and descriptive counts by sex, zone
and role of the forensic head-injury cases (`results/exploratory/`).

### Step 7 — Main models

```bash
python scripts/08_primary_model.py
```

- Negative binomial national trend (2015–2024 and 2015–2021).
- Departmental heterogeneity.
- Logistic and Bayesian mixed models of fatal outcome among forensic cases.

Results go to `results/primary/`.

### Step 8 — Robustness analyses

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

### Step 9 — Spatial analysis and territorial correlates

```bash
python scripts/10_spatial_analysis.py
```

Global and local Moran's I (queen-contiguity and five-nearest-neighbour weights,
999 permutations), Spearman correlations and an ordinary least-squares model of
the log departmental rate. Results go to `results/spatial/`.

### Step 10 — Sensitivity and additional analyses

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
