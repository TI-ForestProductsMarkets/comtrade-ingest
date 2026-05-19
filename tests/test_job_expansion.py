from comtrade_ingest.comtrade.config import JobConfig
from comtrade_ingest.comtrade.pipeline import _expand_year_jobs, _expand_cmd_code_jobs
from comtrade_ingest.comtrade.errors import ConfigValidationError
from conftest import create_test_config

import pytest


def test_expand_year_jobs_rejects_unreasonable_year_range():
    """Validation now happens in pipeline._expand_year_jobs(), raises ConfigValidationError."""
    cfg = create_test_config()
    job = JobConfig(
        name="bad_year_range",
        params={"cmdCode": "440112"},
        output_file="comtrade_{cmdCode}_{period}.csv",
        all_years_start=2017,
        all_years_end=20018,
    )

    with pytest.raises(ConfigValidationError, match="too far in the future"):
        _expand_year_jobs(job, cfg, mode_name="single")

def test_expand_year_jobs_with_explicit_years():
    cfg = create_test_config()
    job = JobConfig(
        name="test",
        params={"cmdCode": "441012"},
        output_file="comtrade_{cmdCode}_{period}.csv",
        all_years_start=2023,
        all_years_end=2025,
    )

    expanded = _expand_year_jobs(job, cfg, mode_name="single")

    assert len(expanded) == 3
    assert [j.params["period"] for j in expanded] == ["2023", "2024", "2025"]
    assert [j.name for j in expanded] == ["test_2023", "test_2024", "test_2025"]


def test_expand_cmd_code_jobs():
    job = JobConfig(
        name="wood",
        params={"cmdCode": ["441012", "441011"]},
        output_file="comtrade_{cmdCode}_{period}.csv",
    )

    expanded = _expand_cmd_code_jobs(job)

    assert len(expanded) == 2
    assert expanded[0].params["cmdCode"] == "441012"
    assert expanded[1].params["cmdCode"] == "441011"
    assert expanded[0].name == "wood_441012"
    assert expanded[1].name == "wood_441011"


