import comtrade_ingest.reference.hs_sets as hs_sets


def test_get_hs_valid_year_range_returns_local_override(monkeypatch):
    """Reference lookup should return LOCAL_HS_VALID_YEARS when available."""
    monkeypatch.setattr(
        hs_sets,
        "LOCAL_HS_VALID_YEARS",
        {
            "123456": (2001, 2005),
        },
    )

    start, end = hs_sets.get_hs_valid_year_range(
        cmd_code="123456",
        fallback_start=2010,
        fallback_end=2020,
    )

    assert start == 2001
    assert end == 2005


def test_get_hs_valid_year_range_uses_fallback(monkeypatch):
    monkeypatch.setattr(hs_sets, "LOCAL_HS_VALID_YEARS", {})

    start, end = hs_sets.get_hs_valid_year_range(
        cmd_code="999999",
        fallback_start=2010,
        fallback_end=2020,
    )

    assert start == 2010
    assert end == 2020