"""Run counters: actions, model calls, recoveries, cache hits, reuse_gain."""

from __future__ import annotations

import json
import time
from pathlib import Path

from .models import RunMetrics

REPO_ROOT = Path(__file__).resolve().parents[1]
METRICS_PATH = REPO_ROOT / "fixtures" / "live" / "run-metrics.json"

_product = ""
_actions = 0
_model_calls = 0
_recoveries = 0
_cache_hits = 0
_started = 0.0


def start_run(product: str) -> None:
    global _product, _actions, _model_calls, _recoveries, _cache_hits, _started
    _product = product
    _actions = 0
    _model_calls = 0
    _recoveries = 0
    _cache_hits = 0
    _started = time.time()


def record_action(n: int = 1) -> None:
    global _actions
    _actions += n


def record_model_call(n: int = 1) -> None:
    global _model_calls
    _model_calls += n


def record_recovery(n: int = 1) -> None:
    global _recoveries
    _recoveries += n


def record_cache_hit(n: int = 1) -> None:
    global _cache_hits
    _cache_hits += n


def snapshot() -> RunMetrics:
    latency = int((time.time() - _started) * 1000) if _started else 0
    return RunMetrics(
        product=_product,
        actions=_actions,
        model_calls=_model_calls,
        recoveries=_recoveries,
        cache_hits=_cache_hits,
        latency_ms=latency,
    )


def reuse_gain(first: RunMetrics, second: RunMetrics) -> dict[str, int]:
    return {
        "actions": first.actions - second.actions,
        "model_calls": first.model_calls - second.model_calls,
        "recoveries": first.recoveries - second.recoveries,
    }


def format_reuse_gain(first: RunMetrics, second: RunMetrics) -> str:
    gain = reuse_gain(first, second)
    return (
        "reuse_gain:\n"
        f"  actions: {first.actions} - {second.actions} = {gain['actions']}\n"
        f"  model_calls: {first.model_calls} - {second.model_calls} = {gain['model_calls']}\n"
        f"  recoveries: {first.recoveries} - {second.recoveries} = {gain['recoveries']}"
    )


def write_run_metrics(
    first: RunMetrics,
    second: RunMetrics,
    path: Path | None = None,
) -> Path:
    destination = path or METRICS_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "first": first.model_dump(),
        "second": second.model_dump(),
        "reuse_gain": reuse_gain(first, second),
    }
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return destination
