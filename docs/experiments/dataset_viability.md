# Dataset Viability and Development Subset Plan

## Objective

Define a practical local development subset and confirm the viability of a wind-focused forecasting pipeline using NOAA ISD data.

---

## Dataset Scope Established in Layer 1

### Raw data understanding
NOAA ISD global hourly CSV data is organized as:

- `year/station.csv`

Each file represents one station-year, and each row is a timestamped weather observation.

Core encoded weather fields identified for the project:

- `WND`
- `TMP`
- `DEW`
- `VIS`
- `CIG`
- `SLP`

Optional sparse fields such as `AA*`, `GA*`, `CN*`, and similar families were found to be too sparse or inconsistent for the v1 core scope.

### Geographic scope
Using NOAA `isd-history.csv`, the project scope was narrowed to contiguous U.S. stations.

Filtering included:

- U.S. stations only
- valid coordinates
- exclusion of Alaska, Hawaii, and territories
- contiguous U.S. geographic bounding box
- removal of stations with missing state information

This produced a clean contiguous U.S. station master suitable for downstream development.

---

## Wind-Only Viability Decision

### Primary modeling signal
The `WND` field contains the key information required for a wind-focused project:

- wind direction
- wind direction QC
- wind observation type
- wind speed
- wind speed QC

This is sufficient to support downstream wind speed extraction and wind potential modeling.

### Supporting variables
The following fields are retained as secondary weather context:

- `TMP`
- `DEW`
- `SLP`
- optionally `VIS` and `CIG`

These fields may be useful as secondary predictive features but are not the primary target.

### Scope decision
- wind is the primary focus
- sparse auxiliary weather fields are secondary
- solar is out of scope

### Conclusion
A wind-only project is feasible using `WND` plus station metadata and selected secondary weather variables.

---

## Development Subset Plan for Local Work

To support fast local development, debugging, and validation, the project will use a small representative subset before scaling to Spark.

### Local development subset
- approximately **150 stations**
- approximately **3 years**
- representative selection across multiple climate regions

### Initial states
The first local development subset should prioritize a small set of diverse and wind-relevant states:

- **California (CA)** — coastal and inland variability
- **Texas (TX)** — major wind-energy relevance
- **Minnesota (MN)** — upper Midwest wind regime
- **Florida (FL)** — contrasting southeastern climate

### Initial years
Recommended first years for local work:

- **2018**
- **2019**
- **2020**

### Why this subset
This subset is large enough to:
- validate parsing and cleaning logic
- test metadata joins
- inspect temporal behavior
- support initial feature engineering and modeling experiments

It is also small enough for:
- local notebooks
- unit-test-sized samples
- fast iteration before EC2/Spark scaling

---

## Scale-Up Plan

The local development subset is not the final project dataset.

After local validation, the same logic will be scaled to the full project scope:

- contiguous U.S. stations
- full selected project time window
- distributed execution on EC2 + Spark

This preserves a local-first workflow while still targeting large-scale processing later.

---

## Final Scope Statement

### Included in v1
- contiguous U.S. stations
- wind-focused modeling
- core weather fields:
  - `WND`
  - `TMP`
  - `DEW`
  - `VIS`
  - `CIG`
  - `SLP`
- station metadata:
  - station_id
  - latitude
  - longitude
  - elevation
  - state
  - active year range

### Excluded from v1
- solar forecasting
- global station scope
- sparse optional encoded columns not central to wind modeling

---

## Outcome

The Layer 1 development scope is now fixed:

- contiguous U.S. station scope is fixed
- core columns are fixed
- local development subset is fixed
- wind-only direction is approved internally

This provides a clear input to Layer 2:
- sample raw data
- station master
- field understanding
- fixed development subset