# October 2026 revision notes

The notebooks use synthetic records and display BigQuery SQL. Checks cover local execution; validation against a live BigQuery dataset remains necessary before real-data use.

## Technical changes

- Rebuilt the cohort as sequential complete stages; no missing schema columns or unpopulated prerequisite flags.
- Preserved admission IDs across joins and updates, checked uniqueness and overlapping admissions, and bounded measurement linkage by admission.
- Required temporally paired measurements plus synthetic invasive-support evidence; made episode and extubation-proxy limitations explicit.
- Normalised FiO₂ units before thresholds and selected one deterministic earliest qualifying pair.
- Implemented all 14 features at both landmarks with preceding windows, precise nearest-value ordering and explicit slope intervals.
- Separated incremental volumes from rates/counters, prevented adjacent-window double counting, and retained missingness unless recording completeness is established.
- Added explicit follow-up states and consistent inclusive 48-hour outcome boundaries.
- Retained the original early-death exclusion as the main example and added a sensitivity definition including early deaths, as requested by the author.
- Used separate in-memory exercises and fail-on-existing output tables instead of routine DROP/TRUNCATE operations.
- Demonstrated replacement updates that clear stale values, coordinated writes and derived-feature dependencies.
- Fixed the opening plot and cumulative-counter example; added regression tests and fresh-kernel execution checks.

## Editorial changes

Removed repetitive slogans, emojis, categorical clinical claims and unsupported guarantees. Retained the datathon origin and explained the decisions in direct language. Clarified prerequisites, standard versus local concepts, feature units, real-data access, BigQuery costs, the revised Bloom terminology and the retrospective use of Kern's framework.

Added direct notebook/Colab links, an MIT licence authorised by the presenting author, source limitations and an accepted-for-presentation citation. No patient data is included or relicensed.

## Abstract reference notes

The accepted abstract PDF appears to swap reference numbers 3 and 5 relative to their uses in the text: Yao et al. supports the medical-education discussion; Overhage et al. supports the common data model. The project also records an accepted-record author-name transposition. These are matters for the official abstract/supplement record; editing the repository does not amend that record. No request has been sent to the organisers as part of this code revision.
