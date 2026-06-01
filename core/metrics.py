# core/metrics.py
"""
JAQ-AI v2.0 — Metrics Toplama Modülü

In-memory istatistikler (bot restart'ta sıfırlanır):
  - Toplam istek sayısı
  - Agent kullanım dağılımı
  - Ortalama / min / max yanıt süresi
  - Hata sayısı ve oranı
  - Rate limit red sayısı

Kullanım:
    metrics = get_metrics()
    metrics.record_request(agent="ResearchAgent", duration_s=4.2, success=True)
    stats = metrics.get_stats()
"""

from __future__ import annotations

import time
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class AgentStats:
    """Tek bir agent için istatistikler."""
    count: int = 0
    errors: int = 0
    total_duration: float = 0.0
    min_duration: float = float("inf")
    max_duration: float = 0.0

    def record(self, duration_s: float, success: bool) -> None:
        self.count += 1
        if not success:
            self.errors += 1
        self.total_duration += duration_s
        self.min_duration = min(self.min_duration, duration_s)
        self.max_duration = max(self.max_duration, duration_s)

    @property
    def avg_duration(self) -> float:
        return round(self.total_duration / self.count, 2) if self.count else 0.0

    @property
    def error_rate(self) -> float:
        return round(self.errors / self.count * 100, 1) if self.count else 0.0


class MetricsCollector:
    """
    Thread-safe, in-memory metrics toplayıcı.
    Bot başladığı andan itibaren tüm istatistikleri tutar.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._start_time = time.monotonic()
        self._total_requests = 0
        self._rate_limited = 0
        self._validation_errors = 0
        self._timeouts = 0
        self._agent_stats: dict[str, AgentStats] = defaultdict(AgentStats)

    def record_request(
        self,
        agent: str,
        duration_s: float,
        success: bool,
        chat_id: int = 0,
    ) -> None:
        """Bir isteği kaydet."""
        with self._lock:
            self._total_requests += 1
            self._agent_stats[agent].record(duration_s, success)
        logger.debug(f"Metrics: agent={agent}, {duration_s:.1f}s, ok={success}")

    def record_rate_limit(self) -> None:
        """Rate limit nedeniyle reddedilen istek."""
        with self._lock:
            self._rate_limited += 1

    def record_validation_error(self) -> None:
        """Input validation hatası."""
        with self._lock:
            self._validation_errors += 1

    def record_timeout(self) -> None:
        """Zaman aşımı."""
        with self._lock:
            self._timeouts += 1

    def get_stats(self) -> dict:
        """Tüm istatistikleri dict olarak döner."""
        with self._lock:
            uptime_s = int(time.monotonic() - self._start_time)
            uptime_h = uptime_s // 3600
            uptime_m = (uptime_s % 3600) // 60

            agent_breakdown = {}
            for name, stats in self._agent_stats.items():
                agent_breakdown[name] = {
                    "count": stats.count,
                    "errors": stats.errors,
                    "error_rate_pct": stats.error_rate,
                    "avg_duration_s": stats.avg_duration,
                    "min_duration_s": round(stats.min_duration, 2) if stats.min_duration != float("inf") else 0,
                    "max_duration_s": round(stats.max_duration, 2),
                }

            total_errors = sum(s.errors for s in self._agent_stats.values())

            return {
                "uptime": f"{uptime_h}s {uptime_m}dk",
                "uptime_seconds": uptime_s,
                "total_requests": self._total_requests,
                "total_errors": total_errors,
                "error_rate_pct": round(total_errors / self._total_requests * 100, 1) if self._total_requests else 0,
                "rate_limited": self._rate_limited,
                "validation_errors": self._validation_errors,
                "timeouts": self._timeouts,
                "agents": agent_breakdown,
            }

    def format_for_telegram(self) -> str:
        """Telegram mesajı olarak formatlanmış istatistik metni."""
        s = self.get_stats()
        lines = [
            "📊 *JAQ İstatistikleri*\n",
            f"⏱ Çalışma süresi: `{s['uptime']}`",
            f"📨 Toplam istek: `{s['total_requests']}`",
            f"❌ Hata oranı: `{s['error_rate_pct']}%`",
            f"🚫 Rate limit: `{s['rate_limited']}`",
            f"⚠️ Validasyon hatası: `{s['validation_errors']}`",
            f"⏱ Zaman aşımı: `{s['timeouts']}`",
        ]

        if s["agents"]:
            lines.append("\n*Agent Dağılımı:*")
            sorted_agents = sorted(s["agents"].items(), key=lambda x: x[1]["count"], reverse=True)
            for name, a in sorted_agents:
                emoji = {
                    "ResearchAgent": "🔍",
                    "WriterAgent": "✍️",
                    "MarketAnalysisAgent": "📊",
                    "CodeAgent": "💻",
                    "DIRECT": "💬",
                }.get(name, "🤖")
                lines.append(
                    f"{emoji} {name}: `{a['count']}` istek, "
                    f"ort `{a['avg_duration_s']}s`, hata `{a['error_rate_pct']}%`"
                )

        return "\n".join(lines)


# ── Singleton ─────────────────────────────────────────────────────────────────

_metrics: MetricsCollector | None = None


def get_metrics() -> MetricsCollector:
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
        logger.info("MetricsCollector hazır.")
    return _metrics
