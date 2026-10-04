from datetime import datetime, timedelta

import pandas as pd
import pytest

from datathon_prep import Demo, Pipeline, Rules
from datathon_prep.demo import check_column, cumulative_increments
from datathon_prep.queries import replacement_update


def run(demo=None, rules=None):
    demo = demo or Demo()
    demo.validate_source()
    plan = Pipeline(rules=rules)
    for _, sql in plan.steps():
        demo.query(sql)
    return demo


@pytest.fixture(scope="module")
def completed():
    return run()


def test_admissions_do_not_share_neuro_flags(completed):
    rows = completed.table("work.lesson_cohort").set_index("visit_occurrence_id")
    assert rows.loc[101, "included_primary"]
    assert not rows.loc[102, "included_primary"]
    assert not rows.loc[101, "neuro_excluded"]
    assert rows.loc[102, "neuro_excluded"]


def test_fraction_one_is_not_low_support(completed):
    row = completed.table("work.lesson_cohort").set_index("visit_occurrence_id").loc[601]
    assert pd.isna(row.eligible_time)
    assert not row.included_primary


def test_measurements_without_invasive_support_are_not_confirmed(completed):
    assert 901 not in set(completed.table("work.lesson_episodes").admission_id)


def test_markers_apart_do_not_define_episode():
    demo = Demo()
    demo.query("DELETE FROM source.measurement WHERE visit_occurrence_id=101 AND measurement_concept_id=990003")
    demo.query("""INSERT INTO source.measurement VALUES
        (999999, 1, 101, TIMESTAMP '2026-01-05 00:00:00', 990003, 450, 'ml')""")
    run(demo)
    assert 101 not in set(demo.table("work.lesson_episodes").admission_id)


def test_death_sensitivity_and_observation_boundary(completed):
    rows = completed.table("work.lesson_outcomes").set_index("visit_occurrence_id")
    assert rows.loc[301, "primary_outcome"] == "excluded"
    assert rows.loc[301, "sensitivity_outcome"] == "failure_death"
    assert rows.loc[1001, "primary_outcome"] == "failure_death"  # exactly 48h
    assert rows.loc[401, "primary_outcome"] == "unknown_followup"
    assert rows.loc[201, "primary_outcome"] == "failure_return_to_support"
    assert rows.loc[101, "primary_outcome"] == "no_failure_observed_48h"


def test_missing_coverage_is_not_success():
    demo = Demo()
    demo.query("DELETE FROM source.followup WHERE visit_occurrence_id=101")
    run(demo)
    row = demo.table("work.lesson_outcomes").set_index("visit_occurrence_id").loc[101]
    assert row.primary_outcome == "unknown_followup"


def test_rate_setting_does_not_enter_volumes(completed):
    f = completed.table("work.lesson_fluids").set_index(["visit_occurrence_id", "period"])
    assert f.loc[(701, "eligible_to_weaning"), "output_ml"] == 900
    assert pd.isna(f.loc[(801, "eligible_to_weaning"), "output_ml"])
    assert f.loc[(801, "eligible_to_weaning"), "invalid_output"] == 1


def test_unknown_volume_and_documented_zero_are_distinct(completed):
    f = completed.table("work.lesson_fluids").set_index(["visit_occurrence_id", "period"])
    assert pd.isna(f.loc[(501, "eligible_to_weaning"), "intake_ml"])
    assert pd.isna(f.loc[(501, "eligible_to_weaning"), "balance_ml"])
    assert f.loc[(1101, "eligible_to_weaning"), "intake_ml"] == 0


def test_adjacent_fluid_windows_count_boundary_once(completed):
    f = completed.table("work.lesson_fluids").set_index(["visit_occurrence_id", "period"])
    p1 = f.loc[(101, "imv_to_eligible")]
    p2 = f.loc[(101, "eligible_to_weaning")]
    assert p1.intake_ml == 1200 and p2.intake_ml == 600
    assert p1.output_ml + p2.output_ml == 1500
    assert p2.balance_ml_per_hour == -12.5


def test_nearest_reading_wins_within_the_same_hour_and_tie_is_stable():
    demo = Demo()
    demo.query("DELETE FROM source.measurement WHERE visit_occurrence_id=101 AND measurement_concept_id=990004")
    demo.query("""INSERT INTO source.measurement VALUES
      (900001, 1, 101, TIMESTAMP '2026-01-02 23:01:00', 990004, 80, 'mmHg'),
      (900002, 1, 101, TIMESTAMP '2026-01-02 23:59:00', 990004, 120, 'mmHg'),
      (900003, 1, 101, TIMESTAMP '2026-01-02 23:59:00', 990004, 130, 'mmHg'),
      (900004, 1, 101, TIMESTAMP '2026-01-03 00:01:00', 990004, 140, 'mmHg')""")
    run(demo)
    row = demo.table("work.lesson_slopes").set_index("visit_occurrence_id").loc[101]
    assert row.sbp_at_weaning == 120  # closest preceding, smallest stable ID at tie


@pytest.mark.parametrize("hours,expected", [(4, 2.5), (3.999, None)])
def test_slope_four_hour_boundary(hours, expected):
    demo = Demo()
    # Use the real slope SQL with a minimal, independently defined wide table.
    plan = Pipeline()
    from datathon_prep import FEATURES
    columns = ["visit_occurrence_id INT64"]
    for f in FEATURES:
        for landmark in ("eligible", "weaning"):
            columns.extend([f"{f.name}_at_{landmark} FLOAT64", f"{f.name}_at_{landmark}_time TIMESTAMP"])
    demo.query("CREATE TABLE work.lesson_wide_features (" + ",".join(columns) + ")")
    begin = datetime(2026, 1, 1)
    end = begin + timedelta(hours=hours)
    demo.connection.execute("INSERT INTO work.lesson_wide_features (visit_occurrence_id, fio2_at_eligible, fio2_at_weaning, fio2_at_eligible_time, fio2_at_weaning_time) VALUES (?, ?, ?, ?, ?)", [1, 40, 50, begin, end])
    demo.query(plan.slopes())
    value = demo.table("work.lesson_slopes").iloc[0].fio2_slope
    if expected is None:
        assert pd.isna(value)
    else:
        assert value == expected


def test_all_fourteen_features_have_both_landmarks(completed):
    features = completed.table("work.lesson_features")
    assert features.loc[features.visit_occurrence_id == 101].shape[0] == 28
    completed.assert_unique("work.lesson_analysis")
    assert len(completed.table("work.lesson_analysis")) == 13


def test_replacement_clears_stale_values_and_preserves_others():
    demo = Demo()
    demo.query("CREATE TABLE work.target (visit_occurrence_id INT64, feature FLOAT64, feature_time TIMESTAMP, other FLOAT64)")
    demo.query("INSERT INTO work.target VALUES (1, 99, TIMESTAMP '2026-01-01', 123), (2, 77, TIMESTAMP '2026-01-01', 456)")
    demo.query("CREATE TABLE work.stage (visit_occurrence_id INT64, value FLOAT64, measured_at TIMESTAMP)")
    demo.query("INSERT INTO work.stage VALUES (2, 40, TIMESTAMP '2026-01-02')")
    demo.assert_unique("work.target")
    demo.assert_unique("work.stage")
    sql = replacement_update("work.target", "work.stage", "feature")
    demo.query(sql)
    first = demo.table("work.target").sort_values("visit_occurrence_id").reset_index(drop=True)
    demo.query(sql)
    second = demo.table("work.target").sort_values("visit_occurrence_id").reset_index(drop=True)
    pd.testing.assert_frame_equal(first, second)
    assert pd.isna(first.iloc[0].feature) and pd.isna(first.iloc[0].feature_time)
    assert first.iloc[0].other == 123 and first.iloc[1].other == 456
    assert first.iloc[1].feature == 40


def test_duplicate_keys_block_publication():
    demo = Demo()
    demo.query("CREATE TABLE work.stage AS SELECT 1 AS visit_occurrence_id UNION ALL SELECT 1")
    with pytest.raises(ValueError, match="unique"):
        demo.assert_unique("work.stage")


def test_overlapping_admissions_fail_before_linking():
    demo = Demo()
    demo.query("UPDATE source.visit_occurrence SET visit_start_datetime=TIMESTAMP '2026-01-02' WHERE visit_occurrence_id=102")
    with pytest.raises(ValueError, match="Overlapping"):
        demo.validate_source()


def test_supplied_visit_id_must_agree_with_person_and_time():
    demo = Demo()
    demo.query("UPDATE source.measurement SET visit_occurrence_id=102 WHERE measurement_id=1")
    with pytest.raises(ValueError, match="Measurement linkage"):
        demo.validate_source()


def test_counter_reset_and_missing_baseline():
    assert cumulative_increments([0, 150, 320, 480, 100, 290, 450, 610], initial_zero_known=True) == [0, 150, 170, 160, 100, 190, 160, 160]
    assert cumulative_increments([150, 320, None, 480]) == [None, 170, None, None]


def test_validation_does_not_pass_empty_or_mostly_missing_columns():
    assert check_column(pd.DataFrame({"x": []}), "x", 21, 100)["status"] == "EMPTY"
    assert check_column(pd.DataFrame({"x": [40, None, None, None, None]}), "x", 21, 100)["status"] == "REVIEW"
    assert check_column(pd.DataFrame({"x": [40, 50]}), "x", 21, 100)["status"] == "PASS"


def test_outputs_cannot_be_overwritten_by_accident(completed):
    with pytest.raises(Exception, match="already exists"):
        completed.query(Pipeline().admissions())


def test_external_source_requires_reviewed_mapping():
    with pytest.raises(ValueError, match="reviewed"):
        Pipeline(source="my-project.new_dataset", output="my-project.work")


def test_rules_reject_invalid_thresholds():
    with pytest.raises(ValueError):
        Rules(gap_hours=0)
    with pytest.raises(ValueError):
        Rules(fio2_max=.5)


def test_zero_early_death_exclusion_matches_sensitivity():
    d = run(rules=Rules(early_death_exclusion_hours=0))
    outcomes = d.table("work.lesson_outcomes")
    assert outcomes.primary_outcome.equals(outcomes.sensitivity_outcome)
