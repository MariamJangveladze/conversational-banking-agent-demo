from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from app.demo_bank import DemoBankService
from app.sessions import SessionRegistry
from app.telemetry import TraceRecorder
from app.workflow import BankingWorkflow

HOST = "127.0.0.1"
PORT = 8000
MAX_BODY_BYTES = 16_384
MAX_MESSAGE_CHARS = 800


def build_handler(
    registry: SessionRegistry | None = None,
    workflow: BankingWorkflow | None = None,
) -> type[BaseHTTPRequestHandler]:
    registry = registry or SessionRegistry()
    traces = TraceRecorder()
    workflow = workflow or BankingWorkflow(DemoBankService(), traces)
    allowed_origin = os.getenv("ALLOWED_ORIGIN", "http://127.0.0.1:8080")

    class Handler(BaseHTTPRequestHandler):
        def do_OPTIONS(self) -> None:
            self._respond(HTTPStatus.NO_CONTENT, {})

        def do_GET(self) -> None:
            if self.path == "/health":
                self._respond(HTTPStatus.OK, {"status": "ok", "mode": "synthetic-demo"})
            elif self.path == "/api/telemetry":
                self._respond(HTTPStatus.OK, {"traces": traces.snapshot()})
            else:
                self._respond(HTTPStatus.NOT_FOUND, {"error": "not_found"})

        def do_POST(self) -> None:
            try:
                data = self._read_json()
                if self.path == "/api/chat/start":
                    session = registry.create()
                    self._respond(HTTPStatus.CREATED, {
                        "session_id": session.session_id,
                        "access_token": session.access_token,
                        "reply": "Welcome to Northstar, a synthetic banking-agent demo. No real account or money is connected.",
                    })
                    return
                if self.path == "/api/chat/message":
                    session_id = str(data.get("session_id", ""))
                    token = self.headers.get("X-Demo-Session-Token", "")
                    message = str(data.get("message", "")).strip()
                    if not message or len(message) > MAX_MESSAGE_CHARS:
                        self._respond(HTTPStatus.BAD_REQUEST, {"error": "invalid_message"})
                        return
                    session, session_lock = registry.authorized(session_id, token)
                    with session_lock:
                        self._respond(HTTPStatus.OK, workflow.handle(session, message))
                    return
                self._respond(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            except ValueError as exc:
                self._respond(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            except PermissionError:
                self._respond(HTTPStatus.UNAUTHORIZED, {"error": "invalid_or_expired_session"})
            except RuntimeError:
                self._respond(HTTPStatus.TOO_MANY_REQUESTS, {"error": "capacity_reached"})
            except Exception:
                self._respond(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "request_failed"})

        def _read_json(self) -> dict[str, Any]:
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise ValueError("invalid_content_length") from exc
            if content_length <= 0 or content_length > MAX_BODY_BYTES:
                raise ValueError("invalid_body_size")
            try:
                payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError("invalid_json") from exc
            if not isinstance(payload, dict):
                raise ValueError("json_object_required")
            return payload

        def _respond(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            origin = self.headers.get("Origin")
            if origin == allowed_origin:
                self.send_header("Access-Control-Allow-Origin", allowed_origin)
                self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type,X-Demo-Session-Token")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *args: object) -> None:
            return

    return Handler


def serve() -> None:
    server = ThreadingHTTPServer((HOST, PORT), build_handler())
    print(f"Northstar demo API: http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    serve()
