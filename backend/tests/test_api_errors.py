import json

from app.core.api_response import exception_response


def test_exception_response_logs_safe_context_without_exposing_exception(caplog):
    try:
        raise RuntimeError("sensitive-provider-response")
    except RuntimeError as exc:
        response = exception_response("Operation failed", exc)

    payload = json.loads(response.body)
    assert response.status_code == 500
    assert payload["details"] == "An unexpected server error occurred."
    assert "RuntimeError" in caplog.text
    assert "sensitive-provider-response" not in caplog.text
    assert "sensitive-provider-response" not in payload["details"]