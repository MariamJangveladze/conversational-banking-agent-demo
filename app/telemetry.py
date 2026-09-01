from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Self


@dataclass(frozen=True)
class Trace:
    operation: str
    latency_ms: int
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    outcome: str = "ok"


class TraceRecorder:
    """In-memory demo telemetry. It intentionally stores no message bodies or PII."""

    def __init__(self) -> None:
        self._traces: list[Trace] = []

    def record(self, trace: Trace) -> None:
        self._traces.append(trace)
        self._traces = self._traces[-100:]

    def snapshot(self) -> list[dict[str, Any]]:
        return [trace.__dict__ for trace in self._traces]


class Timer:
    def __enter__(self) -> Self:
        self._started = perf_counter()
        return self

    def __exit__(self, *_: object) -> None:
        self.latency_ms = round((perf_counter() - self._started) * 1000)
