"""
Tier 3A — Performance Intelligence Bridge (metrun integration).

metrun profiluje ReDSL i identyfikuje bottlenecki per-funkcja.
Warstwy:
  1. Bottleneck Engine  — rankuje funkcje po score (czas × częstość × głębokość)
  2. Critical Path      — najdłuższa ścieżka wykonania blokująca pipeline
  3. Fix Suggestions    — konkretne propozycje optymalizacji

Jeśli metrun nie jest zainstalowany, moduł działa w trybie fallback
(cProfile + podstawowa analiza) bez zależności zewnętrznych.
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

_METRUN_RECORDS_DIR = Path(".metrun")


@dataclass
class Bottleneck:
    func: str
    time_ms: float
    calls: int
    score: float


@dataclass
class CriticalStep:
    func: str
    cumulative_ms: float


@dataclass
class PerformanceReport:
    total_time_ms: float
    bottlenecks: list[Bottleneck] = field(default_factory=list)
    critical_path: list[CriticalStep] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    source: str = "metrun"


def _metrun_available() -> bool:
    try:
        result = subprocess.run(
            ["metrun", "--version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _parse_metrun_output(stdout: str) -> PerformanceReport:
    """Parsuj wyjście `metrun inspect` (JSON lub plain text)."""
    if not stdout.strip():
        return PerformanceReport(total_time_ms=0.0, source="metrun-empty")

    try:
        data = json.loads(stdout)
        bottlenecks = [
            Bottleneck(
                func=b.get("func", "unknown"),
                time_ms=float(b.get("time_ms", 0)),
                calls=int(b.get("calls", 0)),
                score=float(b.get("score", 0)),
            )
            for b in data.get("bottlenecks", [])
        ]
        critical_path = [
            CriticalStep(
                func=s.get("func", "unknown"),
                cumulative_ms=float(s.get("cumulative_ms", 0)),
            )
            for s in data.get("critical_path", [])
        ]
        return PerformanceReport(
            total_time_ms=float(data.get("total_time_ms", 0)),
            bottlenecks=bottlenecks,
            critical_path=critical_path,
            suggestions=data.get("suggestions", []),
            source="metrun",
        )
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        logger.debug("metrun JSON parse failed (%s); using empty report", exc)
        return PerformanceReport(total_time_ms=0.0, source="metrun-parse-error")


def _fallback_profile(project_dir: Path) -> PerformanceReport:
    """Fallback — cProfile-based profiling when metrun is unavailable."""
    import cProfile
    import io
    import pstats
    import time

    pr = cProfile.Profile()
    pr.enable()
    start = time.perf_counter()

    try:
        from redsl.analyzers import CodeAnalyzer
        CodeAnalyzer().analyze_project(project_dir)
    except Exception as exc:
        logger.debug("Fallback profile target failed: %s", exc)

    elapsed_ms = (time.perf_counter() - start) * 1000
    pr.disable()

    buf = io.StringIO()
    ps = pstats.Stats(pr, stream=buf).sort_stats("cumulative")
    ps.print_stats(10)

    bottlenecks: list[Bottleneck] = []
    for line in buf.getvalue().splitlines():
        parts = line.split()
        if len(parts) >= 6 and parts[0].replace(".", "", 1).isdigit():
            try:
                calls = int(parts[0])
                cumtime = float(parts[3])
                func_name = parts[-1]
                score = cumtime * calls
                bottlenecks.append(
                    Bottleneck(
                        func=func_name,
                        time_ms=cumtime * 1000,
                        calls=calls,
                        score=score,
                    )
                )
            except (ValueError, IndexError):
                continue

    bottlenecks.sort(key=lambda b: b.score, reverse=True)
    suggestions = []
    if bottlenecks:
        top = bottlenecks[0]
        suggestions.append(
            f"Hottest function: {top.func} ({top.time_ms:.0f}ms, {top.calls} calls)"
        )

    return PerformanceReport(
        total_time_ms=elapsed_ms,
        bottlenecks=bottlenecks[:10],
        critical_path=[],
        suggestions=suggestions,
        source="cprofile-fallback",
    )


def profile_refactor_cycle(project_dir: Path) -> PerformanceReport:
    """Profiluj jeden cykl analizy/refaktoryzacji za pomocą metrun (lub fallback)."""
    if not _metrun_available():
        logger.info("metrun not found — using cProfile fallback")
        return _fallback_profile(project_dir)

    _METRUN_RECORDS_DIR.mkdir(exist_ok=True)
    records_path = _METRUN_RECORDS_DIR / "last.json"

    subprocess.run(
        [
            "metrun", "scan",
            str(project_dir),
            "--records", str(records_path),
        ],
        capture_output=True,
    )

    result = subprocess.run(
        [
            "metrun", "inspect",
            "-m", "redsl.orchestrator",
            "--format", "json",
            "--", str(project_dir),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        logger.warning("metrun inspect failed (rc=%d): %s", result.returncode, result.stderr[:200])
        return _fallback_profile(project_dir)

    return _parse_metrun_output(result.stdout)


def profile_llm_latency() -> dict:
    """Zmierz latencję wywołań LLM — kluczowy bottleneck.

    Returns dict with keys: avg_ms, p95_ms, p99_ms, total_calls.
    Requires metrun with cprofile_bridge; returns empty dict otherwise.
    """
    if not _metrun_available():
        return {}

    result = subprocess.run(
        [
            "metrun", "trace",
            "--target", "redsl.llm.LLMLayer.call",
            "--format", "json",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    try:
        return json.loads(result.stdout) if result.returncode == 0 else {}
    except (json.JSONDecodeError, ValueError):
        return {}


def profile_memory_operations() -> dict:
    """Zmierz czas operacji ChromaDB — store, recall, similarity search.

    Returns dict with per-operation avg_ms stats.
    Requires metrun; returns empty dict otherwise.
    """
    if not _metrun_available():
        return {}

    targets = [
        "redsl.memory.AgentMemory.store_strategy",
        "redsl.memory.AgentMemory.recall_similar_actions",
    ]
    result = subprocess.run(
        [
            "metrun", "trace",
            "--target", ",".join(targets),
            "--format", "json",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    try:
        return json.loads(result.stdout) if result.returncode == 0 else {}
    except (json.JSONDecodeError, ValueError):
        return {}


def generate_optimization_report(project_dir: Path) -> str:
    """Wygeneruj raport z sugestiami optymalizacji (używany przez CLI i loop)."""
    perf = profile_refactor_cycle(project_dir)

    lines = [
        f"Total cycle time: {perf.total_time_ms:.0f}ms  [source: {perf.source}]",
        f"Bottlenecks ({len(perf.bottlenecks)}):",
    ]
    for b in perf.bottlenecks[:5]:
        lines.append(
            f"  {b.func}: {b.time_ms:.0f}ms "
            f"({b.calls} calls, score={b.score:.1f})"
        )

    if perf.critical_path:
        lines.append(f"\nCritical path ({len(perf.critical_path)} steps):")
        for step in perf.critical_path:
            lines.append(f"  → {step.func}: +{step.cumulative_ms:.0f}ms")

    if perf.suggestions:
        lines.append("\nSuggestions:")
        for s in perf.suggestions:
            lines.append(f"  • {s}")

    return "\n".join(lines)
