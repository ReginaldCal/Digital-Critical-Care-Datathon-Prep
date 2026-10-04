"""Readable BigQuery SQL for a worked, retrospective cohort.

The notebooks print these queries before executing them locally on synthetic data.
The source contract and assumptions are documented in docs/adapting-to-bigquery.md.
No query in this module claims to reproduce validated clinical outcomes.
"""

from dataclasses import dataclass
import re


def identifier(value):
    # Allow one-part local names or fully qualified BigQuery tables/datasets.
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*(?:\.[A-Za-z_][A-Za-z0-9_]*){0,2}", value):
        raise ValueError(f"Invalid SQL identifier: {value!r}")
    return f"`{value}`"


def literal(value):
    return "'" + str(value).replace("\\", "\\\\").replace("'", "\\'") + "'"


@dataclass(frozen=True)
class Feature:
    name: str
    concept: int | tuple[int, ...]
    hours_before: int
    unit: str
    low: float
    high: float

    @property
    def ids(self):
        values = (self.concept,) if isinstance(self.concept, int) else self.concept
        if not values or any(type(v) is not int or v <= 0 for v in values):
            raise ValueError("Concept IDs must be positive integers")
        return ", ".join(str(v) for v in values)


# Invented IDs used only by the synthetic fixture. These are NOT OMOP mappings.
FEATURES = (
    Feature("fio2", 990001, 2, "percent", 21, 100),
    Feature("peep", 990002, 2, "cmh2o", 0, 30),
    Feature("sbp", 990004, 4, "mmhg", 40, 300),
    Feature("dbp", 990005, 4, "mmhg", 10, 200),
    Feature("spo2", 990006, 12, "percent", 40, 100),
    Feature("haemoglobin", 990007, 12, "mmol/l", 1, 20),
    Feature("wbc", 990008, 12, "10^9/l", 0, 200),
    Feature("platelets", 990009, 12, "10^9/l", 0, 2000),
    Feature("base_excess", 990010, 12, "mmol/l", -40, 40),
    Feature("crp", 990011, 12, "mg/l", 0, 1000),
    Feature("creatinine", 990012, 12, "umol/l", 10, 3000),
    Feature("albumin", 990013, 12, "g/l", 1, 70),
    Feature("haematocrit", 990014, 12, "fraction", .05, .8),
    Feature("lactate", 990015, 12, "mmol/l", 0, 40),
)


@dataclass(frozen=True)
class Rules:
    gap_hours: int = 6
    simultaneous_minutes: int = 30
    min_ventilation_hours: int = 24
    min_after_admission_hours: int = 6
    min_slope_hours: int = 4
    fio2_max: float = 50
    peep_max: float = 10
    early_death_exclusion_hours: int = 12
    outcome_hours: int = 48
    # Preserve the original retrospective exclusion buffers, explicitly.
    drug_pre_start_hours: int = 6
    drug_post_end_hours: int = 3

    def __post_init__(self):
        for name in ("gap_hours", "simultaneous_minutes", "min_ventilation_hours",
                     "min_after_admission_hours", "min_slope_hours", "outcome_hours"):
            if type(getattr(self, name)) is not int or getattr(self, name) <= 0:
                raise ValueError(f"{name} must be a positive integer")
        for name in ("early_death_exclusion_hours", "drug_pre_start_hours", "drug_post_end_hours"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        if not 21 <= self.fio2_max <= 100 or not 0 <= self.peep_max <= 30:
            raise ValueError("Thresholds must use percent FiO2 and cmH2O PEEP")


class Pipeline:
    """Build sequential queries; never delete or replace an existing output table."""

    def __init__(self, source="source", output="work", prefix="lesson", rules=None, features=FEATURES, concepts=None):
        identifier(source)
        identifier(output)
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", prefix):
            raise ValueError("Use letters, numbers and underscores for the run prefix")
        self.source, self.output, self.prefix = source, output, prefix
        self.rules = rules or Rules()
        self.feature_specs = tuple(features)
        if {f.name for f in self.feature_specs} != {f.name for f in FEATURES} or len(self.feature_specs) != len(FEATURES):
            raise ValueError("Supply exactly one specification for each of the 14 named features")
        for f in self.feature_specs:
            identifier(f.name)
            f.ids
            if not isinstance(f.hours_before, int) or f.hours_before <= 0 or f.low > f.high:
                raise ValueError("Invalid feature window or range")
        self.concepts = concepts or {
            "icu_visit": (990100,), "invasive_support": (990200,), "tidal_volume": (990003,),
            "excluded_drugs": (990301, 990302, 990303), "intake": (990401,),
            "output": (990402, 990403),
        }
        for key in ("icu_visit", "invasive_support", "tidal_volume", "excluded_drugs", "intake", "output"):
            self.ids(key)
        if set(self.concepts["intake"]) & set(self.concepts["output"]):
            raise ValueError("Intake and output concept sets must not overlap")
        if source != "source" and (concepts is None or tuple(features) == FEATURES):
            raise ValueError("An external source requires reviewed concept and feature mappings; synthetic IDs are not real mappings")

    def ids(self, key):
        values = self.concepts[key]
        if not values or any(type(v) is not int or v <= 0 for v in values):
            raise ValueError(f"{key}: supply positive integer concept IDs")
        return ", ".join(str(v) for v in values)

    def feature(self, name):
        return next(f for f in self.feature_specs if f.name == name)

    def src(self, name):
        return identifier(f"{self.source}.{name}")

    def table(self, name):
        return identifier(f"{self.output}.{self.prefix}_{name}")

    def admissions(self):
        return f"""CREATE TABLE {self.table('admissions')} AS
SELECT visit_occurrence_id, person_id,
       visit_start_datetime AS admission_start,
       visit_end_datetime AS admission_end
FROM {self.src('visit_occurrence')}
WHERE visit_concept_id IN ({self.ids('icu_visit')})
  AND visit_start_datetime IS NOT NULL
  AND visit_end_datetime > visit_start_datetime
"""

    @staticmethod
    def normalized(feature, alias="m"):
        value = f"{alias}.value_as_number"
        unit = f"LOWER(TRIM({alias}.unit_source_value))"
        if feature.unit == "percent":
            return (f"CASE WHEN {unit} IN ('%', 'percent') THEN {value} "
                    f"WHEN {unit} = 'fraction' THEN {value} * 100 ELSE NULL END")
        return f"CASE WHEN {unit} = {literal(feature.unit)} THEN {value} ELSE NULL END"

    def measurements(self):
        # Attach by person and time only after rejecting overlapping admissions.
        # A supplied visit ID must agree with that interval; unknown links are not guessed.
        return f"""CREATE TABLE {self.table('measurements')} AS
SELECT a.visit_occurrence_id AS admission_id, m.*
FROM {self.table('admissions')} a
JOIN {self.src('measurement')} m ON m.person_id = a.person_id
 AND m.measurement_datetime >= a.admission_start
 AND m.measurement_datetime < a.admission_end
 AND (m.visit_occurrence_id IS NULL OR m.visit_occurrence_id = a.visit_occurrence_id)
"""

    def episodes(self):
        r = self.rules
        m = self.table('measurements')
        return f"""CREATE TABLE {self.table('episodes')} AS
WITH paired AS (
  SELECT DISTINCT p.admission_id, p.person_id, p.measurement_datetime AS ts
  FROM {m} p
  JOIN {m} t ON t.admission_id = p.admission_id
   AND t.measurement_concept_id IN ({self.ids('tidal_volume')})
   AND ABS(TIMESTAMP_DIFF(t.measurement_datetime, p.measurement_datetime, SECOND)) <= {r.simultaneous_minutes * 60}
  WHERE p.measurement_concept_id IN ({self.feature('peep').ids})
    AND LOWER(TRIM(p.unit_source_value)) = 'cmh2o' AND p.value_as_number BETWEEN 0 AND 30
    AND LOWER(TRIM(t.unit_source_value)) = 'ml' AND t.value_as_number BETWEEN 50 AND 2000
    -- Synthetic invasive-support record confirms the candidate measurement pair.
    AND EXISTS (
      SELECT 1 FROM {self.src('device_exposure')} d
      WHERE d.person_id = p.person_id AND d.device_concept_id IN ({self.ids('invasive_support')})
        AND p.measurement_datetime >= d.device_exposure_start_datetime
        AND p.measurement_datetime < d.device_exposure_end_datetime
        AND t.measurement_datetime >= d.device_exposure_start_datetime
        AND t.measurement_datetime < d.device_exposure_end_datetime
    )
), gaps AS (
  SELECT *, TIMESTAMP_DIFF(ts, LAG(ts) OVER (PARTITION BY admission_id ORDER BY ts), SECOND) AS gap_seconds
  FROM paired
), numbered AS (
  SELECT *, SUM(CASE WHEN gap_seconds IS NULL OR gap_seconds >= {r.gap_hours * 3600} THEN 1 ELSE 0 END)
    OVER (PARTITION BY admission_id ORDER BY ts ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS episode_number
  FROM gaps
)
SELECT admission_id, person_id, episode_number, MIN(ts) AS episode_start, MAX(ts) AS episode_end,
       COUNT(*) AS marker_count
FROM numbered GROUP BY admission_id, person_id, episode_number
"""

    def landmarks(self):
        r = self.rules
        nf = self.normalized(self.feature("fio2"), "f")
        np = self.normalized(self.feature("peep"), "p")
        return f"""CREATE TABLE {self.table('landmarks')} AS
WITH first_episode AS (
 SELECT e.*, LEAD(episode_start) OVER (PARTITION BY admission_id ORDER BY episode_number) AS second_start
 FROM {self.table('episodes')} e
), eligible_pairs AS (
 SELECT e.admission_id, f.measurement_datetime AS eligible_time,
        {nf} AS eligible_fio2, {np} AS eligible_peep
 FROM first_episode e
 JOIN {self.table('admissions')} a ON a.visit_occurrence_id = e.admission_id
 JOIN {self.table('measurements')} f ON f.admission_id = e.admission_id AND f.measurement_concept_id IN ({self.feature('fio2').ids})
 JOIN {self.table('measurements')} p ON p.admission_id = e.admission_id AND p.measurement_concept_id IN ({self.feature('peep').ids})
 WHERE e.episode_number = 1
   AND {nf} BETWEEN 21 AND {r.fio2_max}
   AND {np} BETWEEN 0 AND {r.peep_max}
   AND f.measurement_datetime BETWEEN e.episode_start AND e.episode_end
   AND p.measurement_datetime BETWEEN e.episode_start AND e.episode_end
   AND ABS(TIMESTAMP_DIFF(f.measurement_datetime, p.measurement_datetime, SECOND)) <= {r.simultaneous_minutes * 60}
   AND f.measurement_datetime >= TIMESTAMP_ADD(a.admission_start, INTERVAL {r.min_after_admission_hours} HOUR)
   AND NOT EXISTS (
     SELECT 1 FROM {self.src('drug_exposure')} d
     WHERE d.person_id = e.person_id AND d.drug_concept_id IN ({self.ids('excluded_drugs')})
       -- Unknown end times are treated conservatively as continuing exposure.
       AND f.measurement_datetime >= TIMESTAMP_SUB(d.drug_exposure_start_datetime, INTERVAL {r.drug_pre_start_hours} HOUR)
       AND (d.drug_exposure_end_datetime IS NULL OR
            f.measurement_datetime <= TIMESTAMP_ADD(d.drug_exposure_end_datetime, INTERVAL {r.drug_post_end_hours} HOUR))
   )
 QUALIFY ROW_NUMBER() OVER (PARTITION BY e.admission_id
   ORDER BY f.measurement_datetime,
     ABS(TIMESTAMP_DIFF(f.measurement_datetime, p.measurement_datetime, SECOND)),
     f.measurement_id, p.measurement_id) = 1
), deaths AS (
 SELECT person_id, MIN(death_datetime) AS death_time FROM {self.src('death')} GROUP BY person_id
)
SELECT a.*, e.episode_start AS ventilation_start, e.episode_end AS weaning_proxy_time,
       e.second_start, ep.eligible_time, ep.eligible_fio2, ep.eligible_peep, d.death_time,
       TIMESTAMP_DIFF(e.episode_end, e.episode_start, SECOND) / 3600.0 AS ventilation_hours,
       EXISTS (SELECT 1 FROM {self.src('condition_occurrence')} n
         WHERE n.person_id = a.person_id
           AND n.condition_start_datetime >= a.admission_start AND n.condition_start_datetime < a.admission_end
           AND LOWER(n.condition_source_value) IN ('head trauma', 'hoofdtrauma', 'subarachnoid haemorrhage')) AS neuro_excluded,
       fu.observed_through, fu.ventilation_capture_complete, fu.death_capture_complete
FROM {self.table('admissions')} a
LEFT JOIN first_episode e ON e.admission_id = a.visit_occurrence_id AND e.episode_number = 1
LEFT JOIN eligible_pairs ep ON ep.admission_id = a.visit_occurrence_id
LEFT JOIN deaths d ON d.person_id = a.person_id
LEFT JOIN {self.src('followup')} fu ON fu.visit_occurrence_id = a.visit_occurrence_id
"""

    def cohort(self):
        r = self.rules
        return f"""CREATE TABLE {self.table('cohort')} AS
WITH flags AS (
 SELECT *,
   weaning_proxy_time IS NOT NULL AND eligible_time IS NOT NULL
   AND ventilation_hours >= {r.min_ventilation_hours} AND NOT neuro_excluded
   AND (death_time IS NULL OR death_time >= weaning_proxy_time) AS meets_base_criteria,
   death_time >= weaning_proxy_time AND death_time < TIMESTAMP_ADD(weaning_proxy_time, INTERVAL {r.early_death_exclusion_hours} HOUR) AS early_death
 FROM {self.table('landmarks')}
)
SELECT *, COALESCE(meets_base_criteria, FALSE) AS included_sensitivity,
       COALESCE(meets_base_criteria AND NOT COALESCE(early_death, FALSE), FALSE) AS included_primary
FROM flags
"""

    def features(self):
        selects = []
        for feature in self.feature_specs:
            for landmark, field in (("eligible", "eligible_time"), ("weaning", "weaning_proxy_time")):
                value = self.normalized(feature)
                selects.append(f"""SELECT c.visit_occurrence_id, {literal(feature.name)} AS feature,
 {literal(landmark)} AS landmark, {value} AS value,
 m.measurement_datetime AS measured_at, c.{field} AS landmark_at
FROM {self.table('cohort')} c
JOIN {self.table('measurements')} m ON m.admission_id = c.visit_occurrence_id
WHERE c.included_sensitivity AND m.measurement_concept_id IN ({feature.ids})
 AND m.measurement_datetime BETWEEN TIMESTAMP_SUB(c.{field}, INTERVAL {feature.hours_before} HOUR) AND c.{field}
 AND {value} BETWEEN {feature.low} AND {feature.high}
QUALIFY ROW_NUMBER() OVER (PARTITION BY c.visit_occurrence_id
 ORDER BY TIMESTAMP_DIFF(c.{field}, m.measurement_datetime, MICROSECOND), m.measurement_id) = 1""")
        return f"CREATE TABLE {self.table('features')} AS\n" + "\nUNION ALL\n".join(selects)

    def wide_features(self):
        columns = []
        for feature in self.feature_specs:
            for landmark in ("eligible", "weaning"):
                condition = f"feature = '{feature.name}' AND landmark = '{landmark}'"
                columns.extend([f"MAX(CASE WHEN {condition} THEN value END) AS {feature.name}_at_{landmark}",
                                f"MAX(CASE WHEN {condition} THEN measured_at END) AS {feature.name}_at_{landmark}_time"])
        return f"""CREATE TABLE {self.table('wide_features')} AS
SELECT visit_occurrence_id, {', '.join(columns)}
FROM {self.table('features')} GROUP BY visit_occurrence_id
"""

    def slopes(self):
        expressions = []
        for feature in self.feature_specs:
            f = feature.name
            seconds = f"TIMESTAMP_DIFF({f}_at_weaning_time, {f}_at_eligible_time, SECOND)"
            expressions.append(f"CASE WHEN {seconds} >= {self.rules.min_slope_hours * 3600} THEN "
                               f"SAFE_DIVIDE({f}_at_weaning - {f}_at_eligible, {seconds} / 3600.0) END AS {f}_slope")
        return f"CREATE TABLE {self.table('slopes')} AS\nSELECT *, {', '.join(expressions)} FROM {self.table('wide_features')}"

    def fluid_windows(self):
        return f"""CREATE TABLE {self.table('fluid_windows')} AS
SELECT visit_occurrence_id, 'imv_to_eligible' AS period, ventilation_start AS window_start, eligible_time AS window_end
FROM {self.table('cohort')} WHERE included_sensitivity
UNION ALL
SELECT visit_occurrence_id, 'eligible_to_weaning', eligible_time, weaning_proxy_time
FROM {self.table('cohort')} WHERE included_sensitivity
UNION ALL
SELECT visit_occurrence_id, 'last_24h', TIMESTAMP_SUB(weaning_proxy_time, INTERVAL 24 HOUR), weaning_proxy_time
FROM {self.table('cohort')} WHERE included_sensitivity
"""

    def fluids(self):
        # Only volume concepts enter this calculation. Rate/setpoint/counter concepts do not.
        return f"""CREATE TABLE {self.table('fluids')} AS
WITH sums AS (
 SELECT w.visit_occurrence_id, w.period, w.window_start, w.window_end,
   SUM(CASE WHEN m.measurement_concept_id IN ({self.ids('intake')}) AND LOWER(TRIM(m.unit_source_value)) = 'ml' AND m.value_as_number >= 0 THEN m.value_as_number END) AS intake_sum,
   SUM(CASE WHEN m.measurement_concept_id IN ({self.ids('output')}) AND LOWER(TRIM(m.unit_source_value)) = 'ml' AND m.value_as_number >= 0 THEN m.value_as_number END) AS output_sum,
   COUNTIF(m.measurement_concept_id IN ({self.ids('intake')}) AND (m.unit_source_value IS NULL OR LOWER(TRIM(m.unit_source_value)) != 'ml' OR m.value_as_number IS NULL OR m.value_as_number < 0)) AS invalid_intake,
   COUNTIF(m.measurement_concept_id IN ({self.ids('output')}) AND (m.unit_source_value IS NULL OR LOWER(TRIM(m.unit_source_value)) != 'ml' OR m.value_as_number IS NULL OR m.value_as_number < 0)) AS invalid_output
 FROM {self.table('fluid_windows')} w
 LEFT JOIN {self.table('measurements')} m ON m.admission_id = w.visit_occurrence_id
  -- Left-open, right-closed: a boundary event belongs to exactly one adjacent period.
  AND m.measurement_datetime > w.window_start AND m.measurement_datetime <= w.window_end
  AND m.measurement_concept_id IN ({self.ids('intake')}, {self.ids('output')})
 GROUP BY w.visit_occurrence_id, w.period, w.window_start, w.window_end
), checked AS (
 SELECT s.*,
   EXISTS (SELECT 1 FROM {self.src('fluid_coverage')} f WHERE f.visit_occurrence_id = s.visit_occurrence_id
     AND f.coverage_start <= s.window_start AND f.coverage_end >= s.window_end AND f.intake_complete) AS intake_complete,
   EXISTS (SELECT 1 FROM {self.src('fluid_coverage')} f WHERE f.visit_occurrence_id = s.visit_occurrence_id
     AND f.coverage_start <= s.window_start AND f.coverage_end >= s.window_end AND f.output_complete) AS output_complete
 FROM sums s
), volumes AS (
 SELECT *, CASE WHEN intake_complete AND invalid_intake = 0 THEN COALESCE(intake_sum, 0) END AS intake_ml,
           CASE WHEN output_complete AND invalid_output = 0 THEN COALESCE(output_sum, 0) END AS output_ml
 FROM checked
)
SELECT *, intake_ml - output_ml AS balance_ml,
 CASE WHEN window_end > window_start THEN SAFE_DIVIDE(intake_ml - output_ml,
   TIMESTAMP_DIFF(window_end, window_start, SECOND) / 3600.0) END AS balance_ml_per_hour
FROM volumes
"""

    def outcomes(self):
        r = self.rules
        deadline = f"TIMESTAMP_ADD(weaning_proxy_time, INTERVAL {r.outcome_hours} HOUR)"
        return f"""CREATE TABLE {self.table('outcomes')} AS
WITH classified AS (
 SELECT *, CASE
   WHEN NOT included_sensitivity THEN 'excluded'
   WHEN second_start > weaning_proxy_time AND second_start <= {deadline} THEN 'failure_return_to_support'
   WHEN death_time >= weaning_proxy_time AND death_time <= {deadline} THEN 'failure_death'
   WHEN ventilation_capture_complete AND death_capture_complete
     AND observed_through >= {deadline} AND admission_end >= {deadline} THEN 'no_failure_observed_48h'
   ELSE 'unknown_followup'
 END AS sensitivity_outcome
 FROM {self.table('cohort')}
)
SELECT *, CASE WHEN included_primary THEN sensitivity_outcome ELSE 'excluded' END AS primary_outcome
FROM classified
"""

    def final(self):
        return f"""CREATE TABLE {self.table('analysis')} AS
SELECT o.*, s.* EXCEPT (visit_occurrence_id)
FROM {self.table('outcomes')} o
LEFT JOIN {self.table('slopes')} s USING (visit_occurrence_id)
"""

    def steps(self):
        return [(name, getattr(self, name)()) for name in
                ("admissions", "measurements", "episodes", "landmarks", "cohort", "features",
                 "wide_features", "slopes", "fluid_windows", "fluids", "outcomes", "final")]


def replacement_update(target, staging, feature):
    """Replace every target row's assigned fields, including rows absent from staging.

    Both tables must have unique, non-null visit_occurrence_id values, checked before writing.
    Different columns still require coordinated BigQuery mutation scheduling.
    """
    identifier(feature)
    return f"""UPDATE {identifier(target)} t
SET {feature} = s.value, {feature}_time = s.measured_at
FROM (
 SELECT c.visit_occurrence_id, f.value, f.measured_at
 FROM {identifier(target)} c
 LEFT JOIN {identifier(staging)} f USING (visit_occurrence_id)
) s
WHERE t.visit_occurrence_id = s.visit_occurrence_id
"""
