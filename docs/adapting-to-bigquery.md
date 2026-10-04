# Adapting the exercise to a future BigQuery dataset

The public notebooks do not authenticate to Google Cloud or write to a remote database. The original AmsterdamUMCdb instance is no longer accessible to the presenting author, and the next datathon dataset may differ. This guide describes work that still requires access and review; it is not a claim that the historical pipeline has been retested.

## Establish the source contract

Ask the organisers for the current dataset identifier, data dictionary, access procedure and region. Read the [official AmsterdamUMCdb setup notebook](https://github.com/AmsterdamUMC/AmsterdamUMCdb/blob/master/bigquery/getting_started_v2.ipynb) when that is the chosen source.

Before adapting a query, inspect table schemas and units. BigQuery metadata queries use the dataset-qualified form:

```sql
SELECT table_name
FROM `YOUR_PROJECT.YOUR_DATASET.INFORMATION_SCHEMA.TABLES`;

SELECT column_name, data_type
FROM `YOUR_PROJECT.YOUR_DATASET.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'measurement';
```

Module 1's metadata cells use the local DuckDB catalogue, whose naming differs. The cohort queries themselves are generated in BigQuery dialect and locally translated for the exercise.

The revised SQL expects a reviewed staging layer with these fields:

| Table | Fields used |
|---|---|
| `visit_occurrence` | Unique `visit_occurrence_id`, `person_id`, start/end datetimes, `visit_concept_id` |
| `measurement` | Unique `measurement_id`, `person_id`, nullable visit ID, measurement datetime, concept ID, numeric value, source unit |
| `device_exposure` | Person, reviewed invasive-support concept, start/end datetimes |
| `condition_occurrence` | Person, condition start datetime, source label |
| `drug_exposure` | Person, reviewed drug concept, start/end datetimes |
| `death` | Person and validated death datetime |
| `followup` | Admission ID, `observed_through`, and separate completeness flags for ventilation and death capture |
| `fluid_coverage` | Admission ID, coverage start/end, separate intake/output completeness flags |

The last two tables are **additional evidence tables**, not standard OMOP tables. Do not populate their flags with TRUE merely because records exist. Define and justify completeness criteria. Leave evidence absent or false when it cannot be established; outcomes or totals will remain unknown. Dates without precise times require explicit handling rather than silently inventing a time of death.

Resolve overlapping visits and duplicate IDs before linking measurements by time. Check invalid supplied visit IDs rather than treating every non-null ID as trustworthy. Record counts of unmatched, ambiguous and rejected records. Do not deduplicate distinct admissions using patient ID.

The synthetic neuro source-label set is deliberately small. Replace it with a reviewed concept set or documented local rule. The pairing example expects PEEP in cmH₂O and tidal volume in mL; convert source units in the staging layer. The full source mapping needs version control alongside the analysis.

## Replace the synthetic concept mapping

All `990...` identifiers in the exercises are invented. `Pipeline` refuses an external dataset name unless explicit feature and concept mappings are supplied.

`Feature` supports a single concept ID or a tuple of validated IDs. Specify all 14 features using the names in `FEATURES`; each definition includes the preceding time window, output unit and plausibility bounds. `concepts` requires reviewed ID tuples for `icu_visit`, `invasive_support`, `tidal_volume`, `excluded_drugs`, `intake` and `output`.

For example, after constructing `reviewed_features` and `reviewed_concepts` from the new dictionary:

```python
from datathon_prep import Pipeline, Rules

plan = Pipeline(
    source="YOUR_PROJECT.reviewed_source",
    output="YOUR_PROJECT.teaching_sandbox",
    prefix="review_2026_10_04",
    features=reviewed_features,
    concepts=reviewed_concepts,
    rules=Rules(),
)
for name, sql in plan.steps():
    print(name, sql)
```

This generates SQL only. It does not create datasets, grant access or submit jobs. Use a new output prefix for each run. `CREATE TABLE` deliberately fails on existing outputs; do not change it to replace a shared analysis table by default.

The old source used `36303816` for inspired tidal volume and `19003953` for rocuronium. The old ultrafiltration setting concept `2000000063` has mixed rate/volume unit labels in the published dictionary. These are historical observations, not a ready-made mapping for the next dataset. Standard OMOP concept meanings and local recording practices are separate questions.

## Review clinical assumptions before execution

Read [Methods and limitations](methods.md). The six-hour episode gap, drug buffers, neurological exclusions and low-support criteria are retrospective research assumptions. The drug buffer includes future exposure information and therefore cannot define a prospective prediction landmark unchanged.

The original 12-hour early-death exclusion is retained in the main example, at the author's request, with the alternate definition alongside it. Explicit withdrawal-of-care records and validated extubation events would support better definitions. Do not present a recording gap as confirmed tube removal.

## Check permissions, location and cost

Use your authorised Google account and billing project. The source, scratch tables and query jobs must have compatible locations. Follow the organiser's current region instructions rather than treating `eu` as a universal rule.

Set a `maximum_bytes_billed` limit on the query configuration. Inspect dry-run estimates and begin with a deliberately bounded source sample. A `LIMIT` on returned rows does not generally cap bytes scanned. Inspect the actual query plan and errors; do not infer a successful connection from constructing a client object.

The client merges its default job configuration with per-query settings. The original getting-started notebook supplies a workaround with separate configurations; attribute that example rather than teaching it as an undocumented universal requirement. Both Python client queries and `%%bigquery --params` support parameters. Use parameters for values and validate dataset/table identifiers separately.

## Required real-data checks

Before describing an adapted version as runnable on the new source:

1. Validate the source schemas, unique keys and admission intervals.
2. Check concept names, source mappings, units and coverage with the new dictionary.
3. Inspect the phenotype against source airway/device events for sampled admissions.
4. Review selected feature readings, rejected records, fluid intervals and outcome follow-up.
5. Run BigQuery dry runs and a cost-limited execution in a separate scratch dataset.
6. Repeat the edge-case tests on the adapted queries; SQL translation tests alone are insufficient.
7. Record source version, code revision, query location, execution date and known limitations.

For team work, calculate features independently in staging tables, validate unique admission keys, and coordinate writes to the shared table. Derived features run after their inputs. Replacing assigned columns must also clear stale values for admissions that no longer match the corrected calculation.
