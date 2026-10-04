"""An in-memory database of invented records; never connects to patient data."""

from datetime import datetime, timedelta
import math

import duckdb
import pandas as pd
import sqlglot

from .queries import FEATURES, identifier


class Demo:
    def __init__(self):
        self.connection = duckdb.connect(":memory:")
        self.connection.execute("CREATE SCHEMA source")
        self.connection.execute("CREATE SCHEMA work")
        self._populate()
        self.validate_source()

    def query(self, sql):
        """Run BigQuery-dialect teaching SQL on DuckDB after explicit translation.

        This checks local behaviour, not BigQuery permissions, costs or engine equivalence.
        No persistent file or external database is written.
        """
        result = None
        for translated in sqlglot.transpile(sql, read="bigquery", write="duckdb"):
            result = self.connection.execute(translated)
        return result.fetchdf()

    def table(self, name):
        return self.query(f"SELECT * FROM {identifier(name)}")

    def _create(self, name, schema, rows):
        self.connection.execute(f"CREATE TABLE source.{name} ({schema})")
        if rows:
            placeholders = ", ".join("?" for _ in rows[0])
            self.connection.executemany(f"INSERT INTO source.{name} VALUES ({placeholders})", rows)

    def _populate(self):
        origin = datetime(2026, 1, 1)
        visits, measurements, devices, conditions, deaths, drugs, followup, coverage = ([] for _ in range(8))
        descriptions = []
        concepts = [(f.concept, f.name, "Measurement", "Synthetic") for f in FEATURES]
        concepts += [(990003, "inspired tidal volume", "Measurement", "Synthetic"),
                     (990100, "ICU admission", "Visit", "Synthetic"),
                     (990200, "confirmed invasive support (fixture)", "Device", "Synthetic"),
                     (990301, "norepinephrine", "Drug", "Synthetic"),
                     (990302, "propofol", "Drug", "Synthetic"),
                     (990303, "rocuronium", "Drug", "Synthetic"),
                     (990401, "recorded intake volume", "Measurement", "Synthetic"),
                     (990402, "recorded urine volume", "Measurement", "Synthetic"),
                     (990403, "delivered ultrafiltration volume", "Measurement", "Synthetic"),
                     (990404, "ultrafiltration rate setting", "Measurement", "Synthetic"),
                     (990405, "cumulative ultrafiltration counter", "Measurement", "Synthetic")]
        cases = [
            (101, 1, 0, 120, "complete follow-up"),
            (102, 1, 10, 120, "repeat admission with neurological exclusion"),
            (201, 2, 0, 150, "return to support 12h later"),
            (301, 3, 0, 54, "death 6h later"),
            (401, 4, 0, 60, "insufficient follow-up"),
            (501, 5, 0, 120, "fluid recording incomplete"),
            (601, 6, 0, 120, "FiO2 fraction 1.0 throughout"),
            (701, 7, 0, 120, "rate setting present, not a volume"),
            (801, 8, 0, 120, "invalid unit on an output-volume record"),
            (901, 9, 0, 120, "no invasive-support confirmation"),
            (1001, 10, 0, 96, "death at the 48h outcome boundary"),
            (1101, 11, 0, 120, "documented complete recording with zero intake"),
            (1201, 12, 0, 120, "drug exclusion delays eligibility"),
        ]
        defaults = {"sbp": 110, "dbp": 60, "spo2": 96, "haemoglobin": 7,
                    "wbc": 12, "platelets": 200, "base_excess": 1, "crp": 80,
                    "creatinine": 90, "albumin": 25, "haematocrit": .35, "lactate": 1.5}

        def add(person, visit, time, concept, value, unit):
            measurements.append((len(measurements) + 1, person, visit, time, concept, value, unit))

        for visit, person, day, end_hour, explanation in cases:
            start = origin + timedelta(days=day)
            end = start + timedelta(hours=end_hour)
            visits.append((visit, person, start, end, 990100))
            descriptions.append({"visit_occurrence_id": visit, "scenario": explanation})
            followup.append((visit, end, True, True))
            coverage.append((visit, start, end, visit != 501, visit != 501))
            if visit == 102:
                conditions.append((person, start + timedelta(hours=1), "Head trauma"))
            if visit in (301, 1001):
                deaths.append((person, end))
            if visit == 1201:
                drugs.append((person, 990302, start + timedelta(hours=10), start + timedelta(hours=35)))
            segments = [(0, 48)] + ([(60, 80)] if visit == 201 else [])
            for begin, finish in segments:
                if visit != 901:
                    devices.append((person, 990200, start + timedelta(hours=begin), start + timedelta(hours=finish, minutes=1)))
                for hour in range(begin, finish + 1, 4):
                    time = start + timedelta(hours=hour)
                    fio2 = 1.0 if visit == 601 else (.6 if hour < 24 else (.4 if hour < 48 else .35))
                    add(person, visit, time, 990001, fio2, "fraction")
                    add(person, visit, time, 990002, 12 if hour < 24 else 8, "cmH2O")
                    add(person, visit, time, 990003, 450, "ml")
                    for feature in FEATURES[2:]:
                        unit = "%" if feature.unit == "percent" else feature.unit
                        add(person, visit, time, feature.concept, defaults[feature.name], unit)
            # Each volume record represents the increment ending at this time.
            for hour in range(4, 49, 4):
                time = start + timedelta(hours=hour)
                if visit not in (501, 1101):
                    add(person, visit, time, 990401, 200 if hour <= 24 else 100, "ml")
                if visit != 501:
                    add(person, visit, time, 990402, 100 if hour <= 24 else 150, "ml")
            if visit == 701:
                add(person, visit, start + timedelta(hours=28), 990404, 200, "ml/hour")
            if visit == 801:
                add(person, visit, start + timedelta(hours=28), 990403, 200, "ml/hour")

        self.scenarios = pd.DataFrame(descriptions)
        self._create("concept", "concept_id BIGINT, concept_name VARCHAR, domain_id VARCHAR, vocabulary_id VARCHAR", concepts)
        self._create("visit_occurrence", "visit_occurrence_id BIGINT, person_id BIGINT, visit_start_datetime TIMESTAMP, visit_end_datetime TIMESTAMP, visit_concept_id BIGINT", visits)
        self._create("measurement", "measurement_id BIGINT, person_id BIGINT, visit_occurrence_id BIGINT, measurement_datetime TIMESTAMP, measurement_concept_id BIGINT, value_as_number DOUBLE, unit_source_value VARCHAR", measurements)
        self._create("device_exposure", "person_id BIGINT, device_concept_id BIGINT, device_exposure_start_datetime TIMESTAMP, device_exposure_end_datetime TIMESTAMP", devices)
        self._create("condition_occurrence", "person_id BIGINT, condition_start_datetime TIMESTAMP, condition_source_value VARCHAR", conditions)
        self._create("drug_exposure", "person_id BIGINT, drug_concept_id BIGINT, drug_exposure_start_datetime TIMESTAMP, drug_exposure_end_datetime TIMESTAMP", drugs)
        self._create("death", "person_id BIGINT, death_datetime TIMESTAMP", deaths)
        self._create("followup", "visit_occurrence_id BIGINT, observed_through TIMESTAMP, ventilation_capture_complete BOOLEAN, death_capture_complete BOOLEAN", followup)
        self._create("fluid_coverage", "visit_occurrence_id BIGINT, coverage_start TIMESTAMP, coverage_end TIMESTAMP, intake_complete BOOLEAN, output_complete BOOLEAN", coverage)

    def validate_source(self):
        """Reject ambiguous identifiers/admission intervals instead of deduplicating blindly."""
        self.assert_unique("source.visit_occurrence", "visit_occurrence_id")
        self.assert_unique("source.measurement", "measurement_id")
        self.assert_unique("source.followup", "visit_occurrence_id")
        overlap = self.query("""SELECT a.visit_occurrence_id
        FROM source.visit_occurrence a JOIN source.visit_occurrence b
        ON a.person_id = b.person_id AND a.visit_occurrence_id < b.visit_occurrence_id
        AND a.visit_start_datetime < b.visit_end_datetime AND b.visit_start_datetime < a.visit_end_datetime""")
        if len(overlap):
            raise ValueError("Overlapping admissions: time-based measurement linkage would be ambiguous")
        bad = self.query("""SELECT * FROM source.visit_occurrence
        WHERE person_id IS NULL OR visit_start_datetime IS NULL OR visit_end_datetime IS NULL
           OR visit_end_datetime <= visit_start_datetime""")
        if len(bad):
            raise ValueError("Admissions need person IDs and valid, complete intervals")
        bad_links = self.query("""SELECT m.measurement_id
        FROM source.measurement m
        LEFT JOIN source.visit_occurrence v ON v.visit_occurrence_id = m.visit_occurrence_id
        WHERE m.measurement_datetime IS NULL OR m.person_id IS NULL
           OR (m.visit_occurrence_id IS NOT NULL AND
              (v.visit_occurrence_id IS NULL OR v.person_id != m.person_id
               OR m.measurement_datetime < v.visit_start_datetime
               OR m.measurement_datetime >= v.visit_end_datetime))""")
        if len(bad_links):
            raise ValueError("Measurement linkage: missing timestamps or supplied visit IDs disagree with person/time")

    def assert_unique(self, table, key="visit_occurrence_id"):
        result = self.query(f"SELECT {identifier(key)}, COUNT(*) AS n FROM {identifier(table)} "
                            f"GROUP BY {identifier(key)} HAVING COUNT(*) != 1 OR {identifier(key)} IS NULL")
        if len(result):
            raise ValueError(f"{table}: {key} must be unique and non-null")


def cumulative_increments(values, *, initial_zero_known=False):
    """Example counter conversion for ONE ordered patient/device series.

    A fall is only treated as a reset for this exercise. Real resets require evidence;
    corrections and missing readings can look similar. Unknown initial volume stays None.
    """
    out, previous = [], None
    for index, value in enumerate(values):
        if value is None or not math.isfinite(value) or value < 0:
            out.append(None)
            previous = None
            continue
        if previous is None:
            out.append(value if index == 0 and initial_zero_known else None)
        else:
            out.append(value if value < previous else value - previous)
        previous = value
    return out


def check_column(frame, column, low, high, *, max_missing_fraction=.2):
    """Report empty/missing/range failures independently; never infer correctness from a range."""
    values = pd.to_numeric(frame[column], errors="coerce")
    if len(values) == 0:
        return {"column": column, "status": "EMPTY", "rows": 0, "missing_fraction": None}
    missing = float(values.isna().mean())
    out_of_range = int((values.notna() & ~values.between(low, high)).sum())
    return {"column": column, "rows": len(values), "missing_fraction": missing,
            "out_of_range": out_of_range,
            "status": "REVIEW" if missing > max_missing_fraction or out_of_range else "PASS"}
