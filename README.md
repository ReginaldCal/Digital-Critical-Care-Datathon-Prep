# Digital Critical Care Datathon Prep

**Preparing Clinicians for ICU Datathons: A Three-Module Curriculum Built from the ESICM INDICATE 2026 Experience**

A freely available, modular curriculum for clinician-researchers preparing for ICU datathons. Developed after the 2026 ESICM INDICATE datathon using AmsterdamUMCdb (OMOP CDM, BigQuery).

## Modules

| Module | Notebook | What you will learn |
|--------|----------|---------------------|
| **1 — Finding Your Way Around** | `module1_quick_start.ipynb` | Navigate OMOP CDM, validate concept IDs, avoid five common pitfalls |
| **2 — Cohort Workflow** | `module2_cohort_workflow.ipynb` | Build an end-to-end cohort pipeline — from clinical hypothesis through feature extraction to outcome classification |
| **3 — Wide Table Pattern** | `module3_bigtable_pattern.ipynb` | Coordinate parallel team analysis using a schema-first, shared-table design with built-in validation |

Each module is a self-contained Google Colab notebook. Modules build on each other but can be used independently depending on your team's skill gaps.

## Getting Started

1. Request access to **AmsterdamUMCdb** via the [ESICM datathon portal](https://amsterdammedicaldatascience.nl/)
2. Open any module in [Google Colab](https://colab.research.google.com/)
3. Follow the setup cell at the top of each notebook (project ID, dataset, location)

All notebooks are designed for self-directed learning before a datathon event.

## Pedagogical Approach

- Built using [Kern's six-step framework](https://doi.org/10.56021/9781421444086) for medical curriculum development
- Learner needs identified from real errors encountered during the datathon
- Learning objectives mapped to Bloom's revised taxonomy (knowledge → application → synthesis)
- Recurring structure: **Clinical Thinking → Data Translation → Sanity Check**

## Authors

- Reginald Caldecott
- Bairbre McNicholas
- Tony McNicholas
- Michael Madden
- Ayushi Kashyap

## Citation

If you use these materials, please cite the accompanying abstract:

> Caldecott R, McNicholas B, McNicholas T, Madden M, Kashyap A. Preparing Clinicians for ICU Datathons: A Three-Module Curriculum Built from the ESICM INDICATE 2026 Experience. *ESICM LIVES 2026.*

## License

These educational materials are provided for academic and datathon preparation purposes.
