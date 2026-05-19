import pytest

from comtrade_ingest.configs.config import _load_jobs


def test_bulk_years_requires_start():
    section_cfg = {
        "jobs": [
            {
                "name": "hs_all_reporters",
                "params": {
                    "typeCode": "C",
                    "freqCode": "A",
                    "clCode": "HS",
                    "reporterCode": "all",
                    "partnerCode": "all",
                },
                "output_file": "Comtrade_bulk_HS_{period}_all_reporters.zip",
                "years": {
                    "start": None,
                    "end": 2025,
                },
            }
        ]
    }

    with pytest.raises(ValueError, match="years requires both start and end"):
        _load_jobs("bulk", section_cfg)


def test_bulk_years_requires_end():
    section_cfg = {
        "jobs": [
            {
                "name": "hs_all_reporters",
                "params": {
                    "typeCode": "C",
                    "freqCode": "A",
                    "clCode": "HS",
                    "reporterCode": "all",
                    "partnerCode": "all",
                },
                "output_file": "Comtrade_bulk_HS_{period}_all_reporters.zip",
                "years": {
                    "start": 2024,
                    "end": None,
                },
            }
        ]
    }

    with pytest.raises(ValueError, match="years requires both start and end"):
        _load_jobs("bulk", section_cfg)


def test_bulk_years_parses_valid_range():
    section_cfg = {
        "jobs": [
            {
                "name": "hs_all_reporters",
                "params": {
                    "typeCode": "C",
                    "freqCode": "A",
                    "clCode": "HS",
                    "reporterCode": "all",
                    "partnerCode": "all",
                },
                "output_file": "Comtrade_bulk_HS_{period}_all_reporters.zip",
                "years": {
                    "start": 2024,
                    "end": 2025,
                },
            }
        ]
    }

    jobs = _load_jobs("bulk", section_cfg)

    assert len(jobs) == 1
    assert jobs[0].all_years_start == 2024
    assert jobs[0].all_years_end == 2025

def test_single_reference_false_requires_fallback_years():
    section_cfg = {
        "jobs": [
            {
                "name": "wood_panel_direct",
                "params": {
                    "reporterCode": None,
                    "partnerCode": None,
                    "cmdCode": "440112",
                    "flowCode": "FLOW_ALL",
                },
                "output_file": "comtrade_{cmdCode}_{period}.csv",
                "use_reference_years": False,
                "fallback_years_start": None,
                "fallback_years_end": None,
            }
        ]
    }

    with pytest.raises(ValueError, match="use_reference_years=false"):
        _load_jobs("single", section_cfg)


def test_single_reference_false_parses_fallback_years():
    section_cfg = {
        "jobs": [
            {
                "name": "wood_panel_direct",
                "params": {
                    "reporterCode": None,
                    "partnerCode": None,
                    "cmdCode": "440112",
                    "flowCode": "FLOW_ALL",
                },
                "output_file": "comtrade_{cmdCode}_{period}.csv",
                "use_reference_years": False,
                "fallback_years_start": 2020,
                "fallback_years_end": 2021,
            }
        ]
    }

    jobs = _load_jobs("single", section_cfg)

    assert len(jobs) == 1
    assert jobs[0].use_reference_years is False
    assert jobs[0].fallback_years_start == 2020
    assert jobs[0].fallback_years_end == 2021

def test_bulk_years_start_cannot_be_after_end():
    section_cfg = {
        "jobs": [
            {
                "name": "hs_all_reporters",
                "params": {
                    "typeCode": "C",
                    "freqCode": "A",
                    "clCode": "HS",
                    "reporterCode": "all",
                    "partnerCode": "all",
                },
                "output_file": "Comtrade_bulk_HS_{period}_all_reporters.zip",
                "years": {
                    "start": 2025,
                    "end": 2024,
                },
            }
        ]
    }

    with pytest.raises(ValueError, match="greater than"):
        _load_jobs("bulk", section_cfg)