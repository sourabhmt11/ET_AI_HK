"""FastAPI middleware for cosmac HTTP request scanning."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import JSONResponse, Response
except ImportError as err:
    raise ImportError("Install fastapi extras: pip install cosmac[fastapi]") from err

from cosmac.engine import CosmacEngine
from cosmac.models import Action

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request


class CosmacASGIMiddleware(BaseHTTPMiddleware):
    """FastAPI/Starlette middleware that scans request bodies for prompt injection."""

    def __init__(
        self,
        app: Any,
        config_path: str | None = None,
        mode: str = "block",
        scan_fields: list[str] | None = None,
        on_detection: Callable[..., Awaitable[None]] | None = None,
        allow_unparsed: bool = False,
        data_dir: str | None = None,
    ) -> None:
        super().__init__(app)
        self.engine = CosmacEngine(
            config_path=config_path,
            config_dict={"mode": mode} if mode != "block" else None,
            data_dir=data_dir,
        )
        self.scan_fields = scan_fields or ["body.prompt", "body.messages.*.content"]
        self.on_detection = on_detection
        #: DEF-03 / FR-7. False (the default) refuses a body this middleware
        #: cannot parse. Set True only when something else in the stack
        #: scans the content - it reinstates the inherited behaviour of
        #: forwarding unscanned bodies.
        self.allow_unparsed = allow_unparsed

    #: Content types this middleware knows how to read. A body in any other
    #: type cannot be scanned, so by default it is refused rather than
    #: forwarded (FR-7). Operators who terminate scanning elsewhere can widen
    #: this, or set ``allow_unparsed=True``.
    _PARSEABLE_TYPES = ("application/json", "+json", "text/json")

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        if request.method not in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        raw = await request.body()
        if not raw:
            # Nothing to scan. A bodyless POST is not a parse failure.
            return await call_next(request)

        content_type = request.headers.get("content-type", "").lower()
        if content_type and not any(t in content_type for t in self._PARSEABLE_TYPES):
            if self.allow_unparsed:
                return await call_next(request)
            return JSONResponse(
                status_code=415,
                content={
                    "error": "Unsupported media type",
                    "detail": (
                        f"COSMAC cannot parse {content_type!r}, so this body "
                        "cannot be scanned. It was refused rather than "
                        "forwarded unscanned (FR-7). Set allow_unparsed=True "
                        "if scanning happens elsewhere in your stack."
                    ),
                },
            )

        # DEF-03 / FR-7. The inherited code swallowed every parse error and
        # called the application anyway, so sending a malformed body was a
        # way to skip the scanner entirely. A body that cannot be parsed is
        # now refused.
        try:
            body = json.loads(raw)
        except (ValueError, UnicodeDecodeError) as exc:
            if self.allow_unparsed:
                return await call_next(request)
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Malformed request body",
                    "detail": (
                        f"Could not parse the request body as JSON: {exc}. "
                        "It was refused rather than forwarded unscanned "
                        "(FR-7)."
                    ),
                },
            )

        texts_to_scan = self._extract_fields(body)
        for text in texts_to_scan:
            if not text or not isinstance(text, str):
                continue
            report = self.engine.scan(text, context={"gate": "http", "source": "fastapi"})
            if report.action == Action.BLOCK:
                if self.on_detection:
                    await self.on_detection(request, report)
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Prompt injection detected",
                        "scan_id": report.scan_id,
                        "risk_score": report.overall_risk_score,
                    },
                )
        return await call_next(request)

    def _extract_fields(self, body: Any) -> list[str]:
        """Extract text fields from request body based on scan_fields config."""
        texts: list[str] = []
        for field_path in self.scan_fields:
            parts = field_path.replace("body.", "", 1).split(".")
            texts.extend(self._resolve_path(body, parts))
        return texts

    def _resolve_path(self, obj: Any, parts: list[str]) -> list[str]:
        if not parts:
            return [str(obj)] if obj else []
        key = parts[0]
        rest = parts[1:]
        if key == "*" and isinstance(obj, list):
            results: list[str] = []
            for item in obj:
                results.extend(self._resolve_path(item, rest))
            return results
        if isinstance(obj, dict) and key in obj:
            return self._resolve_path(obj[key], rest)
        return []
