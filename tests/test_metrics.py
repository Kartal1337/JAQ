# tests/test_metrics.py
"""Metrics collector birim testleri."""

import pytest
from core.metrics import MetricsCollector


@pytest.fixture
def metrics():
    return MetricsCollector()


def test_baslangicta_sifir(metrics):
    stats = metrics.get_stats()
    assert stats["total_requests"] == 0
    assert stats["rate_limited"] == 0


def test_istek_kaydedilir(metrics):
    metrics.record_request(agent="ResearchAgent", duration_s=2.5, success=True)
    stats = metrics.get_stats()
    assert stats["total_requests"] == 1
    assert "ResearchAgent" in stats["agents"]
    assert stats["agents"]["ResearchAgent"]["count"] == 1


def test_hata_orani_hesaplanir(metrics):
    metrics.record_request(agent="CodeAgent", duration_s=1.0, success=True)
    metrics.record_request(agent="CodeAgent", duration_s=1.0, success=False)
    stats = metrics.get_stats()
    assert stats["agents"]["CodeAgent"]["error_rate_pct"] == 50.0


def test_rate_limit_sayilir(metrics):
    metrics.record_rate_limit()
    metrics.record_rate_limit()
    stats = metrics.get_stats()
    assert stats["rate_limited"] == 2


def test_validation_error_sayilir(metrics):
    metrics.record_validation_error()
    stats = metrics.get_stats()
    assert stats["validation_errors"] == 1


def test_timeout_sayilir(metrics):
    metrics.record_timeout()
    stats = metrics.get_stats()
    assert stats["timeouts"] == 1


def test_ortalama_sure_hesaplanir(metrics):
    metrics.record_request(agent="WriterAgent", duration_s=2.0, success=True)
    metrics.record_request(agent="WriterAgent", duration_s=4.0, success=True)
    stats = metrics.get_stats()
    assert stats["agents"]["WriterAgent"]["avg_duration_s"] == 3.0


def test_format_for_telegram_string(metrics):
    metrics.record_request(agent="DIRECT", duration_s=0.5, success=True)
    text = metrics.format_for_telegram()
    assert "JAQ İstatistikleri" in text
    assert "DIRECT" in text
