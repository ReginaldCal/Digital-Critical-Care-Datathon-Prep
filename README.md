# Preparing Clinicians for ICU Datathons

These three notebooks grew out of our team's work at the 2026 ESICM Digital Critical Care Datathon. They cover finding and checking variables, building an admission-level cohort, and sharing feature-extraction work across a team.

**You can run the current exercises without database access.** They use invented records and concept IDs, with examples of repeat admissions, missing follow-up and unit errors. The notebooks include a guide to adapting the SQL to the dataset used at your event.

## Start here

| Notebook | What you will practise | Run it |
|---|---|---|
| [1. Finding your way around the data](module1_quick_start.ipynb) | Inspect tables, check concepts and units, and distinguish admissions, rates, volumes and counters | [Open in Colab](https://colab.research.google.com/github/ReginaldCal/Digital-Critical-Care-Datathon-Prep/blob/main/module1_quick_start.ipynb) |
| [2. From a clinical question to a cohort](module2_cohort_workflow.ipynb) | Build a complete synthetic cohort, extract 14 features at two landmarks, calculate fluid summaries and classify outcomes with explicit uncertainty | [Open in Colab](https://colab.research.google.com/github/ReginaldCal/Digital-Critical-Care-Datathon-Prep/blob/main/module2_cohort_workflow.ipynb) |
| [3. Building a shared wide table](module3_bigtable_pattern.ipynb) | Assign column ownership, coordinate writes, clear stale results on reruns and validate the shared table | [Open in Colab](https://colab.research.google.com/github/ReginaldCal/Digital-Critical-Care-Datathon-Prep/blob/main/module3_bigtable_pattern.ipynb) |

Open a notebook and run the cells in order. The first code cell installs the teaching helpers in a fresh Colab session. All database operations then run locally in memory. To start again, restart the runtime and run from the beginning; existing output tables are not silently replaced.

The material is intended for ICU clinicians working with analysts. You do not need to be a programmer to follow the clinical decisions, but completing the exercises involves reading short SQL queries and changing code. Module 1 introduces the query structure. If notebooks are unfamiliar, begin with [Colab's introduction](https://colab.research.google.com/notebooks/intro.ipynb).

## What the examples do—and what has been checked

The SQL describes a retrospective teaching cohort. It does not establish that fluid trajectories predict extubation outcomes, that a measurement gap is an extubation event, or that completing these notebooks improves datathon performance.

The exercises retain the original 12-hour early-death exclusion as the main definition and show a sensitivity analysis that includes those deaths. Incomplete follow-up remains unknown. All included patient records, concept IDs and displayed results are synthetic.

The displayed cohort SQL is written for BigQuery and translated to DuckDB for local execution. Tests cover the complete synthetic pipeline and specific failure cases. This is **not a recent BigQuery validation**: real-data permissions, mappings, units, source completeness and engine behaviour need checking before reuse. See [Methods and limitations](docs/methods.md), [Adapting to BigQuery](docs/adapting-to-bigquery.md), and the [revision record](docs/revision-notes.md).

## Using another dataset

Start with that dataset's access process and dictionary. For AmsterdamUMCdb, consult its [official repository](https://github.com/AmsterdamUMC/AmsterdamUMCdb) and [getting-started notebook](https://github.com/AmsterdamUMC/AmsterdamUMCdb/blob/master/bigquery/getting_started_v2.ipynb). Confirm the current instance with the organisers; the historical `van_gogh_2026_datathon` and `_update` names are not promises of current access.

The workflow can be adapted to other datasets. Concept sets, source mappings, unit handling, admission linkage and outcome definitions still require local review. BigQuery work also needs a project authorised to run queries, an appropriately located writable dataset, and a query-cost budget. The synthetic route needs none of these.

## Educational design

Learner needs came from the team's experience of the datathon. Kern's six-step framework helped structure the curriculum; the needs assessment was informal and the objectives were refined during development. The exercises ask learners to apply and evaluate data checks, construct a cohort, and design a collaborative workflow. These action-based objectives are consistent with the revised Bloom taxonomy; they are not a formal assessment of learning.

The curriculum has not been prospectively evaluated. Evaluation at a future datathon is planned, subject to access and event arrangements, using learner feedback and measures of usability, confidence and time to a valid result.

## ESICM LIVES 2026

This repository accompanies abstract **000327**, accepted for presentation at ESICM LIVES 2026 in Lisbon:

> Caldecott R, McNicholas B, Madden MG, McNicholas T, Kashyap A. *Preparing Clinicians for ICU Datathons: A Three-Module Curriculum Built from the ESICM Digital Critical Care Datathon 2026 Experience.* Accepted for presentation at ESICM LIVES 2026, Lisbon, 12 October 2026. Abstract 000327.

A final journal citation will be added when the supplement record and bibliographic details have been checked.

The presentation's “BigTable pattern” is described here as a **shared wide table**, to distinguish it from Google Cloud Bigtable.

## Authors and contributions

Reginald Caldecott, Bairbre McNicholas, Michael G. Madden, Tony McNicholas and Ayushi Kashyap; University Hospital Galway and University of Galway.

The teaching material draws on the team's datathon pipeline and discussion. The runnable examples use synthetic records to demonstrate the workflow and its checks.

## Run and check locally

Use Python 3.10 or newer in a virtual environment:

```bash
pip install -e '.[test]'
pytest -q
python scripts/check_notebooks.py --execute
```

The helper code is in [`datathon_prep/`](datathon_prep/). `queries.py` contains the cohort SQL, `demo.py` constructs the invented records, and `tests/` checks edge cases. Notebook execution uses a fresh kernel for each module. No patient-data credentials are used.

## Licence

The code, notebooks and accompanying teaching documentation are available under the [MIT licence](LICENSE). This licence grants no rights to AmsterdamUMCdb or any other patient dataset; their own access and use conditions apply.
