# Ze źródeł

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Workflows](#workflows)
- [Quality Pipeline (`pyqual.yaml`)](#quality-pipeline-pyqualyaml)
- [Dependencies](#dependencies)
- [Source Map](#source-map)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `redsl`
- **version**: `1.2.31`
- **python_requires**: `>=3.11`
- **license**: Apache-2.0
- **ai_model**: `openrouter/openai/gpt-5-mini`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, requirements.txt, Taskfile.yml, Makefile, app.doql.css, goal.yaml, .env.example, Dockerfile, docker-compose.yml, src(5 mod), project/(5 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.css`)

```css markpact:doql path=app.doql.css
app {
  name: "redsl";
  version: "1.2.28";
}

interface[type="cli"] {
  framework: click;
}
interface[type="cli"] page[name="redsl"] {

}

workflow[name="install"] {
  trigger: "manual";
  step-1: run cmd=$(PIP) install -r requirements.txt;
}

workflow[name="dev-install"] {
  trigger: "manual";
  step-1: run cmd=$(PIP) install -r requirements.txt;
  step-2: run cmd=$(PIP) install -e ".[dev]";
}

workflow[name="test"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m pytest tests/ -v -m "not slow";
}

workflow[name="test-fast"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m pytest tests/ -q -m "not slow and not integration and not e2e";
}

workflow[name="test-all"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m pytest tests/ -v;
}

workflow[name="lint"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m ruff check redsl/ tests/;
}

workflow[name="type-check"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m mypy redsl/;
}

workflow[name="format"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m ruff format redsl/ tests/;
  step-2: run cmd=$(PYTHON) -m ruff check --fix redsl/ tests/;
}

workflow[name="format-check"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m ruff format --check redsl/ tests/;
}

workflow[name="docker-up"] {
  trigger: "manual";
  step-1: run cmd=$(DOCKER_COMPOSE) up -d;
}

workflow[name="docker-down"] {
  trigger: "manual";
  step-1: run cmd=$(DOCKER_COMPOSE) down;
}

workflow[name="docker-build"] {
  trigger: "manual";
  step-1: run cmd=$(DOCKER_COMPOSE) build;
}

workflow[name="run"] {
  trigger: "manual";
  step-1: depend target=docker-up;
}

workflow[name="run-local"] {
  trigger: "manual";
  step-1: run cmd=$(PYTHON) -m uvicorn redsl.api:app --reload --host 0.0.0.0 --port 8000;
}

workflow[name="clean"] {
  trigger: "manual";
  step-1: run cmd=find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true;
  step-2: run cmd=find . -type f -name "*.pyc" -delete 2>/dev/null || true;
  step-3: run cmd=find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true;
  step-4: run cmd=find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true;
  step-5: run cmd=rm -rf refactor_output/ 2>/dev/null || true;
}

workflow[name="fmt"] {
  trigger: "manual";
  step-1: run cmd=ruff format .;
}

workflow[name="build"] {
  trigger: "manual";
  step-1: run cmd=python -m build;
}

workflow[name="health"] {
  trigger: "manual";
  step-1: run cmd=docker compose ps;
  step-2: run cmd=docker compose exec app echo "Health check passed";
}

workflow[name="up"] {
  trigger: "manual";
  step-1: run cmd=docker compose up -d;
}

workflow[name="down"] {
  trigger: "manual";
  step-1: run cmd=docker compose down;
}

workflow[name="logs"] {
  trigger: "manual";
  step-1: run cmd=docker compose logs -f;
}

workflow[name="ps"] {
  trigger: "manual";
  step-1: run cmd=docker compose ps;
}

workflow[name="import-makefile-hint"] {
  trigger: "manual";
  step-1: run cmd=echo 'Run: taskfile import Makefile to import existing targets.';
}

workflow[name="help"] {
  trigger: "manual";
  step-1: run cmd=echo \"Dost\u0119pne komendy:\; 
  step-2: run cmd=echo \"  install       - Instalacja zale\u017Cno\u015Bci produkcyjnych\; 
  step-3: run cmd=echo \"  dev-install   - Instalacja zale\u017Cno\u015Bci deweloperskich\; 
  step-4: run cmd=echo \"  test          - Uruchomienie test\xF3w pytest (bez slow)\; 
  step-5: run cmd=echo "  test-fast     - Szybkie testy (bez slow/integration/e2e)";
  step-6: run cmd=echo \"  test-all      - Wszystkie testy w\u0142\u0105cznie z slow\; 
  step-7: run cmd=echo "  lint          - Sprawdzenie lintingu ruff";
  step-8: run cmd=echo \"  type-check    - Sprawdzenie typ\xF3w mypy\; 
  step-9: run cmd=echo "  format        - Formatowanie kodu ruff";
  step-10: run cmd=echo "  format-check  - Sprawdzenie formatowania kodu";
  step-11: run cmd=echo \"  docker-up     - Uruchomienie us\u0142ug Docker\; 
  step-12: run cmd=echo \"  docker-down   - Zatrzymanie us\u0142ug Docker\; 
  step-13: run cmd=echo \"  docker-build  - Budowanie obraz\xF3w Docker\; 
  step-14: run cmd=echo "  run           - Uruchomienie aplikacji w Docker";
  step-15: run cmd=echo "  run-local     - Uruchomienie aplikacji lokalnie";
  step-16: run cmd=echo \"  clean         - Czyszczenie plik\xF3w tymczasowych\; 
}

deploy {
  target: docker-compose;
  compose_file: docker-compose.yml;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: ".env";
}

workflow[name="all"] {
  trigger: "manual";
  step-1: run cmd=taskfile run install;
  step-2: run cmd=taskfile run lint;
  step-3: run cmd=taskfile run test;
}
```

### Source Modules

- `redsl.config`
- `redsl.consciousness_loop`
- `redsl.history`
- `redsl.main`
- `redsl.orchestrator`

## Workflows

### Taskfile Tasks (`Taskfile.yml`)

```yaml markpact:taskfile path=Taskfile.yml
version: '1'
name: redsl
description: Minimal Taskfile
variables:
  APP_NAME: redsl
environments:
  local:
    container_runtime: docker
    compose_command: docker compose
pipeline:
  python_version: "3.12"
  runner_image: ubuntu-latest
  branches: [main]
  cache: [~/.cache/pip]
  artifacts: [dist/]

  stages:
    - name: lint
      tasks: [lint]

    - name: test
      tasks: [test]

    - name: build
      tasks: [build]
      when: "branch:main"

tasks:
  install:
    desc: Install Python dependencies (editable)
    cmds:
    - pip install -e .[dev]
  test:
    desc: Run pytest suite
    cmds:
    - pytest -q
  lint:
    desc: Run ruff lint check
    cmds:
    - ruff check .
  fmt:
    desc: Auto-format with ruff
    cmds:
    - ruff format .
  build:
    desc: Build wheel + sdist
    cmds:
    - python -m build
  clean:
    desc: Remove build artefacts
    cmds:
    - rm -rf build/ dist/ *.egg-info
  up:
    desc: Start services via docker compose
    cmds:
    - docker compose up -d
  down:
    desc: Stop services
    cmds:
    - docker compose down
  logs:
    desc: Tail compose logs
    cmds:
    - docker compose logs -f
  ps:
    desc: Show running compose services
    cmds:
    - docker compose ps
  docker-build:
    desc: Build docker image
    cmds:
    - docker build -t redsl:latest .
  help:
    desc: '[imported from Makefile] help'
    cmds:
    - "echo \"Dost\u0119pne komendy:\""
    - "echo \"  install       - Instalacja zale\u017Cno\u015Bci produkcyjnych\""
    - "echo \"  dev-install   - Instalacja zale\u017Cno\u015Bci deweloperskich\""
    - "echo \"  test          - Uruchomienie test\xF3w pytest (bez slow)\""
    - echo "  test-fast     - Szybkie testy (bez slow/integration/e2e)"
    - "echo \"  test-all      - Wszystkie testy w\u0142\u0105cznie z slow\""
    - echo "  lint          - Sprawdzenie lintingu ruff"
    - "echo \"  type-check    - Sprawdzenie typ\xF3w mypy\""
    - echo "  format        - Formatowanie kodu ruff"
    - echo "  format-check  - Sprawdzenie formatowania kodu"
    - "echo \"  docker-up     - Uruchomienie us\u0142ug Docker\""
    - "echo \"  docker-down   - Zatrzymanie us\u0142ug Docker\""
    - "echo \"  docker-build  - Budowanie obraz\xF3w Docker\""
    - echo "  run           - Uruchomienie aplikacji w Docker"
    - echo "  run-local     - Uruchomienie aplikacji lokalnie"
    - "echo \"  clean         - Czyszczenie plik\xF3w tymczasowych\""
  dev-install:
    desc: '[imported from Makefile] dev-install'
    cmds:
    - $(PIP) install -r requirements.txt
    - $(PIP) install -e ".[dev]"
  test-fast:
    desc: '[imported from Makefile] test-fast'
    cmds:
    - $(PYTHON) -m pytest tests/ -q -m "not slow and not integration and not e2e"
  test-all:
    desc: '[imported from Makefile] test-all'
    cmds:
    - $(PYTHON) -m pytest tests/ -v
  type-check:
    desc: '[imported from Makefile] type-check'
    cmds:
    - $(PYTHON) -m mypy redsl/
  format:
    desc: '[imported from Makefile] format'
    cmds:
    - $(PYTHON) -m ruff format redsl/ tests/
    - $(PYTHON) -m ruff check --fix redsl/ tests/
  format-check:
    desc: '[imported from Makefile] format-check'
    cmds:
    - $(PYTHON) -m ruff format --check redsl/ tests/
  docker-up:
    desc: '[imported from Makefile] docker-up'
    cmds:
    - $(DOCKER_COMPOSE) up -d
  docker-down:
    desc: '[imported from Makefile] docker-down'
    cmds:
    - $(DOCKER_COMPOSE) down
  run:
    desc: '[imported from Makefile] run'
    deps:
    - docker-up
  run-local:
    desc: '[imported from Makefile] run-local'
    cmds:
    - $(PYTHON) -m uvicorn redsl.api:app --reload --host 0.0.0.0 --port 8000
  health:
    desc: '[from doql] workflow: health'
    cmds:
    - docker compose ps
    - docker compose exec app echo "Health check passed"
  import-makefile-hint:
    desc: '[from doql] workflow: import-makefile-hint'
    cmds:
    - 'echo ''Run: taskfile import Makefile to import existing targets.'''
  all:
    desc: Run install, lint, test
    cmds:
    - taskfile run install
    - taskfile run lint
    - taskfile run test
```

## Quality Pipeline (`pyqual.yaml`)

```yaml markpact:pyqual path=pyqual.yaml
project_root: .
package_name: redsl
include:
- '**/*.py'
exclude:
- '**/__pycache__/**'
- '**/node_modules/**'
- '**/.venv/**'
- '**/venv/**'
- '**/.git/**'
- '**/build/**'
- '**/dist/**'
- '**/*.egg-info/**'
- '**/tests/**'
tools:
  parallel: true
  cache: true
  ruff:
    enabled: true
    max_line_length: 88
    select:
    - E
    - F
    - W
    - I
    - C
    - B
    - A
    - COM
    - C4
    - DTZ
    - T10
    - EM
    - EXE
    - FA
    - ISC
    - ICN
    - G
    - INP
    - PIE
    - T20
    - PT
    - Q
    - RSE
    - RET
    - SIM
    - TID
    - TCH
    - ARG
    - PTH
    - ERA
    - PGH
    - PL
    - TRY
    - FLAKE8-PYTESTSTYLE
    - RUF
    ignore:
    - E501
    - PLR0913
    - PLR0915
  mypy:
    enabled: true
    strict: false
    ignore_missing_imports: true
    disallow_untyped_defs: false
    disallow_incomplete_defs: false
    check_untyped_defs: true
    disallow_untyped_decorators: false
    no_implicit_optional: true
    warn_redundant_casts: true
    warn_unused_ignores: true
    warn_no_return: true
    warn_unreachable: true
    strict_equality: true
  isort:
    enabled: true
    profile: black
    multi_line_output: 3
    line_length: 88
  bandit:
    enabled: true
    exclude_dirs:
    - tests
  coverage:
    enabled: true
    fail_under: 80
  pydocstyle:
    enabled: true
    convention: google
  vulture:
    enabled: true
    min_confidence: 60
performance:
  max_workers: 4
  cache_size: 104857600
  chunk_size: 10
metrics:
  complexity:
    enabled: true
    max_complexity: 10
    tools:
    - radon
    - xenon
  maintainability:
    enabled: true
    min_maintainability: 70
    tools:
    - radon
  duplication:
    enabled: true
    min_similarity: 0.85
    tools:
    - jscpd
  test_coverage:
    enabled: true
    min_coverage: 80
    tools:
    - coverage
rules:
  unused-imports:
    enabled: true
    tools:
    - ruff
    - autoflake
    severity: error
  magic-numbers:
    enabled: true
    threshold: 2
    exclude:
    - 0
    - 1
    - -1
    - 2
    severity: warning
  print-statements:
    enabled: true
    severity: warning
  TODO-comments:
    enabled: true
    severity: info
  long-lines:
    enabled: true
    max_length: 88
    severity: warning
  missing-docstrings:
    enabled: true
    public_only: true
    severity: warning
  type-hints:
    enabled: true
    require_return_type: true
    require_param_types: false
    severity: warning
  security-issues:
    enabled: true
    tools:
    - bandit
    severity: error
  code-smells:
    enabled: true
    tools:
    - ruff
    - mypy
    severity: warning
plugins:
  enabled: true
  directories:
  - ~/.pyqual/plugins
  - ./.pyqual/plugins
environments:
  development:
    rules:
      print-statements:
        enabled: true
      magic-numbers:
        enabled: false
      TODO-comments:
        severity: warning
    performance:
      max_workers: 2
  production:
    rules:
      print-statements:
        enabled: false
      magic-numbers:
        enabled: true
      TODO-comments:
        severity: error
    performance:
      max_workers: 8
  testing:
    rules:
      print-statements:
        enabled: true
      magic-numbers:
        enabled: false
      missing-docstrings:
        enabled: false
    metrics:
      test_coverage:
        enabled: true
        min_coverage: 90
reporting:
  output_formats:
  - yaml
  - json
  - html
  include_summary: true
  include_details: true
  include_recommendations: true
  output_file: pyqual_report
```

## Dependencies

### Runtime

```text markpact:deps python
fastapi>=0.115.0
uvicorn>=0.44.0
pydantic>=2.10.0
litellm>=1.52.0
chromadb>=0.6.0
pyyaml>=6.0.2
rich>=13.9.0
httpx>=0.28.0
click>=8.1.7
python-dotenv>=1.0.1
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
```

### Development

```text markpact:deps python scope=dev
pytest>=9.0
pytest-xdist>=3.5
pytest-cov>=7.1
ruff>=0.15.0
mypy>=1.13
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
```

## Source Map

*Top 5 modules by symbol density — signatures for LLM orientation.*

### `redsl.main` (`redsl/main.py`)

```python
def _get_orchestrator(model)  # CC=2, fan=2
def _analysis_source_method(orch, path)  # CC=2, fan=3
def _analysis_function_metrics(result)  # CC=4, fan=1
def _print_analysis_summary(result, path, source_method)  # CC=2, fan=1
def _print_top_functions(func_metrics)  # CC=5, fan=1
def _print_alerts(result, func_metrics)  # CC=6, fan=2
def _print_duplicates(result)  # CC=3, fan=3
def _print_analysis_plan(result, path)  # CC=5, fan=7
def cmd_analyze(project_dir)  # CC=2, fan=13
def cmd_explain(project_dir)  # CC=1, fan=4
def _print_refactor_report(report, orch)  # CC=3, fan=3
def cmd_refactor(project_dir, dry_run, auto, max_actions, model)  # CC=2, fan=5
def cmd_memory_stats()  # CC=1, fan=4
def cmd_serve(port, host)  # CC=1, fan=1
def _print_usage()  # CC=1, fan=1
def _get_arg(args, name, default)  # CC=4, fan=2
def _has_flag(args, name)  # CC=1, fan=0
def _dispatch_analyze(args)  # CC=1, fan=2
def _dispatch_explain(args)  # CC=1, fan=2
def _dispatch_refactor(args)  # CC=2, fan=4
def _dispatch_memory_stats(args)  # CC=1, fan=1
def _dispatch_serve(args)  # CC=1, fan=3
def main()  # CC=3, fan=6
```

### `redsl.history` (`redsl/history.py`)

```python
def _default_history_dir(project_dir)  # CC=1, fan=0
class HistoryEvent:  # A single persisted event in the refactor history.
class HistoryWriter:  # Append-only history logger backed by .redsl/history.jsonl.
    def __init__(project_dir)  # CC=1
    def record(event)  # CC=1
    def record_event(event_type)  # CC=1
    def decision_signature()  # CC=2
    def has_recent_signature(signature, limit)  # CC=5
class HistoryReader:  # Read-only access to .redsl/history.jsonl for querying and de
    def __init__(project_dir)  # CC=1
    def load_events()  # CC=5
    def filter_by_file(target_file)  # CC=3
    def filter_by_type(event_type)  # CC=3
    def has_recent_proposal(target_file, action)  # CC=7
    def has_recent_ticket(title_prefix)  # CC=7
    def generate_decision_report()  # CC=11 ⚠
```

### `redsl.consciousness_loop` (`redsl/consciousness_loop.py`)

```python
def main_loop()  # CC=4, fan=6
class ConsciousnessLoop:  # Ciągła pętla „świadomości" agenta.
    def __init__(project_dir, interval_seconds, config)  # CC=2
    def run()  # CC=5
    def _inner_thought(cycle)  # CC=3
    def _self_assessment(cycle)  # CC=3
    def _profile_performance(cycle)  # CC=3
    def stop()  # CC=1
```

### `redsl.config` (`redsl/config.py`)

```python
def _default_llm_model()  # CC=6, fan=1
def _resolve_provider_key(model)  # CC=6, fan=3
class LLMConfig:  # Konfiguracja warstwy LLM.
    def is_local()  # CC=1
    def api_key()  # CC=1
    def api_key(value)  # CC=1
class MemoryConfig:  # Konfiguracja systemu pamięci.
class AnalyzerConfig:  # Konfiguracja analizatora kodu.
class RefactorConfig:  # Konfiguracja silnika refaktoryzacji.
class AgentConfig:  # Główna konfiguracja agenta.
    def from_env(cls)  # CC=3
```

### `redsl.orchestrator` (`redsl/orchestrator.py`)

```python
class CycleReport:  # Raport z jednego cyklu refaktoryzacji.
class RefactorOrchestrator:  # Główny orkiestrator — „mózg" systemu.
    def __init__(config)  # CC=2
    def run_cycle(project_dir, max_actions, use_code2llm, validate_regix, rollback_on_failure, use_sandbox, target_file)  # CC=1
    def run_from_toon_content(project_toon, duplication_toon, validation_toon, source_files, max_actions)  # CC=1
    def add_custom_rules(rules_yaml)  # CC=1
    def _resolve_limits(project_dir, default_max)  # CC=8
```

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 193f 26486L | python:191,shell:2 | 2026-04-19
# CC̄=3.8 | critical:0/1126 | dups:0 | cycles:0

HEALTH[0]: ok

REFACTOR[0]: none needed

PIPELINES[536]:
  [1] Src [main]: main → run_basic_analysis_example → load_example_yaml → _resolve_yaml_path → ...(1 more)
      PURITY: 100% pure
  [2] Src [main]: main → run_memory_learning_example → load_example_yaml → _resolve_yaml_path → ...(1 more)
      PURITY: 100% pure
  [3] Src [main]: main → run_full_pipeline_example → load_example_yaml → _resolve_yaml_path → ...(1 more)
      PURITY: 100% pure
  [4] Src [main]: main → run_badge_example → load_example_yaml → _resolve_yaml_path → ...(1 more)
      PURITY: 100% pure
  [5] Src [main]: main → run_custom_rules_example → load_example_yaml → _resolve_yaml_path → ...(1 more)
      PURITY: 100% pure

LAYERS:
  archive/                        CC̄=4.8    ←in:0  →out:0
  │ hybrid_llm_refactor        386L  0C   16m  CC=10     ←1
  │ hybrid_quality_refactor    253L  0C   10m  CC=10     ←4
  │ batch_quality_refactor     167L  0C    2m  CC=14     ←0
  │ batch_refactor_semcod      154L  0C    3m  CC=12     ←0
  │ apply_semcod_refactor       79L  0C    1m  CC=8      ←0
  │ debug_decisions             62L  0C    1m  CC=7      ←0
  │ debug_llm_config            55L  0C    1m  CC=5      ←0
  │
  redsl/                          CC̄=3.8    ←in:19  →out:19  !! split
  │ sumd_bridge                412L  2C   13m  CC=11     ←0
  │ pipeline                   398L  1C   15m  CC=10     ←1
  │ radon_analyzer             388L  0C   23m  CC=10     ←1
  │ decision                   372L  0C    9m  CC=8      ←6
  │ cli_autonomy               350L  0C   20m  CC=6      ←0
  │ engine                     336L  1C    9m  CC=12     ←1
  │ reporting                  331L  0C   24m  CC=12     ←2
  │ quality_gate               325L  1C   10m  CC=11     ←4
  │ __init__                   325L  2C   16m  CC=10     ←0
  │ doctor_detectors           319L  0C   16m  CC=10     ←1
  │ regix_bridge               317L  0C    8m  CC=9      ←1
  │ validator                  314L  0C    7m  CC=12     ←1
  │ vallm_bridge               314L  0C    8m  CC=10     ←1
  │ hybrid                     304L  0C   14m  CC=9      ←0
  │ project_parser             300L  1C   18m  CC=12     ←0
  │ refactor_routes            298L  0C    6m  CC=3      ←1
  │ testql_bridge              297L  2C   10m  CC=12     ←0
  │ toon_analyzer              296L  1C   13m  CC=14     ←0
  │ perf_bridge                295L  3C   11m  CC=6      ←2
  │ incremental                291L  2C   17m  CC=8      ←18
  │ __init__                   290L  1C   13m  CC=11     ←0
  │ engine                     290L  6C   12m  CC=10     ←0
  │ refactor                   287L  0C   13m  CC=6      ←1
  │ llx_router                 287L  1C   15m  CC=9      ←2
  │ diff_manager               283L  0C    9m  CC=9      ←0
  │ growth_control             277L  3C   12m  CC=11     ←0
  │ prompts                    277L  0C    3m  CC=9      ←1
  │ python_analyzer            273L  1C    8m  CC=12     ←3
  │ main                       272L  0C   23m  CC=6      ←1
  │ rule_generator             271L  2C   11m  CC=6      ←0
  │ semantic_chunker           270L  2C   11m  CC=11     ←0
  │ scheduler                  264L  2C   16m  CC=9      ←0
  │ github_actions             260L  1C    6m  CC=6      ←0
  │ multi_project              251L  3C   10m  CC=5      ←0
  │ metrics                    249L  1C   11m  CC=7      ←2
  │ pyqual_bridge              249L  0C   12m  CC=11     ←2
  │ redup_bridge               245L  0C    8m  CC=9      ←1
  │ __init__                   235L  4C   18m  CC=8      ←0
  │ cycle                      233L  0C   11m  CC=9      ←1
  │ sandbox                    224L  3C    9m  CC=11     ←0
  │ auto_fix                   220L  1C   13m  CC=8      ←2
  │ doctor_fixers              214L  0C    8m  CC=10     ←0
  │ scan                       213L  1C    9m  CC=8      ←0
  │ __init__                   213L  2C    7m  CC=7      ←0
  │ direct_imports             213L  1C   15m  CC=7      ←0
  │ batch                      212L  0C   12m  CC=7      ←4
  │ history                    210L  3C   13m  CC=11     ←0
  │ quality_visitor            209L  1C   18m  CC=8      ←0
  │ consciousness_loop         204L  1C    7m  CC=5      ←0
  │ git_ops                    204L  0C    7m  CC=6      ←1
  │ body_restorer              203L  0C    7m  CC=11     ←1
  │ planfile_bridge            201L  0C    7m  CC=10     ←0
  │ _indent_fixers             194L  0C   10m  CC=9      ←2
  │ runner                     194L  0C   10m  CC=8      ←1
  │ _guard_fixers              185L  0C    8m  CC=11     ←1
  │ refactor                   183L  0C    9m  CC=7      ←3
  │ code2llm_bridge            178L  0C    5m  CC=5      ←1
  │ timeline_toon              173L  1C   10m  CC=11     ←1
  │ cycle                      172L  0C    5m  CC=7      ←0
  │ orchestrator               170L  2C    5m  CC=8      ←0
  │ timeline_analysis          169L  1C    7m  CC=11     ←1
  │ intent                     167L  0C    7m  CC=8      ←1
  │ git_timeline               165L  1C   23m  CC=5      ←0
  │ doctor_fstring_fixers      161L  0C   11m  CC=10     ←1
  │ _scan_report               158L  0C    8m  CC=10     ←0
  │ badge                      158L  0C    8m  CC=6      ←2
  │ audit                      157L  0C    4m  CC=6      ←2
  │ analyzer                   155L  0C    6m  CC=8      ←1
  │ resolution                 154L  0C    6m  CC=9      ←3
  │ health_model               151L  3C    6m  CC=9      ←0
  │ reporter                   148L  1C    5m  CC=8      ←0
  │ functions_parser           148L  1C    6m  CC=9      ←0
  │ review                     143L  0C    6m  CC=9      ←1
  │ utils                      140L  0C    9m  CC=7      ←4
  │ batch                      139L  0C    7m  CC=4      ←0
  │ reporting                  138L  0C    5m  CC=12     ←1
  │ proactive                  138L  2C    5m  CC=7      ←0
  │ pr_bot                     136L  0C    6m  CC=7      ←2
  │ config                     134L  5C    4m  CC=6      ←18
  │ __init__                   134L  0C    2m  CC=13     ←1
  │ ecosystem                  134L  2C   10m  CC=10     ←0
  │ direct_guard               132L  1C    7m  CC=8      ←0
  │ direct_constants           132L  1C    7m  CC=9      ←0
  │ ast_transformers           131L  2C    9m  CC=8      ←0
  │ direct_types               127L  1C    6m  CC=8      ←0
  │ timeline_git               127L  1C    7m  CC=8      ←1
  │ pipeline                   126L  0C    6m  CC=6      ←1
  │ change_patterns            125L  2C    6m  CC=12     ←0
  │ doctor                     124L  0C    3m  CC=8      ←1
  │ smart_scorer               122L  0C    5m  CC=7      ←0
  │ examples                   121L  0C   13m  CC=4      ←1
  │ self_model                 121L  3C    7m  CC=6      ←0
  │ memory_learning            117L  0C    3m  CC=9      ←2
  │ cli_doctor                 116L  0C    8m  CC=8      ←0
  │ batch                      116L  0C    6m  CC=3      ←1
  │ verdict                    109L  0C    7m  CC=10     ←1
  │ webhook                    109L  0C    3m  CC=4      ←1
  │ timeline_models            107L  3C    3m  CC=3      ←0
  │ adaptive_executor          106L  1C    3m  CC=7      ←0
  │ reflector                  106L  0C    2m  CC=5      ←1
  │ awareness                  101L  0C    6m  CC=6      ←2
  │ resolver                    97L  1C    4m  CC=8      ←1
  │ models                      96L  13C    0m  CC=0.0    ←0
  │ example_routes              95L  0C    4m  CC=7      ←1
  │ _common                     94L  0C    6m  CC=4      ←12
  │ ast_analyzer                88L  1C    2m  CC=7      ←0
  │ config_gen                  87L  0C    4m  CC=4      ←1
  │ __init__                    87L  0C    0m  CC=0.0    ←0
  │ reporter                    86L  0C    4m  CC=9      ←6
  │ cli_awareness               83L  0C    8m  CC=1      ←0
  │ discovery                   81L  0C    7m  CC=7      ←2
  │ __init__                    81L  0C    3m  CC=1      ←0
  │ metrics                     81L  2C    2m  CC=2      ←0
  │ pyqual_example              74L  0C    2m  CC=8      ←2
  │ executor                    74L  0C    0m  CC=0.0    ←0
  │ todo_gen                    72L  0C    3m  CC=8      ←1
  │ analyzer                    71L  1C    8m  CC=1      ←0
  │ __init__                    70L  0C    2m  CC=1      ←0
  │ sandbox_execution           69L  0C    1m  CC=4      ←1
  │ custom_rules                68L  0C    3m  CC=6      ←2
  │ full_pipeline               67L  0C    2m  CC=4      ←2
  │ __init__                    65L  0C    0m  CC=0.0    ←0
  │ __init__                    64L  0C    0m  CC=0.0    ←0
  │ direct                      63L  1C    6m  CC=1      ←0
  │ models                      62L  1C    0m  CC=0.0    ←0
  │ mypy_analyzer               61L  1C    2m  CC=7      ←0
  │ debug                       60L  0C    5m  CC=3      ←1
  │ hybrid                      57L  0C    1m  CC=7      ←2
  │ validation                  57L  0C    2m  CC=6      ←1
  │ duplication_parser          57L  1C    1m  CC=12     ←0
  │ runner                      56L  0C    2m  CC=6      ←0
  │ debug_routes                56L  0C    1m  CC=1      ←1
  │ __init__                    55L  0C    0m  CC=0.0    ←0
  │ basic_analysis              54L  0C    2m  CC=3      ←2
  │ ruff_analyzer               49L  1C    1m  CC=10     ←0
  │ models                      49L  3C    0m  CC=0.0    ←0
  │ logging                     48L  0C    1m  CC=6      ←3
  │ bandit_analyzer             47L  1C    1m  CC=9      ←0
  │ models                      46L  6C    0m  CC=0.0    ←0
  │ utils                       45L  0C    2m  CC=3      ←0
  │ doctor_data                 41L  2C    1m  CC=2      ←0
  │ api_integration             41L  0C    2m  CC=2      ←2
  │ scan                        41L  0C    2m  CC=6      ←0
  │ __init__                    41L  0C    0m  CC=0.0    ←0
  │ doctor_helpers              40L  0C    2m  CC=5      ←1
  │ reporter                    40L  0C    3m  CC=4      ←1
  │ validation_parser           40L  1C    1m  CC=12     ←0
  │ __init__                    38L  0C    0m  CC=0.0    ←0
  │ debug                       36L  0C    1m  CC=6      ←0
  │ pyqual                      35L  0C    4m  CC=1      ←1
  │ pyqual_routes               33L  0C    1m  CC=1      ←1
  │ __init__                    33L  0C    0m  CC=0.0    ←0
  │ doctor_indent_fixers        31L  0C    0m  CC=0.0    ←0
  │ models                      30L  1C    0m  CC=0.0    ←0
  │ __init__                    30L  0C    0m  CC=0.0    ←0
  │ __init__                    29L  1C    0m  CC=0.0    ←0
  │ __init__                    28L  0C    0m  CC=0.0    ←0
  │ discovery                   26L  0C    2m  CC=5      ←0
  │ __init__                    22L  0C    0m  CC=0.0    ←0
  │ health_routes               20L  0C    1m  CC=1      ←1
  │ helpers                     17L  0C    2m  CC=1      ←2
  │ __init__                    17L  0C    0m  CC=0.0    ←0
  │ webhook_routes              16L  0C    1m  CC=1      ←1
  │ __init__                    15L  0C    0m  CC=0.0    ←0
  │ __init__                    15L  0C    0m  CC=0.0    ←0
  │ core                        14L  0C    1m  CC=1      ←2
  │ __main__                     6L  0C    0m  CC=0.0    ←0
  │ __main__                     1L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │
  test_sample_project/            CC̄=2.3    ←in:0  →out:0
  │ sample                      32L  0C    3m  CC=4      ←0
  │
  .goal/                          CC̄=2.0    ←in:0  →out:0
  │ pre-commit-hook             23L  0C    1m  CC=2      ←0
  │ vallm-pre-commit.sh         17L  0C    0m  CC=0.0    ←0
  │
  examples/                       CC̄=1.9    ←in:0  →out:0
  │ 00_orders__service          88L  0C    6m  CC=6      ←0
  │ main                        32L  0C    1m  CC=1      ←0
  │ main                        30L  0C    1m  CC=1      ←0
  │ main                        29L  0C    1m  CC=1      ←0
  │ main                        27L  0C    1m  CC=1      ←0
  │ main                        27L  0C    1m  CC=1      ←0
  │ main                        27L  0C    1m  CC=1      ←0
  │ main                        26L  0C    1m  CC=1      ←0
  │ main                        25L  0C    1m  CC=1      ←0
  │ main                        25L  0C    1m  CC=1      ←0
  │ main                        25L  0C    1m  CC=1      ←0
  │
  refactor_output/                CC̄=1.4    ←in:0  →out:0
  │ 00_app__models              29L  0C    5m  CC=3      ←0
  │
  app/                            CC̄=0.0    ←in:0  →out:0
  │ models                      48L  3C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ project.sh                  35L  0C    0m  CC=0.0    ←0
  │

COUPLING:
                                  redsl.commands                   redsl          redsl.autonomy         redsl.analyzers         redsl.execution          redsl.examples               redsl.cli               redsl.api        redsl.validation  archive.legacy_scripts        redsl.formatters         redsl.refactors               redsl.llm       redsl.diagnostics      redsl.integrations
          redsl.commands                      ──                       2                      13                       6                       3                                                                                               7                       6                       2                       1                                                                          hub
                   redsl                      ←2                      ──                      ←6                                               4                      ←1                       5                       6                      ←1                      ←3                                                                       2                       2                      ←1  hub
          redsl.autonomy                       7                       6                      ──                       8                       3                                              ←1                                                                                                                                                                                                  hub
         redsl.analyzers                      ←6                                              ←8                      ──                      ←3                      ←1                                                                      ←1                      ←1                                              ←5                                                                          hub
         redsl.execution                      ←3                      ←4                      ←3                       3                      ──                      ←1                      ←1                      ←3                       3                       1                                               1                       4                                                  hub
          redsl.examples                                               1                                               1                       1                      ──                     ←11                      ←2                                                                                                                                                                          hub
               redsl.cli                                               2                       1                                               1                      11                      ──                                                                                               3                                                                       1                          hub
               redsl.api                                               3                                                                       3                       2                                              ──                                                                       6                                                                                               1  hub
        redsl.validation                      ←7                       1                                               1                      ←3                                                                                              ──                                                                      ←3                                                                          hub
  archive.legacy_scripts                      ←6                       3                                               1                      ←1                                                                                                                      ──                                                                                                                          hub
        redsl.formatters                      ←2                                                                                                                                              ←3                      ←6                                                                      ──                                                                                                  hub
         redsl.refactors                      ←1                                                                       5                      ←1                                                                                               3                                                                      ──                                                                          !! fan-out
               redsl.llm                                              ←2                                                                      ←4                                                                                                                                                                                              ──                                                  hub
       redsl.diagnostics                                              ←2                                                                                                                      ←1                                                                                                                                                                      ──                        
      redsl.integrations                                               1                                                                                                                                              ←1                                                                                                                                                                      ──
  CYCLES: none
  HUB: redsl.validation/ (fan-in=13)
  HUB: redsl.formatters/ (fan-in=11)
  HUB: redsl.autonomy/ (fan-in=14)
  HUB: redsl/ (fan-in=19)
  HUB: redsl.commands/ (fan-in=7)
  HUB: redsl.api/ (fan-in=6)
  HUB: redsl.examples/ (fan-in=23)
  HUB: redsl.execution/ (fan-in=15)
  HUB: redsl.llm/ (fan-in=6)
  HUB: archive.legacy_scripts/ (fan-in=7)
  HUB: redsl.cli/ (fan-in=5)
  HUB: redsl.analyzers/ (fan-in=27)
  SMELL: redsl.autonomy/ fan-out=24 → split needed
  SMELL: redsl/ fan-out=19 → split needed
  SMELL: redsl.commands/ fan-out=40 → split needed
  SMELL: redsl.api/ fan-out=15 → split needed
  SMELL: redsl.execution/ fan-out=12 → split needed
  SMELL: redsl.refactors/ fan-out=8 → split needed
  SMELL: redsl.cli/ fan-out=19 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 25 groups | 188f 25832L | 2026-04-19

SUMMARY:
  files_scanned: 188
  total_lines:   25832
  dup_groups:    25
  dup_fragments: 76
  saved_lines:   297
  scan_ms:       6291

DUPLICATES[25] (ranked by impact):
  [bf09142e1f461c0a] ! STRU  example_basic_analysis  L=4 N=9 saved=32 sim=1.00
      redsl/cli/examples.py:19-22  (example_basic_analysis)
      redsl/cli/examples.py:28-31  (example_custom_rules)
      redsl/cli/examples.py:47-50  (example_memory_learning)
      redsl/cli/examples.py:56-59  (example_api_integration)
      redsl/cli/examples.py:65-68  (example_awareness)
      redsl/cli/examples.py:74-77  (example_pyqual)
      redsl/cli/examples.py:83-86  (example_audit)
      redsl/cli/examples.py:92-95  (example_pr_bot)
      redsl/cli/examples.py:101-104  (example_badge)
  [88cd2d34ab2799c8]   STRU  _metrun_available  L=10 N=4 saved=30 sim=1.00
      redsl/diagnostics/perf_bridge.py:50-59  (_metrun_available)
      redsl/llm/llx_router.py:147-152  (_llx_available)
      redsl/validation/sandbox.py:37-46  (_docker_available)
      redsl/validation/sandbox.py:49-58  (_pactfix_available)
  [3827f031a50510f3]   STRU  main  L=3 N=9 saved=24 sim=1.00
      redsl/examples/api_integration.py:35-37  (main)
      redsl/examples/audit.py:151-153  (main)
      redsl/examples/awareness.py:95-97  (main)
      redsl/examples/badge.py:152-154  (main)
      redsl/examples/basic_analysis.py:48-50  (main)
      redsl/examples/custom_rules.py:62-64  (main)
      redsl/examples/memory_learning.py:111-113  (main)
      redsl/examples/pr_bot.py:130-132  (main)
      redsl/examples/pyqual_example.py:68-70  (main)
  [3b031ed301b05772]   STRU  _process_single_project  L=21 N=2 saved=21 sim=1.00
      archive/legacy_scripts/hybrid_quality_refactor.py:145-165  (_process_single_project)
      redsl/commands/hybrid.py:263-283  (_process_single_project)
  [e4ebf1a748620d64]   STRU  fix_stolen_indent  L=19 N=2 saved=19 sim=1.00
      redsl/commands/doctor_fixers.py:37-55  (fix_stolen_indent)
      redsl/commands/doctor_fixers.py:57-75  (fix_broken_fstrings)
  [56e9b1820f8f85b6]   STRU  is_available  L=19 N=2 saved=19 sim=1.00
      redsl/validation/regix_bridge.py:32-50  (is_available)
      redsl/validation/vallm_bridge.py:137-148  (is_available)
  [5e00de8bc3caf754]   STRU  _collect_guard_body  L=14 N=2 saved=14 sim=1.00
      redsl/commands/_guard_fixers.py:156-169  (_collect_guard_body)
      redsl/refactors/body_restorer.py:45-59  (_collect_guard_body)
  [f610b9ef4ffea9ff]   EXAC  measure_todo_reduction  L=13 N=2 saved=13 sim=1.00
      archive/legacy_scripts/batch_refactor_semcod.py:39-51  (measure_todo_reduction)
      redsl/commands/batch.py:117-129  (measure_todo_reduction)
  [a9d676c1f7ed34bb]   EXAC  _count_todo_issues  L=6 N=3 saved=12 sim=1.00
      archive/legacy_scripts/hybrid_llm_refactor.py:254-259  (_count_todo_issues)
      archive/legacy_scripts/hybrid_quality_refactor.py:130-135  (_count_todo_issues)
      redsl/commands/hybrid.py:32-37  (_count_todo_issues)
  [000e491efa874bd5]   EXAC  _read_source  L=6 N=3 saved=12 sim=1.00
      redsl/commands/_guard_fixers.py:148-153  (_read_source)
      redsl/commands/_indent_fixers.py:189-194  (_read_source)
      redsl/commands/doctor_fstring_fixers.py:12-16  (_read_source)
  [7704739271167e72]   STRU  is_available  L=3 N=5 saved=12 sim=1.00
      redsl/analyzers/code2llm_bridge.py:40-42  (is_available)
      redsl/analyzers/radon_analyzer.py:25-27  (is_radon_available)
      redsl/analyzers/redup_bridge.py:32-34  (is_available)
      redsl/commands/batch_pyqual/config_gen.py:64-66  (_pyqual_cli_available)
      redsl/commands/batch_pyqual/runner.py:46-48  (_pyqual_cli_available)
  [9bee6edbdc9eaad9]   EXAC  _run_cmd  L=5 N=3 saved=10 sim=1.00
      redsl/commands/batch_pyqual/config_gen.py:10-14  (_run_cmd)
      redsl/commands/batch_pyqual/discovery.py:68-72  (_run_cmd)
      redsl/commands/batch_pyqual/runner.py:14-18  (_run_cmd)
  [b027db1c8d821268]   STRU  _register_history_command  L=10 N=2 saved=10 sim=1.00
      redsl/commands/cli_awareness.py:22-31  (_register_history_command)
      redsl/commands/cli_awareness.py:44-53  (_register_health_command)
  [59ffcfccc57a16ff]   EXAC  get_applied_changes  L=3 N=4 saved=9 sim=1.00
      redsl/refactors/direct_constants.py:127-129  (get_applied_changes)
      redsl/refactors/direct_guard.py:127-129  (get_applied_changes)
      redsl/refactors/direct_imports.py:208-210  (get_applied_changes)
      redsl/refactors/direct_types.py:122-124  (get_applied_changes)
  [fc60c7a33bd63661]   STRU  _count_passed  L=3 N=4 saved=9 sim=1.00
      redsl/commands/batch_pyqual/reporting.py:12-14  (_count_passed)
      redsl/commands/batch_pyqual/reporting.py:17-19  (_count_failed)
      redsl/commands/batch_pyqual/reporting.py:22-24  (_count_ready)
      redsl/commands/batch_pyqual/reporting.py:27-29  (_count_skipped)
  [828e958c9979cd9c]   EXAC  _extract_json  L=8 N=2 saved=8 sim=1.00
      redsl/analyzers/redup_bridge.py:228-235  (_extract_json)
      redsl/validation/vallm_bridge.py:36-43  (_extract_json)
  [d87e95474146674c]   EXAC  _find_projects  L=7 N=2 saved=7 sim=1.00
      archive/legacy_scripts/hybrid_quality_refactor.py:121-127  (_find_projects)
      redsl/commands/hybrid.py:254-260  (_find_projects)
  [77e67270f2ef5b1d]   EXAC  _git_status_lines  L=7 N=2 saved=7 sim=1.00
      redsl/commands/batch_pyqual/discovery.py:75-81  (_git_status_lines)
      redsl/commands/batch_pyqual/runner.py:21-27  (_git_status_lines)
  [bed9eb7cdc5758b5]   EXAC  _resolve_profile  L=7 N=2 saved=7 sim=1.00
      redsl/commands/batch_pyqual/pipeline.py:25-31  (_resolve_profile)
      redsl/commands/batch_pyqual/runner.py:37-43  (_resolve_profile)
  [153b17ca419ad0e4]   EXAC  _regenerate_todo  L=5 N=2 saved=5 sim=1.00
      archive/legacy_scripts/hybrid_llm_refactor.py:262-266  (_regenerate_todo)
      archive/legacy_scripts/hybrid_quality_refactor.py:138-142  (_regenerate_todo)
  [42758e6f93d15e46]   STRU  _check_analysis_passed  L=5 N=2 saved=5 sim=1.00
      redsl/commands/batch_pyqual/verdict.py:8-12  (_check_analysis_passed)
      redsl/commands/batch_pyqual/verdict.py:15-19  (_check_gates_passed)
  [77d5f2d33a9f8d05]   STRU  _extract_file_path  L=3 N=2 saved=3 sim=1.00
      redsl/autonomy/auto_fix.py:65-67  (_extract_file_path)
      redsl/autonomy/auto_fix.py:70-72  (_extract_function_name)
  [3e72ce8df48766bc]   STRU  batch_hybrid  L=3 N=2 saved=3 sim=1.00
      redsl/cli/batch.py:50-52  (batch_hybrid)
      redsl/cli/pyqual.py:29-31  (pyqual_fix)
  [4e0c5433bfda0d64]   STRU  _dispatch_analyze  L=3 N=2 saved=3 sim=1.00
      redsl/main.py:214-216  (_dispatch_analyze)
      redsl/main.py:219-221  (_dispatch_explain)
  [ad5eba30a9b3ea60]   STRU  process_data  L=3 N=2 saved=3 sim=1.00
      refactor_output/refactor_extract_functions_20260407_143102/00_app__models.py:12-14  (process_data)
      refactor_output/refactor_extract_functions_20260407_143102/00_app__models.py:17-19  (validate_data)

REFACTOR[25] (ranked by priority):
  [1] ○ extract_function   → redsl/cli/utils/example_basic_analysis.py
      WHY: 9 occurrences of 4-line block across 1 files — saves 32 lines
      FILES: redsl/cli/examples.py
  [2] ○ extract_function   → redsl/utils/_metrun_available.py
      WHY: 4 occurrences of 10-line block across 3 files — saves 30 lines
      FILES: redsl/diagnostics/perf_bridge.py, redsl/llm/llx_router.py, redsl/validation/sandbox.py
  [3] ○ extract_function   → redsl/examples/utils/main.py
      WHY: 9 occurrences of 3-line block across 9 files — saves 24 lines
      FILES: redsl/examples/api_integration.py, redsl/examples/audit.py, redsl/examples/awareness.py, redsl/examples/badge.py, redsl/examples/basic_analysis.py +4 more
  [4] ○ extract_function   → utils/_process_single_project.py
      WHY: 2 occurrences of 21-line block across 2 files — saves 21 lines
      FILES: archive/legacy_scripts/hybrid_quality_refactor.py, redsl/commands/hybrid.py
  [5] ○ extract_function   → redsl/commands/utils/fix_stolen_indent.py
      WHY: 2 occurrences of 19-line block across 1 files — saves 19 lines
      FILES: redsl/commands/doctor_fixers.py
  [6] ○ extract_function   → redsl/validation/utils/is_available.py
      WHY: 2 occurrences of 19-line block across 2 files — saves 19 lines
      FILES: redsl/validation/regix_bridge.py, redsl/validation/vallm_bridge.py
  [7] ○ extract_function   → redsl/utils/_collect_guard_body.py
      WHY: 2 occurrences of 14-line block across 2 files — saves 14 lines
      FILES: redsl/commands/_guard_fixers.py, redsl/refactors/body_restorer.py
  [8] ○ extract_function   → utils/measure_todo_reduction.py
      WHY: 2 occurrences of 13-line block across 2 files — saves 13 lines
      FILES: archive/legacy_scripts/batch_refactor_semcod.py, redsl/commands/batch.py
  [9] ○ extract_function   → utils/_count_todo_issues.py
      WHY: 3 occurrences of 6-line block across 3 files — saves 12 lines
      FILES: archive/legacy_scripts/hybrid_llm_refactor.py, archive/legacy_scripts/hybrid_quality_refactor.py, redsl/commands/hybrid.py
  [10] ○ extract_function   → redsl/commands/utils/_read_source.py
      WHY: 3 occurrences of 6-line block across 3 files — saves 12 lines
      FILES: redsl/commands/_guard_fixers.py, redsl/commands/_indent_fixers.py, redsl/commands/doctor_fstring_fixers.py
  [11] ○ extract_function   → redsl/utils/is_available.py
      WHY: 5 occurrences of 3-line block across 5 files — saves 12 lines
      FILES: redsl/analyzers/code2llm_bridge.py, redsl/analyzers/radon_analyzer.py, redsl/analyzers/redup_bridge.py, redsl/commands/batch_pyqual/config_gen.py, redsl/commands/batch_pyqual/runner.py
  [12] ○ extract_function   → redsl/commands/batch_pyqual/utils/_run_cmd.py
      WHY: 3 occurrences of 5-line block across 3 files — saves 10 lines
      FILES: redsl/commands/batch_pyqual/config_gen.py, redsl/commands/batch_pyqual/discovery.py, redsl/commands/batch_pyqual/runner.py
  [13] ○ extract_function   → redsl/commands/utils/_register_history_command.py
      WHY: 2 occurrences of 10-line block across 1 files — saves 10 lines
      FILES: redsl/commands/cli_awareness.py
  [14] ○ extract_function   → redsl/refactors/utils/get_applied_changes.py
      WHY: 4 occurrences of 3-line block across 4 files — saves 9 lines
      FILES: redsl/refactors/direct_constants.py, redsl/refactors/direct_guard.py, redsl/refactors/direct_imports.py, redsl/refactors/direct_types.py
  [15] ○ extract_function   → redsl/commands/batch_pyqual/utils/_count_passed.py
      WHY: 4 occurrences of 3-line block across 1 files — saves 9 lines
      FILES: redsl/commands/batch_pyqual/reporting.py
  [16] ○ extract_function   → redsl/utils/_extract_json.py
      WHY: 2 occurrences of 8-line block across 2 files — saves 8 lines
      FILES: redsl/analyzers/redup_bridge.py, redsl/validation/vallm_bridge.py
  [17] ○ extract_function   → utils/_find_projects.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: archive/legacy_scripts/hybrid_quality_refactor.py, redsl/commands/hybrid.py
  [18] ○ extract_function   → redsl/commands/batch_pyqual/utils/_git_status_lines.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: redsl/commands/batch_pyqual/discovery.py, redsl/commands/batch_pyqual/runner.py
  [19] ○ extract_function   → redsl/commands/batch_pyqual/utils/_resolve_profile.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: redsl/commands/batch_pyqual/pipeline.py, redsl/commands/batch_pyqual/runner.py
  [20] ○ extract_function   → archive/legacy_scripts/utils/_regenerate_todo.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: archive/legacy_scripts/hybrid_llm_refactor.py, archive/legacy_scripts/hybrid_quality_refactor.py
  [21] ○ extract_function   → redsl/commands/batch_pyqual/utils/_check_analysis_passed.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: redsl/commands/batch_pyqual/verdict.py
  [22] ○ extract_function   → redsl/autonomy/utils/_extract_file_path.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: redsl/autonomy/auto_fix.py
  [23] ○ extract_function   → redsl/cli/utils/batch_hybrid.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: redsl/cli/batch.py, redsl/cli/pyqual.py
  [24] ○ extract_function   → redsl/utils/_dispatch_analyze.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: redsl/main.py
  [25] ○ extract_function   → refactor_output/refactor_extract_functions_20260407_143102/utils/process_data.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: refactor_output/refactor_extract_functions_20260407_143102/00_app__models.py

METRICS-TARGET:
  dup_groups:  25 → 0
  saved_lines: 297 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 1066 func | 144f | 2026-04-19

NEXT[0]: no refactoring needed

RISKS[0]: none

METRICS-TARGET:
  CC̄:          3.8 → ≤2.7
  max-CC:      14 → ≤7
  god-modules: 0 → 0
  high-CC(≥15): 0 → ≤0
  hub-types:   0 → ≤0

PATTERNS (language parser shared logic):
  _extract_declarations() in base.py — unified extraction for:
    - TypeScript: interfaces, types, classes, functions, arrow funcs
    - PHP: namespaces, traits, classes, functions, includes
    - Ruby: modules, classes, methods, requires
    - C++: classes, structs, functions, #includes
    - C#: classes, interfaces, methods, usings
    - Java: classes, interfaces, methods, imports
    - Go: packages, functions, structs
    - Rust: modules, functions, traits, use statements

  Shared regex patterns per language:
    - import: language-specific import/require/using patterns
    - class: class/struct/trait declarations with inheritance
    - function: function/method signatures with visibility
    - brace_tracking: for C-family languages ({ })
    - end_keyword_tracking: for Ruby (module/class/def...end)

  Benefits:
    - Consistent extraction logic across all languages
    - Reduced code duplication (~70% reduction in parser LOC)
    - Easier maintenance: fix once, apply everywhere
    - Standardized FunctionInfo/ClassInfo models

HISTORY:
  prev CC̄=3.8 → now CC̄=3.8
```

### Validation (`project/validation.toon.yaml`)

```toon markpact:analysis path=project/validation.toon.yaml
# vallm batch | 302f | 226✓ 0⚠ 0✗ | 2026-04-19

SUMMARY:
  scanned: 302  passed: 226 (74.8%)  warnings: 0  errors: 0  unsupported: 76

UNSUPPORTED[5]{bucket,count}:
  *.md,55
  Dockerfile*,1
  *.txt,3
  *.yml,2
  other,15
```

## Intent

ReDSL — Refactor + DSL + Self-Learning. LLM-powered autonomous code refactoring.
