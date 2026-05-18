import pytest
from comtrade_ingest.reference.hs_sets import get_hs_valid_year_range


def test_get_hs_valid_year_range_returns_local_override():
    """Reference lookup should return LOCAL_HS_VALID_YEARS when available."""
    start, end = get_hs_valid_year_range(
        cmd_code="440112",
        fallback_start=2010,
        fallback_end=2020,
    )
    # LOCAL_HS_VALID_YEARS has "440112": (2017, 2025)
    assert start == 2017
    assert end == 2025


def test_get_hs_valid_year_range_uses_fallback():
    """Reference lookup should use fallback when cmdCode not found."""
    start, end = get_hs_valid_year_range(
        cmd_code="999999",
        fallback_start=2010,
        fallback_end=2020,
    )
    assert start == 2010
    assert end == 2020