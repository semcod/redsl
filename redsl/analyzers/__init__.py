"""
Analizator kodu — parser plików toon.yaml + metryki.

Konwertuje dane z:
- project_toon.yaml  (health, alerts, hotspots)
- analysis_toon.yaml (layers, CC, pipelines)
- evolution_toon.yaml (recommendations, risks)
- duplication_toon.yaml (duplicate blocks)
- validation_toon.yaml (linter errors, warnings)

na zunifikowane konteksty DSL do ewaluacji przez DSLEngine.

Backward compatibility re-exports - all symbols available from submodules.
"""

from __future__ import annotations

# Re-export all public symbols from submodules for backward compatibility
from . import code2llm_bridge, redup_bridge
from .analyzer import CodeAnalyzer
from .incremental import EvolutionaryCache, IncrementalAnalyzer, get_changed_files
from .semantic_chunker import SemanticChunk, SemanticChunker
from .metrics import AnalysisResult, CodeMetrics
from .parsers import ToonParser
from .python_analyzer import PythonAnalyzer, ast_cyclomatic_complexity, ast_max_nesting_depth
from .radon_analyzer import is_radon_available, run_radon_cc, enhance_metrics_with_radon
from .resolver import PathResolver
from .toon_analyzer import ToonAnalyzer
from .utils import _load_gitignore_patterns, _should_ignore_file, _try_number

__all__ = [
    # Facade
    "CodeAnalyzer",
    # Specialized analyzers
    "ToonAnalyzer",
    "PythonAnalyzer",
    "PathResolver",
    # Incremental analysis
    "IncrementalAnalyzer",
    "EvolutionaryCache",
    "get_changed_files",
    # Semantic chunker
    "SemanticChunker",
    "SemanticChunk",
    # Bridges
    "code2llm_bridge",
    "redup_bridge",
    # Data classes
    "CodeMetrics",
    "AnalysisResult",
    # Parsers
    "ToonParser",
    # Utilities
    "ast_cyclomatic_complexity",
    "ast_max_nesting_depth",
    "_load_gitignore_patterns",
    "_should_ignore_file",
    "_try_number",
    # Radon integration (T008)
    "is_radon_available",
    "run_radon_cc",
    "enhance_metrics_with_radon",
]
