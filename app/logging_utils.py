"""JSON structured logging + request-id propagation (draft — Package J).

Every log line becomes one JSON object (level/logger/message/request_id/
time) so a log aggregator can filter/correlate without regex-parsing text.
request_id_var is a contextvar set by RequestIdMiddleware per request and
read back by JsonFormatter — no explicit passing through call chains.
"""

import json
import logging
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Reads X-Request-Id from the inbound request (or generates one),
    makes it available to every log line emitted while handling this
    request (via request_id_var), and echoes it back in the response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        req_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        token = request_id_var.set(req_id)
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-Id"] = req_id
        return response
