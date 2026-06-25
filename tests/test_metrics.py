import pytest
from survey_finder.hardening.metrics import MetricsRegistry, metrics


def test_metrics_counter():
    metrics.reset()
    metrics.counter("test_counter", 1.0)
    metrics.counter("test_counter", 2.0)
    
    value = metrics.get_counter_value("test_counter")
    assert value == 3.0


def test_metrics_gauge():
    metrics.reset()
    metrics.gauge("test_gauge", 5.0)
    metrics.gauge("test_gauge", 10.0)
    
    value = metrics.get_gauge_value("test_gauge")
    assert value == 10.0


def test_metrics_histogram():
    metrics.reset()
    metrics.histogram("test_histogram", 100.0)
    metrics.histogram("test_histogram", 200.0)
    
    data = metrics.get_metrics("test_histogram")
    assert len(data["test_histogram"]) == 2
