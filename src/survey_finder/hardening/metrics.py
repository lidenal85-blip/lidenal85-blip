from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import threading


@dataclass
class Metric:
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class MetricsRegistry:
    """Simple metrics registry (Prometheus-like)."""

    _instance: Optional["MetricsRegistry"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._metrics: Dict[str, List[Metric]] = {}
        return cls._instance

    def counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter."""
        metric = Metric(name=name, value=value, labels=labels or {})
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append(metric)

    def gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge value."""
        metric = Metric(name=name, value=value, labels=labels or {})
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append(metric)

    def histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram observation."""
        metric = Metric(name=name, value=value, labels=labels or {})
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append(metric)

    def get_metrics(self, name: Optional[str] = None) -> Dict[str, List[Metric]]:
        """Get all metrics or specific metric."""
        if name:
            return {name: self._metrics.get(name, [])}
        return self._metrics.copy()

    def get_counter_value(self, name: str) -> float:
        """Get total value of a counter."""
        metrics = self._metrics.get(name, [])
        return sum(m.value for m in metrics)

    def get_gauge_value(self, name: str) -> Optional[float]:
        """Get latest gauge value."""
        metrics = self._metrics.get(name, [])
        if metrics:
            return metrics[-1].value
        return None

    def reset(self) -> None:
        """Reset all metrics."""
        self._metrics.clear()


# Global metrics instance
metrics = MetricsRegistry()


def record_pipeline_metrics(cycle_id: str, step: str, duration_ms: float, success: bool):
    """Record pipeline step metrics."""
    metrics.histogram(
        "pipeline_step_duration_ms",
        duration_ms,
        {"step": step}
    )
    metrics.counter(
        "pipeline_step_total",
        1,
        {"step": step, "status": "success" if success else "failure"}
    )


def record_survey_metrics(source: str, status: str):
    """Record survey processing metrics."""
    metrics.counter(
        "survey_processed_total",
        1,
        {"source": source, "status": status}
    )


def record_circuit_breaker_metrics(name: str, state: str):
    """Record circuit breaker state changes."""
    metrics.gauge(
        "circuit_breaker_state",
        1 if state == "open" else 0,
        {"name": name}
    )
