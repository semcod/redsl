"""Testy analizatora kodu — parser toon.yaml + metryki."""

from pathlib import Path

import pytest

from redsl.analyzers import CodeAnalyzer, CodeMetrics, ToonParser
from redsl.analyzers.utils import _matches_gitignore_patterns, _should_ignore_file


SAMPLE_PROJECT_TOON = """
# nlp2dsl | 177 func | 29f | 8279L | python | 2026-04-07

HEALTH:
  CC̄=3.2  critical=10 (limit:10)  dup=3  cycles=0

ALERTS[20]:
  !!! cc_exceeded      _extract_entities = 36 (limit:15)
  !!! high_fan_out     _extract_entities = 26 (limit:10)
  !!  high_fan_out     run_workflow = 18 (limit:10)
  !!  high_fan_out     _process_message = 18 (limit:10)
  !   cc_exceeded      _process_message = 17 (limit:15)

MODULES[41] (top by size):
  M[nlp-service/app/main.py] 522L C:0 F:20 CC↑10 D:0 (python)
  M[nlp-service/app/registry.py] 352L C:0 F:4 CC↑5 D:3 (python)
  M[nlp-service/app/parser_rules.py] 274L C:0 F:5 CC↑36 D:2 (python)

HOTSPOTS[10]:
  ★ _extract_entities fan=26
  ★ run_workflow fan=18
  ★ _process_message fan=18

REFACTOR[7]:
  [1] H/L Split _extract_entities (CC=36)
  [2] H/H Split god module nlp-service/app/main.py (522L)
"""


SAMPLE_DUPLICATION_TOON = """
# redup/duplication | 10 groups | 33f 5056L | 2026-04-07

DUPLICATES[10] (ranked by impact):
  [1899ff8e67d31c77] ! STRU  setup_logging  L=25 N=3 saved=50 sim=1.00
      nlp-service/app/logging_setup.py:0-24  (setup_logging)
      backend/app/logging_setup.py:0-24  (setup_logging)
      worker/logging_setup.py:0-24  (setup_logging)
  [ce00be02a9b12238] ! STRU  generate_invoice_from_text  L=15 N=4 saved=45 sim=1.00
      examples/01-invoice/main.py:0-14  (generate_invoice_from_text)
      examples/02-email/main.py:0-14  (generate_email_from_text)
"""


class TestToonParser:
    def setup_method(self):
        self.parser = ToonParser()

    def test_parse_alerts(self):
        data = self.parser.parse_project_toon(SAMPLE_PROJECT_TOON)
        alerts = data["alerts"]
        assert len(alerts) >= 3
        assert alerts[0]["name"] == "_extract_entities"
        assert alerts[0]["value"] == 36
        assert alerts[0]["severity"] == 3  # !!!

    def test_parse_modules(self):
        data = self.parser.parse_project_toon(SAMPLE_PROJECT_TOON)
        modules = data["modules"]
        assert len(modules) == 3
        assert modules[0]["path"] == "nlp-service/app/main.py"
        assert modules[0]["lines"] == 522
        assert modules[0]["functions"] == 20
        assert modules[0]["max_cc"] == 10

    def test_parse_hotspots(self):
        data = self.parser.parse_project_toon(SAMPLE_PROJECT_TOON)
        hotspots = data["hotspots"]
        assert len(hotspots) >= 2
        assert hotspots[0]["name"] == "_extract_entities"
        assert hotspots[0]["fan_out"] == 26

    def test_parse_duplication(self):
        dups = self.parser.parse_duplication_toon(SAMPLE_DUPLICATION_TOON)
        assert len(dups) >= 1
        assert dups[0]["name"] == "setup_logging"
        assert dups[0]["lines"] == 25
        assert dups[0]["occurrences"] == 3
        assert dups[0]["similarity"] == 1.0


class TestCodeMetrics:
    def test_to_dsl_context(self):
        m = CodeMetrics(
            file_path="test.py",
            function_name="complex_func",
            cyclomatic_complexity=25,
            fan_out=15,
            module_lines=300,
        )
        ctx = m.to_dsl_context()
        assert ctx["file_path"] == "test.py"
        assert ctx["cyclomatic_complexity"] == 25
        assert ctx["fan_out"] == 15


class TestCodeAnalyzer:
    def test_analyze_from_toon_content(self):
        analyzer = CodeAnalyzer()
        result = analyzer.analyze_from_toon_content(
            project_toon=SAMPLE_PROJECT_TOON,
            duplication_toon=SAMPLE_DUPLICATION_TOON,
        )
        assert result.total_files > 0
        assert len(result.metrics) > 0
        assert len(result.alerts) > 0

    def test_metrics_include_alerts(self):
        analyzer = CodeAnalyzer()
        result = analyzer.analyze_from_toon_content(project_toon=SAMPLE_PROJECT_TOON)

        # Szukaj metryki _extract_entities z alertów
        entity_metrics = [
            m for m in result.metrics
            if m.function_name == "_extract_entities"
        ]
        assert len(entity_metrics) > 0
        assert entity_metrics[0].cyclomatic_complexity == 36

    def test_to_dsl_contexts(self):
        analyzer = CodeAnalyzer()
        result = analyzer.analyze_from_toon_content(project_toon=SAMPLE_PROJECT_TOON)
        contexts = result.to_dsl_contexts()
        assert len(contexts) > 0
        assert all("file_path" in c for c in contexts)


class TestIntegrationAnalyzerDSL:
    """Test integracji Analyzer → DSL Engine."""

    def test_full_pipeline(self):
        from redsl.dsl import DSLEngine

        analyzer = CodeAnalyzer()
        result = analyzer.analyze_from_toon_content(
            project_toon=SAMPLE_PROJECT_TOON,
            duplication_toon=SAMPLE_DUPLICATION_TOON,
        )

        engine = DSLEngine()
        contexts = result.to_dsl_contexts()
        decisions = engine.top_decisions(contexts, limit=5)

        # Powinny być decyzje — mamy CC=36 i god module
        assert len(decisions) > 0
        # Najwyższy score powinien być dla CC=36
        top = decisions[0]
        assert top.score > 0


class TestAnalyzerIgnorePatterns:
    def test_matches_gitignore_directory_pattern(self, tmp_path):
        project_dir: Path = tmp_path / "project"
        project_dir.mkdir()
        target = project_dir / "dist" / "pkg" / "module.py"
        target.parent.mkdir(parents=True)
        target.write_text("print('x')\n")

        assert _matches_gitignore_patterns(target, project_dir, {"dist/"}) is True

    def test_matches_gitignore_glob_pattern(self, tmp_path):
        project_dir: Path = tmp_path / "project"
        project_dir.mkdir()
        target = project_dir / "src" / "generated" / "module.py"
        target.parent.mkdir(parents=True)
        target.write_text("print('x')\n")

        assert _matches_gitignore_patterns(target, project_dir, {"**/generated/*.py"}) is True

    def test_matches_gitignore_literal_pattern(self, tmp_path):
        project_dir: Path = tmp_path / "project"
        project_dir.mkdir()
        target = project_dir / "build" / "tool.py"
        target.parent.mkdir(parents=True)
        target.write_text("print('x')\n")

        assert _matches_gitignore_patterns(target, project_dir, {"build"}) is True

    def test_should_ignore_file_uses_default_patterns(self, tmp_path):
        project_dir: Path = tmp_path / "project"
        project_dir.mkdir()
        target = project_dir / ".venv" / "lib" / "site.py"
        target.parent.mkdir(parents=True)
        target.write_text("print('x')\n")

        assert _should_ignore_file(target, project_dir, set()) is True
