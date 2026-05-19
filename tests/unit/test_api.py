import pytest
from comtrade_ingest.comtrade.api import (
    AuthConfig,
    build_query_params,
    redact_url,
    parse_retry_after_seconds,
    validate_auth_preflight,
)


def test_redact_url_removes_sensitive_token():
    url = "https://example.com/data?token=secret123&cmdCode=441012"
    redacted = redact_url(url)

    assert "secret123" not in redacted
    assert "token=%2A%2A%2A" in redacted or "token=***" in redacted
    assert "cmdCode=441012" in redacted


def test_parse_retry_after_seconds_from_text():
    text = "Rate limit exceeded. Try again in 17 seconds."
    assert parse_retry_after_seconds(text, fallback=2.0) == 17.0


def test_parse_retry_after_seconds_uses_fallback():
    assert parse_retry_after_seconds("no wait info", fallback=5.0) == 5.0


def test_build_query_params_omits_all_flow_code():
    auth = AuthConfig(
        enabled=False,
        method="header",
        header_name="Ocp-Apim-Subscription-Key",
        env_var_name="COMTRADE_API_KEY",
        query_param_name="token",
        env_file=None,
    )

    params = build_query_params(
        default_params={"format": "csv", "maxRecords": 250000},
        job_params={"cmdCode": "441012", "flowCode": "-1"},
        auth=auth,
    )

    assert params["cmdCode"] == "441012"
    assert "flowCode" not in params


def test_validate_auth_preflight_raises_when_token_missing(monkeypatch):
    monkeypatch.delenv("COMTRADE_API_KEY", raising=False)

    auth = AuthConfig(
        enabled=True,
        method="header",
        header_name="Ocp-Apim-Subscription-Key",
        env_var_name="COMTRADE_API_KEY",
        query_param_name="token",
        env_file=None,
    )

    with pytest.raises(ValueError, match="Missing token variable"):
        validate_auth_preflight(auth)