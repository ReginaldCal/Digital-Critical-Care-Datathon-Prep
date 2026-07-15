# Preparing Clinicians for ICU Datathons

**A Three-Module Curriculum Built from the ESICM Digital Critical Care Datathon 2026 Experience**

A freely available, modular curriculum that prepares ICU clinicians for clinical-data-science datathons. It closes the gap that datathons expose: participants must navigate an unfamiliar dataset, build a valid cohort, and coordinate a team analysis all at once, and none of it is taught in clinical training. The three notebooks let a clinician arrive already able to do the work.

## Background

The curriculum was built directly from the SQL pipeline and lessons of the 2026 ESICM Digital Critical Care Datathon. Learner needs were drawn from the actual errors teams hit during the event, so the materials run against real data from the first cell. It is designed for ICU trainees and early-career intensivists, with no coding experience assumed.

## What's inside

Three executable Google Colab notebooks, 100 cells in total (44 code, 56 explanatory), each anchoring technical steps in clinical reasoning through a recurring "clinical thinking, data translation, sanity check" structure.

| Module | Learning objective | Pedagogical approach |
|--------|--------------------|----------------------|
| 1. Finding Your Way Around | Navigate an OMOP CDM dataset and validate concept selections | Pitfall-based: five real datathon errors, each with a worked fix |
| 2. Cohort Workflow | Build a reproducible cohort from hypothesis to outcome classification | Clinical question to study cohort, measured at two clinical landmarks |
| 3. BigTable Pattern | Coordinate parallel feature extraction in a shared team table | Schema-first, parallel-safe design so teammates add columns at once without overwriting |

Notebooks in this repository:

- `module1_quick_start.ipynb`
- `module2_cohort_workflow.ipynb`
- `module3_bigtable_pattern.ipynb`

## Dataset and access

The notebooks run against AmsterdamUMCdb mapped to the OMOP Common Data Model, queried through Google BigQuery. Because the cohort logic and the shared-table pattern use standard OMOP CDM, the curriculum transfers to any other OMOP-mapped ICU database. All notebooks run in Google Colab once dataset access has been granted, which makes the curriculum suitable for self-directed preparation before an event.

## Running the notebooks

1. Request and confirm access to the AmsterdamUMCdb OMOP CDM BigQuery dataset.
2. Open a module notebook in Google Colab.
3. Set your BigQuery project in the configuration cell.
4. Run the cells in order. Start with Module 1 if you are new to OMOP; teams can otherwise take only the modules that match their gaps.

## Curriculum design

The curriculum was developed with Kern's six-step framework for medical curriculum design. Learning objectives are mapped to Bloom's revised taxonomy (knowledge, application, synthesis). The modular structure lets teams select the modules matching their skill gaps rather than working through everything.

## Evaluation

Prospective evaluation (usability, self-efficacy, and time-to-productivity) is planned at the next Digital Critical Care Datathon, where participants will complete structured feedback.

## Citation

Caldecott R, McNicholas B, Madden MG, McNicholas T, Kashyap A. Preparing Clinicians for ICU Datathons: A Three-Module Curriculum Built from the ESICM Digital Critical Care Datathon 2026 Experience. Presented at ESICM LIVES 2026, Lisbon (e-Poster 000327). Abstract published in ICM Experimental, LIVES 2026 supplement.

## Authors

Reginald Caldecott, Bairbre McNicholas, Michael G. Madden, Tony McNicholas, Ayushi Kashyap (University Hospital Galway and University of Galway).

## License

See the repository license file.
```
