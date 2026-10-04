# Preparing Clinicians for ICU Datathons

**A Three-Module Curriculum Built from the ESICM Digital Critical Care Datathon 2026 Experience**

Three free notebooks for ICU clinicians preparing for a clinical data science datathon. They cover finding the right data, building a cohort and organising a team analysis.

## Background

The curriculum draws on our SQL pipeline and the problems teams encountered at the 2026 ESICM Digital Critical Care Datathon. It is intended for ICU trainees and early-career intensivists, with explanations alongside the code.

## What's inside

The three Google Colab notebooks contain 100 cells: 44 code and 56 explanatory. Each follows the same sequence: clinical thinking, data translation and a sanity check.

| Module | Learning objective | What the module covers |
|--------|--------------------|----------------------|
| 1. Finding Your Way Around | Navigate an OMOP CDM dataset and validate concept selections | Five problems from the datathon, with worked examples |
| 2. Cohort Workflow | Build a reproducible cohort from hypothesis to outcome classification | A clinical question, cohort criteria and measurements at two landmarks |
| 3. BigTable Pattern | Coordinate parallel feature extraction in a shared team table | Define the shared table, assign columns to teammates and check their contributions |

Notebooks in this repository:

- `module1_quick_start.ipynb`
- `module2_cohort_workflow.ipynb`
- `module3_bigtable_pattern.ipynb`

## Dataset and access

The notebooks run against AmsterdamUMCdb mapped to the OMOP Common Data Model, queried through Google BigQuery. Because the cohort logic and the shared-table pattern use standard OMOP CDM, the curriculum transfers to any other OMOP-mapped ICU database. With dataset access, learners can run the notebooks in Google Colab before the event.

## Running the notebooks

1. Request and confirm access to the AmsterdamUMCdb OMOP CDM BigQuery dataset.
2. Open a module notebook in Google Colab.
3. Set your BigQuery project in the configuration cell.
4. Run the cells in order. Start with Module 1 if you are new to OMOP, or choose the module you need.

## Curriculum design

The curriculum was developed with Kern's six-step framework for medical curriculum design. Learning objectives are mapped to Bloom's taxonomy (knowledge, application, synthesis). Teams can work through the full curriculum or choose individual modules.

## Evaluation

Prospective evaluation (usability, self-efficacy, and time-to-productivity) is planned at the next Digital Critical Care Datathon, where participants will complete structured feedback.

## Citation

Caldecott R, McNicholas B, Madden MG, McNicholas T, Kashyap A. Preparing Clinicians for ICU Datathons: A Three-Module Curriculum Built from the ESICM Digital Critical Care Datathon 2026 Experience. Presented at ESICM LIVES 2026, Lisbon (e-Poster 000327). Abstract published in ICM Experimental, LIVES 2026 supplement.

## Authors

Reginald Caldecott, Bairbre McNicholas, Michael G. Madden, Tony McNicholas, Ayushi Kashyap (University Hospital Galway and University of Galway).

## License

See the repository license file.

