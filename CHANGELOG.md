# Changelog

## [Unreleased]

### Features
- **`redsl events` CLI** — nowe subkomendy do przeglądania `.redsl/history.jsonl`:
  - `redsl events show <project>` — kolorowy widok ostatnich N zdarzeń; filtry `--type`, `--file`, `--cycle`, `--json`
  - `redsl events summary <project>` — statystyki: apply rate, rozkład typów, rollback count
  - `redsl events cycles <project>` — per-cykl tabela: model LLM, status, applied/generated, rollback
- **`--to-planfile` flag** — `redsl refactor --dry-run --to-planfile` tworzy zadania w `planfile.yaml` zamiast raportu markdown
- **`add_decision_tasks()`** — `planfile_updater.py`: konwersja decyzji refactoring na planfile todo z deduplikacją `(file, action)`
- **History events kompletne**: `cycle_started`, `cycle_completed`, `cycle_rollback`, `deploy_push`, `deploy_publish`, `validator_gates_*`, `validator_tune_*`
- **TuneConfig**: `run_on_missing_metrics` + `create_planfile_task_on_failure` konfigurowane per-projekt w `redsl.yaml`
- **DecideConfig**: `llm_model` + `llm_temperature` — override modelu LLM per-projekt

### Fixes
- `cycle_rollback` event zapisywany do history gdy cykl kończy się wyjątkiem i pliki są przywracane
- `deploy_push`/`deploy_publish` — wynik (ok/error) zapisywany do history zamiast tylko do logów

### Docs
- **README.md** — dodano: workflow `--to-planfile`/`--from-planfile`, sekcja "Obserwowalność i historia decyzji", tabela typów zdarzeń, sekcja konfiguracji `redsl.yaml` z wszystkimi nowymi polami

### Docs — Fundamentalna zmiana opisu projektu

- **README.md, README_EN.md, SUMR.md** — Kompletna rewizja dokumentacji:
  - Nowy positioning: "AI-Native DevOps & Refactoring OS" (zamiast "DSL do refaktoryzacji")
  - Dodano sekcję "🧠 Co to naprawdę jest ReDSL?" z wyjaśnieniem paradygmatu
  - Wyjaśniono kluczową zmianę: ❌ typowy DSL vs ✅ autonomiczny system developmentu
  - Dokumentacja architektury: `SUMD → DOQL → taskfile → pyqual → testQL → LLM → deployment`
  - Dodano porównanie "Markdown + AI" vs "ReDSL" z tabelą kryteriów
  - Realna ocena projektu: Innowacyjność 9/10, Techniczna spójność 8.5/10, Adopcja 6/10, Ryzyko wysokie
  - Finalna konkluzja: eksperymentalny system operacyjny dla AI-driven software engineering

## [1.2.55] - 2026-04-20

### Docs
- Update README.md

### Test
- Update tests/test_redeploy_bridge.py

### Other
- Update redsl/cli/__init__.py
- Update redsl/cli/deploy.py

## [1.2.54] - 2026-04-20

### Docs
- Update README.md
- Update redsl/project/context.md

### Test
- Update tests/test_autonomy.py
- Update tests/test_direct_bugs_and_bridges.py
- Update tests/test_examples.py
- Update tests/test_pipeline.py

### Other
- Update redsl/bridges/__init__.py
- Update redsl/bridges/base.py
- Update redsl/bridges/redeploy_bridge.py
- Update redsl/commands/planfile_bridge.py
- Update redsl/project/analysis.toon.yaml
- Update redsl/project/batch_1/analysis.toon.yaml
- Update redsl/project/batch_2/analysis.toon.yaml
- Update redsl/project/root/analysis.toon.yaml
- Update redsl/validation/pyqual_bridge.py
- Update www/config-editor.php
- ... and 8 more files

## [1.2.53] - 2026-04-20

### Docs
- Update README.md
- Update TODO.md
- Update redsl/project/context.md
- Update www/docs/README.md
- Update www/tests/README_TESTS.md

### Other
- Update redsl/execution/decision.py
- Update redsl/project/analysis.toon.yaml
- Update redsl/project/batch_1/analysis.toon.yaml
- Update redsl/project/batch_2/analysis.toon.yaml
- Update redsl/project/root/analysis.toon.yaml
- Update www/config-api.php
- Update www/debug.php
- Update www/debug_lang.php
- Update www/i18n/de.json
- Update www/i18n/en.json
- ... and 9 more files

## [1.2.52] - 2026-04-20

### Docs
- Update README.md
- Update TODO.md
- Update redsl/project/README.md
- Update redsl/project/context.md

### Other
- Update redsl/cli/planfile.py
- Update redsl/project/analysis.toon.yaml
- Update redsl/project/batch_1/analysis.toon.yaml
- Update redsl/project/batch_2/analysis.toon.yaml
- Update redsl/project/evolution.toon.yaml
- Update redsl/project/root/analysis.toon.yaml
- Update www/i18n/de.json
- Update www/i18n/en.json
- Update www/i18n/pl.json
- Update www/index.php
- ... and 2 more files

## [1.2.51] - 2026-04-20

### Docs
- Update README.md
- Update TODO.md
- Update redsl/project/README.md
- Update redsl/project/context.md
- Update www/README.md
- Update www/docs/README.md

### Other
- Update redsl/cli/__init__.py
- Update redsl/cli/events.py
- Update redsl/execution/cycle.py
- Update redsl/project/analysis.toon.yaml
- Update redsl/project/batch_1/analysis.toon.yaml
- Update redsl/project/batch_2/analysis.toon.yaml
- Update redsl/project/evolution.toon.yaml
- Update redsl/project/root/analysis.toon.yaml
- Update www/composer.lock
- Update www/config-api.php
- ... and 6 more files

## [1.2.50] - 2026-04-20

### Docs
- Update README.md
- Update redsl/project/context.md

### Test
- Update tests/test_planfile_updater.py

### Other
- Update redsl/project/analysis.toon.yaml
- Update redsl/project/batch_1/analysis.toon.yaml
- Update redsl/project/batch_2/analysis.toon.yaml
- Update redsl/project/root/analysis.toon.yaml
- Update www/api/redsl.php
- Update www/docker-compose.yml
- Update www/index.php
- Update www/proposals.php
- Update www/propozycje.php

## [1.2.49] - 2026-04-20

### Docs
- Update CHANGELOG.md
- Update README.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md
- Update redsl/project/README.md
- Update redsl/project/context.md
- Update www/README-PLESK.md
- Update www/README.md

### Other
- Update VERSION
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- ... and 49 more files

## [1.2.48] - 2026-04-20

### Docs
- Update README.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md
- Update redsl/project/README.md
- Update redsl/project/context.md
- Update www/README-PLESK.md
- Update www/README.md

### Other
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- ... and 38 more files

## [1.2.47] - 2026-04-19

### Docs
- Update README.md
- Update redsl/project/README.md
- Update redsl/project/context.md
- Update www/README.md
- Update www/tests/README_TESTS.md

### Other
- Update redsl/project/analysis.toon.yaml
- Update redsl/project/batch_1/analysis.toon.yaml
- Update redsl/project/batch_2/analysis.toon.yaml
- Update redsl/project/evolution.toon.yaml
- Update redsl/project/root/analysis.toon.yaml
- Update www/phpunit.xml
- Update www/tests/e2e/package.json

## [1.2.46] - 2026-04-19

### Docs
- Update README.md
- Update SUMR.md
- Update www/README.md
- Update www/README_CONFIG.md
- Update www/README_NDA.md
- Update www/README_PROPozycje.md

### Other
- Update project/map.toon.yaml
- Update redsl/analyzers/parsers/duplication_parser.py
- Update redsl/execution/planfile_updater.py
- Update sumd.json
- Update www/.gitignore
- Update www/.htaccess
- Update www/Dockerfile
- Update www/app.js
- Update www/blog/index.php
- Update www/composer.json
- ... and 19 more files

## [1.2.45] - 2026-04-19

### Docs
- Update CHANGELOG.md
- Update README.md
- Update README_EN.md
- Update SUMD.md
- Update SUMR.md
- Update docs/CONFIG_CHEATSHEET.md
- Update docs/CONFIG_MIGRATION.md
- Update docs/CONFIG_STANDARD.md
- Update docs/README.md
- Update project/README.md
- ... and 8 more files

### Test
- Update tests/test_cli_refactor.py
- Update tests/test_github_sync.py
- Update tests/test_planfile_sync.py
- Update tests/test_sumd_bridge.py
- Update tests/test_test_validation.py
- Update tests/test_tier3.py

### Other
- Update .gitignore
- Update Makefile
- Update VERSION
- Update planfile.yaml
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- ... and 74 more files

## [1.2.44] - 2026-04-19

### Docs
- Update CHANGELOG.md
- Update README.md
- Update README_EN.md
- Update SUMD.md
- Update SUMR.md
- Update docs/CONFIG_CHEATSHEET.md
- Update docs/CONFIG_MIGRATION.md
- Update docs/CONFIG_STANDARD.md
- Update docs/README.md
- Update project/README.md
- ... and 8 more files

### Test
- Update tests/test_github_sync.py
- Update tests/test_planfile_sync.py
- Update tests/test_sumd_bridge.py
- Update tests/test_tier3.py

### Other
- Update .gitignore
- Update Makefile
- Update VERSION
- Update planfile.yaml
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- ... and 61 more files

## [1.2.43] - 2026-04-19

### Docs
- Update CHANGELOG.md
- Update README.md
- Update README_EN.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md
- Update project_test/README.md
- Update project_test/context.md
- Update redsl/project/README.md
- Update redsl/project/context.md
- ... and 1 more files

### Test
- Update tests/test_planfile_sync.py
- Update tests/test_sumd_bridge.py
- Update tests/test_tier3.py

### Other
- Update .gitignore
- Update Makefile
- Update VERSION
- Update planfile.yaml
- Update project/analysis.toon.yaml
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/index.html
- Update project/map.toon.yaml
- Update project/project.toon.yaml
- ... and 42 more files

## [1.2.42] - 2026-04-19

### Docs
- Update CHANGELOG.md
- Update README.md
- Update README_EN.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md
- Update project_test/README.md
- Update project_test/context.md
- Update redsl/project/README.md
- Update redsl/project/context.md
- ... and 1 more files

### Test
- Update tests/test_planfile_sync.py
- Update tests/test_sumd_bridge.py
- Update tests/test_tier3.py

### Other
- Update .gitignore
- Update Makefile
- Update VERSION
- Update planfile.yaml
- Update project/analysis.toon.yaml
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/index.html
- Update project/map.toon.yaml
- Update project/project.toon.yaml
- ... and 41 more files

## [1.2.41] - 2026-04-19

### Docs
- Update CHANGELOG.md
- Update README.md
- Update README_EN.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md
- Update project_test/README.md
- Update project_test/context.md
- Update redsl/project/README.md
- Update redsl/project/context.md
- ... and 1 more files

### Test
- Update tests/test_planfile_sync.py
- Update tests/test_sumd_bridge.py
- Update tests/test_tier3.py

### Other
- Update Makefile
- Update VERSION
- Update planfile.yaml
- Update project/analysis.toon.yaml
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/index.html
- Update project/map.toon.yaml
- Update project/project.toon.yaml
- Update project/prompt.txt
- ... and 40 more files

## [1.2.40] - 2026-04-19

### Docs
- Update README.md
- Update docs/README.md
- Update project_test/README.md
- Update project_test/context.md
- Update redsl/project/README.md
- Update redsl/project/context.md
- Update redsl_scan_report.md

### Test
- Update tests/test_planfile_sync.py

### Other
- Update planfile.yaml
- Update project/duplication.toon.yaml
- Update project/validation.toon.yaml
- Update project_test/analysis.toon.yaml
- Update project_test/evolution.toon.yaml
- Update project_test/index.html
- Update project_test/map.toon.yaml
- Update project_test/project.toon.yaml
- Update project_test/prompt.txt
- Update redsl/cli/__init__.py
- ... and 21 more files

## [1.2.39] - 2026-04-19

### Docs
- Update README.md
- Update redsl/project/context.md
- Update redsl_scan_report.md

### Other
- Update redsl/config_standard/__init__.py
- Update redsl/config_standard/agent_bridge.py
- Update redsl/config_standard/catalog.py
- Update redsl/config_standard/core.py
- Update redsl/config_standard/llm_policy.py
- Update redsl/config_standard/models.py
- Update redsl/config_standard/nlp_handlers.py
- Update redsl/config_standard/profiles.py
- Update redsl/config_standard/proposals.py
- Update redsl/config_standard/secrets.py
- ... and 6 more files

## [1.2.38] - 2026-04-19

### Docs
- Update CHANGELOG.md
- Update README.md
- Update docs/README.md
- Update redsl/project/README.md
- Update redsl/project/context.md
- Update redsl_scan_report.md

### Test
- Update tests/test_agent_bridge.py
- Update tests/test_api.py
- Update tests/test_cli_config.py
- Update tests/test_config_standard.py

### Other
- Update VERSION
- Update project/duplication.toon.yaml
- Update project/validation.toon.yaml
- Update redsl/__init__.py
- Update redsl/api/debug_routes.py
- Update redsl/cli/__init__.py
- Update redsl/cli/config.py
- Update redsl/cli/models.py
- Update redsl/config.py
- Update redsl/config_standard/__init__.py
- ... and 14 more files

## [1.2.37] - 2026-04-19

### Docs
- Update CHANGELOG.md
- Update README.md
- Update docs/README.md
- Update redsl/project/README.md
- Update redsl/project/context.md
- Update redsl_scan_report.md

### Test
- Update tests/test_api.py
- Update tests/test_cli_config.py
- Update tests/test_config_standard.py

### Other
- Update VERSION
- Update project/duplication.toon.yaml
- Update project/validation.toon.yaml
- Update redsl/__init__.py
- Update redsl/api/debug_routes.py
- Update redsl/cli/__init__.py
- Update redsl/cli/config.py
- Update redsl/cli/models.py
- Update redsl/config_standard/__init__.py
- Update redsl/config_standard/applier.py
- ... and 12 more files

## [1.2.36] - 2026-04-19

### Docs
- Update README.md
- Update docs/README.md
- Update redsl/project/README.md
- Update redsl/project/context.md
- Update redsl_scan_report.md

### Other
- Update project/duplication.toon.yaml
- Update project/validation.toon.yaml
- Update redsl/cli/models.py
- Update redsl/llm/registry/sources/base.py
- Update redsl/llm/selection.py
- Update redsl/project/analysis.toon.yaml
- Update redsl/project/batch_1/analysis.toon.yaml
- Update redsl/project/batch_2/analysis.toon.yaml
- Update redsl/project/evolution.toon.yaml
- Update redsl/project/root/analysis.toon.yaml

## [1.2.35] - 2026-04-19

### Docs
- Update README.md
- Update docs/README.md
- Update redsl/project/context.md
- Update redsl_scan_report.md

### Test
- Update tests/test_tier3.py

### Other
- Update config/default_rules.yaml
- Update project/duplication.toon.yaml
- Update project/validation.toon.yaml
- Update redsl/cli/__init__.py
- Update redsl/cli/models.py
- Update redsl/config.py
- Update redsl/llm/__init__.py
- Update redsl/llm/registry/__init__.py
- Update redsl/llm/registry/aggregator.py
- Update redsl/llm/registry/models.py
- ... and 7 more files

## [1.2.34] - 2026-04-19

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update docs/README.md
- Update docs/model-policy-quickstart.md
- Update docs/model-policy.md
- Update examples/11-model-policy/README.md
- Update project/README.md
- Update project/context.md
- Update redsl/project/README.md
- ... and 2 more files

### Test
- Update test_refactor_bad/complex_code.py
- Update test_refactor_bad/redsl_refactor_report.md
- Update test_refactor_project/bad_code.py
- Update test_refactor_project/redsl_refactor_plan.md
- Update test_refactor_project/redsl_refactor_report.md
- Update tests/test_model_policy.py
- Update tests/test_pipeline.py
- Update tests/test_tier3.py

### Other
- Update .gitignore
- Update .redup_ignore
- Update archive/legacy_scripts/apply_semcod_refactor.py
- Update archive/legacy_scripts/batch_quality_refactor.py
- Update archive/legacy_scripts/batch_refactor_semcod.py
- Update archive/legacy_scripts/debug_decisions.py
- Update archive/legacy_scripts/debug_llm_config.py
- Update archive/legacy_scripts/hybrid_llm_refactor.py
- Update archive/legacy_scripts/hybrid_quality_refactor.py
- Update examples/11-model-policy/main.py
- ... and 60 more files

## [1.2.33] - 2026-04-19

### Docs
- Update CHANGELOG.md
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update redsl/project/README.md
- Update redsl/project/context.md
- Update redsl_scan_report.md

### Other
- Update .planfile/config.yaml
- Update .planfile/config.yaml.lock
- Update .planfile/sprints/backlog.yaml
- Update .planfile/sprints/backlog.yaml.lock
- Update .planfile/sprints/current.yaml
- Update .planfile/sprints/current.yaml.lock
- Update project/refactor_plan.yaml
- Update redsl/cli/examples.py
- Update redsl/cli/refactor.py
- Update redsl/commands/_fixer_utils.py
- ... and 19 more files

## [1.2.32] - 2026-04-19

### Docs
- Update CHANGELOG.md
- Update README.md
- Update README_EN.md
- Update SUMD.md
- Update SUMR.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md
- Update redsl/project/context.md
- Update redsl_scan_report.md

### Other
- Update project/analysis.toon.yaml
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/index.html
- Update project/map.toon.yaml
- Update project/project.toon.yaml
- Update project/prompt.txt
- Update project/validation.toon.yaml
- Update redsl/project/analysis.toon.yaml
- Update redsl/project/batch_1/analysis.toon.yaml
- ... and 3 more files

## [1.2.31] - 2026-04-19

### Docs
- **docs/README.md** — Kompletna aktualizacja dokumentacji:
  - Aktualizacja wersji do 1.2.30 z metrykami (781 funkcji, 112 klas, CC̄=4.1)
  - Nowa sekcja "CLI Usage — Refaktoryzacja" z przykładami `redsl refactor`, `batch hybrid/semcod`, `pyqual`
  - Nowa sekcja "Python API" z przykładami użycia `RefactorOrchestrator`
  - Aktualizacja "Generated Output" — opis raportów refaktoryzacji (`.redsl/history.jsonl`, `redsl_refactor_plan.md`, `redsl_pyqual_report.md`)
  - Nowa sekcja "Configuration" z regułami DSL (high_complexity, unused_imports, long_function)
  - Nowa sekcja "Ecosystem Bridges" z tabelą integracji (code2llm, regix, pyqual, planfile, vallm, redup, testql, metrun)
  - Nowa sekcja "Transparency (Przezroczystość)" z opisem CLI/API do śledzenia decyzji
  - Nowy diagram architektury "Pętla świadomości" (PERCEIVE→DECIDE→PLAN→EXECUTE→REFLECT)
- Update README.md
- Update redsl/project/README.md
- Update redsl/project/context.md
- Update redsl_scan_report.md

### Other
- Update redsl/project/analysis.toon.yaml
- Update redsl/project/batch_1/analysis.toon.yaml
- Update redsl/project/batch_2/analysis.toon.yaml
- Update redsl/project/evolution.toon.yaml
- Update redsl/project/root/analysis.toon.yaml

## [1.2.30] - 2026-04-19

### Docs
- Update README.md
- Update docs/README.md
- Update project/context.md
- Update redsl/dsl/project/README.md
- Update redsl/project/README.md
- Update redsl/project/context.md
- Update redsl_scan_report.md

### Test
- Update tests/test_autonomy.py
- Update tests/test_sumd_bridge.py
- Update tests/test_testql_bridge.py

### Other
- Update .gitignore
- Update project/analysis.toon.yaml
- Update project/duplication.toon.yaml
- Update project/index.html
- Update project/map.toon.yaml
- Update project/prompt.txt
- Update project/validation.toon.yaml
- Update redsl/analyzers/__init__.py
- Update redsl/analyzers/sumd_bridge.py
- Update redsl/commands/autonomy_pr/__init__.py
- ... and 14 more files

## [1.2.29] - 2026-04-19

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md

### Other
- Update sumd.json

## [1.2.28] - 2026-04-14

### Docs
- Update README.md

### Test
- Update test_sample_project/redsl_pyqual_report.md
- Update test_sample_project/redsl_refactor_plan.md


All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### Fixed
- **Analyzer**: Fixed false positive unused import detection for submodule imports like `import urllib.request` used as `urllib.request.urlopen()` — now correctly detects usage via attribute chain
- **Guard Refactorer**: Fixed `fix_module_execution_block` wrapping FastAPI/Flask configuration calls (e.g., `app.add_middleware()`, `app.include_router()`) in `__main__` guard — now skips config methods

### Test
- Add regression tests in `tests/test_direct_bugs_and_bridges.py`:
  - `TestQualityVisitorSubmoduleImports` (3 tests): Verify submodule imports are not falsely reported as unused
  - `TestDirectGuardConfigSkip` (4 tests): Verify FastAPI/Flask config calls are not wrapped in `__main__` guard

### Docs
- Update README.md with the current 2026-04-09 analysis snapshot and hotspot priorities
- Update README_EN.md with the current 2026-04-09 analysis snapshot and hotspot priorities
- Update TODO.md with the current backlog priorities

### Docs
- Update README.md
- Update docs/README.md
- Update project/context.md

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/index.html
- Update project/map.toon.yaml

### Docs
- Update README.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md
- Update redsl/dsl/project/README.md
- Update redsl/project/README.md
- Update redsl/project/context.md
- Update redsl_scan_report.md

### Test
- Update test_sample_project/redsl_pyqual_report.md
- Update test_sample_project/redsl_refactor_plan.md
- Update tests/test_awareness.py
- Update tests/test_batch_pyqual.py
- Update tests/test_e2e.py

### Other
- Update .goal/pre-commit-hook.py
- Update .pre-commit-config.yaml
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- ... and 19 more files

### Test
- Update tests/test_direct_bugs_and_bridges.py

### Other
- Update redsl/project/analysis.toon.yaml
- Update redsl/project/batch_1/analysis.toon.yaml
- Update redsl/project/root/analysis.toon.yaml

### Docs
- Update README.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md
- Update redsl/project/README.md
- Update redsl/project/context.md

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- ... and 9 more files

### Docs
- Update CHANGELOG.md
- Update README.md
- Update README_EN.md
- Update TODO.md
- Update docs/README.md
- Update docs/algitex-progresywna-algorytmizacja.md
- Update docs/ats-benchmark.md
- Update docs/clickmd-markdown-terminal.md
- Update docs/code2docs-automatyczna-dokumentacja.md
- Update docs/code2llm-analiza-przeplywu-kodu.md
- ... and 31 more files

### Test
- Update tests/test_autonomy.py
- Update tests/test_batch_pyqual.py
- Update tests/test_cli_refactor.py
- Update tests/test_direct_bugs_and_bridges.py

### Other
- Update examples/01-basic-analysis/advanced.yaml
- Update examples/01-basic-analysis/default.yaml
- Update examples/01-basic-analysis/main.py
- Update examples/02-custom-rules/advanced.yaml
- Update examples/02-custom-rules/default.yaml
- Update examples/02-custom-rules/main.py
- Update examples/03-full-pipeline/advanced.yaml
- Update examples/03-full-pipeline/default.yaml
- Update examples/03-full-pipeline/main.py
- Update examples/04-memory-learning/advanced.yaml
- ... and 51 more files

### Docs
- Update CHANGELOG.md
- Update README.md
- Update docs/README.md

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/duplication.toon.yaml
- Update project/index.html
- Update project/map.toon.yaml
- Update redsl/project/analysis.toon.yaml
- Update redsl/project/batch_1/analysis.toon.yaml
- Update redsl/project/root/analysis.toon.yaml
- Update requirements.txt

### Added
- **Markdown Report Generation** - Automatic Markdown reports for refactor and batch commands:
  - `redsl_refactor_plan.md` — dry-run output saved next to project
  - `redsl_refactor_report.md` — executed refactor cycle report
  - `redsl_batch_semcod_report.md` — batch summary for `batch semcod`
  - `redsl_batch_hybrid_report.md` — batch summary for `batch hybrid`
- **Formatter Module** - New `redsl/formatters.py` with Markdown generation functions
  - `format_cycle_report_markdown()` — Format refactor cycle as Markdown
  - `format_batch_report_markdown()` — Format batch run as Markdown

### Changed
- **Batch Persistence** - All batch runs now persist Markdown reports to disk
- **Report Structure** - Reports include summary, decisions, and file changes

### Test
- **test_tier3.py** - Added tests for Markdown report creation and batch persistence

### Docs
- Update README.md with Markdown report documentation
- Update README_EN.md with Markdown report documentation
- Update docs/README.md (auto-generated)
- Update project documentation files

### Other
- Update project analysis artifacts (toon.yaml, diagrams)

### Docs
- Update README.md
- Update redsl/project/context.md

### Other
- Update redsl/project/analysis.toon.yaml
- Update redsl/project/batch_1/analysis.toon.yaml
- Update redsl/project/root/analysis.toon.yaml

### Docs
- Update README.md
- Update redsl/project/README.md
- Update redsl/project/context.md

### Test
- Update tests/test_api.py
- Update tests/test_bridges.py
- Update tests/test_tier3.py

### Other
- Update redsl/autonomy/auto_fix.py
- Update redsl/autonomy/intent.py
- Update redsl/cli.py
- Update redsl/commands/cli_autonomy.py
- Update redsl/commands/cli_awareness.py
- Update redsl/commands/cli_doctor.py
- Update redsl/execution/cycle.py
- Update redsl/llm/llx_router.py
- Update redsl/project/analysis.toon.yaml
- Update redsl/project/batch_1/analysis.toon.yaml
- ... and 3 more files

### Docs
- Update README.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md
- Update redsl/project/README.md
- Update redsl/project/context.md

### Test
- Update tests/test_autonomy.py

### Other
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- ... and 16 more files

### Other
- Update redsl/analyzers/radon_analyzer.py
- Update redsl/project/analysis.toon.yaml

### Docs
- Update README.md
- Update redsl/project/README.md
- Update redsl/project/context.md

### Test
- Update tests/test_doctor.py

### Other
- Update project/analysis.toon.yaml
- Update project/evolution.toon.yaml
- Update project/project.toon.yaml
- Update redsl/api.py
- Update redsl/commands/doctor.py
- Update redsl/project/analysis.toon.yaml

### Docs
- Update README.md
- Update TODO.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md
- Update redsl/project/README.md
- Update redsl/project/context.md

### Test
- Update tests/test_integration.py

### Docs
- Update README.md
- Update README_EN.md
- Update TODO.md
- Update redsl/project/README.md
- Update redsl/project/context.md

### Test
- Update tests/test_awareness.py
- Update tests/test_config_loading.py

### Other
- Update examples/03-full-pipeline/main.py
- Update redsl/awareness/__init__.py
- Update redsl/cli.py
- Update redsl/config.py
- Update redsl/llm/__init__.py
- Update redsl/project/analysis.toon.yaml

### Test
- Update tests/test_cli_refactor.py

### Other
- Update examples/03-full-pipeline/main.py
- Update project/evolution.toon.yaml
- Update redsl/awareness/__init__.py
- Update redsl/cli.py
- Update redsl/execution/cycle.py
- Update redsl/execution/validation.py
- Update redsl/orchestrator.py
- Update redsl/project/analysis.toon.yaml

### Docs
- Update README.md
- Update docs/README.md
- Update project/README.md
- Update project/REFACTORING_SUMMARY_2026-04-08.md
- Update project/context.md
- Update redsl/project/README.md
- Update redsl/project/context.md

### Test
- Update tests/test_analyzer.py
- Update tests/test_awareness.py
- Update tests/test_cli_refactor.py
- Update tests/test_direct_bugs_and_bridges.py
- Update tests/test_direct_refactor.py
- Update tests/test_git_timeline.py
- Update tests/test_llm_execution.py
- Update tests/test_tier3.py

### Other
- Update examples/03-full-pipeline/main.py
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- ... and 46 more files

### Docs
- Update README.md
- Update README_EN.md
- Update docs/README.md
- Update redsl/project/context.md

### Test
- Update tests/test_direct_bugs_and_bridges.py

### Other
- Update .code2llmignore
- Update .gitignore
- Update archive/legacy_scripts/hybrid_llm_refactor.py
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- ... and 6 more files

### Docs
- Update README.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md
- Update redsl/project/README.md
- Update redsl/project/context.md

### Test
- Update tests/test_direct_bugs_and_bridges.py

### Added
- **DirectRefactorEngine** - Silnik bezpośredniej refaktoryzacji bez LLM:
  - `REMOVE_UNUSED_IMPORTS` - usuwanie nieużywanych importów (zachowuje `__future__`, `__all__`)
  - `FIX_MODULE_EXECUTION_BLOCK` - naprawa bloków `if __name__ == "__main__"` w środku pliku
  - `EXTRACT_CONSTANTS` - ekstrakcja magic numbers do stałych
  - `ADD_RETURN_TYPES` - dodawanie `-> None` dla funkcji bez return
- **body_restorer.py** - Naprawa skradzionych ciał klas/funkcji po błędach FIX_MODULE_EXECUTION_BLOCK
- **New Bridges** - Integracja z ekosystemem semcod:
  - `regix_bridge.py` - wykrywanie regresji metryk po refaktoryzacji
  - `pyqual_bridge.py` - integracja z pyqual CLI (doctor, gates, status)
  - `planfile_bridge.py` - tworzenie ticketów planfile dla zadań refaktoryzacji
- **llx_router.py** - Inteligentny routing modeli LLM z `apply_provider_prefix()` dla LiteLLM

### Fixed
- **regix_bridge** - użycie `regix --help` zamiast `--version` w `is_available()`
- **regix_bridge** - poprawne sprawdzanie klucza `regressions` zamiast `has_regressions`
- **regix_bridge** - usunięcie nieobsługiwanego `--format json` z `diff` i `gates`
- **pyqual** - wykluczenie `.venv/`, `venv/`, `node_modules/` z analizy (11k+ files fix)
- **pyqual** - timeout=60 dla mypy/bandit, timeout=30 dla ruff
- **direct.py** - poprawne liczenie linii dla multi-line imports w `EXTRACT_CONSTANTS`

### Changed
- **Orchestrator** - pełna pętla: PERCEIVE → DECIDE → PLAN → EXECUTE → REFLECT → REMEMBER → IMPROVE
- **CLI** - wsparcie formatów `--format yaml|json|text` dla wszystkich komend

### Docs
- Aktualizacja README.md z nową architekturą i akcjami refaktoryzacji
- Aktualizacja docs/README.md (328 testów, wersja 1.2.8)

### Test
- 328 testów przechodzi (dodano testy dla bridges i DirectRefactorEngine)

### Docs
- Update README.md
- Update redsl/project/context.md

### Other
- Update redsl/project/analysis.toon.yaml
- Update redsl/validation/regix_bridge.py

### Docs
- Update README.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md
- Update redsl/dsl/project/README.md
- Update redsl/dsl/project/context.md
- Update redsl/project/README.md
- Update redsl/project/context.md

### Test
- Update tests/test_bridges.py
- Update tests/test_chunker_and_rules.py
- Update tests/test_incremental_and_ci.py
- Update tests/test_multi_project.py
- Update tests/test_pipeline.py
- Update tests/test_tier3.py

### Docs
- Update README.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Test
- Update tests/test_bootstrap.py
- Update tests/test_validation_and_diff.py

### Docs
- Update README.md
- Update docs/README.md

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/duplication.toon.yaml
- Update project/index.html
- Update project/map.toon.yaml
- Update project/project.toon.yaml
- Update redsl/analyzers/__init__.py
- Update redsl/analyzers/analyzer.py
- Update redsl/analyzers/parsers/__init__.py
- ... and 18 more files

### Other
- Update project/validation.toon.yaml

### Docs
- Update README.md
- Update docs/README.md
- Update project/context.md

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/index.html
- Update project/map.toon.yaml
- Update project/project.toon.yaml

### Docs
- Update CHANGELOG.md
- Update README.md
- Update README_EN.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Test
- Update test_sample_project/TODO.md
- Update test_sample_project/hybrid_llm_refactor_results_direct.json
- Update test_sample_project/hybrid_llm_refactor_results_llm.json
- Update test_sample_project/planfile.yaml
- Update test_sample_project/prefact.yaml
- Update test_sample_project/sample.py
- Update tests/__pycache__/__init__.cpython-313.pyc
- Update tests/__pycache__/test_analyzer.cpython-313-pytest-8.3.5.pyc
- Update tests/__pycache__/test_dsl_engine.cpython-313-pytest-8.3.5.pyc
- Update tests/__pycache__/test_memory.cpython-313-pytest-8.3.5.pyc
- ... and 7 more files

### Other
- Update VERSION
- Update app/__pycache__/__init__.cpython-313.pyc
- Update app/analyzers/__pycache__/__init__.cpython-313.pyc
- Update app/dsl/__pycache__/__init__.cpython-313.pyc
- Update app/dsl/__pycache__/engine.cpython-313.pyc
- Update app/memory/__pycache__/__init__.cpython-313.pyc
- Update archive/legacy_scripts/apply_semcod_refactor.py
- Update archive/legacy_scripts/batch_quality_refactor.py
- Update archive/legacy_scripts/batch_refactor_semcod.py
- Update archive/legacy_scripts/debug_decisions.py
- ... and 52 more files

### Added
- **YAML/JSON Output Support**: All CLI commands now support `--format yaml|json|text` option
- **REST API**: Complete FastAPI-based REST API mirroring CLI commands
  - POST /refactor - Run refactoring on a project
  - POST /batch/semcod - Batch refactor semcod projects
  - POST /batch/hybrid - Hybrid quality refactoring
  - GET /debug/config - Get configuration info
  - GET /debug/decisions - Get DSL decisions
  - POST /pyqual/analyze - Python code quality analysis
  - POST /pyqual/fix - Apply automatic quality fixes
  - GET /health - Health check endpoint
- **Python-dotenv Support**: Automatic loading of .env files for configuration
- **Enhanced Documentation**: Added extensive usage examples and API documentation
- **Formatter Module**: Centralized output formatting for consistent CLI and API responses

### Changed
- **CLI Structure**: Updated to use AgentConfig.from_env() for consistent configuration
- **Batch Commands**: Now support structured output formats
- **API Responses**: All endpoints return structured data matching CLI output

### Fixed
- **Import Issues**: Added python-dotenv to dependencies
- **Configuration**: Improved environment variable handling

### Added
- **CLI Interface**: Complete command-line interface with Click
  - `redsl refactor` - Single project refactoring
  - `redsl batch semcod` - Batch processing for semcod projects
  - `redsl batch hybrid` - Hybrid quality refactoring (no LLM)
  - `redsl debug config` - Configuration debugging
  - `redsl debug decisions` - DSL decision inspection
- **Package Structure**: Converted from loose scripts to proper Python package
- **Direct Refactoring**: Four quality refactor actions without LLM dependency
  - `REMOVE_UNUSED_IMPORTS`
  - `EXTRACT_CONSTANTS`
  - `FIX_MODULE_EXECUTION_BLOCK`
  - `ADD_RETURN_TYPES`
- **CodeQualityVisitor**: AST-based detection of code quality issues
- **Batch Processing**: Support for processing multiple semcod projects
- **English Documentation**: README_EN.md for international users

### Changed
- **Module Renamed**: `app/` → `redsl/`
- **Import Statements**: All imports updated from `from app.` to `from redsl.`
- **Package Metadata**: Enhanced pyproject.toml with proper classifiers and metadata
- **Test Organization**: Moved test files to proper `tests/` directory

### Fixed
- **Import Errors**: Fixed all import statements after package restructuring
- **Indexing Bug**: Fixed `extract_constants` line indexing issue
- **Module Execution Block**: Improved detection and fixing logic
- **Return Type Inference**: Enhanced `ADD_RETURN_TYPES` with better type detection

### Deprecated
- Legacy scripts moved to `archive/legacy_scripts/`

### Test
- Update tests/test_integration.py

### Other
- Update .gitignore
- Update app/__pycache__/__init__.cpython-313.pyc
- Update app/analyzers/__pycache__/__init__.cpython-313.pyc
- Update app/dsl/__pycache__/engine.cpython-313.pyc
- Update apply_semcod_refactor.py
- Update batch_refactor_semcod.py

### Other
- Update app/__pycache__/__init__.cpython-313.pyc
- Update app/analyzers/__pycache__/__init__.cpython-313.pyc
- Update app/dsl/__pycache__/engine.cpython-313.pyc

### Test
- Update tests/test_integration.py

### Other
- Update app/__pycache__/__init__.cpython-313.pyc
- Update app/analyzers/__pycache__/__init__.cpython-313.pyc

### Other
- Update app/__pycache__/__init__.cpython-313.pyc
- Update app/analyzers/__pycache__/__init__.cpython-313.pyc

### Docs
- Update README.md
- Update TODO.md

### Other
- Update app/__pycache__/__init__.cpython-313.pyc
- Update app/analyzers/__pycache__/__init__.cpython-313.pyc

### Docs
- Update README.md
- Update TODO.md

### Other
- Update .gitignore
- Update app/__pycache__/__init__.cpython-313.pyc

### Other
- Update VERSION
- Update app/__pycache__/__init__.cpython-313.pyc
- Update examples/01-basic-analysis/main.py
- Update examples/02-custom-rules/main.py
- Update examples/03-full-pipeline/main.py
- Update examples/04-memory-learning/main.py
- Update examples/05-api-integration/main.py

### Other
- Update .gitignore
- Update app/__pycache__/__init__.cpython-313.pyc
- Update project_toon.yaml

### Other
- Update .idea/redsl.iml
- Update app/__pycache__/__init__.cpython-313.pyc

### Test
- Update tests/__init__.py
- Update tests/__pycache__/__init__.cpython-313.pyc
- Update tests/__pycache__/test_analyzer.cpython-313-pytest-8.3.5.pyc
- Update tests/__pycache__/test_dsl_engine.cpython-313-pytest-8.3.5.pyc
- Update tests/__pycache__/test_memory.cpython-313-pytest-8.3.5.pyc
- Update tests/test_analyzer.py
- Update tests/test_dsl_engine.py
- Update tests/test_memory.py

### Other
- Update .env.example
- Update .gitignore
- Update .idea/.gitignore
- Update Makefile
- Update app/__pycache__/__init__.cpython-313.pyc
- Update app/analyzers/__pycache__/__init__.cpython-313.pyc
- Update app/dsl/__pycache__/__init__.cpython-313.pyc
- Update app/dsl/__pycache__/engine.cpython-313.pyc
- Update app/memory/__pycache__/__init__.cpython-313.pyc
- Update config/default_rules.yaml
- ... and 1 more files

