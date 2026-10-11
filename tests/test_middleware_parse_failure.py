"""Middleware rejects a body it cannot parse — DEF-03 (FR-7).

The inherited middleware wrapped body parsing in a broad ``except`` and, on
failure, passed the request through to the application **unscanned**. That
turns a malformed body into a way past the scanner: send something the JSON
parser chokes on and the content is never inspected.

FR-7 requires the opposite: content that cannot be parsed is never passed
through. A request whose body cannot be read is refused with a 4xx.
"""

from __future__ import annotations

import json

import pytest

fastapi = pytest.importorskip("fastapi", reason="fastapi extra not installed")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from cosmac.integrations.fastapi_middleware import CosmacASGIMiddleware  # noqa: E402


@pytest.fixture
def client(tmp_path):
    app = FastAPI()
    app.add_middleware(CosmacASGIMiddleware, data_dir=str(tmp_path))

    @app.post("/echo")
    async def echo(payload: dict):  # pragma: no cover - exercised via client
        return {"seen": payload}

    return TestClient(app, raise_server_exceptions=False)


class TestUnparseableBodyIsRefused:
    def test_malformed_json_gets_4xx(self, client):
        response = client.post(
            "/echo",
            content=b'{"text": "hello"',  # truncated: no closing brace
            headers={"content-type": "application/json"},
        )
        assert 400 <= response.status_code < 500, (
            f"expected a 4xx for an unparseable body, got {response.status_code}; "
            "passing it through means the content was never scanned (FR-7)"
        )

    def test_invalid_utf8_gets_4xx(self, client):
        response = client.post(
            "/echo",
            content=b"\xff\xfe\x00\x01 not utf-8",
            headers={"content-type": "application/json"},
        )
        assert 400 <= response.status_code < 500

    def test_refusal_does_not_reach_the_application(self, client):
        """The body must not arrive at the route handler."""
        response = client.post(
            "/echo",
            content=b"{oops",
            headers={"content-type": "application/json"},
        )
        assert 400 <= response.status_code < 500
        assert "seen" not in response.text

    def test_well_formed_body_still_passes(self, client):
        response = client.post(
            "/echo",
            content=json.dumps({"text": "What is the weather today?"}).encode(),
            headers={"content-type": "application/json"},
        )
        assert response.status_code == 200
        assert response.json()["seen"]["text"] == "What is the weather today?"

    def test_error_names_the_problem(self, client):
        """An operator reading logs should see why, not a generic 400."""
        response = client.post(
            "/echo",
            content=b"{oops",
            headers={"content-type": "application/json"},
        )
        body = response.text.lower()
        assert any(word in body for word in ("parse", "decode", "malformed", "invalid")), (
            f"refusal gave no reason: {response.text[:200]}"
        )


class TestFlaskMiddlewareRefuses:
    """DEF-03 requires a negative test for Flask as well as FastAPI."""

    def test_malformed_body_does_not_reach_the_app(self, tmp_path):
        import io
        import json as _json

        from cosmac.integrations.flask_middleware import CosmacFlaskMiddleware

        reached = []

        def app(environ, start_response):  # pragma: no cover - must not run
            reached.append(True)
            start_response("200 OK", [("Content-Type", "application/json")])
            return [b"{}"]

        middleware = CosmacFlaskMiddleware(app)
        body = b"{not json"
        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": io.BytesIO(body),
        }
        statuses = []
        result = middleware(environ, lambda s, h: statuses.append(s))

        assert not reached, "unparseable body reached the application (FR-7)"
        assert statuses and statuses[0].startswith("400")
        assert "parse" in _json.loads(b"".join(result))["detail"].lower()

    def test_well_formed_body_reaches_the_app(self, tmp_path):
        import io
        import json as _json

        from cosmac.integrations.flask_middleware import CosmacFlaskMiddleware

        reached = []

        def app(environ, start_response):
            reached.append(True)
            start_response("200 OK", [("Content-Type", "application/json")])
            return [b"{}"]

        middleware = CosmacFlaskMiddleware(app)
        body = _json.dumps({"prompt": "What is the weather today?"}).encode()
        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": io.BytesIO(body),
        }
        middleware(environ, lambda s, h: None)
        assert reached, "a well-formed benign body should pass through"


class TestDjangoMiddlewareRefuses:
    """DEF-03 requires a negative test for Django as well."""

    def test_malformed_body_does_not_reach_the_view(self):
        django = pytest.importorskip("django", reason="django extra not installed")
        from django.conf import settings

        if not settings.configured:
            settings.configure(DEBUG=True, DEFAULT_CHARSET="utf-8")
            django.setup()

        from cosmac.integrations.django_middleware import CosmacDjangoMiddleware

        reached = []

        def get_response(request):  # pragma: no cover - must not run
            reached.append(True)
            return "view-response"

        class FakeRequest:
            body = b"{not json"
            method = "POST"

        middleware = CosmacDjangoMiddleware(get_response)
        response = middleware(FakeRequest())

        assert not reached, "unparseable body reached the view (FR-7)"
        assert getattr(response, "status_code", None) == 400
