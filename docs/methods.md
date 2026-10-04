# Methods and limitations of the revised exercises

The October 2026 revision is a synthetic teaching implementation based on a historical datathon workflow. It is not a reproduction of the original cohort, a clinical protocol, or a validated prediction model. Every bundled record and concept ID is invented.

## Decisions made explicit

| Decision | Implementation | Limit |
|---|---|---|
| Unit of analysis | First candidate ventilation episode per ICU admission; preserve patient ID | Repeated admissions need patient-level handling in subsequent modelling |
| Admission linkage | Unique admission keys; reject overlapping intervals; a supplied measurement visit ID must agree with the interval | Invalid or ambiguous source links require review, not silent deduplication |
| Ventilation evidence | PEEP and inspired tidal-volume readings within 30 minutes plus synthetic invasive-support confirmation | Real device and airway concepts must be validated; measurements alone are insufficient |
| Episode gaps | Split at gaps of at least six hours | Recording gaps can split continuous support; rapid reintubation can be missed |
| Low-support landmark | FiO₂ ≤50%, PEEP ≤10 cmH₂O, at least six hours after admission, specified drug exclusions | A retrospective data proxy, not complete extubation readiness |
| Drug exclusions | Historical buffer from six hours before exposure starts to three hours after it ends | Uses future information; not appropriate for a prospective prediction landmark without redesign |
| Drug coverage | Synthetic norepinephrine, propofol and rocuronium concepts | Rocuronium does not represent all neuromuscular blocking agents |
| Neurological exclusion | Demonstrated with a small, explicit source-label set | A scope choice; not a comprehensive phenotype or a claim about all causes of failure |
| Second landmark | Last qualifying measurement in the first episode | Not documented tube removal, SBT completion or liberation |
| Features | Fourteen variables at both landmarks, preceding observations only; precise time ranking and stable ID tie-break | Ranges are broad teaching checks, not evidence that observations are correct |
| Feature slopes | Change divided by the actual measurement interval in fractional hours; interval ≥4h | Two-point average, not a reconstructed time series |
| Fluid summaries | Reviewed incremental volumes in mL; two adjacent left-open/right-closed periods, plus a separate last-24h summary | Real rate and counter streams require their own validation; overlapping summaries must not be summed |
| Missing fluid data | Explicit coverage evidence required; invalid contributing units invalidate the total | No observations alone do not establish zero; completeness tables are additions, not standard OMOP facts |
| Early death | Main cohort excludes deaths less than 12h after the second landmark; sensitivity cohort includes them | Neither identifies withdrawal of care; selection can change apparent failure rates |
| Outcome window | Observed return to support or death at or before 48h is failure | Return to support is a proxy for reintubation; NIV, tracheostomy and care withdrawal need separate definitions |
| Negative outcome | Both outcome streams marked complete, observed through 48h within the same admission | Called `no_failure_observed_48h`, not proven successful extubation; otherwise unknown |
| Team writes | Independent calculations, unique keys, coordinated replacement of assigned columns | Different columns do not guarantee conflict-free BigQuery mutations |

The feature extraction includes FiO₂, PEEP, systolic and diastolic blood pressure, SpO₂, haemoglobin, white-cell count, platelets, base excess, CRP, creatinine, albumin, haematocrit and lactate. Windows and units are defined in one place, `FEATURES` in `datathon_prep/queries.py`, and displayed in Module 2.

The real source files used FiO₂ and PEEP thresholds, a six-hour episode gap and an early-death exclusion as pragmatic research choices. Some earlier explanations overstated their clinical specificity. The revised text makes that uncertainty visible. It also removes unsupported assertions about efficacy, novelty, universal portability and expected clinical event rates.

## What the synthetic checks establish

Tests execute the generated SQL after translation to DuckDB. They check repeat-admission isolation, measurement pairing, unit normalisation, exact time boundaries, incomplete follow-up, missing-versus-zero volumes, boundary double-counting, counter resets, all 28 feature extractions, deterministic selection, and replacement updates that clear stale values. The notebooks are executed in separate fresh kernels.

These checks do not establish BigQuery execution equivalence, source mapping validity, clinical phenotype accuracy, or educational effectiveness. A clean local run is one part of the validation process. A future dataset still needs schema inspection, query dry runs, a cost-limited execution, and clinical review of sampled records.

## References

- Thomas PA, Kern DE, Hughes MT, Tackett SA, Chen BY. *Curriculum Development for Medical Education: A Six-Step Approach.* 4th ed. Johns Hopkins University Press; 2022.
- [CDC: learning objectives and the revised Bloom taxonomy](https://www.cdc.gov/training-development/php/about/design-training-learning-objectives.html).
- [OMOP Common Data Model](https://ohdsi.github.io/CommonDataModel/cdm54.html).
- [AmsterdamUMCdb 2026 datathon dictionary](https://github.com/AmsterdamUMC/AmsterdamUMCdb/blob/master/datathons/2026-01-esicm-datathon-colab/data-dictionary.csv).
- [BigQuery DML concurrency](https://docs.cloud.google.com/bigquery/docs/data-manipulation-language#concurrent_jobs).
- [BigQuery row numbering and ties](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/numbering_functions#row_number).
- [Liberation from invasive mechanical ventilation with continued receipt of vasopressor infusions](https://pubmed.ncbi.nlm.nih.gov/35107416/). This study is one reason the previous categorical statement about never extubating on vasopressors was removed; the notebook is not prescribing an extubation policy.
